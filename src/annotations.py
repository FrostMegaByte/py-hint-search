import re
from typing import Dict, List, Optional, Set, Tuple
import libcst as cst
import libcst.matchers as m
from libcst.metadata import PositionProvider


class ParameterTypeAnnotationInserter(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(
        self, parameter: str, annotation: str, function: Tuple[str, ...]
    ) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.parameter = parameter
        self.annotation = annotation
        self.function = function
        self.updated_function_location = None

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
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function:
            for i, param in enumerate(updated_node.params.params):
                if m.matches(param.name, m.Name(self.parameter)):
                    self.updated_function_location = self.get_metadata(
                        PositionProvider, original_node
                    )
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
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, annotation: str, function: Tuple[str, ...]) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.annotation = annotation
        self.function = function
        self.updated_function_location = None

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
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        current_function = tuple(self.stack)
        self.stack.pop()

        if current_function == self.function and updated_node.returns is None:
            self.updated_function_location = self.get_metadata(
                PositionProvider, original_node
            )
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
    wrapper = cst.MetadataWrapper(tree)
    modified_tree = wrapper.visit(transformer)
    return modified_tree, transformer.updated_function_location


def insert_return_annotation(
    tree: cst.Module,
    annotation: str,
    function: Tuple[str, ...] = None,
):
    transformer = ReturnTypeAnnotationInserter(annotation, function)
    wrapper = cst.MetadataWrapper(tree)
    modified_tree = wrapper.visit(transformer)
    return modified_tree, transformer.updated_function_location


class RemoveIncompleteAnnotations(cst.CSTTransformer):
    def leave_Annotation(
        self, original_node: cst.Annotation, updated_node: cst.Annotation
    ) -> cst.Annotation:
        annotation_string = node_to_code(updated_node.annotation)
        if annotation_string in [
            "Incomplete",
            "Optional[Incomplete]",
            "Incomplete | None",
        ]:
            return cst.RemoveFromParent()
        return updated_node


class BinaryTransformer(cst.CSTTransformer):
    def leave_Annotation(
        self, original_node: cst.Annotation, updated_node: cst.Annotation
    ) -> cst.Annotation:
        if isinstance(updated_node.annotation, cst.BinaryOperation):
            union_annotation = transform_binary_operations_to_unions(
                updated_node.annotation
            )
            return updated_node.with_changes(annotation=union_annotation)
        return updated_node


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
        self.all_pyright_annotations: Set[str] = set()

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)

        for param in node.params.params:
            if param.annotation is not None:
                self.all_pyright_annotations.add(
                    node_to_code(param.annotation.annotation)
                )

        if (
            node.returns is None
            and hasattr(node.body, "header")
            and node.body.header.comment is not None
        ):
            comment = node.body.header.comment.value
            annotation = comment.replace("# -> ", "").strip()[:-1]
            if any(symbol in annotation for symbol in ["(", "<"]):
                annotation = ""
            if "…" in annotation:
                annotation = annotation.replace("…", "")
            if "@" in annotation:
                annotation = re.sub(r"@(\w+)", "", annotation)

            return_annotation = (
                cst.Annotation(cst.parse_expression(annotation))
                if annotation != ""
                else None
            )
            self.annotations[tuple(self.stack)] = (node.params, return_annotation)
            self.all_pyright_annotations.add(annotation)
        else:
            self.annotations[tuple(self.stack)] = (node.params, node.returns)
        return False

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()


class BinaryOperationToUnionTransformer(cst.CSTTransformer):
    def leave_BinaryOperation(
        self, original_node: cst.BinaryOperation, updated_node: cst.BinaryOperation
    ) -> cst.Subscript:
        if updated_node.left.value == "None":
            return cst.Subscript(
                value=cst.Name("Optional"),
                slice=[cst.SubscriptElement(slice=cst.Index(value=updated_node.right))],
            )
        elif updated_node.right.value == "None":
            return cst.Subscript(
                value=cst.Name("Optional"),
                slice=[cst.SubscriptElement(slice=cst.Index(value=updated_node.left))],
            )
        else:
            return cst.Subscript(
                value=cst.Name("Union"),
                slice=[
                    cst.SubscriptElement(slice=cst.Index(value=updated_node.left)),
                    cst.SubscriptElement(slice=cst.Index(value=updated_node.right)),
                ],
            )


def node_to_code(node: cst.CSTNode):
    node_string = cst.Module([]).code_for_node(node)
    node_string = node_string.replace("\n", "")
    node_string = re.sub(r"\[\s+", "[", node_string)
    node_string = re.sub(r"\s+\]", "]", node_string)
    return node_string


def transform_binary_operations_to_unions(node: cst.BinaryOperation):
    transformer = BinaryOperationToUnionTransformer()
    transformed_annotation = node.visit(transformer)
    return transformed_annotation


class PyrightTypeAnnotationTransformer(cst.CSTTransformer):
    def __init__(self, annotations, unknown_annotations: Set[str]) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = annotations
        self.unknown_annotations = unknown_annotations

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
            updated_params = list(annotations[0].params)

            updated_params = updated_node.params.with_changes(
                params=tuple(updated_params)
            )

            return_annotation = (
                annotations[1]
                if annotations[1] is not None
                and node_to_code(annotations[1].annotation)
                not in self.unknown_annotations
                else None
            )
            return updated_node.with_changes(
                params=updated_params,
                returns=return_annotation,
            )
        return updated_node
