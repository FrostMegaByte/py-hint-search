import os
import ast
from typing import Dict


def get_classes_from_file(file_path) -> Dict[str, str]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

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
    classes: Dict[str, str], annotation: str, current_file: str
) -> str:
    if annotation in classes:
        relative_path = os.path.relpath(
            classes[annotation],
            current_file,
        )
        path_list = relative_path.removesuffix(".py").split("\\")
        # TODO: Check if [1:] is correct in all cases
        module_path = ".".join(path_list[1:])
        return module_path
    else:
        return None
