from typing import List, Tuple, TypeAlias, Union

TypeSlot: TypeAlias = Tuple[str, ...]
Predictions: TypeAlias = List[List[Union[str, float]]]

EXCEPTIONS_AND_ERRORS = {
    "Exception",
    "BaseException",
    "GeneratorExit",
    "KeyboardInterrupt",
    "SystemExit",
    "Exception",
    "StopIteration",
    "OSError",
    "EnvironmentError",
    "IOError",
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "BufferError",
    "EOFError",
    "ImportError",
    "LookupError",
    "MemoryError",
    "NameError",
    "ReferenceError",
    "RuntimeError",
    "StopAsyncIteration",
    "SyntaxError",
    "SystemError",
    "TypeError",
    "ValueError",
    "FloatingPointError",
    "OverflowError",
    "ZeroDivisionError",
    "ModuleNotFoundError",
    "IndexError",
    "KeyError",
    "UnboundLocalError",
    "BlockingIOError",
    "ChildProcessError",
    "ConnectionError",
    "BrokenPipeError",
    "ConnectionAbortedError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "FileExistsError",
    "FileNotFoundError",
    "InterruptedError",
    "IsADirectoryError",
    "NotADirectoryError",
    "PermissionError",
    "ProcessLookupError",
    "TimeoutError",
    "NotImplementedError",
    "RecursionError",
    "IndentationError",
    "TabError",
    "UnicodeError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeTranslateError",
    "Warning",
    "UserWarning",
    "DeprecationWarning",
    "SyntaxWarning",
    "RuntimeWarning",
    "FutureWarning",
    "PendingDeprecationWarning",
    "ImportWarning",
    "UnicodeWarning",
    "BytesWarning",
    "ResourceWarning",
}

BUILT_IN_TYPES = EXCEPTIONS_AND_ERRORS | {
    "bool",
    "int",
    "float",
    "complex",
    "str",
    "list",
    "tuple",
    "dict",
    "set",
    "frozenset",
    "range",
    "bytes",
    "bytearray",
    "memoryview",
    "None",
    "object",
    "type",
}

# Top 10 annotations
UBIQUITOUS_ANNOTATIONS = {
    "str",
    "int",
    "List",
    "bool",
    "float",
    "Dict",
    "Union",
    "Tuple",
    "Set",
    "Callable",
    # Keep None and Any as ubiquitous, although they are usually filtered out depending on the metric
    "Any",
    "None",
}

# Top 100 annotations (covers 98%)
COMMON_ANNOTATIONS = UBIQUITOUS_ANNOTATIONS | {
    "Connection",
    "Flask",
    "Logger",
    "object",
    "Exception",
    "<List>",
    "Issue",
    "Redis",
    "Literal",
    "Candidates",
    "View",
    "Context",
    "ndarray",
    "Application",
    "Node",
    "Article",
    "Name",
    "Task",
    "Container",
    "PartyID",
    "Tensor",
    "T",
    "Token",
    "bytes",
    "Table",
    "Model",
    "Mapping",
    "URL",
    "Namespace",
    "Configuration",
    "datetime",
    "Settings",
    "Decimal",
    "IO",
    "Parameter",
    "_T",
    "type",
    "Client",
    "Generator",
    "Result",
    "AsyncIterator",
    "UserContext",
    "BaseException",
    "Item",
    "Field",
    "Iterable",
    "Root",
    "Vertex",
    "Request",
    "DataT",
    "GlobalState",
    "Mock",
    "...",
    "Variable",
    "Sequence",
    "Text",
    "date",
    "UserID",
    "BytesIO",
    "MagicMock",
    "Scope",
    "Module",
    "Outcome",
    "Message",
    "DataFrame",
    "Awaitable",
    "Response",
    "User",
    "Session",
    "ArgumentParser",
    "Collection",
    "BlockHeaderAPI",
    "State",
    "ID",
    "CWLObjectType",
    "HttpRequest",
    "Qubit",
    "Type",
    "Nvim",
    "Iterator",
    "Event",
    "Config",
    "LiteralString",
    "Address",
    "Expr",
    "timedelta",
    "Path",
    "Source",
}
