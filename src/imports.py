import os
import ast
import logging
import re
from typing import Dict, List, Optional, Union
import typing
import libcst as cst

EXCEPTIONS_AND_ERROS = {
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

BUILT_IN_TYPES = {
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
    "",
} | EXCEPTIONS_AND_ERROS


def get_classes_from_file(file_path: str) -> Dict[str, str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        print(e)
        logger = logging.getLogger(__name__)
        logger.error(e)

    class_dict = {
        node.name: file_path
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }
    return class_dict


def get_all_classes_in_project(
    project_path: str, venv_path: str | None
) -> Dict[str, str]:
    if venv_path is not None:
        venv_directory = venv_path.split(os.sep)[-1]

    classes = {}
    for root, dirs, files in os.walk(project_path):
        # Ignore the virtual environment directory
        if venv_path and venv_directory in dirs:
            dirs.remove(venv_directory)
        else:
            for venv_name in {"venv", ".venv", "env", ".env", "virtualenv"}:
                if venv_name in dirs:
                    dirs.remove(venv_name)
                    break

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                classes |= get_classes_from_file(file_path)
    return classes


def get_all_classes_in_virtual_environment(venv_path: str) -> Dict[str, str]:
    classes = {}
    packages_path = os.path.join(venv_path, "Lib", "site-packages")
    for root, _, files in os.walk(packages_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                classes |= get_classes_from_file(file_path)
    return classes


def _get_import_module_path(
    project_classes: Dict[str, str], annotation: str, current_file: str
) -> str:
    relative_path = os.path.relpath(
        project_classes[annotation],
        current_file,
    )
    path_list = relative_path.removesuffix(".py").split("\\")
    path_list = [x for x in path_list if x != ".."]
    module_path = ".".join(path_list)
    return module_path


def add_import_to_searchtree(
    all_project_classes: Dict[str, str],
    file_path: str,
    source_code_tree: cst.Module,
    type_annotation: str,
):
    potential_annotation_imports = (
        list(filter(None, re.split("\[|\]|,\s*", type_annotation)))
        if "[" in type_annotation
        else [type_annotation]
    )

    # Handle "|" edge case
    potential_annotation_imports = [
        item.strip() for imp in potential_annotation_imports for item in imp.split("|")
    ]

    # Handle "Literal" edge case
    if "Literal" in potential_annotation_imports:
        literal_index = potential_annotation_imports.index("Literal")
        if literal_index + 1 < len(potential_annotation_imports):
            del potential_annotation_imports[literal_index + 1]

    unknown_annotations = set()
    for annotation in potential_annotation_imports:
        if annotation in BUILT_IN_TYPES:
            continue
        elif annotation == "Incomplete":
            continue
        elif annotation == "Unknown":
            # Check if Unknown would otherwise be classified as unknown_annotations if this condition was not added
            continue
        elif annotation in typing.__all__ or annotation in ["LiteralString", "Self"]:
            transformer = ImportInserter(f"from typing import {annotation}")
            source_code_tree = source_code_tree.visit(transformer)
        elif "." in annotation:
            if annotation == "...":
                continue
            module, annotation = annotation.rsplit(".", 1)
            transformer = ImportInserter(f"from {module} import {annotation}")
            source_code_tree = source_code_tree.visit(transformer)
        elif annotation in all_project_classes:
            import_module_path = _get_import_module_path(
                all_project_classes, annotation, file_path
            )

            if import_module_path == ".":
                continue

            transformer = ImportInserter(
                f"from {import_module_path} import {annotation}"
            )
            source_code_tree = source_code_tree.visit(transformer)
        else:
            unknown_annotations.add(annotation)
            continue
    return source_code_tree, unknown_annotations


class ImportInserter(cst.CSTTransformer):
    def __init__(self, import_statement: str):
        self.import_statement = import_statement
        self.imports: List[Union[cst.Import, cst.ImportFrom]] = []

    def visit_Import(self, node: cst.Import) -> cst.Import:
        self.imports.append(node)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> cst.ImportFrom:
        self.imports.append(node)

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        imp = cst.parse_statement(self.import_statement)
        existing_import_items = set(
            [
                n.evaluated_name
                for i in self.imports
                if not isinstance(i.names, cst.ImportStar)
                for n in i.names
            ]
        )
        import_item = imp.body[0].names[0].evaluated_name
        if import_item not in existing_import_items:
            body_with_import = (imp,) + updated_node.body
            return updated_node.with_changes(body=body_with_import)
        return updated_node


# get_all_classes_in_project(
#     "D:/Documents/test2/plagiarism-checker",
# )
# get_all_classes_in_virtual_environment(
#     "D:/Documents/test2/plagiarism-checker/t/.venv",
# )
