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
)


class FakeEditor:
    _self = None

    def __init__(self):
        self.lsp_client = self._get_LSP_client()
        self.capabilities = self._get_editor_capabilities()
        self.edit_document = None

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
        lsp_endpoint = LspEndpoint(json_rpc_endpoint)
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

    def start(self, root_uri, workspace_folders):
        self.lsp_client.initialize(
            InitializeParams(
                process_id=self.process.pid,
                root_path=None,
                root_uri=root_uri,
                initialization_options=None,
                capabilities=self.capabilities,
                trace="verbose",
                workspace_folders=workspace_folders,
            )
        )
        time.sleep(1)
        self.lsp_client.initialized()

    def open_file(self, file_path):
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
        time.sleep(1)

    def change_file(self, new_python_code):
        self.lsp_client.lsp_endpoint.diagnostics = []  # Clear diagnostics
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

    def has_diagnostics(self):
        time.sleep(1)
        return True if self.lsp_client.lsp_endpoint.diagnostics else False

    def close_file(self):
        document = TextDocumentIdentifier(uri=self.edit_document.uri)
        self.lsp_client.did_close(DidCloseTextDocumentParams(text_document=document))
        self.edit_document = None
        time.sleep(1)

    def stop(self):
        self.lsp_client.shutdown()
        time.sleep(1)
        self.lsp_client.exit()
