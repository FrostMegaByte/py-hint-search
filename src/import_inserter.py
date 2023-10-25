import libcst as cst
import libcst.matchers as m


class ImportInserter(cst.CSTTransformer):
    def __init__(self, import_statement: str):
        self.import_statement = import_statement

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        imp = cst.parse_statement(self.import_statement)
        # import2 = cst.parse_statement("from taart import Taart")

        # # Check if the two import statements match
        # if m.matches(imp, import2):
        #     print("The import statements are the same")
        # else:
        #     print("The import statements are different")

        # import_is_present = bool(
        #     [True for i in updated_node.children if m.matches(i, imp)]
        # )
        # if not import_is_present:
        body_with_import = (imp,) + updated_node.body
        return updated_node.with_changes(body=body_with_import)
