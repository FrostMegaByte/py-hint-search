import logging
from typing import Any, Dict, List, Tuple, Union
import libcst as cst
from libcst.metadata import PositionProvider
from colorama import Fore

from annotations import (
    insert_parameter_annotation,
    insert_return_annotation,
)
from fake_editor import FakeEditor
from imports import add_import_to_searchtree

TypeSlotPredictions = List[List[Union[str, float]]]


def transform_predictions_to_array_to_process(
    func_predictions: List[Dict[str, Any]],
    type_annotated: Dict[Tuple[str, ...], List[str]],
) -> List[TypeSlotPredictions]:
    array_to_process = []
    for func in func_predictions:
        func_name = func["q_name"].split(".")
        if "<locals>" in func_name:
            func_name = [x for x in func_name if x != "<locals>"]
        func_name = tuple(func_name)

        if func_name not in type_annotated:
            continue

        # First try parameters
        for param_name, param_predictions in func["params_p"].items():
            if (
                param_name in {"self", "args", "kwargs"}
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


def build_tree(
    search_tree_layers: List[TypeSlotPredictions], top_k: int
) -> Dict[str, Dict[str, Any]]:
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
    all_project_classes: Dict[str, str],
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

        print(
            f"{layer_index}: {type_slot['func_name']}-{type_slot['param_name']} -> {type_annotation}"
        )

        # Handle imports of type annotations
        current_file_path = editor.edit_document.uri.removeprefix("file:///")
        tree_with_import, is_unknown_annotation = add_import_to_searchtree(
            all_project_classes,
            current_file_path,
            modified_trees[layer_index],
            type_annotation,
        )
        modified_trees[layer_index] = tree_with_import

        if is_unknown_annotation:
            layer_specific_indices[layer_index] += 1
            continue

        # Add type annotation to source code
        modified_tree, modified_location = (
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

        # print(modified_tree.code)
        # print("-----------------------------------")

        partial_tree = None
        wrapper = cst.MetadataWrapper(modified_tree)
        positions = wrapper.resolve(PositionProvider)
        for node, position in positions.items():
            if position == modified_location:
                partial_tree = cst.Module(body=[node])

        if partial_tree is not None:
            editor.change_part_of_file(partial_tree.code, modified_location)
        else:
            editor.change_file(modified_tree.code, modified_location)

        # On error, change pointers to try next type annotation
        if editor.has_diagnostic_error():
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
        print(f"{Fore.RED}No possible combination of type annotations found...")
        logger = logging.getLogger(__name__)
        logger.error("No possible combination of type annotations found...")
        return original_source_code_tree

    if layer_index == number_of_type_slots:
        print(f"{Fore.GREEN}Found a combination of type annotations!")
        logger = logging.getLogger(__name__)
        logger.info("Found a combination of type annotations!")

    return modified_trees[number_of_type_slots]
