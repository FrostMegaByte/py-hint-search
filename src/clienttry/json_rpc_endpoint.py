import json
import re
import threading
import attrs
from lsprotocol import converters
from lsprotocol.types import InitializedParams
import jsonrpc


class MyEncoder(json.JSONEncoder):
    """
    Encodes an object in JSON
    """

    def default(self, o):
        return o.__dict__


class JsonRpcEndpoint(object):
    def __init__(self, stdin, stdout):
        self.stdin = stdin
        self.stdout = stdout
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

    @staticmethod
    def _add_header(json_string):
        JSON_RPC_REQ_FORMAT = "Content-Length: {json_string_len}\r\n\r\n{json_string}"
        return JSON_RPC_REQ_FORMAT.format(
            json_string_len=len(json_string), json_string=json_string
        )

    # def send_message(self, message):
    #     json_string = json.dumps(message, cls=MyEncoder)
    #     print("SENDING:", json_string)
    #     jsonrpc_req = self.__add_header(json_string)
    #     with self.write_lock:
    #         self.stdin.write(jsonrpc_req.encode())
    #         self.stdin.flush()

    def write_message(self, method, params=None, id=None):
        converter = converters.get_converter()
        # params_dict = converter.unstructure(params)
        message = {"jsonrpc": "2.0", "method": method}
        if id is not None:
            message["id"] = id
        if params is not None:
            message["params"] = converter.unstructure_attrs_asdict(
                params
            )  # attrs.asdict(params)

        json_string_message = json.dumps(message)
        print("SENDING:", json_string_message)
        jsonrpc_message = JsonRpcEndpoint._add_header(json_string_message)
        with self.write_lock:
            self.stdin.write(jsonrpc_message.encode())
            self.stdin.flush()

    def read_response(self):
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


# class MyEncoder(json.JSONEncoder):
#     """
#     Encodes an object in JSON
#     """

#     def default(self, o):
#         return o.__dict__


# class JsonRpcEndpoint(threading.Thread):
#     def _send_rpc_message(self, method, params=None, id=None):
#         if not id:
#             current_id = self.next_id
#             self.next_id += 1

#         converter = converters.get_converter()
#         params_dict = converter.unstructure(params)
#         # params2 = attrs.asdict(params)

#         message = {
#             "jsonrpc": "2.0",
#             "id": current_id,
#             "method": method,
#             "params": params_dict or {},
#         }
#         json_string_message = json.dumps(message)
#         print("SENDING:", json_string_message)
#         jsonrpc_message = JsonRpcEndpoint._add_header(json_string_message)
#         with self.write_lock:
#             self.stdin.write(jsonrpc_message.encode())
#             self.stdin.flush()

#     def send_rpc_request(self, method, params=None):
#         current_id = self.next_id
#         self.next_id += 1
#         cond = threading.Condition()
#         self.event_dict[current_id] = cond
#         cond.acquire()
#         self._send_rpc_message(method, params, current_id)
#         cond.wait()
#         cond.release()
#         # TODO: check if error, and throw an exception
#         response = self.response_dict[current_id]
#         return response["result"]

#     def send_rpc_notification(self, method, params=None):
#         self._send_rpc_message(method, params)

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
