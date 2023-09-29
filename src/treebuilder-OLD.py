from api import get_type4py_predictions_example
from typing import List, Union
import libcst as cst

TOP_K = 3

# arr: List[List[List[str, float]]] = [
#    [
#        # ["multiply", "return"],
#         ["bool", 0.22659382019962282],
#         ["int", 0.2022255751506991],
#         ["Union[int, float]", 0.10683424624716305],
#         ["float", 0.09460898903951602],
#         ["Tuple[bool]", 0.09456387416250926],
#         ["Tuple[int, int]", 0.09054582378738726],
#     ],
#     [
#         ["int", 0.37194584766029465],
#         ["str", 0.32219782568421174],
#         ["bool", 0.1037741467367993],
#         ["Optional[str]", 0.09964588642115772],
#     ],
# ]
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
            "c": [
                ["float", 0.22659382019962282],
                ["str", 0.2022255751506991],
                ["bool", 0.10683424624716305],
            ],
            "kwargs": [None],
        },
        "ret_type_p": [
            # ["bool", 0.22659382019962282],
            # ["int", 0.2022255751506991],
            # ["Union[int, float]", 0.10683424624716305],
            # ["float", 0.09460898903951602],
            # ["Tuple[bool]", 0.09456387416250926],
            # ["Tuple[int, int]", 0.09054582378738726],
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

# predictions = get_type4_py_predictions_example()


class Node:
    def __init__(self, typeAnnotation: str, probability: float):
        self.typeAnnotation = typeAnnotation
        self.probability = probability
        self.children = []

    def __repr__(self):
        return f"{self.typeAnnotation}"


def transform_predictions_to_array_to_process(
    func_predictions,
) -> List[List[List[Union[str, float]]]]:
    array_to_process = []
    for func in func_predictions:
        # First try parameters
        for param_name, param_predictions in func["params_p"].items():
            if param_name in ["args", "kwargs"]:
                continue
            else:
                array_to_process.append(param_predictions)

        # Then try return type
        array_to_process.append(func["ret_type_p"])

    return array_to_process


def build_tree(root: Node, arr) -> Node:
    queue = [(root, 0)]
    while queue:
        node, index = queue.pop(0)
        if index >= len(arr):
            continue
        node.children = [Node(x[0], x[1]) for x in arr[index][:TOP_K]]
        for i in range(len(node.children)):
            queue.append((node.children[i], index + 1))
    return root


arr = transform_predictions_to_array_to_process(predictions)
tree = build_tree(Node("Top level node", 1), arr)


def depth_first_traversal(tree: Node):  # , python_code: str:
    if tree is None:
        return []

    result = []
    # Ignore the top level node as it is just a dummy node
    stack = list(reversed(tree.children))
    # source_code_tree = cst.parse_module(python_code)

    while len(stack) > 0:
        current = stack.pop()
        # print(current.typeAnnotation)

        # Add type annotation to source code
        # modified_tree = insert_annotation(tree, current.typeAnnotation)
        # print(modified_tree.code)

        # if typecheck on current type annotation fails {
        #   continue; # As this branch is invalid
        #   Also keep a counter where if all TOP_K type annotations fail, then keep type annotation empty and add top 1 from the next level to the stack to continue the search
        # }
        # if current.typeAnnotation != "int":
        #   continue
        result.append(current.typeAnnotation)

        for child in list(reversed(current.children)):
            stack.append(child)
    return result  # Remove the top level node


print(depth_first_traversal(tree))
