from typing import List, Optional
import libcst as cst
import libcst.matchers as m

# # Open the file and read the code
with open("src/example/example.py", "r") as file:
    python_code = file.read()
    tree = cst.parse_module(python_code)


# class AnnotationInserter(cst.CSTTransformer):
#     def leave_FunctionDef(
#         self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
#     ) -> cst.CSTNode:
#         if (
#             m.matches(updated_node.returns, m.Annotation())
#             or updated_node.returns is None
#         ):
#             return updated_node.with_changes(returns=cst.Annotation(cst.Name("str")))
#         return updated_node


# # tree = cst.parse_module("def foo():\n    return 42")
# transformer = AnnotationInserter()
# modified_tree = tree.visit(transformer)
# print(modified_tree.code)


# -----------------
arr = [
    [
        ["bool", 0.22659382019962282],
        ["int", 0.2022255751506991],
        ["Union[int, float]", 0.10683424624716305],
        ["float", 0.09460898903951602],
        ["Tuple[bool]", 0.09456387416250926],
        ["Tuple[int, int]", 0.09054582378738726],
    ],
    [
        ["int", 0.37194584766029465],
        ["str", 0.32219782568421174],
        ["bool", 0.1037741467367993],
        ["Optional[str]", 0.09964588642115772],
    ],
]


class AnnotationInserter(cst.CSTTransformer):
    def __init__(self, annotation):
        self.annotation: List[List[List[str, float]]] = annotation

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        if (
            m.matches(updated_node.returns, m.Annotation())
            or updated_node.returns is None
        ):
            return updated_node.with_changes(
                returns=cst.Annotation(cst.Name(self.annotation))
            )
        return updated_node


# tree = cst.parse_module("def foo():\n    return 42")
transformer = AnnotationInserter("str")
modified_tree = tree.visit(transformer)
print(modified_tree.code)


# class AnnotationInserter(cst.CSTTransformer):
#     def leave_FunctionDef(self, original_node, updated_node):
#         if not updated_node.returns:
#             updated_node = updated_node.with_changes(
#                 returns=cst.Annotation(cst.Name("None"))
#             )
#         return updated_node


# def insert_type_annotation(tree: cst.Module, annotation: str):
#     # Create an AnnotationInserter transformer
#     transformer = AnnotationInserter()

#     # Insert the type annotation
#     tree = tree.visit(transformer)
#     print(tree)
#     return tree

#     # # Find the function definition node
#     # function_node = next(
#     #     (node for node in tree.body if isinstance(node, cst.FunctionDef))
#     # )

#     # # Add the type annotation to the function definition
#     # function_node = function_node.with_changes(
#     #     returns=cst.Annotation(cst.Name(annotation))
#     # )

#     # # Generate the updated code
#     # updated_code = cst.Module([function_node])

#     # return updated_code


# tree: cst.Module = cst.parse_module(
#     "def foo():\n    return 42\n\ndef bar():\n    return 42"
# )
# modified_tree = insert_type_annotation(tree, "str")
# print(modified_tree.code)
