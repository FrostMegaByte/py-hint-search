import os
import argparse
import libcst as cst

from api import get_type4py_predictions
from annotation_inserter import TypingCollector
from fake_editor import FakeEditor
from treebuilder import (
    transform_predictions_to_array_to_process,
    build_tree,
    depth_first_traversal,
    Node,
)
from typestubs_parser import PyrightAnnotationCollector, PyrightAnnotationTransformer


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python type annotator based on Pyright feedback."
    )

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/example",
        help="The path to the project which will be type annotated.",
        # required=True,
    )
    parser.add_argument(
        "--top-k",
        type=int,
        choices=range(1, 5),
        default="3",
        help="Try the top k type annotation predictions.",
    )

    return parser.parse_args()


def create_pyright_config_file(project_path: str) -> None:
    with open(os.path.join(project_path, "pyrightconfig.json"), "w") as f:
        f.write('{ "typeCheckingMode": "strict"}')


def remove_pyright_config_file(project_path: str) -> None:
    pyright_config_file = os.path.join(project_path, "pyrightconfig.json")
    if os.path.exists(pyright_config_file):
        os.remove(pyright_config_file)


def main():
    args = parse_arguments()
    editor = FakeEditor()

    root_uri = f"file:///{args.project_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    base_dir = args.project_path.rsplit("/", 1)[0]
    stubs_directory = "typings"
    stubs_path = os.path.abspath(os.path.join(args.project_path, "..", stubs_directory))

    typed_directory = "typed"
    typed_path = os.path.abspath(os.path.join(args.project_path, "..", typed_directory))

    create_pyright_config_file(args.project_path)
    editor.start(root_uri, workspace_folders)

    # Walk through project directories and type annotate all python files
    for root, dirs, files in os.walk(args.project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            file_path = os.path.join(root, file)
            editor.open_file(file_path)

            python_code = editor.edit_document.text
            source_code_tree = cst.parse_module(python_code)

            # Add type annotations inferred by Pyright
            relative_stub_subdirectory = os.path.relpath(root, base_dir)
            stub_directory = os.path.join(stubs_path, relative_stub_subdirectory)
            stub_file = os.path.join(stub_directory, file + "i")
            with open(stub_file, "r") as f:
                stub_code = f.read()
            stub_tree = cst.parse_module(stub_code)
            visitor = PyrightAnnotationCollector()
            stub_tree.visit(visitor)
            transformer = PyrightAnnotationTransformer(visitor.annotations)
            pyright_annotated_source_code_tree = source_code_tree.visit(transformer)

            # Get already type annotationed parameters and return types
            visitor = TypingCollector()
            pyright_annotated_source_code_tree.visit(visitor)

            # Get ML type annotation predictions
            ml_predictions = get_type4py_predictions(
                pyright_annotated_source_code_tree.code
            )

            # Transform the predictions and filter out already type annotated parameters and return types
            search_tree_layers = transform_predictions_to_array_to_process(
                ml_predictions, visitor.type_annotated
            )

            # Build the search tree
            search_tree = build_tree(search_tree_layers, args.top_k)

            # Perform depth first traversal to annotate the source code tree (most work)
            type_annotated_source_code_tree = depth_first_traversal(
                search_tree,
                pyright_annotated_source_code_tree,
                editor,
                len(search_tree_layers),
            )

            # Write the type annotated source code to a file
            relative_path = os.path.relpath(root, args.project_path)
            output_typed_directory = os.path.abspath(
                os.path.join(typed_path, relative_path)
            )
            os.makedirs(output_typed_directory, exist_ok=True)
            open(os.path.join(output_typed_directory, file), "w").write(
                type_annotated_source_code_tree.code
            )

            editor.close_file()

    editor.stop()
    remove_pyright_config_file(args.project_path)


if __name__ == "__main__":
    main()
