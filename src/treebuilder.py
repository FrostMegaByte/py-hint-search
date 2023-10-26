import re
from typing import Any, Dict, List
import typing
import libcst as cst
from annotation_inserter import insert_parameter_annotation, insert_return_annotation
from classes_gatherer import get_import_module_path
from fake_editor import FakeEditor
from import_inserter import ImportInserter

BUILT_IN_TYPES = [
    "bool",
    "int",
    "float",
    "complex",
    "str",
    "list",
    "tuple",
    "range",
    "bytes",
    "bytearray",
    "memoryview",
    "dict",
    "set",
    "frozenset",
    "None",
    "",
]

# def filter_parameters(param, annotated_function_params):
#     return param not in ["args", "kwargs"] or param not in annotated_function_params


def transform_predictions_to_array_to_process(func_predictions, type_annotated):
    array_to_process = []
    for func in func_predictions:
        func_name = func["name"]
        # First try parameters
        for param_name, param_predictions in func[
            "params_p"
        ].items():  # TODO: use filter function
            if (
                param_name in ["self", "args", "kwargs"]
                or param_name in type_annotated[func_name]
            ):
                continue

            # Dirty trick of adding function name and parameter name information to the predictions
            param_predictions.insert(0, [func_name, param_name])
            array_to_process.append(param_predictions)

        # Then try return type
        # Continuation of dirty trick of adding function name and parameter name information to the predictions
        if "return" in type_annotated[func_name]:
            continue

        if "ret_type_p" in func:
            func["ret_type_p"].insert(0, [func_name, "return"])
            array_to_process.append(func["ret_type_p"])
        else:
            array_to_process.append([[func_name, "return"], ["None", 1.0]])

    return array_to_process


def build_tree(search_tree_layers, top_k: int) -> Dict[str, Dict[str, Any]]:
    search_tree = {}
    for layer_index in range(len(search_tree_layers)):
        func_name, param_name = search_tree_layers[layer_index].pop(0)
        search_tree[f"layer_{layer_index}"] = {
            "func_name": func_name,
            "param_name": param_name,
            "predictions": search_tree_layers[layer_index][:top_k] + [["", 0]],
        }

    return search_tree


def depth_first_traversal(
    search_tree: Dict[str, Dict[str, Any]],
    original_source_code_tree: cst.Module,
    editor: FakeEditor,
    number_of_type_slots: int,
    all_project_classes,
):
    layer_index = 0
    layer_specific_indices = [0] * number_of_type_slots
    slot_annotations = [""] * number_of_type_slots
    modified_trees = [original_source_code_tree] + [None] * number_of_type_slots

    while 0 <= layer_index < number_of_type_slots:
        type_slot = search_tree[f"layer_{layer_index}"]
        type_annotation = type_slot["predictions"][layer_specific_indices[layer_index]][
            0
        ]

        # Type4Py sometimes returns type annotations with quotes which breaks some stuff, so must be removed
        if '"' in type_annotation:
            type_annotation = type_annotation.strip('"')

        slot_annotations[layer_index] = type_annotation
        # Clear right side of the array as those type annotations are not yet known because of backtracking
        slot_annotations[layer_index + 1 :] = [""] * (
            number_of_type_slots - (layer_index + 1)
        )

        # Handle imports of type annotations
        potential_annotation_imports = (
            list(filter(None, re.split("\[|\]|,\s*", type_annotation)))
            if "[" in type_annotation
            else [type_annotation]
        )

        unknown_annotation = False
        for annotation in potential_annotation_imports:
            if annotation in BUILT_IN_TYPES:
                continue
            elif annotation in typing.__all__:
                transformer = ImportInserter(f"from typing import {annotation}")
                modified_trees[layer_index] = modified_trees[layer_index].visit(
                    transformer
                )
            elif annotation in all_project_classes:
                current_file_path = editor.edit_document.uri.removeprefix("file:///")
                import_module_path = get_import_module_path(
                    all_project_classes, annotation, current_file_path
                )

                if import_module_path is None:
                    unknown_annotation = True
                    break

                transformer = ImportInserter(
                    f"from {import_module_path} import {annotation}"
                )
                modified_trees[layer_index] = modified_trees[layer_index].visit(
                    transformer
                )
            else:
                unknown_annotation = True
                break

        if unknown_annotation:
            layer_specific_indices[layer_index] += 1
            continue

        # Add type annotation to source code
        modified_tree = (
            insert_return_annotation(
                modified_trees[layer_index],
                type_annotation,
                type_slot["func_name"],
            )
            if type_slot["param_name"] == "return"
            else insert_parameter_annotation(
                modified_trees[layer_index],
                type_annotation,
                type_slot["func_name"],
                type_slot["param_name"],
            )
        )

        print(modified_tree.code)
        print("-----------------------------------")

        editor.change_file(modified_tree.code)

        # On error, change pointers to try next type annotation
        if editor.has_diagnostic_error():
            print("Diagnostic error found!")
            layer_specific_indices[layer_index] += 1
            while layer_specific_indices[layer_index] >= len(
                search_tree[f"layer_{layer_index}"]["predictions"]
            ):
                layer_specific_indices[layer_index] = 0
                layer_index -= 1
                if layer_index < 0:
                    break
                layer_specific_indices[layer_index] += 1
        else:
            modified_trees[layer_index + 1] = modified_tree
            modified_trees[layer_index + 2 :] = [None] * (
                number_of_type_slots - (layer_index + 1)
            )
            layer_index += 1

    if layer_index < 0:
        print("No possible combination of type annotations found...")
        return original_source_code_tree

    if layer_index == number_of_type_slots:
        print("Found a combination of type annotations!")

    return modified_trees[number_of_type_slots]
