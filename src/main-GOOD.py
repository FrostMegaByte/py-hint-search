import os
import subprocess
import argparse

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

    root_path = f"{os.getcwd()}/src/example/"
    root_uri = f"file:///{root_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    lsp_client.initialize(
        InitializeParams(
            process_id=p.pid,
            root_path=None,
            root_uri=root_uri,
            initialization_options=None,
            capabilities=capabilities,
            trace="verbose",
            workspace_folders=workspace_folders,
        )
    )
    time.sleep(2)
    lsp_client.initialized()
    time.sleep(2)

    python_files = [file for file in os.listdir(root_path) if file.endswith(".py")]
    for file in python_files:
        print("Processing file:", file)

        file_path = f"{root_path}/{file}"
        # uri = "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/lsp-mark-python/src/example/example.py"
        uri = f"file:///{file_path}"
        version = 1
        python_code = open(file_path, "r").read()
        lsp_client.didOpen(
            DidOpenTextDocumentParams(
                text_document=TextDocumentItem(
                    uri=uri,
                    language_id="python",
                    version=version,
                    text=python_code,
                )
            )
        )
        time.sleep(1)

        # GET PREDICTIONS FROM TYPE4PY FOR FILE
        # ml_predictions = get_type4_py_predictions(file_path)

        # BUILD SEARCH TREE
        # search_tree = build_tree(Node("Top level node", 1), ml_predictions)
        # depth_first_traversal(search_tree, python_code)

        # PERFORM CHANGE
        # for annotation in ml_predictions:
        #     print("ANNOTATION:", annotation)

        # new_text = AnnotationInserter.insert_annotations(text)

        file_path_wrong = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example-wrong.py"
        version = version + 1
        new_python_code = open(file_path_wrong, "r").read()
        document = VersionedTextDocumentIdentifier(uri=uri, version=version + 1)
        change = TextDocumentContentChangeEvent_Type2(text=new_python_code)
        lsp_client.didChange(
            DidChangeTextDocumentParams(
                text_document=document, content_changes=[change]
            )
        )

        time.sleep(1)

        if lsp_client.lsp_endpoint.diagnostics:
            print("!-> DIAG:", lsp_client.lsp_endpoint.diagnostics)

    time.sleep(3)
    lsp_client.shutdown()
    time.sleep(1)
    lsp_client.exit()


if __name__ == "__main__":
    main()
