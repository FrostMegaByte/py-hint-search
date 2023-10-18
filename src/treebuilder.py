import copy
from typing import Any, Dict, List
import libcst as cst
from annotation_inserter import insert_parameter_annotation, insert_return_annotation
from fake_editor import FakeEditor

predictions = [
    {
        "name": "multiply",
        "params_p": {
            "a": [
                ["int", 0.22659382019962282],
                ["bool", 0.2022255751506991],
                ["float", 0.10683424624716305],
            ],
            "args": [None],
            "b": [
                ["str", 0.22659382019962282],
                ["int", 0.2022255751506991],
                ["float", 0.10683424624716305],
            ],
            # "c": [
            #     ["float", 0.22659382019962282],
            #     ["str", 0.2022255751506991],
            #     ["bool", 0.10683424624716305],
            # ],
            "kwargs": [None],
        },
        "ret_type_p": [
            ["bool", 0.22659382019962282],
            ["int", 0.2022255751506991],
            ["Union[int, float]", 0.10683424624716305],
            ["float", 0.09460898903951602],
            ["Tuple[bool]", 0.09456387416250926],
            ["Tuple[int, int]", 0.09054582378738726],
        ],
    },
    # {
    #     "name": "sum",
    #     "params_p": {
    #         "x": [
    #             ["q", 0.22659382019962282],
    #             ["w", 0.2022255751506991],
    #             ["f", 0.10683424624716305],
    #         ],
    #         "args": [None],
    #         "y": [
    #             ["p", 0.22659382019962282],
    #             ["g", 0.2022255751506991],
    #             ["j", 0.10683424624716305],
    #         ],
    #         "kwargs": [None],
    #     },
    #     "ret_type_p": [
    #         ["l", 0.37194584766029465],
    #         ["u", 0.32219782568421174],
    #         ["y", 0.1037741467367993],
    #     ],
    # },
]


class Node:
    def __init__(
        self,
        typeAnnotation: str,
        probability: float,
        func_name: str,
        param_name: str,
        layer_index: int,
    ):
        self.typeAnnotation = typeAnnotation
        self.probability = probability
        self.func_name = func_name
        self.param_name = param_name
        self.layer_index = layer_index
        self.children: List[Node] = []

    def __repr__(self):
        return f"{self.typeAnnotation}"


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


def build_tree1(root: Node, search_tree_layers, top_k: int) -> Node:
    queue = [(root, 0)]
    next_layer_index = 0
    while queue:
        node, index = queue.pop(0)
        if index >= len(search_tree_layers):
            continue

        # Needed because of the dirty trick to pass extra information
        if index == next_layer_index:
            func_name, param_name = search_tree_layers[index].pop(0)
            next_layer_index += 1

        node.children = [
            Node(x[0], x[1], func_name, param_name, index + 1)
            for x in search_tree_layers[index][:top_k]
        ]
        node.children.append(Node("", 1, func_name, param_name, index + 1))
        for child_node in node.children:
            queue.append((child_node, child_node.layer_index))
    return root


#  Faster version of build_tree due to caching of children
def build_tree2(root: Node, search_tree_layers, top_k: int) -> Node:
    queue = [(root, 0)]
    next_layer_index = 0
    while queue:
        node, index = queue.pop(0)
        if index >= len(search_tree_layers):
            continue

        # Needed because of the dirty trick to pass extra information
        if index == next_layer_index:
            func_name, param_name = search_tree_layers[index].pop(0)
            children = [
                Node(x[0], x[1], func_name, param_name, index + 1)
                for x in search_tree_layers[index][:top_k]
            ]
            children.append(Node("", 1, func_name, param_name, index + 1))
            next_layer_index += 1

        node.children = children
        for child_node in node.children:
            queue.append((child_node, child_node.layer_index))
    return root


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
):
    layer_index = 0
    layer_specific_indices = [0] * number_of_type_slots
    slot_annotations = [""] * number_of_type_slots
    modified_trees = [original_source_code_tree] + [None] * number_of_type_slots
    source_code_tree = copy.deepcopy(original_source_code_tree)

    while 0 <= layer_index < number_of_type_slots:
        type_slot = search_tree[f"layer_{layer_index}"]
        type_annotation = type_slot["predictions"][layer_specific_indices[layer_index]][
            0
        ]
        slot_annotations[layer_index] = type_annotation
        # Clear right side of the array as those type annotations are not yet known because of backtracking
        slot_annotations[layer_index + 1 :] = [""] * (
            number_of_type_slots - (layer_index + 1)
        )

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

        modified_trees[layer_index + 1] = modified_tree
        modified_trees[layer_index + 2 :] = [None] * (
            number_of_type_slots - (layer_index + 1)
        )

        print(modified_tree.code)
        print("-----------------------------------")

        editor.change_file(modified_tree.code)

        if editor.has_diagnostic_error():
            print("Diagnostic error found!")
            if layer_specific_indices[layer_index] >= len(type_slot["predictions"]) - 1:
                layer_specific_indices[layer_index] = 0
                layer_index -= 1
            layer_specific_indices[layer_index] += 1
        else:
            source_code_tree = modified_tree
            layer_index += 1

    if layer_index == number_of_type_slots:
        print("Found a combination of type annotations!")

    return source_code_tree


# def depth_first_traversal(
#     tree: Node,
#     original_source_code_tree: cst.Module,
#     editor: FakeEditor,
#     number_of_type_slots: int,
# ):
#     if not tree:
#         return original_source_code_tree

#     # Ignore the top level node as it is just a dummy node
#     stack: List[Node] = list(reversed(tree.children))
#     slot_annotations = [""] * number_of_type_slots
#     modified_trees = [original_source_code_tree] + [None] * number_of_type_slots

#     source_code_tree = copy.deepcopy(original_source_code_tree)

#     while len(stack) > 0:
#         current = stack.pop()
#         slot_annotations[current.layer_index - 1] = current.typeAnnotation
#         # Clear right side of the array as those type annotations are not yet known because of backtracking
#         slot_annotations[current.layer_index :] = [""] * (
#             number_of_type_slots - current.layer_index
#         )

#         # Add type annotation to source code
#         modified_tree = (
#             insert_return_annotation(
#                 modified_trees[current.layer_index - 1],
#                 current.typeAnnotation,
#                 current.func_name,
#             )
#             if current.param_name == "return"
#             else insert_parameter_annotation(
#                 modified_trees[current.layer_index - 1],
#                 current.typeAnnotation,
#                 current.func_name,
#                 current.param_name,
#             )
#         )

#         modified_trees[current.layer_index] = modified_tree
#         modified_trees[current.layer_index + 1 :] = [None] * (
#             number_of_type_slots - current.layer_index
#         )

#         print(modified_tree.code)
#         print("-----------------------------------")

#         editor.change_file(modified_tree.code)

#         if editor.has_diagnostic_error():
#             print("Diagnostic error found!")
#             continue

#         source_code_tree = modified_tree

#         # If leaf node and no errors found, then we have found the correct type annotations
#         if len(current.children) == 0:
#             print("Found a combination of type annotations!")
#             break

#         # if typecheck on current type annotation fails {
#         #   continue; # As this branch is invalid
#         #   Also keep a counter where if all TOP_K type annotations fail, then keep type annotation empty and add top 1 from the next level to the stack to continue the search
#         # }

#         for child in list(reversed(current.children)):
#             stack.append(child)

#     if len(stack) == 0:
#         print("No correct combination of type annotations found...")
#         return original_source_code_tree

#     return source_code_tree
