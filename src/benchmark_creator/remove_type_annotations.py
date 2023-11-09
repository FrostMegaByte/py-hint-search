import libcst as cst
import libcst.matchers as m


class RemoveTypeAnnotationsTransformer(cst.CSTTransformer):
    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        return updated_node.with_changes(returns=None)

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        return updated_node.with_changes(annotation=None)

    def leave_Import(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        return (
            updated_node
            if updated_node.names[0].evaluated_name != "typing"
            else cst.RemovalSentinel.REMOVE
        )

    def leave_ImportFrom(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        return (
            updated_node
            if updated_node.module.value != "typing"
            else cst.RemovalSentinel.REMOVE
        )

    # TODO: Uncomment the following code to remove type annotations from assignments.
    # My ML algorithm only works on function parameters and return types, so therefore it is not needed
    # def leave_Assign(
    #     self, original_node: cst.Assign, updated_node: cst.Assign
    # ) -> cst.BaseSmallStatement:
    #     if m.matches(
    #         original_node, m.Assign(targets=[m.AssignTarget(target=m.Annotation())])
    #     ):
    #         return cst.Assign(
    #             targets=[
    #                 cst.AssignTarget(target=target.target)
    #                 for target in updated_node.targets
    #             ],
    #             value=updated_node.value,
    #         )
    #     return updated_node

    # def leave_AnnAssign(
    #     self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
    # ) -> cst.BaseSmallStatement:
    #     return cst.Assign(
    #         targets=[cst.AssignTarget(target=updated_node.target)],
    #         value=updated_node.value,
    #     )


def remove_type_hints(source: str):
    module = cst.parse_module(source)
    transformer = RemoveTypeAnnotationsTransformer()
    transformed_module = module.visit(transformer)
    return transformed_module.code
