import os
import subprocess
import threading
import argparse

import time

from clientgood.json_rpc_endpoint import JsonRpcEndpoint
from clientgood.lsp_client import LspClient
from clientgood.lsp_endpoint import LspEndpoint

from lsprotocol.types import (
    TextDocumentItem,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    VersionedTextDocumentIdentifier,
    TextDocumentContentChangeEvent_Type2,
    InitializeParams,
    ClientCapabilities,
)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Start the Pyright language server.")
    # parser.add_argument(
    #     "--tcp",
    #     action="store_true",
    #     help="Use TCP socket to communicate with the server",
    # )
    parser.add_argument(
        "pyright_langserver",
        type=str,
        default="pyright-langserver --stdio",
        help="Start the Pyright language server on stdin/stdout.",
        nargs="?",
    )
    # Path to the project that can be set as workspace root to run the language server over.

    return parser.parse_args()


def main():
    # args = parse_arguments()

    p = subprocess.Popen(
        args=["pyright-langserver", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    json_rpc_endpoint = JsonRpcEndpoint(p.stdin, p.stdout)
    lsp_endpoint = LspEndpoint(json_rpc_endpoint)

    lsp_client = LspClient(lsp_endpoint)

    capabilities = ClientCapabilities(
        {
            "workspace": {
                "applyEdit": True,
                "workspaceEdit": {
                    "documentChanges": True,
                },
                "workspaceFolders": True,
            },
        }
    )
    # capabilities = ClientCapabilities(
    #     **{
    #         "text_document": {
    #             "synchronization": {"dynamicRegistration": True},
    #             "publishDiagnostics": {"relatedInformation": True},
    #             "diagnostic": {
    #                 "dynamicRegistration": True,
    #                 "relatedDocumentSupport": True,
    #             },
    #         },
    #         "workspace": {
    #             "applyEdit": True,
    #             "workspaceEdit": {
    #                 "documentChanges": True,
    #             },
    #             "didChangeConfiguration": {"dynamicRegistration": True},
    #             "configuration": True,  # Needed for workspace/configuration to work which allows pyright to send diagnostics
    #             "workspaceFolders": True,
    #         },
    #     }
    # )

    cwd = os.getcwd()
    root_uri = f"file:///{cwd}"
    # workspace_folders = [{"name": "python-lsp", "uri": root_uri}]
    workspace_folders = [
        {
            "name": "t",
            "uri": "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t",
        }
    ]

    lsp_client.initialize(
        InitializeParams(
            **{
                "process_id": p.pid,
                "root_path": None,
                "root_uri": root_uri,
                "initialization_options": None,
                "capabilities": capabilities,
                "trace": "verbose",
                "workspace_folders": workspace_folders,
            }
        )
    )
    time.sleep(2)
    lsp_client.initialized()
    time.sleep(2)
    lsp_client.register()
    time.sleep(2)

    file_path = "d:/Documents/TU Delft/Year 6/Master's Thesis/t/test.py"
    uri = "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t/test.py"
    # file_path = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example.py"
    # uri = "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/lsp-mark-python/src/example/example.py"
    # uri = "file:///" + file_path
    version = 1
    text = open(file_path, "r").read()
    lsp_client.didOpen(
        DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=uri,
                language_id="python",
                version=version,
                text=text,
            )
        )
    )
    time.sleep(2)
    lsp_client.didChangeConfiguration()
    time.sleep(2)
    lsp_client.sendPythonConfiguration()
    time.sleep(2)

    file_path_wrong = "d:/Documents/TU Delft/Year 6/Master's Thesis/t/test.py"
    # file_path_wrong = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example-wrong.py"
    new_text = open(file_path_wrong, "r").read()
    document = VersionedTextDocumentIdentifier(uri=uri, version=version + 1)
    change = TextDocumentContentChangeEvent_Type2(text=new_text)
    lsp_client.didChange(
        DidChangeTextDocumentParams(text_document=document, content_changes=[change])
    )

    time.sleep(5)
    lsp_client.shutdown()
    time.sleep(1)
    lsp_client.exit()


if __name__ == "__main__":
    main()
