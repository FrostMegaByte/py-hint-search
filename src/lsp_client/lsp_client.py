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
