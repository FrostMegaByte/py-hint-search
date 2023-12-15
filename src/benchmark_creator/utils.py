import re
import libcst as cst


def node_to_code(node: cst.CSTNode):
    node_string = cst.Module([]).code_for_node(node)
    node_string = node_string.replace("\n", "")
    node_string = re.sub(r"\[\s+", "[", node_string)
    node_string = re.sub(r"\s+\]", "]", node_string)
    return node_string


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


def transform_binary_operations_to_unions(node: cst.BinaryOperation):
    transformer = BinaryOperationToUnionTransformer()
    transformed_annotation = node.visit(transformer)
    return node_to_code(transformed_annotation)
