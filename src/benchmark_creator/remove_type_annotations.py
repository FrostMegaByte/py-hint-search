import os
import argparse
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
            if updated_node.names[0]
            and updated_node.names[0].evaluated_name != "typing"
            else cst.RemovalSentinel.REMOVE
        )

    def leave_ImportFrom(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        return (
            updated_node
            if updated_node.relative
            or (updated_node.module and updated_node.module.value != "typing")
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


def remove_type_hints(source: str) -> str:
    module = cst.parse_module(source)
    transformer = RemoveTypeAnnotationsTransformer()
    transformed_module = module.visit(transformer)
    return transformed_module.code


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove type annotations from Python code"
    )

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        help="The path to the Python files directory of the project which will be stripped from type annotations.",
        required=True,
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.project_path, "..")))
    working_directory = os.getcwd()
    stripped_path = os.path.abspath(os.path.join(working_directory, "stripped"))
    os.makedirs(stripped_path, exist_ok=True)

    for root, dirs, files in os.walk(args.project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.project_path)
            print(f"Stripping file: {os.path.join(relative_path, file)}")

            file_path = os.path.join(root, file)
            try:
                python_code = open(file_path, "r", encoding="utf-8").read()
            except Exception as e:
                print(e)

            stripped_python_code = remove_type_hints(python_code)

            output_stripped_directory = os.path.abspath(
                os.path.join(stripped_path, relative_path)
            )
            os.makedirs(output_stripped_directory, exist_ok=True)
            open(
                os.path.join(output_stripped_directory, file), "w", encoding="utf-8"
            ).write(stripped_python_code)


if __name__ == "__main__":
    main()
