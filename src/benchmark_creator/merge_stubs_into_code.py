import os
import argparse
import libcst as cst
import libcst.matchers as m
from typing import List, Tuple, Dict, Optional, Union


class TypingCollector(cst.CSTVisitor):
    def __init__(self):
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = {}
        self.imports: List[Union[cst.Import, cst.ImportFrom]] = []

    def leave_Import(self, node: cst.Import) -> cst.Import:
        self.imports.append(node)

    def leave_ImportFrom(self, node: cst.ImportFrom) -> cst.ImportFrom:
        self.imports.append(node)

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        self.annotations[tuple(self.stack)] = (node.params, node.returns)
        return False

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()


class TypingTransformer(cst.CSTTransformer):
    def __init__(self, annotations, imports):
        self.stack: List[Tuple[str, ...]] = []
        self.annotations: Dict[
            Tuple[str, ...],
            Tuple[cst.Parameters, Optional[cst.Annotation]],
        ] = annotations
        self.imports: List[Union[cst.Import, cst.ImportFrom]] = imports

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        body = []
        for import_node in self.imports:
            body.append(import_node)
            body.append(cst.EmptyLine())
        return updated_node.with_changes(body=tuple(body) + updated_node.body)

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.CSTNode:
        self.stack.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.CSTNode:
        # IMPORTANT: We assume that the inline type hints are more up to date than those in the corresponding stub files.
        # Therefore, we keep the inline type hints and only add the missing ones from the stub files.
        key = tuple(self.stack)
        self.stack.pop()
        if key in self.annotations:
            params_annotations, return_annotation = self.annotations[key]
            updated_params = list(updated_node.params.params)
            for i, param in enumerate(updated_node.params.params):
                if param.annotation is None:
                    for stub_param in params_annotations.params:
                        if m.matches(stub_param.name, param.name):
                            updated_params[i] = param.with_changes(
                                annotation=stub_param.annotation
                            )

            updated_params = updated_node.params.with_changes(
                params=tuple(updated_params)
            )
            return_annotation = (
                return_annotation
                if updated_node.returns is None
                else updated_node.returns
            )
            return updated_node.with_changes(
                params=updated_params, returns=return_annotation
            )
        return updated_node


def merge_stub_annotations_in_code(source_code: str, stub_code: str) -> str:
    source_tree = cst.parse_module(source_code)
    stub_tree = cst.parse_module(stub_code)
    visitor = TypingCollector()
    stub_tree.visit(visitor)
    transformer = TypingTransformer(visitor.annotations, visitor.imports)
    modified_tree = source_tree.visit(transformer)
    return modified_tree.code


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge stub file annotations into Python code."
    )

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/bleach/bleach",
        help="The path to the project that will be type annotated.",
        # required=True,
    )
    parser.add_argument(
        "--stubs-path",
        type=dir_path,
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/typeshed/stubs/bleach/bleach",
        help="The path to the stub files of the project that will be type annotated.",
        # required=True,
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.project_path, "..")))
    working_directory = os.getcwd()
    stubs_path = os.path.normpath(args.stubs_path)
    fully_annotated_path = os.path.abspath(
        os.path.join(working_directory, "fully-annotated")
    )
    os.makedirs(fully_annotated_path, exist_ok=True)

    for root, dirs, files in os.walk(args.project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.project_path)
            stub_code_file_path = os.path.abspath(
                os.path.join(stubs_path, relative_path, file + "i")
            )
            has_mathing_stub = os.path.exists(stub_code_file_path)

            if has_mathing_stub:
                print(f"Merging stub and file: {os.path.join(relative_path, file)}")

                source_code_file_path = os.path.join(root, file)
                try:
                    python_code = open(
                        source_code_file_path, "r", encoding="utf-8"
                    ).read()
                    stub_code = open(stub_code_file_path, "r", encoding="utf-8").read()
                except Exception as e:
                    print(e)

                merged_python_code = merge_stub_annotations_in_code(
                    python_code, stub_code
                )

                output_fully_annotated_directory = os.path.abspath(
                    os.path.join(fully_annotated_path, relative_path)
                )
                os.makedirs(output_fully_annotated_directory, exist_ok=True)
                open(
                    os.path.join(output_fully_annotated_directory, file),
                    "w",
                    encoding="utf-8",
                ).write(merged_python_code)


if __name__ == "__main__":
    main()
