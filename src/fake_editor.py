import re
import subprocess
import time
from client.json_rpc_endpoint import JsonRpcEndpoint
from client.lsp_client import LspClient
from client.lsp_endpoint import LspEndpoint

from lsprotocol.types import (
    TextDocumentItem,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    VersionedTextDocumentIdentifier,
    TextDocumentContentChangeEvent_Type2,
    InitializeParams,
    ClientCapabilities,
    TextDocumentIdentifier,
    DidCloseTextDocumentParams,
    TraceValues,
)


class FakeEditor:
    _self = None

    def __init__(self):
        self.lsp_client = self._get_LSP_client()
        self.capabilities = self._get_editor_capabilities()
        self.received_diagnostics = False
        self.diagnostics = []

    # Singleton class
    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def _get_LSP_client(self):
        self.process = subprocess.Popen(
            args=["pyright-langserver", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        json_rpc_endpoint = JsonRpcEndpoint(self.process.stdin, self.process.stdout)
        lsp_endpoint = LspEndpoint(
            json_rpc_endpoint,
            callbacks={"textDocument/publishDiagnostics": self._handle_diagnostics},
        )
        return LspClient(lsp_endpoint)

    def _get_editor_capabilities(self):
        return ClientCapabilities(
            workspace={
                "apply_edit": True,
                "workspace_edit": {
                    "document_changes": True,
                },
                # DO NOT ENABLE BECAUSE PYRIGHT THEN WON'T SEND DIAGNOSTICS!!!
                # "did_change_configuration": {"dynamic_registration": True},
                # "configuration": True,  # Needed for workspace/configuration to work which allows pyright to send diagnostics
                "workspace_folders": True,
            },
            text_document={
                "synchronization": {"dynamic_registration": True},
                "publish_diagnostics": {"related_information": True},
                "diagnostic": {
                    "dynamic_registration": True,
                    "related_document_support": True,
                },
            },
        )

    def _handle_diagnostics(self, jsonrpc_message):
        self.diagnostics = jsonrpc_message["params"]["diagnostics"]
        self.received_diagnostics = True

    def start(self, root_uri: str, workspace_folders):
        self.lsp_client.initialize(
            InitializeParams(
                process_id=self.process.pid,
                root_path=None,
                root_uri=root_uri,
                initialization_options=None,
                capabilities=self.capabilities,
                trace=TraceValues.Verbose,
                workspace_folders=workspace_folders,
            )
        )
        time.sleep(1)
        self.lsp_client.initialized()

    def open_file(self, file_path: str):
        uri = f"file:///{file_path}"
        python_code = open(file_path, "r").read()
        self.edit_document = TextDocumentItem(
            uri=uri,
            language_id="python",
            version=1,
            text=python_code,
        )
        self.lsp_client.did_open(
            DidOpenTextDocumentParams(text_document=self.edit_document)
        )

        # Wait for diagnostics to be received. Currently the best async solution I could come up with
        while not self.received_diagnostics:
            time.sleep(0.001)
        self.received_diagnostics = False

    def change_file(self, new_python_code: str):
        self.edit_document.version += 1
        document = VersionedTextDocumentIdentifier(
            uri=self.edit_document.uri,
            version=self.edit_document.version,
        )
        change = TextDocumentContentChangeEvent_Type2(text=new_python_code)
        self.lsp_client.did_change(
            DidChangeTextDocumentParams(
                text_document=document,
                content_changes=[change],
            )
        )

    def has_diagnostic_error(self):
        DIAGNOSTIC_ERROR_PATTERN = r"cannot be assigned to|is not defined|Operator \".\" not supported for types \".*\" and \".*\""
        # TODO: Check that the diagnostic error is only for that function where the annotation was changed

        # Wait for diagnostics to be received. Currently the best async solution I could come up with
        while not self.received_diagnostics:
            time.sleep(0.001)
        self.received_diagnostics = False

        for diagnostic in self.diagnostics:
            if len(re.findall(DIAGNOSTIC_ERROR_PATTERN, diagnostic["message"])) > 0:
                return True
        return False

    def close_file(self):
        document = TextDocumentIdentifier(uri=self.edit_document.uri)
        self.lsp_client.did_close(DidCloseTextDocumentParams(text_document=document))
        self.edit_document = None

    def stop(self):
        self.lsp_client.shutdown()
        time.sleep(1)
        self.lsp_client.exit()
