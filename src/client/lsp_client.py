import json
from attrs import asdict
from pylspclient import lsp_structs


class LspClient(object):
    def __init__(self, lsp_endpoint):
        """
        Constructs a new LspClient instance.

        :param lsp_endpoint: TODO
        """
        self.lsp_endpoint = lsp_endpoint

    def initialize(
        self,
        processId,
        rootPath,
        rootUri,
        initializationOptions,
        capabilities,
        trace,
        workspaceFolders,
    ):
        """
        The initialize request is sent as the first request from the client to the server. If the server receives a request or notification
        before the initialize request it should act as follows:

        1. For a request the response should be an error with code: -32002. The message can be picked by the server.
        2. Notifications should be dropped, except for the exit notification. This will allow the exit of a server without an initialize request.

        Until the server has responded to the initialize request with an InitializeResult, the client must not send any additional requests or
        notifications to the server. In addition the server is not allowed to send any requests or notifications to the client until it has responded
        with an InitializeResult, with the exception that during the initialize request the server is allowed to send the notifications window/showMessage,
        window/logMessage and telemetry/event as well as the window/showMessageRequest request to the client.

        The initialize request may only be sent once.

        :param int processId: The process Id of the parent process that started the server. Is null if the process has not been started by another process.
                                If the parent process is not alive then the server should exit (see exit notification) its process.
        :param str rootPath: The rootPath of the workspace. Is null if no folder is open. Deprecated in favour of rootUri.
        :param DocumentUri rootUri: The rootUri of the workspace. Is null if no folder is open. If both `rootPath` and `rootUri` are set
                                    `rootUri` wins.
        :param any initializationOptions: User provided initialization options.
        :param ClientCapabilities capabilities: The capabilities provided by the client (editor or tool).
        :param Trace trace: The initial trace setting. If omitted trace is disabled ('off').
        :param list workspaceFolders: The workspace folders configured in the client when the server starts. This property is only available if the client supports workspace folders.
                                        It can be `null` if the client supports workspace folders but none are configured.
        """
        self.lsp_endpoint.start()
        return self.lsp_endpoint.call_method(
            "initialize",
            processId=processId,
            rootPath=rootPath,
            rootUri=rootUri,
            initializationOptions=initializationOptions,
            capabilities=capabilities,
            trace=trace,
            workspaceFolders=workspaceFolders,
        )

    def initialized(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.send_notification("initialized")

    def didChangeConfiguration(self):
        self.lsp_endpoint.send_notification(
            "workspace/didChangeConfiguration",
            settings={
                # "python": {
                #     "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                #     "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                #     "languageServer": "Default",
                #     "interpreter": {
                #     "infoVisibility": "onPythonRelated"
                #     },
                #     "logging": {
                #         "level": "error"
                #     },
                #     "poetryPath": "poetry",
                # },
                "python": {
                    "activeStateToolPath": "state",
                    "autoComplete": {"extraPaths": []},
                    "createEnvironment": {"contentButton": "hide"},
                    "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                    "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                    "diagnostics": {"sourceMapsEnabled": False},
                    "envFile": "${workspaceFolder}/.env",
                    "experiments": {"enabled": True, "optInto": [], "optOutFrom": []},
                    "formatting": {
                        "autopep8Args": [],
                        "autopep8Path": "autopep8",
                        "blackArgs": [],
                        "blackPath": "black",
                        "provider": "none",
                        "yapfArgs": [],
                        "yapfPath": "yapf",
                    },
                    "globalModuleInstallation": False,
                    "languageServer": "Default",
                    "linting": {
                        "banditArgs": [],
                        "banditEnabled": False,
                        "banditPath": "bandit",
                        "cwd": None,
                        "enabled": True,
                        "flake8Args": [],
                        "flake8CategorySeverity": {
                            "E": "Error",
                            "F": "Error",
                            "W": "Warning",
                        },
                        "flake8Enabled": False,
                        "flake8Path": "flake8",
                        "ignorePatterns": ["**/site-packages/**/*.py", ".vscode/*.py"],
                        "lintOnSave": True,
                        "maxNumberOfProblems": 100,
                        "mypyArgs": [
                            "--follow-imports=silent",
                            "--ignore-missing-imports",
                            "--show-column-numbers",
                            "--no-pretty",
                        ],
                        "mypyCategorySeverity": {
                            "error": "Error",
                            "note": "Information",
                        },
                        "mypyEnabled": False,
                        "mypyPath": "mypy",
                        "prospectorArgs": [],
                        "prospectorEnabled": False,
                        "prospectorPath": "prospector",
                        "pycodestyleArgs": [],
                        "pycodestyleCategorySeverity": {"E": "Error", "W": "Warning"},
                        "pycodestyleEnabled": False,
                        "pycodestylePath": "pycodestyle",
                        "pydocstyleArgs": [],
                        "pydocstyleEnabled": False,
                        "pydocstylePath": "pydocstyle",
                        "pylamaArgs": [],
                        "pylamaEnabled": False,
                        "pylamaPath": "pylama",
                        "pylintArgs": [],
                        "pylintCategorySeverity": {
                            "convention": "Information",
                            "error": "Error",
                            "fatal": "Error",
                            "refactor": "Hint",
                            "warning": "Warning",
                        },
                        "pylintEnabled": False,
                        "pylintPath": "pylint",
                    },
                    "interpreter": {"infoVisibility": "onPythonRelated"},
                    "logging": {"level": "error"},
                    "missingPackage": {"severity": "Hint"},
                    "pipenvPath": "pipenv",
                    "poetryPath": "poetry",
                    "sortImports": {"args": [], "path": ""},
                    "tensorBoard": {"logDirectory": ""},
                    "terminal": {
                        "activateEnvInCurrentTerminal": False,
                        "activateEnvironment": True,
                        "executeInFileDir": False,
                        "focusAfterLaunch": False,
                        "launchArgs": [],
                    },
                    "testing": {
                        "autoTestDiscoverOnSaveEnabled": True,
                        "cwd": None,
                        "debugPort": 3000,
                        "promptToConfigure": True,
                        "pytestArgs": [],
                        "pytestEnabled": False,
                        "pytestPath": "pytest",
                        "unittestArgs": ["-v", "-s", ".", "-p", "*test*.py"],
                        "unittestEnabled": False,
                    },
                    "venvFolders": [],
                    "venvPath": "",
                    "analysis": {
                        "inlayHints": {
                            "functionReturnTypes": True,
                            "pytestParameters": True,
                        }
                    },
                }
            },
        )

    def sendPythonConfiguration(self):
        # self.lsp_endpoint.send_result("workspace/configuration", [{
        #     "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
        #     "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
        #     "languageServer": "Default",
        #     "interpreter": {
        #         "infoVisibility": "onPythonRelated"
        #     },
        #     "logging": {
        #         "level": "error"
        #     },
        #     "poetryPath": "poetry",
        # }])
        self.lsp_endpoint.send_result(
            "workspace/configuration",
            [
                {
                    "activeStateToolPath": "state",
                    "autoComplete": {"extraPaths": []},
                    "createEnvironment": {"contentButton": "hide"},
                    "condaPath": "C:\\Users\\markb\\anaconda3\\_conda.exe",
                    "defaultInterpreterPath": "C:\\Users\\markb\\anaconda3\\python.exe",
                    "diagnostics": {"sourceMapsEnabled": False},
                    "envFile": "${workspaceFolder}/.env",
                    "experiments": {"enabled": True, "optInto": [], "optOutFrom": []},
                    "formatting": {
                        "autopep8Args": [],
                        "autopep8Path": "autopep8",
                        "blackArgs": [],
                        "blackPath": "black",
                        "provider": "none",
                        "yapfArgs": [],
                        "yapfPath": "yapf",
                    },
                    "globalModuleInstallation": False,
                    "languageServer": "Default",
                    "linting": {
                        "banditArgs": [],
                        "banditEnabled": False,
                        "banditPath": "bandit",
                        "enabled": True,
                        "flake8Args": [],
                        "flake8CategorySeverity": {
                            "E": "Error",
                            "F": "Error",
                            "W": "Warning",
                        },
                        "flake8Enabled": False,
                        "flake8Path": "flake8",
                        "ignorePatterns": ["**/site-packages/**/*.py", ".vscode/*.py"],
                        "lintOnSave": True,
                        "maxNumberOfProblems": 100,
                        "mypyArgs": [
                            "--follow-imports=silent",
                            "--ignore-missing-imports",
                            "--show-column-numbers",
                            "--no-pretty",
                        ],
                        "mypyCategorySeverity": {
                            "error": "Error",
                            "note": "Information",
                        },
                        "mypyEnabled": False,
                        "mypyPath": "mypy",
                        "prospectorArgs": [],
                        "prospectorEnabled": False,
                        "prospectorPath": "prospector",
                        "pycodestyleArgs": [],
                        "pycodestyleCategorySeverity": {"E": "Error", "W": "Warning"},
                        "pycodestyleEnabled": False,
                        "pycodestylePath": "pycodestyle",
                        "pydocstyleArgs": [],
                        "pydocstyleEnabled": False,
                        "pydocstylePath": "pydocstyle",
                        "pylamaArgs": [],
                        "pylamaEnabled": False,
                        "pylamaPath": "pylama",
                        "pylintArgs": [],
                        "pylintCategorySeverity": {
                            "convention": "Information",
                            "error": "Error",
                            "fatal": "Error",
                            "refactor": "Hint",
                            "warning": "Warning",
                        },
                        "pylintEnabled": False,
                        "pylintPath": "pylint",
                    },
                    "interpreter": {"infoVisibility": "onPythonRelated"},
                    "logging": {"level": "error"},
                    "missingPackage": {"severity": "Hint"},
                    "pipenvPath": "pipenv",
                    "poetryPath": "poetry",
                    "sortImports": {"args": [], "path": ""},
                    "tensorBoard": {"logDirectory": ""},
                    "terminal": {
                        "activateEnvInCurrentTerminal": False,
                        "activateEnvironment": True,
                        "executeInFileDir": False,
                        "focusAfterLaunch": False,
                        "launchArgs": [],
                    },
                    "testing": {
                        "autoTestDiscoverOnSaveEnabled": True,
                        "debugPort": 3000,
                        "promptToConfigure": True,
                        "pytestArgs": [],
                        "pytestEnabled": False,
                        "pytestPath": "pytest",
                        "unittestArgs": ["-v", "-s", ".", "-p", "*test*.py"],
                        "unittestEnabled": False,
                    },
                    "venvFolders": [],
                    "venvPath": "",
                    "analysis": {
                        "inlayHints": {
                            "functionReturnTypes": True,
                            "pytestParameters": True,
                        }
                    },
                }
            ],
        )

    def register(self):
        return self.lsp_endpoint.send_message("client/registerCapability", None)

    def shutdown(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.stop()
        return self.lsp_endpoint.call_method("shutdown")

    def exit(self):
        """
        The initialized notification is sent from the client to the server after the client received the result of the initialize request
        but before the client is sending any other request or notification to the server. The server can use the initialized notification
        for example to dynamically register capabilities. The initialized notification may only be sent once.
        """
        self.lsp_endpoint.send_notification("exit")

    def didOpen(self, textDocumentItem):
        """
        The document open notification is sent from the client to the server to signal newly opened text documents. The document's truth is
        now managed by the client and the server must not try to read the document's truth using the document's uri. Open in this sense
        means it is managed by the client. It doesn't necessarily mean that its content is presented in an editor. An open notification must
        not be sent more than once without a corresponding close notification send before. This means open and close notification must be
        balanced and the max open count for a particular textDocument is one.

        :param TextDocumentItem textDocument: The initial trace setting. If omitted trace is disabled ('off').
        """
        import jsonrpc
        from lsprotocol import converters

        converter = converters.get_converter()
        test = json.dumps(
            converter.unstructure(textDocumentItem)
        )  # asdict(textDocumentItem)

        return self.lsp_endpoint.send_notification(
            "textDocument/didOpen", textDocument=test
        )

    def didChange(self, textDocumentChangeParams):
        """
        The document change notification is sent from the client to the server to signal changes to a text document.

        :param
        """
        return self.lsp_endpoint.send_notification(
            "textDocument/didChange", **vars(textDocumentChangeParams)
        )

    def pullDiagnostics(self, documentDiagnosticParams):
        """
        The document change notification is sent from the client to the server to signal changes to a text document.

        :param
        """
        return self.lsp_endpoint.send_notification(
            "textDocument/diagnostic", **vars(documentDiagnosticParams)
        )

    def documentSymbol(self, textDocument):
        """
        The document symbol request is sent from the client to the server to return a flat list of all symbols found in a given text document.
        Neither the symbol's location range nor the symbol's container name should be used to infer a hierarchy.

        :param TextDocumentItem textDocument: The text document.
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/documentSymbol", textDocument=textDocument
        )
        return [lsp_structs.SymbolInformation(**sym) for sym in result_dict]

    def definition(self, textDocument, position):
        """
        The goto definition request is sent from the client to the server to resolve the definition location of a symbol at a given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document..
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/definition", textDocument=textDocument, position=position
        )
        return [lsp_structs.Location(**l) for l in result_dict]

    def typeDefinition(self, textDocument, position):
        """
        The goto type definition request is sent from the client to the server to resolve the type definition location of a symbol at a given text document position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document..
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/definition", textDocument=textDocument, position=position
        )
        return [lsp_structs.Location(**l) for l in result_dict]

    def signatureHelp(self, textDocument, position):
        """
        The signature help request is sent from the client to the server to request signature information at a given cursor position.

        :param TextDocumentItem textDocument: The text document.
        :param Position position: The position inside the text document..
        """
        result_dict = self.lsp_endpoint.call_method(
            "textDocument/signatureHelp", textDocument=textDocument, position=position
        )
        return lsp_structs.SignatureHelp(**result_dict)
