import os
import ast
import logging
import re
import fnmatch
import pkgutil
import inspect
import importlib
import contextlib
import sys
from types import ModuleType
from typing import Dict, List, Optional, Set, Union
import typing
import libcst as cst
import libcst.matchers as m

from constants import BUILT_IN_TYPES


def get_classes_from_file(file_path: str) -> Dict[str, str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        logger = logging.getLogger("main")
        logger.error(e)

    classes = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        classes[node.name] = file_path
    return classes


def get_all_classes_in_project(
    project_path: str, venv_path: str | None
) -> Dict[str, str]:
    if venv_path is not None:
        venv_directory = venv_path.split(os.sep)[-1]

    all_classes = {}
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
                all_classes |= get_classes_from_file(file_path)
    return all_classes


def find_site_packages(venv_path: str) -> str | None:
    for root, dirnames, filenames in os.walk(venv_path):
        for dirname in fnmatch.filter(dirnames, "site-packages"):
            return os.path.join(root, dirname)


def get_classes_from_module(module: ModuleType):
    classes = {}
    for name, _ in inspect.getmembers(module, inspect.isclass):
        if not name.startswith("_"):
            classes[name] = module.__file__

    # Store the original sys.argv and clear it to avoid argument clashes during the import of a module using importlib
    original_args = sys.argv
    sys.argv = []
    if hasattr(module, "__path__"):
        for _, name, _ in pkgutil.iter_modules(module.__path__):
            try:
                submodule = importlib.import_module(f"{module.__name__}.{name}")
                classes.update(get_classes_from_module(submodule))
            except Exception:
                continue
    # Restore the original sys.argv
    sys.argv = original_args
    return classes


def get_all_classes_in_virtual_environment(venv_path: str):
    all_classes = {}
    packages_path = find_site_packages(venv_path)
    for finder, name, ispkg in pkgutil.iter_modules([packages_path]):
        try:
            with contextlib.redirect_stdout(open(os.devnull, "w")):
                module = importlib.import_module(name)
        except Exception:
            continue

        all_classes.update(get_classes_from_module(module))

    return all_classes


def _get_import_module_path(
    project_classes: Dict[str, str], annotation: str, current_file: str
) -> str:
    relative_path = os.path.relpath(
        project_classes[annotation],
        current_file,
    )
    path_list = relative_path.removesuffix(".py").split(os.sep)
    if "site-packages" in path_list:
        path_list = path_list[path_list.index("site-packages") + 1 :]
    path_list = [x for x in path_list if x != ".."]
    module_path = ".".join(path_list)
    return module_path


def add_import_to_source_code_tree(
    source_code_tree: cst.Module,
    type_annotation: str,
    all_project_classes: Dict[str, str],
    file_path: str,
):
    logger = logging.getLogger("main")
    if type_annotation.startswith("(") and type_annotation.endswith(")"):
        type_annotation = type_annotation[1:-1]

    # Handle "Literal" edge case
    if "Literal" in type_annotation:
        type_annotation = re.sub(r"Literal\[[^\]]*\]", "Literal", type_annotation)

    potential_annotation_imports = list(
        filter(None, re.split("\[|\]|,\s*|\s*\|\s*", type_annotation))
    )
    potential_annotation_imports = list(dict.fromkeys(potential_annotation_imports))

    visitor_imports = ImportsCollector()
    source_code_tree.visit(visitor_imports)

    visitor_aliases = TypeAliasesCollector()
    source_code_tree.visit(visitor_aliases)

    unknown_annotations = set()
    for annotation in potential_annotation_imports:
        if annotation in BUILT_IN_TYPES or annotation == "":
            continue
        elif annotation in visitor_imports.existing_import_items:
            continue
        elif annotation in visitor_aliases.existing_type_aliases:
            continue
        elif annotation in typing.__all__ or annotation in ["LiteralString", "Self"]:
            transformer = ImportInserter(f"from typing import {annotation}")
            source_code_tree = source_code_tree.visit(transformer)
        elif annotation == "Unknown":
            # If Pyright cannot infer the type, it occasionally uses "Unknown" as the type.
            # Although not officially supported, it is similar to "Any" and thus we need a TypeAlias for it.
            transformer_alias = TypeAliasInserter("Unknown: TypeAlias = Any")
            source_code_tree = source_code_tree.visit(transformer_alias)
            if "TypeAlias" not in visitor_imports.existing_import_items:
                transformer_import_type_alias = ImportInserter(
                    f"from typing_extensions import TypeAlias"
                )
                source_code_tree = source_code_tree.visit(transformer_import_type_alias)
            if "Any" not in visitor_imports.existing_import_items:
                transformer_import = ImportInserter(f"from typing import Any")
                source_code_tree = source_code_tree.visit(transformer_import)
        elif "." in annotation:
            if annotation == "...":
                continue
            module, annotation = annotation.rsplit(".", 1)
            try:
                transformer = ImportInserter(f"from {module} import {annotation}")
                source_code_tree = source_code_tree.visit(transformer)
            except Exception as e:
                print(
                    f"Import error. Original type '{type_annotation}'. Import 'from {module} import {annotation}' failed"
                )
                logger.error(
                    f"Import error. Original type '{type_annotation}'. Import 'from {module} import {annotation}' failed"
                )
                logger.error(e)
                continue
        elif annotation in all_project_classes:
            import_module_path = _get_import_module_path(
                all_project_classes, annotation, file_path
            )

            if import_module_path == ".":
                continue

            try:
                transformer = ImportInserter(
                    f"from {import_module_path} import {annotation}"
                )
                source_code_tree = source_code_tree.visit(transformer)
            except Exception as e:
                print(
                    f"Import error. Original type '{type_annotation}'. Import 'from {import_module_path} import {annotation}' failed"
                )
                logger.error(
                    f"Import error. Original type '{type_annotation}'. Import 'from {import_module_path} import {annotation}' failed"
                )
                logger.error(e)
                continue
        else:
            unknown_annotations.add(annotation)
            continue
    return source_code_tree, unknown_annotations


class ImportsCollector(cst.CSTVisitor):
    def __init__(self):
        self.imports: List[Union[cst.Import, cst.ImportFrom]] = []
        self.existing_import_items: Set[str] = set()

    def visit_Import(self, node: cst.Import) -> Optional[bool]:
        self.imports.append(node)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> Optional[bool]:
        self.imports.append(node)

    def leave_Module(self, node: cst.Module) -> None:
        self.existing_import_items = set()
        for i in self.imports:
            if m.matches(i.names, m.ImportStar()):
                continue
            for n in i.names:
                self.existing_import_items.add(n.evaluated_name)
                if n.evaluated_alias is not None:
                    self.existing_import_items.add(n.evaluated_alias)


class ImportInserter(cst.CSTTransformer):
    def __init__(self, import_statement: str):
        self.import_statement = import_statement

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        imp = cst.parse_statement(self.import_statement)
        body_with_import = (imp,) + updated_node.body
        return updated_node.with_changes(body=body_with_import)


class TypeAliasesCollector(cst.CSTVisitor):
    def __init__(self):
        self.type_aliases: List[cst.AnnAssign] = []
        self.existing_type_aliases: Set[str] = set()

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if m.matches(node.annotation, m.Annotation(annotation=m.Name("TypeAlias"))):
            self.type_aliases.append(node)

    def leave_Module(self, node: cst.Module) -> None:
        self.existing_type_aliases = set([ta.target.value for ta in self.type_aliases])


class TypeAliasInserter(cst.CSTTransformer):
    def __init__(self, type_alias: str):
        self.type_alias = type_alias

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        type_alias = cst.parse_statement(self.type_alias)
        body_with_type_alias = (type_alias,) + updated_node.body
        return updated_node.with_changes(body=body_with_type_alias)


def handle_binary_operation_imports(
    source_code_tree: cst.Module,
    should_import_optional: bool,
    should_import_union: bool,
) -> cst.Module:
    if not should_import_optional and not should_import_union:
        return source_code_tree

    imports = []
    if should_import_optional:
        imports.append("Optional")
    if should_import_union:
        imports.append("Union")

    import_statement = "from typing import " + ", ".join(imports)
    transformer = ImportInserter(import_statement)
    source_code_tree = source_code_tree.visit(transformer)
    return source_code_tree
