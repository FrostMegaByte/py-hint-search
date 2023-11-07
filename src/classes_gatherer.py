import logging
import os
import ast
from typing import Dict


def get_classes_from_file(file_path) -> Dict[str, str]:
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


def get_all_classes_in_project(project_path) -> Dict[str, str]:
    classes = {}
    for root, _, files in os.walk(project_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                classes |= get_classes_from_file(file_path)
    return classes


def get_import_module_path(
    project_classes: Dict[str, str], annotation: str, current_file: str
) -> str:
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
