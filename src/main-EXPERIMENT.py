import os
import subprocess
import threading
import argparse

import time

from client.json_rpc_endpoint import JsonRpcEndpoint
from client.lsp_client import LspClient
from client.lsp_endpoint import LspEndpoint

# from client.lsp_structs import (
#     DidChangeTextDocumentParams,
#     TextDocumentContentChangeEvent,
#     TextDocumentItem,
#     VersionedTextDocumentIdentifier,
# )
from lsprotocol.types import TextDocumentItem


class ReadPipe(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.pipe = pipe

    def run(self):
        line = self.pipe.readline().decode("utf-8")
        while line:
            print(line)
            line = self.pipe.readline().decode("utf-8")


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

    read_pipe = ReadPipe(p.stderr)
    read_pipe.start()
    json_rpc_endpoint = JsonRpcEndpoint(p.stdin, p.stdout)
    lsp_endpoint = LspEndpoint(json_rpc_endpoint)

    lsp_client = LspClient(lsp_endpoint)

    # capabilities = ClientCapabilities(
    #     {
    #         "workspace": {
    #             "applyEdit": True,
    #             "workspaceEdit": {
    #                 "documentChanges": True,
    #             },
    #             "workspaceFolders": True,
    #         },
    #     }
    # )
    # capabilities = {
    #     "textDocument": {
    #         "synchronization": {"dynamicRegistration": True},
    #         "publishDiagnostics": {"relatedInformation": True},
    #         "diagnostic": {"dynamicRegistration": True, "relatedDocumentSupport": True},
    #     },
    #     "workspace": {
    #         "applyEdit": True,
    #         "workspaceEdit": {
    #             "documentChanges": True,
    #         },
    #         "didChangeConfiguration": {"dynamicRegistration": True},
    #         "configuration": True,  # Needed for workspace/configuration to work which allows pyright to send diagnostics
    #         "workspaceFolders": True,
    #     },
    # }
    capabilities = {
        "workspace": {
            "applyEdit": True,
            "workspaceEdit": {
                "documentChanges": True,
                "resourceOperations": ["create", "rename", "delete"],
                "failureHandling": "textOnlyTransactional",
                "normalizesLineEndings": True,
                "changeAnnotationSupport": {"groupsOnLabel": True},
            },
            "configuration": True,
            "didChangeWatchedFiles": {
                "dynamicRegistration": True,
                "relativePatternSupport": True,
            },
            "symbol": {
                "dynamicRegistration": True,
                "symbolKind": {
                    "valueSet": [
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        24,
                        25,
                        26,
                    ]
                },
                "tagSupport": {"valueSet": [1]},
                "resolveSupport": {"properties": ["location.range"]},
            },
            "codeLens": {"refreshSupport": True},
            "executeCommand": {"dynamicRegistration": True},
            "didChangeConfiguration": {"dynamicRegistration": True},
            "workspaceFolders": True,
            "semanticTokens": {"refreshSupport": True},
            "fileOperations": {
                "dynamicRegistration": True,
                "didCreate": True,
                "didRename": True,
                "didDelete": True,
                "willCreate": True,
                "willRename": True,
                "willDelete": True,
            },
            "inlineValue": {"refreshSupport": True},
            "inlayHint": {"refreshSupport": True},
            "diagnostics": {"refreshSupport": True},
        },
        "textDocument": {
            "publishDiagnostics": {
                "relatedInformation": True,
                "versionSupport": False,
                "tagSupport": {"valueSet": [1, 2]},
                "codeDescriptionSupport": True,
                "dataSupport": True,
            },
            "synchronization": {
                "dynamicRegistration": True,
                "willSave": True,
                "willSaveWaitUntil": True,
                "didSave": True,
            },
            "completion": {
                "dynamicRegistration": True,
                "contextSupport": True,
                "completionItem": {
                    "snippetSupport": True,
                    "commitCharactersSupport": True,
                    "documentationFormat": ["markdown", "plaintext"],
                    "deprecatedSupport": True,
                    "preselectSupport": True,
                    "tagSupport": {"valueSet": [1]},
                    "insertReplaceSupport": True,
                    "resolveSupport": {
                        "properties": ["documentation", "detail", "additionalTextEdits"]
                    },
                    "insertTextModeSupport": {"valueSet": [1, 2]},
                    "labelDetailsSupport": True,
                },
                "insertTextMode": 2,
                "completionItemKind": {
                    "valueSet": [
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        24,
                        25,
                    ]
                },
                "completionList": {
                    "itemDefaults": [
                        "commitCharacters",
                        "editRange",
                        "insertTextFormat",
                        "insertTextMode",
                    ]
                },
            },
            "hover": {
                "dynamicRegistration": True,
                "contentFormat": ["markdown", "plaintext"],
            },
            "signatureHelp": {
                "dynamicRegistration": True,
                "signatureInformation": {
                    "documentationFormat": ["markdown", "plaintext"],
                    "parameterInformation": {"labelOffsetSupport": True},
                    "activeParameterSupport": True,
                },
                "contextSupport": True,
            },
            "definition": {"dynamicRegistration": True, "linkSupport": True},
            "references": {"dynamicRegistration": True},
            "documentHighlight": {"dynamicRegistration": True},
            "documentSymbol": {
                "dynamicRegistration": True,
                "symbolKind": {
                    "valueSet": [
                        1,
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        24,
                        25,
                        26,
                    ]
                },
                "hierarchicalDocumentSymbolSupport": True,
                "tagSupport": {"valueSet": [1]},
                "labelSupport": True,
            },
            "codeAction": {
                "dynamicRegistration": True,
                "isPreferredSupport": True,
                "disabledSupport": True,
                "dataSupport": True,
                "resolveSupport": {"properties": ["edit"]},
                "codeActionLiteralSupport": {
                    "codeActionKind": {
                        "valueSet": [
                            "",
                            "quickfix",
                            "refactor",
                            "refactor.extract",
                            "refactor.inline",
                            "refactor.rewrite",
                            "source",
                            "source.organizeImports",
                        ]
                    }
                },
                "honorsChangeAnnotations": False,
            },
            "codeLens": {"dynamicRegistration": True},
            "formatting": {"dynamicRegistration": True},
            "rangeFormatting": {"dynamicRegistration": True},
            "onTypeFormatting": {"dynamicRegistration": True},
            "rename": {
                "dynamicRegistration": True,
                "prepareSupport": True,
                "prepareSupportDefaultBehavior": 1,
                "honorsChangeAnnotations": True,
            },
            "documentLink": {"dynamicRegistration": True, "tooltipSupport": True},
            "typeDefinition": {"dynamicRegistration": True, "linkSupport": True},
            "implementation": {"dynamicRegistration": True, "linkSupport": True},
            "colorProvider": {"dynamicRegistration": True},
            "foldingRange": {
                "dynamicRegistration": True,
                "rangeLimit": 5000,
                "lineFoldingOnly": True,
                "foldingRangeKind": {"valueSet": ["comment", "imports", "region"]},
                "foldingRange": {"collapsedText": False},
            },
            "declaration": {"dynamicRegistration": True, "linkSupport": True},
            "selectionRange": {"dynamicRegistration": True},
            "callHierarchy": {"dynamicRegistration": True},
            "semanticTokens": {
                "dynamicRegistration": True,
                "tokenTypes": [
                    "namespace",
                    "type",
                    "class",
                    "enum",
                    "interface",
                    "struct",
                    "typeParameter",
                    "parameter",
                    "variable",
                    "property",
                    "enumMember",
                    "event",
                    "function",
                    "method",
                    "macro",
                    "keyword",
                    "modifier",
                    "comment",
                    "string",
                    "number",
                    "regexp",
                    "operator",
                    "decorator",
                ],
                "tokenModifiers": [
                    "declaration",
                    "definition",
                    "readonly",
                    "static",
                    "deprecated",
                    "abstract",
                    "async",
                    "modification",
                    "documentation",
                    "defaultLibrary",
                ],
                "formats": ["relative"],
                "requests": {"range": True, "full": {"delta": True}},
                "multilineTokenSupport": False,
                "overlappingTokenSupport": False,
                "serverCancelSupport": True,
                "augmentsSyntaxTokens": True,
            },
            "linkedEditingRange": {"dynamicRegistration": True},
            "typeHierarchy": {"dynamicRegistration": True},
            "inlineValue": {"dynamicRegistration": True},
            "inlayHint": {
                "dynamicRegistration": True,
                "resolveSupport": {
                    "properties": [
                        "tooltip",
                        "textEdits",
                        "label.tooltip",
                        "label.location",
                        "label.command",
                    ]
                },
            },
            "diagnostic": {
                "dynamicRegistration": True,
                "relatedDocumentSupport": False,
            },
        },
        "window": {
            "showMessage": {"messageActionItem": {"additionalPropertiesSupport": True}},
            "showDocument": {"support": True},
            "workDoneProgress": True,
        },
        "general": {
            "staleRequestSupport": {
                "cancel": True,
                "retryOnContentModified": [
                    "textDocument/semanticTokens/full",
                    "textDocument/semanticTokens/range",
                    "textDocument/semanticTokens/full/delta",
                ],
            },
            "regularExpressions": {"engine": "ECMAScript", "version": "ES2020"},
            "markdown": {"parser": "marked", "version": "1.1.0"},
            "positionEncodings": ["utf-16"],
        },
        "notebookDocument": {
            "synchronization": {
                "dynamicRegistration": True,
                "executionSummarySupport": True,
            }
        },
    }

    # [Trace - 3:45:12 PM] Received request 'workspace/configuration - (1)'.
    # Params: {
    #     "items": [
    #         {
    #             "scopeUri": "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t",
    #             "section": "python"
    #         }
    #     ]
    # }

    # [Trace - 3:45:12 PM] Sending response 'workspace/configuration - (1)'. Processing request took 1ms
    # Result: [
    #     {
    #         "activeStateToolPath": "state",
    #         "autoComplete": {
    #             "extraPaths": []
    #         },
    #         "createEnvironment": {
    #             "contentButton": "hide"
    #         },
    #         "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
    #         "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
    #         "diagnostics": {
    #             "sourceMapsEnabled": False
    #         },
    #         "envFile": "${workspaceFolder}/.env",
    #         "experiments": {
    #             "enabled": True,
    #             "optInto": [],
    #             "optOutFrom": []
    #         },
    #         "formatting": {
    #             "autopep8Args": [],
    #             "autopep8Path": "autopep8",
    #             "blackArgs": [],
    #             "blackPath": "black",
    #             "provider": "none",
    #             "yapfArgs": [],
    #             "yapfPath": "yapf"
    #         },
    #         "globalModuleInstallation": False,
    #         "languageServer": "Default",
    #         "linting": {
    #             "banditArgs": [],
    #             "banditEnabled": False,
    #             "banditPath": "bandit",
    #             "cwd": null,
    #             "enabled": True,
    #             "flake8Args": [],
    #             "flake8CategorySeverity": {
    #                 "E": "Error",
    #                 "F": "Error",
    #                 "W": "Warning"
    #             },
    #             "flake8Enabled": False,
    #             "flake8Path": "flake8",
    #             "ignorePatterns": [
    #                 "**/site-packages/**/*.py",
    #                 ".vscode/*.py"
    #             ],
    #             "lintOnSave": True,
    #             "maxNumberOfProblems": 100,
    #             "mypyArgs": [
    #                 "--follow-imports=silent",
    #                 "--ignore-missing-imports",
    #                 "--show-column-numbers",
    #                 "--no-pretty"
    #             ],
    #             "mypyCategorySeverity": {
    #                 "error": "Error",
    #                 "note": "Information"
    #             },
    #             "mypyEnabled": False,
    #             "mypyPath": "mypy",
    #             "prospectorArgs": [],
    #             "prospectorEnabled": False,
    #             "prospectorPath": "prospector",
    #             "pycodestyleArgs": [],
    #             "pycodestyleCategorySeverity": {
    #                 "E": "Error",
    #                 "W": "Warning"
    #             },
    #             "pycodestyleEnabled": False,
    #             "pycodestylePath": "pycodestyle",
    #             "pydocstyleArgs": [],
    #             "pydocstyleEnabled": False,
    #             "pydocstylePath": "pydocstyle",
    #             "pylamaArgs": [],
    #             "pylamaEnabled": False,
    #             "pylamaPath": "pylama",
    #             "pylintArgs": [],
    #             "pylintCategorySeverity": {
    #                 "convention": "Information",
    #                 "error": "Error",
    #                 "fatal": "Error",
    #                 "refactor": "Hint",
    #                 "warning": "Warning"
    #             },
    #             "pylintEnabled": False,
    #             "pylintPath": "pylint"
    #         },
    #         "interpreter": {
    #             "infoVisibility": "onPythonRelated"
    #         },
    #         "logging": {
    #             "level": "error"
    #         },
    #         "missingPackage": {
    #             "severity": "Hint"
    #         },
    #         "pipenvPath": "pipenv",
    #         "poetryPath": "poetry",
    #         "sortImports": {
    #             "args": [],
    #             "path": ""
    #         },
    #         "tensorBoard": {
    #             "logDirectory": ""
    #         },
    #         "terminal": {
    #             "activateEnvInCurrentTerminal": False,
    #             "activateEnvironment": True,
    #             "executeInFileDir": False,
    #             "focusAfterLaunch": False,
    #             "launchArgs": []
    #         },
    #         "testing": {
    #             "autoTestDiscoverOnSaveEnabled": True,
    #             "cwd": null,
    #             "debugPort": 3000,
    #             "promptToConfigure": True,
    #             "pytestArgs": [],
    #             "pytestEnabled": False,
    #             "pytestPath": "pytest",
    #             "unittestArgs": [
    #                 "-v",
    #                 "-s",
    #                 ".",
    #                 "-p",
    #                 "*test*.py"
    #             ],
    #             "unittestEnabled": False
    #         },
    #         "venvFolders": [],
    #         "venvPath": "",
    #         "analysis": {
    #             "inlayHints": {
    #                 "functionReturnTypes": True,
    #                 "pytestParameters": True
    #             }
    #         }
    #     }
    # ]

    # [Trace - 3:45:12 PM] Received request 'workspace/configuration - (2)'.
    # Params: {
    #     "items": [
    #         {
    #             "scopeUri": "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t",
    #             "section": "python.analysis"
    #         }
    #     ]
    # }

    # [Trace - 3:45:12 PM] Sending response 'workspace/configuration - (2)'. Processing request took 0ms
    # Result: [
    #     {
    #         "inlayHints": {
    #             "functionReturnTypes": True,
    #             "pytestParameters": True
    #         }
    #     }
    # ]

    # [Trace - 3:45:12 PM] Received request 'workspace/configuration - (3)'.
    # Params: {
    #     "items": [
    #         {
    #             "scopeUri": "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t",
    #             "section": "pyright"
    #         }
    #     ]
    # }

    # [Trace - 3:45:12 PM] Sending response 'workspace/configuration - (3)'. Processing request took 1ms
    # Result: [
    #     null
    # ]

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
        processId=p.pid,
        rootPath=None,
        rootUri=root_uri,
        initializationOptions=None,
        capabilities=capabilities,
        trace="verbose",
        workspaceFolders=workspace_folders,
    )
    time.sleep(1)
    lsp_client.initialized()
    time.sleep(1)
    lsp_client.register()
    time.sleep(1)

    file_path = "d:/Documents/TU Delft/Year 6/Master's Thesis/t/test.py"
    uri = "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/t/test.py"
    # file_path = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example.py"
    # uri = "file:///d%3A/Documents/TU%20Delft/Year%206/Master%27s%20Thesis/lsp-mark-python/src/example/example.py"
    # uri = "file:///" + file_path
    text = open(file_path, "r").read()
    languageId = "python"
    version = 1
    lsp_client.didOpen(TextDocumentItem(uri, languageId, version, text))
    # time.sleep(4)

    # lsp_client.didChangeConfiguration()
    # time.sleep(4)
    # lsp_client.sendPythonConfiguration()
    # time.sleep(4)

    # file_path_wrong = "d:/Documents/TU Delft/Year 6/Master's Thesis/t/test.py"
    # # file_path_wrong = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example-wrong.py"
    # new_text = open(file_path_wrong, "r").read()
    # document = VersionedTextDocumentIdentifier(uri, version + 1)
    # change = TextDocumentContentChangeEvent(new_text)
    # lsp_client.didChange(DidChangeTextDocumentParams(document, [change]))
    # # lsp_client.pullDiagnostics(
    # #     pylspclient.lsp_structs.DocumentDiagnosticParams(
    # #         pylspclient.lsp_structs.TextDocumentIdentifier(uri)
    # #     )
    # # )
    # time.sleep(4)

    # lsp_client.shutdown()
    # time.sleep(1)
    # lsp_client.exit()


if __name__ == "__main__":
    main()
