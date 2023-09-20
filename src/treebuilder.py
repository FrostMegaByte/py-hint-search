from api import get_type4_py_predictions

TOP_K = 3

# arr = [
#     [
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

arr = get_type4_py_predictions()


class Node:
    def __init__(self, typeAnnotation: str, probability: float):
        self.typeAnnotation = typeAnnotation
        self.probability = probability
        self.children = []


def build_tree(root, arr):
    queue = [(root, 0)]
    while queue:
        node, index = queue.pop(0)
        if index >= len(arr):
            continue
        node.children = [Node(x[0], x[1]) for x in arr[index][:TOP_K]]
        for i in range(len(node.children)):
            queue.append((node.children[i], index + 1))
    return root


tree = build_tree(Node("Top level node", 1), arr)


def depth_first_traversal(root):
    if root is None:
        return []

    result = []
    # Ignore the top level node as it is just a dummy node
    stack = list(reversed(root.children))

    while len(stack) > 0:
        current = stack.pop()
        # print(current.typeAnnotation)
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
