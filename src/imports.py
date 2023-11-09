import os
import ast
import logging
from typing import Dict, Optional
import libcst as cst
import libcst.matchers as m


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


def get_all_classes_in_project(project_path: str) -> Dict[str, str]:
    classes = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                classes |= get_classes_from_file(file_path)
    return classes


def get_import_module_path(
    project_classes: Dict[str, str], annotation: str, current_file: str
) -> Optional[str]:
    if annotation in project_classes:
        relative_path = os.path.relpath(
            project_classes[annotation],
            current_file,
        )
        path_list = relative_path.removesuffix(".py").split("\\")
        path_list = [x for x in path_list if x != ".."]
        module_path = ".".join(path_list)
        return module_path
    else:
        return None


class ImportInserter(cst.CSTTransformer):
    def __init__(self, import_statement: str):
        self.import_statement = import_statement

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        imp = cst.parse_statement(self.import_statement)
        # import2 = cst.parse_statement("from taart import Taart")

        # # Check if the two import statements match
        # if m.matches(imp, import2):
        #     print("The import statements are the same")
        # else:
        #     print("The import statements are different")

        # import_is_present = bool(
        #     [True for i in updated_node.children if m.matches(i, imp)]
        # )
        # if not import_is_present:
        body_with_import = (imp,) + updated_node.body
        return updated_node.with_changes(body=body_with_import)
