from clientgood.lsp_endpoint import LspEndpoint
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
                    # "python": {
                    #     "activeStateToolPath": "state",
                    #     "autoComplete": {"extraPaths": []},
                    #     "createEnvironment": {"contentButton": "hide"},
                    #     "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                    #     "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                    #     "diagnostics": {"sourceMapsEnabled": False},
                    #     "envFile": "${workspaceFolder}/.env",
                    #     "experiments": {
                    #         "enabled": True,
                    #         "optInto": [],
                    #         "optOutFrom": [],
                    #     },
                    #     "formatting": {
                    #         "autopep8Args": [],
                    #         "autopep8Path": "autopep8",
                    #         "blackArgs": [],
                    #         "blackPath": "black",
                    #         "provider": "none",
                    #         "yapfArgs": [],
                    #         "yapfPath": "yapf",
                    #     },
                    #     "globalModuleInstallation": False,
                    #     "languageServer": "Default",
                    #     "linting": {
                    #         "banditArgs": [],
                    #         "banditEnabled": False,
                    #         "banditPath": "bandit",
                    #         "cwd": None,
                    #         "enabled": True,
                    #         "flake8Args": [],
                    #         "flake8CategorySeverity": {
                    #             "E": "Error",
                    #             "F": "Error",
                    #             "W": "Warning",
                    #         },
                    #         "flake8Enabled": False,
                    #         "flake8Path": "flake8",
                    #         "ignorePatterns": [
                    #             "**/site-packages/**/*.py",
                    #             ".vscode/*.py",
                    #         ],
                    #         "lintOnSave": True,
                    #         "maxNumberOfProblems": 100,
                    #         "mypyArgs": [
                    #             "--follow-imports=silent",
                    #             "--ignore-missing-imports",
                    #             "--show-column-numbers",
                    #             "--no-pretty",
                    #         ],
                    #         "mypyCategorySeverity": {
                    #             "error": "Error",
                    #             "note": "Information",
                    #         },
                    #         "mypyEnabled": False,
                    #         "mypyPath": "mypy",
                    #         "prospectorArgs": [],
                    #         "prospectorEnabled": False,
                    #         "prospectorPath": "prospector",
                    #         "pycodestyleArgs": [],
                    #         "pycodestyleCategorySeverity": {
                    #             "E": "Error",
                    #             "W": "Warning",
                    #         },
                    #         "pycodestyleEnabled": False,
                    #         "pycodestylePath": "pycodestyle",
                    #         "pydocstyleArgs": [],
                    #         "pydocstyleEnabled": False,
                    #         "pydocstylePath": "pydocstyle",
                    #         "pylamaArgs": [],
                    #         "pylamaEnabled": False,
                    #         "pylamaPath": "pylama",
                    #         "pylintArgs": [],
                    #         "pylintCategorySeverity": {
                    #             "convention": "Information",
                    #             "error": "Error",
                    #             "fatal": "Error",
                    #             "refactor": "Hint",
                    #             "warning": "Warning",
                    #         },
                    #         "pylintEnabled": False,
                    #         "pylintPath": "pylint",
                    #     },
                    #     "interpreter": {"infoVisibility": "onPythonRelated"},
                    #     "logging": {"level": "error"},
                    #     "missingPackage": {"severity": "Hint"},
                    #     "pipenvPath": "pipenv",
                    #     "poetryPath": "poetry",
                    #     "sortImports": {"args": [], "path": ""},
                    #     "tensorBoard": {"logDirectory": ""},
                    #     "terminal": {
                    #         "activateEnvInCurrentTerminal": False,
                    #         "activateEnvironment": True,
                    #         "executeInFileDir": False,
                    #         "focusAfterLaunch": False,
                    #         "launchArgs": [],
                    #     },
                    #     "testing": {
                    #         "autoTestDiscoverOnSaveEnabled": True,
                    #         "cwd": None,
                    #         "debugPort": 3000,
                    #         "promptToConfigure": True,
                    #         "pytestArgs": [],
                    #         "pytestEnabled": False,
                    #         "pytestPath": "pytest",
                    #         "unittestArgs": ["-v", "-s", ".", "-p", "*test*.py"],
                    #         "unittestEnabled": False,
                    #     },
                    #     "venvFolders": [],
                    #     "venvPath": "",
                    #     "analysis": {
                    #         "inlayHints": {
                    #             "functionReturnTypes": True,
                    #             "pytestParameters": True,
                    #         }
                    #     },
                    # }
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
        # self.send_result(
        #     "workspace/configuration",
        #     [
        #         {
        #             "activeStateToolPath": "state",
        #             "autoComplete": {"extraPaths": []},
        #             "createEnvironment": {"contentButton": "hide"},
        #             "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
        #             "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
        #             "diagnostics": {"sourceMapsEnabled": False},
        #             "envFile": "${workspaceFolder}/.env",
        #             "experiments": {"enabled": True, "optInto": [], "optOutFrom": []},
        #             "formatting": {
        #                 "autopep8Args": [],
        #                 "autopep8Path": "autopep8",
        #                 "blackArgs": [],
        #                 "blackPath": "black",
        #                 "provider": "none",
        #                 "yapfArgs": [],
        #                 "yapfPath": "yapf",
        #             },
        #             "globalModuleInstallation": False,
        #             "languageServer": "Default",
        #             "linting": {
        #                 "banditArgs": [],
        #                 "banditEnabled": False,
        #                 "banditPath": "bandit",
        #                 "enabled": True,
        #                 "flake8Args": [],
        #                 "flake8CategorySeverity": {
        #                     "E": "Error",
        #                     "F": "Error",
        #                     "W": "Warning",
        #                 },
        #                 "flake8Enabled": False,
        #                 "flake8Path": "flake8",
        #                 "ignorePatterns": ["**/site-packages/**/*.py", ".vscode/*.py"],
        #                 "lintOnSave": True,
        #                 "maxNumberOfProblems": 100,
        #                 "mypyArgs": [
        #                     "--follow-imports=silent",
        #                     "--ignore-missing-imports",
        #                     "--show-column-numbers",
        #                     "--no-pretty",
        #                 ],
        #                 "mypyCategorySeverity": {
        #                     "error": "Error",
        #                     "note": "Information",
        #                 },
        #                 "mypyEnabled": False,
        #                 "mypyPath": "mypy",
        #                 "prospectorArgs": [],
        #                 "prospectorEnabled": False,
        #                 "prospectorPath": "prospector",
        #                 "pycodestyleArgs": [],
        #                 "pycodestyleCategorySeverity": {"E": "Error", "W": "Warning"},
        #                 "pycodestyleEnabled": False,
        #                 "pycodestylePath": "pycodestyle",
        #                 "pydocstyleArgs": [],
        #                 "pydocstyleEnabled": False,
        #                 "pydocstylePath": "pydocstyle",
        #                 "pylamaArgs": [],
        #                 "pylamaEnabled": False,
        #                 "pylamaPath": "pylama",
        #                 "pylintArgs": [],
        #                 "pylintCategorySeverity": {
        #                     "convention": "Information",
        #                     "error": "Error",
        #                     "fatal": "Error",
        #                     "refactor": "Hint",
        #                     "warning": "Warning",
        #                 },
        #                 "pylintEnabled": False,
        #                 "pylintPath": "pylint",
        #             },
        #             "interpreter": {"infoVisibility": "onPythonRelated"},
        #             "logging": {"level": "error"},
        #             "missingPackage": {"severity": "Hint"},
        #             "pipenvPath": "pipenv",
        #             "poetryPath": "poetry",
        #             "sortImports": {"args": [], "path": ""},
        #             "tensorBoard": {"logDirectory": ""},
        #             "terminal": {
        #                 "activateEnvInCurrentTerminal": False,
        #                 "activateEnvironment": True,
        #                 "executeInFileDir": False,
        #                 "focusAfterLaunch": False,
        #                 "launchArgs": [],
        #             },
        #             "testing": {
        #                 "autoTestDiscoverOnSaveEnabled": True,
        #                 "debugPort": 3000,
        #                 "promptToConfigure": True,
        #                 "pytestArgs": [],
        #                 "pytestEnabled": False,
        #                 "pytestPath": "pytest",
        #                 "unittestArgs": ["-v", "-s", ".", "-p", "*test*.py"],
        #                 "unittestEnabled": False,
        #             },
        #             "venvFolders": [],
        #             "venvPath": "",
        #             "analysis": {
        #                 "inlayHints": {
        #                     "functionReturnTypes": True,
        #                     "pytestParameters": True,
        #                 }
        #             },
        #         }
        #     ],
        # )

    # def pullDiagnostics(self, documentDiagnosticParams):
    #     """
    #     The document change notification is sent from the client to the server to signal changes to a text document.

    #     :param
    #     """
    #     return self.lsp_endpoint.send_notification(
    #         "textDocument/diagnostic", **vars(documentDiagnosticParams)
    #     )

    # def documentSymbol(self, textDocument):
    #     """
    #     The document symbol request is sent from the client to the server to return a flat list of all symbols found in a given text document.
    #     Neither the symbol's location range nor the symbol's container name should be used to infer a hierarchy.

    #     :param TextDocumentItem textDocument: The text document.
    #     """
    #     result_dict = self.lsp_endpoint.send_request(
    #         "textDocument/documentSymbol", textDocument=textDocument
    #     )
    #     return [lsp_structs.SymbolInformation(**sym) for sym in result_dict]

    # def definition(self, textDocument, position):
    #     """
    #     The goto definition request is sent from the client to the server to resolve the definition location of a symbol at a given text document position.

    #     :param TextDocumentItem textDocument: The text document.
    #     :param Position position: The position inside the text document..
    #     """
    #     result_dict = self.lsp_endpoint.send_request(
    #         "textDocument/definition", textDocument=textDocument, position=position
    #     )
    #     return [lsp_structs.Location(**l) for l in result_dict]

    # def typeDefinition(self, textDocument, position):
    #     """
    #     The goto type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.

    #     :param TextDocumentItem textDocument: The text document.
    #     :param Position position: The position inside the text document..
    #     """
    #     result_dict = self.lsp_endpoint.send_request(
    #         "textDocument/definition", textDocument=textDocument, position=position
    #     )
    #     return [lsp_structs.Location(**l) for l in result_dict]

    # def signatureHelp(self, textDocument, position):
    #     """
    #     The signature help request is sent from the client to the server to request signature information at a given cursor position.

    #     :param TextDocumentItem textDocument: The text document.
    #     :param Position position: The position inside the text document..
    #     """
    #     result_dict = self.lsp_endpoint.send_request(
    #         "textDocument/signatureHelp", textDocument=textDocument, position=position
    #     )
    #     return lsp_structs.SignatureHelp(**result_dict)
