import os
from typing import Dict, List, Optional, Tuple
import libcst as cst
import libcst.matchers as m


class PyrightAnnotationCollector(cst.CSTVisitor):
    def __init__(self):
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = {}

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        if node.returns is None and node.body.header.comment is not None:
            comment = node.body.header.comment.value
            annotation = comment.split("->")[1].strip()[:-1]
            return_annotation = cst.Annotation(cst.parse_expression(annotation))
            self.annotations[tuple(self.stack)] = (node.params, return_annotation)
        else:
            self.annotations[tuple(self.stack)] = (node.params, node.returns)
        return False

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()


class PyrightAnnotationTransformer(cst.CSTTransformer):
    def __init__(self, annotations):
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = annotations

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:
        self.stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        key = tuple(self.stack)
        self.stack.pop()
        if key in self.annotations:
            annotations = self.annotations[key]
            return updated_node.with_changes(
                params=annotations[0], returns=annotations[1]
            )
        return updated_node


# class PyrightAnnotationCollector(cst.CSTVisitor):
#     # def __init__(self):
#     #     self.type_annotated: Dict[str, List[str]] = {}

#     def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
#         # self.type_annotated[node.name.value] = []
#         print(node.body.header.comment)
#         return False


# class PyrightAnnotationCollector(cst.CSTTransformer):
#     def __init__(self, annotation: str, function_name: str):
#         self.annotation = annotation
#         self.function_name = function_name

#     def leave_FunctionDef(
#         self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
#     ) -> cst.FunctionDef:
#         if m.matches(updated_node.name, m.Name(self.function_name)) and (
#             m.matches(updated_node.returns, m.Annotation())
#             or updated_node.returns is None
#         ):
#             annotation = (
#                 cst.Annotation(cst.parse_expression(self.annotation))
#                 if self.annotation != ""
#                 else None
#             )
#             return updated_node.with_changes(returns=annotation)
#         return updated_node


def parse_typestubs(project_path):
    stubs_directory = "typings"
    stubs_path = os.path.abspath(os.path.join(project_path, "..", stubs_directory))

    for root, dirs, files in os.walk(stubs_path):
        for file in files:
            stub_file = os.path.join(root, file)
            with open(stub_file, "r") as f:
                code = f.read()

            stub_tree = cst.parse_module(code)
            visitor = PyrightAnnotationCollector()
            stub_tree.visit(visitor)
            transformer = PyrightAnnotationTransformer(visitor.annotations)
            modified_tree = stub_tree.visit(transformer)
            # modified_tree = source_tree.visit(transformer)


parse_typestubs(
    "D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/example"
)
