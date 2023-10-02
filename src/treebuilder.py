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
        self, typeAnnotation: str, probability: float, func_name: str, param_name: str
    ):
        self.typeAnnotation = typeAnnotation
        self.probability = probability
        self.func_name = func_name
        self.param_name = param_name
        self.children = []

    def __repr__(self):
        return f"{self.typeAnnotation}"


def transform_predictions_to_array_to_process(func_predictions):
    array_to_process = []
    for func in func_predictions:
        # First try parameters
        for param_name, param_predictions in func["params_p"].items():
            # Dirty trick of adding function name and parameter name information to the predictions
            param_predictions.insert(0, [func["name"], param_name])
            if param_name in ["args", "kwargs"]:
                continue
            else:
                array_to_process.append(param_predictions)

        # Then try return type
        # Continuation of dirty trick of adding function name and parameter name information to the predictions
        func["ret_type_p"].insert(0, [func["name"], "return"])
        array_to_process.append(func["ret_type_p"])

    return array_to_process


TOP_K = 3


def build_tree(root: Node, arr) -> Node:
    queue = [(root, 0)]
    next_level = 0
    while queue:
        node, index = queue.pop(0)
        if index >= len(arr):
            continue
        if index == next_level:
            func_name, param_name = arr[index].pop(0)
            next_level += 1
        node.children = [
            Node(x[0], x[1], func_name, param_name) for x in arr[index][:TOP_K]
        ]
        for i in range(len(node.children)):
            queue.append((node.children[i], index + 1))
    return root


# arr = transform_predictions_to_array_to_process(predictions)
# tree = build_tree(Node("Top level node", 1, "", ""), arr)


def depth_first_traversal(tree: Node, python_code: str, editor: FakeEditor):
    if tree is None:
        return []

    # result = []
    # Ignore the top level node as it is just a dummy node
    stack = list(reversed(tree.children))
    source_code_tree = cst.parse_module(python_code)

    while len(stack) > 0:
        current = stack.pop()

        # Add type annotation to source code
        if current.param_name == "return":
            modified_tree = insert_return_annotation(
                source_code_tree,
                current.typeAnnotation,
                current.func_name,
            )
        else:
            modified_tree = insert_parameter_annotation(
                source_code_tree,
                current.typeAnnotation,
                current.func_name,
                current.param_name,
            )

        print(modified_tree.code)

        editor.change_file(modified_tree.code)

        if editor.has_diagnostics():
            print("Diagnostics found!")
            continue

        source_code_tree = modified_tree

        # If leaf node and no errors found, then we have found the correct type annotations
        if len(current.children) == 0:
            break

        # if typecheck on current type annotation fails {
        #   continue; # As this branch is invalid
        #   Also keep a counter where if all TOP_K type annotations fail, then keep type annotation empty and add top 1 from the next level to the stack to continue the search
        # }
        # if current.typeAnnotation != "int":
        #   continue
        # result.append(current.typeAnnotation)

        for child in list(reversed(current.children)):
            stack.append(child)
    return source_code_tree.code
    # return result  # Remove the top level node


# print(depth_first_traversal(tree))
