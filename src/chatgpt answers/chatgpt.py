import os
import subprocess
import json
import threading
import queue

from pylspclient import lsp_structs
from pylspclient import lsp_client
from pylspclient import rpc


class LSPClient:
    def __init__(self):
        self.server_process = None
        self.server_stdin = None
        self.server_stdout = None
        self.response_queue = queue.Queue()

    def start_server(self):
        # Replace this with the command to start your LSP server
        server_command = ["path/to/your/language-server-binary", "--stdio"]

        self.server_process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            universal_newlines=True,
            shell=False,
        )

        self.server_stdin = self.server_process.stdin
        self.server_stdout = self.server_process.stdout

        # Start a thread to read responses from the server
        threading.Thread(target=self._read_responses).start()

    def stop_server(self):
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()

    def _read_responses(self):
        while True:
            response = self.server_stdout.readline()
            if not response:
                break
            response_dict = json.loads(response)
            self.response_queue.put(response_dict)

    def send_request(self, request):
        request_str = json.dumps(request)
        self.server_stdin.write(request_str + "\n")
        self.server_stdin.flush()

    def wait_for_response(self, request_id):
        while True:
            response_dict = self.response_queue.get()
            if (
                "id" in response_dict
                and response_dict["id"] == request_id
                and "result" in response_dict
            ):
                return response_dict["result"]


if __name__ == "__main__":
    lsp_client = LSPClient()
    lsp_client.start_server()

    initialize_request = lsp_structs.InitializeParams()
    lsp_client.send_request(
        rpc.request(
            "initialize",
            initialize_request,
            request_id="1",
        )
    )

    response = lsp_client.wait_for_response("1")
    print("Initialize response:", response)

    # You can send other LSP requests and handle their responses here

    lsp_client.stop_server()
