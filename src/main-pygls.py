import asyncio
import logging
import pathlib
import sys
from concurrent.futures import Future
from typing import Dict
from typing import List
from typing import Type

# import pytest
# import pytest_asyncio
from lsprotocol import types

from pygls import uris
from pygls.exceptions import JsonRpcMethodNotFound
from pygls.lsp.client import BaseLanguageClient
from pygls.client import JsonRPCClient
from pygls.protocol import LanguageServerProtocol
from pygls.protocol import default_converter

logging.basicConfig(filename="pygls.log", filemode="w", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LanguageClientProtocol(LanguageServerProtocol):
    """An extended protocol class with extra methods that are useful for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._notification_futures = {}

    def _handle_notification(self, method_name, params):
        if method_name == types.CANCEL_REQUEST:
            self._handle_cancel_notification(params.id)
            return

        future = self._notification_futures.pop(method_name, None)
        if future:
            future.set_result(params)

        try:
            handler = self._get_handler(method_name)
            self._execute_notification(handler, params)
        except (KeyError, JsonRpcMethodNotFound):
            logger.warning("Ignoring notification for unknown method '%s'", method_name)
        except Exception:
            logger.exception(
                "Failed to handle notification '%s': %s", method_name, params
            )

    def wait_for_notification(self, method: str, callback=None):
        future: Future = Future()
        if callback:

            def wrapper(future: Future):
                result = future.result()
                callback(result)

            future.add_done_callback(wrapper)

        self._notification_futures[method] = future
        return future

    def wait_for_notification_async(self, method: str):
        future = self.wait_for_notification(method)
        return asyncio.wrap_future(future)


class LanguageClient(BaseLanguageClient):
    """Language client used to drive test cases."""

    def __init__(
        self,
        protocol_cls: Type[LanguageClientProtocol] = LanguageClientProtocol,
        *args,
        **kwargs,
    ):
        super().__init__(
            "pygls-test-client", "v1", protocol_cls=protocol_cls, *args, **kwargs
        )

        self.diagnostics: Dict[str, List[types.Diagnostic]] = {}
        """Used to hold any recieved diagnostics."""

        self.messages: List[types.ShowMessageParams] = []
        """Holds any received ``window/showMessage`` requests."""

        self.log_messages: List[types.LogMessageParams] = []
        """Holds any received ``window/logMessage`` requests."""

    async def wait_for_notification(self, method: str):
        """Block until a notification with the given method is received.

        Parameters
        ----------
        method
           The notification method to wait for, e.g. ``textDocument/publishDiagnostics``
        """
        return await self.protocol.wait_for_notification_async(method)


async def main():
    capabilities = {
        "textDocument": {
            "synchronization": {"dynamicRegistration": True},
            "publishDiagnostics": {"relatedInformation": True},
        },
        "workspace": {
            "applyEdit": True,
            "workspaceEdit": {
                "documentChanges": True,
            },
            "workspaceFolders": True,
        },
    }

    client = LanguageClient(converter_factory=default_converter)

    # @client.feature(types.TEXT_DOCUMENT_PUBLISH_DIAGNOSTICS)
    # def publish_diagnostics(
    #     client: LanguageClient, params: types.PublishDiagnosticsParams
    # ):
    #     client.diagnostics[params.uri] = params.diagnostics

    # @client.feature(types.WINDOW_LOG_MESSAGE)
    # def log_message(client: LanguageClient, params: types.LogMessageParams):
    #     client.log_messages.append(params)

    #     levels = ["ERROR: ", "WARNING: ", "INFO: ", "LOG: "]
    #     log_level = levels[params.type.value - 1]

    #     print(log_level, params.message)

    # @client.feature(types.WINDOW_SHOW_MESSAGE)
    # def show_message(client: LanguageClient, params):
    #     client.messages.append(params)

    server_dir = pathlib.Path(__file__, "..", "..", "examples", "servers").resolve()
    root_dir = pathlib.Path(__file__, "..", "..", "examples", "workspace").resolve()

    await client.start_io(sys.executable, str(server_dir / server_name))

    # Initialize the server
    response = await client.initialize_async(
        types.InitializeParams(
            capabilities=types.ClientCapabilities(),
            root_uri=uris.from_fs_path(root_dir),
        )
    )
    assert response is not None

    yield client, response

    await client.shutdown_async(None)
    client.exit(None)

    await client.stop()

    # file_path = "D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/example/example.py"
    # uri = "file://" + file_path
    # text = open(file_path, "r").read()
    # languageId = pylspclient.lsp_structs.LANGUAGE_IDENTIFIER.PYTHON
    # version = 1
    # lsp_client.didOpen(
    #     pylspclient.lsp_structs.TextDocumentItem(uri, languageId, version, text)
    # )

    # file_path_wrong = "D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/example/example-wrong.py"
    # new_text = open(file_path_wrong, "r").read()
    # document = pylspclient.lsp_structs.VersionedTextDocumentIdentifier(uri, version)
    # change = pylspclient.lsp_structs.TextDocumentContentChangeEvent(new_text)
    # lsp_client.didChange(
    #     pylspclient.lsp_structs.DidChangeTextDocumentParams(document, [change])
    # )


async def test_main():
    class TestClient(JsonRPCClient):
        server_exit_called = False

        async def server_exit(self, server: asyncio.subprocess.Process):
            self.server_exit_called = True
            assert server.returncode == 0

    client = TestClient()
    await client.start_io(sys.executable, "-c", "print('Hello, World!')")
    await asyncio.sleep(1)
    await client.stop()

    message = "Expected the `server_exit` method to have been called."
    assert client.server_exit_called, message


if __name__ == "__main__":
    asyncio.run(test_main())
