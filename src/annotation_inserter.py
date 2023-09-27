import libcst as cst
import libcst.matchers as m


class ParameterTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(self, parameter, annotation, function_name):
        self.parameter: str = parameter
        self.annotation: str = annotation
        self.function_name: str = function_name

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        if m.matches(updated_node.name, m.Name(self.function_name)):
            for i, param in enumerate(updated_node.params.params):
                if m.matches(param.name, m.Name(self.parameter)):
                    return updated_node.with_changes(
                        params=cst.Parameters(
                            params=updated_node.params.children[:i]
                            + [
                                param.with_changes(
                                    annotation=cst.Annotation(cst.Name(self.annotation))
                                )
                            ]
                            + updated_node.params.children[i + 1 :]
                        )
                    )
        return updated_node


class ReturnTypeAnnotationInserter(cst.CSTTransformer):
    def __init__(self, annotation, function_name):
        self.annotation: str = annotation
        self.function_name: str = function_name

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        if m.matches(updated_node.name, m.Name(self.function_name)) and (
            m.matches(updated_node.returns, m.Annotation())
            or updated_node.returns is None
        ):
            return updated_node.with_changes(
                returns=cst.Annotation(cst.Name(self.annotation))
            )
        return updated_node


def insert_parameter_annotation(
    tree: cst.Module, annotation: str, function_name=None, parameter_name=None
):
    transformer = ParameterTypeAnnotationInserter(
        parameter_name, annotation, function_name
    )
    modified_tree = tree.visit(transformer)
    return modified_tree


def insert_return_annotation(tree: cst.Module, annotation: str, function_name=None):
    transformer = ReturnTypeAnnotationInserter(annotation, function_name)
    modified_tree = tree.visit(transformer)
    return modified_tree


with open("src/example/example.py", "r") as file:
    python_code = file.read()
    tree = cst.parse_module(python_code)
    modified_tree = insert_parameter_annotation(tree, "None", "multiply", "b")
    modified_tree = insert_return_annotation(modified_tree, "int", "multiply")
    print(modified_tree.code)
