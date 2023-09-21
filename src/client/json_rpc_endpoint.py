import json
import re
import threading
import attrs
from lsprotocol import converters
import jsonrpc


# class MyEncoder(json.JSONEncoder):
#     """
#     Encodes an object in JSON
#     """

#     def default(self, o):
#         return o.__dict__


class JsonRpcEndpoint(threading.Thread):
    def __init__(self, stdin, stdout, default_callback=print, callbacks={}):
        threading.Thread.__init__(self)
        self.stdin = stdin
        self.stdout = stdout
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

        self.default_callback = default_callback
        self.callbacks = callbacks
        self.event_dict = {}
        self.response_dict = {}
        self.next_id = 0
        self.shutdown_flag = False

    @staticmethod
    def _add_header(json_string):
        JSON_RPC_REQ_FORMAT = "Content-Length: {json_string_len}\r\n\r\n{json_string}"
        return JSON_RPC_REQ_FORMAT.format(
            json_string_len=len(json_string), json_string=json_string
        )

    def _send_rpc_message(self, method, params=None, id=None):
        if not id:
            current_id = self.next_id
            self.next_id += 1

        converter = converters.get_converter()
        params_dict = converter.unstructure(params)
        # params2 = attrs.asdict(params)

        message = {
            "jsonrpc": "2.0",
            "id": current_id,
            "method": method,
            "params": params_dict or {},
        }
        json_string_message = json.dumps(message)
        print("SENDING:", json_string_message)
        jsonrpc_message = JsonRpcEndpoint._add_header(json_string_message)
        with self.write_lock:
            self.stdin.write(jsonrpc_message.encode())
            self.stdin.flush()

    def send_rpc_request(self, method, params=None):
        current_id = self.next_id
        self.next_id += 1
        cond = threading.Condition()
        self.event_dict[current_id] = cond
        cond.acquire()
        self._send_rpc_message(method, params, current_id)
        cond.wait()
        cond.release()
        # TODO: check if error, and throw an exception
        response = self.response_dict[current_id]
        return response["result"]

    def send_rpc_notification(self, method, params=None):
        self._send_rpc_message(method, params)

    # def send_rpc_result(self, method, result=None):
    #     current_id = self.next_id
    #     self.next_id += 1
    #     request = {
    #         "jsonrpc": "2.0",
    #         "id": current_id,
    #         "method": method,
    #         "result": result or {},
    #     }
    #     jsonrpc_req = self._add_header(request)
    #     with self.write_lock:
    #         self.stdin.write(jsonrpc_req.encode())
    #         self.stdin.flush()

    def receive_response(self):
        JSON_RPC_RES_REGEX = "Content-Length: ([0-9]*)\r\n"
        with self.read_lock:
            line = self.stdout.readline()
            if not line:
                return None
            line = line.decode()
            print("\n" + line)
            match = re.match(JSON_RPC_RES_REGEX, line)
            if match is None or not match.groups():
                raise RuntimeError("Bad header: " + line)
            size = int(match.groups()[0])
            line = self.stdout.readline()
            if not line:
                return None
            line = line.decode()
            if line != "\r\n":
                raise RuntimeError("Bad header: missing newline")
            jsonrpc_res = self.stdout.read(size)
            return json.loads(jsonrpc_res)

    def stop(self):
        self.shutdown_flag = True

    def handle_result(self, jsonrpc_res):
        self.response_dict[jsonrpc_res["id"]] = jsonrpc_res
        cond = self.event_dict[jsonrpc_res["id"]]
        cond.acquire()
        cond.notify()
        cond.release()

    def run(self):
        while not self.shutdown_flag:
            jsonrpc_response = self.receive_response()

            if jsonrpc_response is None:
                print("Server quit")
                break

            print("RECIEVED MESSAGE:", jsonrpc_response)
            if "result" in jsonrpc_response or "error" in jsonrpc_response:
                self.handle_result(jsonrpc_response)
            elif "method" in jsonrpc_response:
                if jsonrpc_response["method"] in self.callbacks:
                    self.callbacks[jsonrpc_response["method"]](jsonrpc_response)
                else:
                    self.default_callback(jsonrpc_response)
            else:
                print("Unknown jsonrpc message")
