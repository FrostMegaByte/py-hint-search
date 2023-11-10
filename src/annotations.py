from typing import Dict, List, Optional, Tuple
import libcst as cst
import libcst.matchers as m
from libcst.metadata import PositionProvider


class ParameterTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(
        self, parameter: str, annotation: str, function: Tuple[str, ...]
    ) -> None:
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


class ParameterTypeAnnotationLocationCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self, parameter: str, annotation: str, function: Tuple[str, ...]
    ) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.parameter = parameter
        self.annotation = annotation
        self.function = function
        self.updated_location = None

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> cst.ClassDef:
        self.stack.pop()
        return node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function:
            for param in node.params.params:
                if m.matches(param.name, m.Name(self.parameter)):
                    self.updated_location = self.get_metadata(
                        PositionProvider, param.annotation
                    )
                    position = self.updated_location
                    print(
                        f"Parameter type hint at {position.start.line}:{position.start.column} to {position.end.line}:{position.end.column}"
                    )
        return node


class ReturnTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(self, annotation: str, function: Tuple[str, ...]) -> None:
        self.stack: List[Tuple[str, ...]] = []
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

        if current_function == self.function and original_node.returns is None:
            annotation = (
                cst.Annotation(cst.parse_expression(self.annotation))
                if self.annotation != ""
                else None
            )
            return updated_node.with_changes(returns=annotation)
        return updated_node


class ReturnTypeAnnotationLocationCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, annotation: str, function: Tuple[str, ...]) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.annotation = annotation
        self.function = function
        self.updated_location = None

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> cst.ClassDef:
        self.stack.pop()
        return node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function and node.returns is not None:
            self.updated_location = self.get_metadata(PositionProvider, node.returns)
            position = self.updated_location
            print(
                f"Return type hint at {position.start.line}:{position.start.column} to {position.end.line}:{position.end.column}"
            )
        return node


def insert_parameter_annotation(
    tree: cst.Module,
    annotation: str,
    function: Tuple[str, ...] = None,
    parameter_name: str = "",
):
    transformer = ParameterTypeAnnotationInserter(parameter_name, annotation, function)
    modified_tree = tree.visit(transformer)
    wrapper = cst.MetadataWrapper(modified_tree)
    visitor = ParameterTypeAnnotationLocationCollector(
        parameter_name, annotation, function
    )
    wrapper.visit(visitor)
    return modified_tree, visitor.updated_location


def insert_return_annotation(
    tree: cst.Module,
    annotation: str,
    function: Tuple[str, ...] = None,
):
    transformer = ReturnTypeAnnotationInserter(annotation, function)
    modified_tree = tree.visit(transformer)
    wrapper = cst.MetadataWrapper(modified_tree)
    visitor = ReturnTypeAnnotationLocationCollector(annotation, function)
    wrapper.visit(visitor)
    return modified_tree, visitor.updated_location


class AlreadyTypeAnnotatedCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.already_type_annotated: Dict[Tuple[str, ...], List[str]] = {}

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        self.already_type_annotated[tuple(self.stack)] = []
        for param in node.params.params:
            if param.annotation is not None:
                self.already_type_annotated[tuple(self.stack)].append(param.name.value)

        if node.returns is not None:
            self.already_type_annotated[tuple(self.stack)].append("return")
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()


class PyrightTypeAnnotationCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = {}

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
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


class PyrightTypeAnnotationTransformer(cst.CSTTransformer):
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
    ) -> cst.ClassDef:
        self.stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        key = tuple(self.stack)
        self.stack.pop()
        if key in self.annotations:
            annotations = self.annotations[key]
            return updated_node.with_changes(
                params=annotations[0], returns=annotations[1]
            )
        return updated_node
