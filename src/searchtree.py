import logging
import re
import time
from typing import Any, Dict, List, Tuple, Union, TypeAlias
import libcst as cst
from colorama import Fore

from annotations import (
    insert_parameter_annotation,
    insert_return_annotation,
)
from fake_editor import FakeEditor
from imports import add_import_to_source_code_tree

TypeSlot: TypeAlias = Tuple[str, ...]
Predictions: TypeAlias = List[List[Union[str, float]]]


def transform_predictions_to_slots_to_search(
    func_predictions: List[Dict[str, Any]],
    available_slots: List[TypeSlot],
) -> Dict[TypeSlot, Predictions]:
    slots_to_search = {}
    for func in func_predictions:
        func_name = func["q_name"].split(".")
        if "<locals>" in func_name:
            func_name = [x for x in func_name if x != "<locals>"]

        # First try parameters
        for param_name, param_predictions in func["params_p"].items():
            type_slot = tuple(func_name + [param_name])
            if type_slot not in available_slots:
                continue

            slots_to_search[type_slot] = param_predictions

        # Then try return type
        type_slot = tuple(func_name + ["return"])
        if type_slot not in available_slots:
            continue

        if "ret_type_p" in func:
            slots_to_search[type_slot] = func["ret_type_p"]
        else:
            slots_to_search[type_slot] = [["None", 1.0]]

    return slots_to_search


def build_search_tree(
    search_tree_layers: Dict[TypeSlot, Predictions],
    top_k: int,
) -> Dict[str, Dict[str, Any]]:
    search_tree = {}
    for layer_index, (slot, preds) in enumerate(search_tree_layers.items()):
        func_name, param_name = slot[:-1], slot[-1]
        search_tree[f"layer_{layer_index}"] = {
            "func_name": func_name,
            "param_name": param_name,
            "predictions": preds[:top_k] + [["", 0]],
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
    logger = logging.getLogger("main")

    start_time = time.time()
    while 0 <= layer_index < number_of_type_slots:
        if time.time() - start_time > 5 * 60:
            print(
                f"{Fore.RED}Timeout after 5 minutes. File takes too long to process. Likely backtracking is taking too long..."
            )
            logger.error(
                "Timeout after 5 minutes. File takes too long to process. Likely backtracking is taking too long..."
            )
            return original_source_code_tree

        type_slot = search_tree[f"layer_{layer_index}"]
        type_annotation = type_slot["predictions"][layer_specific_indices[layer_index]][
            0
        ]

        # Type4Py sometimes returns type annotations with quotes which breaks some stuff, so must be removed
        if '"' in type_annotation or "'" in type_annotation:
            type_annotation = re.sub(r"[\"']", "", type_annotation)

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
        tree_with_import, is_unknown_annotation = add_import_to_source_code_tree(
            modified_trees[layer_index],
            type_annotation,
            all_project_classes,
            current_file_path,
        )
        modified_trees[layer_index] = tree_with_import

        if is_unknown_annotation:
            layer_specific_indices[layer_index] += 1
            continue

        if "." in type_annotation and "[" in type_annotation:
            type_annotations_to_strip = list(
                filter(None, re.split("\[|\]|,\s*", type_annotation))
            )
            for annotation in type_annotations_to_strip:
                if "." in annotation and not "..." in annotation:
                    annotation_stripped = annotation.rsplit(".", 1)[1]
                    type_annotation = type_annotation.replace(
                        annotation, annotation_stripped
                    )

        if "." in type_annotation and not "..." in type_annotation:
            type_annotation = type_annotation.rsplit(".", 1)[1]

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
        logger.error("No possible combination of type annotations found...")
        return original_source_code_tree

    if layer_index == number_of_type_slots:
        print(f"{Fore.GREEN}Found a combination of type annotations!")
        logger.info("Found a combination of type annotations!")

    return modified_trees[number_of_type_slots]
