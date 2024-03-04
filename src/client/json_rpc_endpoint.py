from __future__ import print_function
import json
import re
import threading
from typing import IO

JSON_RPC_REQ_FORMAT = "Content-Length: {json_string_len}\r\n\r\n{json_string}"
JSON_RPC_RES_REGEX = "Content-Length: ([0-9]*)\r\n"


class MyEncoder(json.JSONEncoder):
    """
    Encodes an object in JSON
    """

    def default(self, o):
        return o.__dict__


class JsonRpcEndpoint(object):
    """
    Thread safe JSON RPC endpoint implementation. Responsible to recieve and send JSON RPC messages, as described in the
    protocol. More information can be found: https://www.jsonrpc.org/
    """

    def __init__(self, stdin: IO[bytes], stdout: IO[bytes]) -> None:
        self.stdin = stdin
        self.stdout = stdout
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

    @staticmethod
    def _add_header(json_string: str) -> str:
        return JSON_RPC_REQ_FORMAT.format(
            json_string_len=len(json_string),
            json_string=json_string,
        )

    def write_message(self, message):
        json_string = json.dumps(message, cls=MyEncoder)
        # print("\nSENDING:", json_string)
        jsonrpc_req = self._add_header(json_string)
        with self.write_lock:
            self.stdin.write(jsonrpc_req.encode())
            self.stdin.flush()

    def read_response(self):
        with self.read_lock:
            line = self.stdout.readline()
            if not line:
                return None
            line = line.decode()
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
