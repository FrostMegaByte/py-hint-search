import libcst as cst


class StubTransformer(cst.CSTTransformer):
    def __init__(self):
        self.in_class_count = 0
        self.in_function_count = 0

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.in_class_count += 1
        return self.in_class_count == 1

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:
        self.in_class_count -= 1
        if self.in_class_count == 0:
            return updated_node
        else:
            return cst.parse_statement("...")

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.in_function_count += 1
        return self.in_function_count == 1

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        """Remove function bodies"""
        self.in_function_count -= 1
        if self.in_function_count == 0 or (
            self.in_function_count == 1 and self.in_class_count == 1
        ):
            return updated_node.with_changes(body=cst.parse_statement("..."))
        else:
            return cst.parse_statement("...")

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Remove everything from the body that is not an import, class def or function def."""
        newbody = [
            node
            for node in updated_node.body
            if any(
                isinstance(node, cls)
                for cls in [cst.ClassDef, cst.FunctionDef, cst.SimpleStatementLine]
            )
        ]
        return updated_node.with_changes(body=newbody)

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.CSTNode:
        newbody = [
            node
            for node in updated_node.body
            if any(isinstance(node, cls) for cls in [cst.Import, cst.ImportFrom])
        ]
        return updated_node.with_changes(body=newbody)
