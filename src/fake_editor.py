from __future__ import annotations
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict

from libcst.metadata import CodeRange

from client.json_rpc_endpoint import JsonRpcEndpoint
from client.lsp_client import LspClient
from client.lsp_endpoint import LspEndpoint

from lsprotocol.types import *


class FakeEditor:
    _self = None

    def __init__(self):
        self.lsp_client = self._get_LSP_client()
        self.capabilities = self._get_editor_capabilities()
        self.received_diagnostics = False
        self.modified_location = None
        self.start_errors = set()
        self.diagnostics = []

    # Singleton class
    def __new__(cls) -> FakeEditor:
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

    def _get_LSP_client(self) -> LspClient:
        project_path = os.getcwd()
        # Change directory to py-hint-search project to be able to start pyright-langserver
        current_file_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(current_file_path)

        self.process = subprocess.Popen(
            args=["poetry", "run", "pyright-langserver", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        os.chdir(project_path)

        json_rpc_endpoint = JsonRpcEndpoint(self.process.stdin, self.process.stdout)
        lsp_endpoint = LspEndpoint(
            json_rpc_endpoint,
            callbacks={"textDocument/publishDiagnostics": self._handle_diagnostics},
        )
        return LspClient(lsp_endpoint)

    def _get_editor_capabilities(self) -> ClientCapabilities:
        return ClientCapabilities(
            text_document=TextDocumentClientCapabilities(
                synchronization=TextDocumentSyncClientCapabilities(
                    dynamic_registration=True
                ),
                publish_diagnostics=PublishDiagnosticsClientCapabilities(
                    related_information=True
                ),
                diagnostic=DiagnosticClientCapabilities(
                    dynamic_registration=True,
                    related_document_support=True,
                ),
            ),
        )

    def _handle_diagnostics(self, jsonrpc_message: Dict[str, Any]) -> None:
        self.diagnostics = jsonrpc_message["params"]["diagnostics"]
        self.received_diagnostics = True

    def _wait_for_diagnostics(self) -> None:
        # Wait for diagnostics to be received. Currently the best async solution I could come up with
        while not self.received_diagnostics:
            time.sleep(0.001)
        self.received_diagnostics = False

    def start(self, root_uri: str) -> None:
        workspace_folders = [WorkspaceFolder(name="py-hint-search", uri=root_uri)]
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
        time.sleep(1)

    def open_file(self, file_path: str) -> None:
        uri_file_path = (
            file_path.lstrip("/") if file_path.startswith("/") else file_path
        )
        uri = f"file:///{uri_file_path}"
        try:
            python_code = open(file_path, "r", encoding="utf-8").read()
        except Exception as e:
            print(e)
            logger = logging.getLogger(__name__)
            logger.error(e)

        self.edit_document = TextDocumentItem(
            uri=uri,
            language_id="python",
            version=1,
            text=python_code,
        )
        self.lsp_client.did_open(
            DidOpenTextDocumentParams(text_document=self.edit_document)
        )
        self._wait_for_diagnostics()

    def change_file(
        self, new_python_code: str, modified_location: CodeRange | None
    ) -> None:
        self.modified_location = modified_location
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
        self._wait_for_diagnostics()

    def _error_in_modified_location(self, range: Dict) -> bool:
        return (
            self.modified_location is not None
            and range["start"]["line"] >= self.modified_location.start.line
            and range["start"]["character"] >= self.modified_location.start.column
            and range["end"]["line"] <= self.modified_location.end.line
            and range["end"]["character"] <= self.modified_location.end.column
        )

    def has_diagnostic_error(self, at_start: bool = False) -> bool:
        ERROR_PATTERN = r'cannot be assigned to|is not defined|Operator ".*" not supported for types ".*" and ".*"'
        ALLOWED_PATTERN = r'"Unknown" is not defined'

        for diagnostic in self.diagnostics:
            diagnostic_has_error = (
                len(re.findall(ERROR_PATTERN, diagnostic["message"])) > 0
            )
            if diagnostic_has_error and at_start:
                self.start_errors.add(diagnostic["message"])

            if diagnostic_has_error and self._error_in_modified_location(
                diagnostic["range"]
            ):
                diagnostic_is_allowed = (
                    len(re.findall(ALLOWED_PATTERN, diagnostic["message"])) > 0
                    or diagnostic["message"] in self.start_errors
                )
                if diagnostic_is_allowed:
                    continue

                return True
        return False

    def close_file(self) -> None:
        document = TextDocumentIdentifier(uri=self.edit_document.uri)
        self.lsp_client.did_close(DidCloseTextDocumentParams(text_document=document))
        self.edit_document = None
        self._wait_for_diagnostics()

    def stop(self) -> None:
        self.lsp_client.shutdown()
        self.lsp_client.exit()
