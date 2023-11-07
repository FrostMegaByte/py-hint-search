from typing import Dict, List, Optional, Tuple
import libcst as cst
import libcst.matchers as m


class ParameterTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(self, parameter: str, annotation: str, function: str):
        self.stack: List[Tuple[str, ...]] = []
        self.parameter = parameter
        self.annotation = annotation
        self.function = function

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function:
            for i, param in enumerate(updated_node.params.params):
                if m.matches(param.name, m.Name(self.parameter)):
                    annotation = (
                        cst.Annotation(cst.parse_expression(self.annotation))
                        if self.annotation != ""
                        else None
                    )
                    updated_params = updated_node.params.with_changes(
                        params=updated_node.params.params[:i]
                        + (param.with_changes(annotation=annotation),)
                        + updated_node.params.params[i + 1 :]
                    )
                    return updated_node.with_changes(params=updated_params)
        return updated_node


class ReturnTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(self, annotation: str, function_name: str):
        self.stack: List[Tuple[str, ...]] = []
        self.annotation = annotation
        self.function_name = function_name

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function_name:
            if updated_node.returns is None:
                annotation = (
                    cst.Annotation(cst.parse_expression(self.annotation))
                    if self.annotation != ""
                    else None
                )
                return updated_node.with_changes(returns=annotation)
        return updated_node


def insert_parameter_annotation(
    tree: cst.Module,
    annotation: str,
    function: Tuple[str, ...] = None,
    parameter_name: str = "",
):
    transformer = ParameterTypeAnnotationInserter(parameter_name, annotation, function)
    modified_tree = tree.visit(transformer)
    return modified_tree


def insert_return_annotation(
    tree: cst.Module,
    annotation: str,
    function: Tuple[str, ...] = None,
):
    transformer = ReturnTypeAnnotationInserter(annotation, function)
    modified_tree = tree.visit(transformer)
    return modified_tree


class TypingCollector(cst.CSTVisitor):
    def __init__(self):
        self.stack: List[Tuple[str, ...]] = []
        self.type_annotated: Dict[Tuple[str, ...], List[str]] = {}

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        self.type_annotated[tuple(self.stack)] = []
        for param in node.params.params:
            if param.annotation is not None:
                self.type_annotated[tuple(self.stack)].append(param.name.value)

        if node.returns is not None:
            self.type_annotated[tuple(self.stack)].append("return")
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()
