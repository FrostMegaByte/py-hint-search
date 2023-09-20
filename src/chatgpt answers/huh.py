import os
import subprocess
import json
from pygls import LanguageClient, lsp

# Define the path to the language server executable.
# Replace 'python-language-server' with the actual path to your language server.
language_server_path = "/path/to/python-language-server"

# Define the command to launch the language server.
command = [language_server_path]

# Start the language server as a subprocess.
language_server = subprocess.Popen(
    command,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
    bufsize=1,  # Line buffered
)

# Create an instance of LanguageClient using stdio.
client = LanguageClient()


# Define a function to send messages to the language server.
def send_to_server(message):
    language_server.stdin.write(json.dumps(message) + "\n")
    language_server.stdin.flush()


# Define a function to receive messages from the language server.
def receive_from_server():
    while True:
        line = language_server.stdout.readline()
        if not line:
            break
        message = json.loads(line)
        client._handle_response(message)  # Handle the response.


# Start receiving messages from the language server in a separate thread.
import threading

thread = threading.Thread(target=receive_from_server)
thread.daemon = True
thread.start()

# Initialize the client and send the 'initialize' message.
initialize_params = {
    "processId": os.getpid(),
    "rootUri": "file:///path/to/your/project",
    "capabilities": {},
}
send_to_server(lsp.Initialize(params=initialize_params))

# Send the 'initialized' notification.
send_to_server(lsp.Initialized())

# Send any other LSP messages as needed.

# Example: Send a 'textDocument/didOpen' notification.
did_open_params = {
    "textDocument": {
        "uri": "file:///path/to/your/file.py",
        "languageId": "python",
        "version": 1,
        "text": "Hello, LSP!",
    }
}
send_to_server(lsp.DidOpenTextDocument(params=did_open_params))

# You can continue to send and receive LSP messages as needed.

# Example: Send a 'textDocument/completion' request.
completion_params = {
    "textDocument": {
        "uri": "file:///path/to/your/file.py",
    },
    "position": {
        "line": 0,
        "character": 0,
    },
}
request_id = client._next_request_id()
send_to_server(lsp.Completion(params=completion_params, request_id=request_id))

# Clean up and exit when done.
client._shutdown()
send_to_server(lsp.Exit())
language_server.stdin.close()
language_server.wait()
