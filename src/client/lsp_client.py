from typing import Any
from client.lsp_endpoint import LspEndpoint
from lsprotocol import converters
from lsprotocol.types import (
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    InitializeParams,
)


class LspClient(object):
    def __init__(self, lsp_endpoint: LspEndpoint):
        self.lsp_endpoint = lsp_endpoint
        self.converter = converters.get_converter()

    def send_request(self, method: str, params: Any = None):
        self.lsp_endpoint.send_request(method, params)

    def send_notification(self, method: str, params: Any = None):
        self.lsp_endpoint.send_notification(method, params)

    def send_result(self, method: str, result: Any = None):
        self.lsp_endpoint.send_result(method, result)

    # --- Standard LSP methods ---
    def initialize(self, params: InitializeParams):
        self.lsp_endpoint.start()
        return self.send_request(
            "initialize", self.converter.unstructure(params, InitializeParams)
        )

    def initialized(self):
        self.send_notification("initialized", {})

    def register(self):
        return self.send_notification("client/registerCapability")

    def did_open(self, params: DidOpenTextDocumentParams):
        return self.send_notification(
            "textDocument/didOpen",
            self.converter.unstructure(params, DidOpenTextDocumentParams),
        )

    def did_change(self, params: DidChangeTextDocumentParams):
        return self.send_notification(
            "textDocument/didChange",
            self.converter.unstructure(params, DidChangeTextDocumentParams),
        )

    def show_completions(self, uri):
        return self.send_request(
            "textDocument/completion",
            {
                "textDocument": {"uri": uri},
                "position": {"line": 0, "character": 23},  # 24, 36
                "context": {"triggerKind": 1},
            },
        )

    # def resolve_completion(self):
    #     return self.send_request(
    #         "completionItem/resolve",
    #         {
    #             "label": "Potato",
    #             "labelDetails": {"description": "potato"},
    #             "detail": "Auto-import",
    #             "documentation": {
    #                 "kind": "markdown",
    #                 "value": "```\nfrom potato import Potato\n```",
    #             },
    #             "insertTextFormat": 1,
    #             "textEdit": {
    #                 "newText": "Potato",
    #                 "range": {
    #                     "start": {"line": 3, "character": 24},
    #                     "end": {"line": 3, "character": 26},
    #                 },
    #             },
    #             "kind": 7,
    #             "sortText": "12.9999.Potato.06.potato",
    #             "additionalTextEdits": [
    #                 {
    #                     "range": {
    #                         "start": {"line": 3, "character": 0},
    #                         "end": {"line": 3, "character": 0},
    #                     },
    #                     "newText": "from potato import Potato\r\n\r\n\r\n",
    #                 }
    #             ],
    #             "data": {
    #                 "workspacePath": "D:\\Documents\\TU Delft\\Year 6\\Master's Thesis\\t",
    #                 "filePath": "D:\\Documents\\TU Delft\\Year 6\\Master's Thesis\\t\\test.py",
    #                 "position": {"line": 3, "character": 26},
    #                 "autoImportText": "```\nfrom potato import Potato\n```",
    #                 "symbolLabel": "Potato",
    #             },
    #         },
    #     )

    def did_close(self, params: DidCloseTextDocumentParams):
        return self.send_notification(
            "textDocument/didClose",
            self.converter.unstructure(params, DidCloseTextDocumentParams),
        )

    def shutdown(self):
        return self.send_request("shutdown")

    def exit(self):
        self.send_notification("exit")
        self.lsp_endpoint.stop()

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
