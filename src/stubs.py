import os
import libcst as cst
import libcst.matchers as m
from libcst import RemoveFromParent


class ClassDefFinder(cst.CSTVisitor):
    def __init__(self):
        self.has_nested_class = False

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self.has_nested_class = True


class FunctionDefFinder(cst.CSTVisitor):
    def __init__(self):
        self.has_nested_function = False

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.has_nested_function = True


class StubTransformer(cst.CSTTransformer):
    def __init__(self):
        self.in_function_count = 0

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:
        finder_classes = ClassDefFinder()
        updated_node.body.visit(finder_classes)

        finder_funcs = FunctionDefFinder()
        updated_node.body.visit(finder_funcs)

        if not finder_classes.has_nested_class and not finder_funcs.has_nested_function:
            return updated_node.with_changes(body=cst.parse_statement("..."))
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.in_function_count += 1
        if self.in_function_count == 2:
            return False
        return True

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.CSTNode:
        if updated_node.default is not None:
            return updated_node.with_changes(default=cst.parse_expression("..."))
        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        """Remove function bodies"""
        self.in_function_count -= 1
        if self.in_function_count == 1:
            return RemoveFromParent()

        finder = ClassDefFinder()
        updated_node.visit(finder)
        if not finder.has_nested_class:
            return updated_node.with_changes(body=cst.parse_statement("..."))
        return updated_node

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.CSTNode:
        """Only keep import and type alias statements."""
        keep_statement = False
        if m.matches(updated_node.body[0], m.Import() | m.ImportFrom()):
            keep_statement = True
        elif m.matches(
            updated_node.body[0],
            m.AnnAssign(annotation=m.Annotation(annotation=m.Name("TypeAlias"))),
        ):
            keep_statement = True

        if keep_statement:
            return updated_node
        return updated_node.with_changes(body=())

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Remove everything that is not an import, type alias, class def or function def."""
        newbody = tuple(
            [
                node
                for node in updated_node.body
                if m.matches(
                    node, m.ClassDef() | m.FunctionDef() | m.SimpleStatementLine()
                )
            ]
        )
        return updated_node.with_changes(body=tuple(newbody))


def create_stub_file(
    source_code_tree: cst.Module,
    typed_path: str,
    relative_path: str,
    file_name: str,
    keep_source_code_file: bool = True,
) -> None:
    # Write the type annotated source code to a file
    output_typed_source_directory = os.path.abspath(
        os.path.join(typed_path + "-source-code", relative_path)
    )
    os.makedirs(output_typed_source_directory, exist_ok=True)
    source_code_file = os.path.join(output_typed_source_directory, file_name)
    open(source_code_file, "w", encoding="utf-8").write(source_code_tree.code)

    transformer = StubTransformer()
    type_annotated_stub_tree = source_code_tree.visit(transformer)

    # Write the type annotated stub to a file
    output_typed_directory = os.path.abspath(os.path.join(typed_path, relative_path))
    os.makedirs(output_typed_directory, exist_ok=True)
    open(
        os.path.join(output_typed_directory, file_name + "i"), "w", encoding="utf-8"
    ).write(type_annotated_stub_tree.code)

    if not keep_source_code_file:
        os.remove(source_code_file)
        os.rmdir(output_typed_source_directory)
