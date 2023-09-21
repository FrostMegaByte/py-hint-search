from client.lsp_endpoint import LspEndpoint
from lsprotocol import converters
from lsprotocol.types import (
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    InitializeParams,
)


class LspClient(object):
    def __init__(self, lsp_endpoint: LspEndpoint):
        self.lsp_endpoint = lsp_endpoint
        self.converter = converters.get_converter()

    def send_request(self, method, params=None):
        self.lsp_endpoint.send_request(method, params)

    def send_notification(self, method, params=None):
        self.lsp_endpoint.send_notification(method, params)

    def send_result(self, method, result=None):
        self.lsp_endpoint.send_result(method, result)

    # --- Standard LSP methods ---
    def initialize(self, params):
        self.lsp_endpoint.start()
        return self.send_request(
            "initialize", self.converter.unstructure(params, InitializeParams)
        )

    def initialized(self):
        self.send_notification("initialized", {})

    def register(self):
        return self.send_notification("client/registerCapability")

    def didOpen(self, params):
        return self.send_notification(
            "textDocument/didOpen",
            self.converter.unstructure(params, DidOpenTextDocumentParams),
        )

    def didChange(self, params):
        return self.send_notification(
            "textDocument/didChange",
            self.converter.unstructure(params, DidChangeTextDocumentParams),
        )

    def shutdown(self):
        self.lsp_endpoint.stop()
        return self.send_request("shutdown")

    def exit(self):
        self.send_notification("exit")

    def didChangeConfiguration(self):
        self.send_notification(
            "workspace/didChangeConfiguration",
            {
                "settings": {
                    "python": {
                        "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                        "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                        "languageServer": "Default",
                        "interpreter": {"infoVisibility": "onPythonRelated"},
                        "logging": {"level": "error"},
                        "poetryPath": "poetry",
                    },
                }
            },
        )

    def sendPythonConfiguration(self):
        self.send_result(
            "workspace/configuration",
            [
                {
                    "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                    "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                    "languageServer": "Default",
                    "interpreter": {"infoVisibility": "onPythonRelated"},
                    "logging": {"level": "error"},
                    "poetryPath": "poetry",
                }
            ],
        )
