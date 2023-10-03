import os
import argparse
import libcst as cst

from api import get_type4py_predictions
from annotation_inserter import TypingCollector
from fake_editor import FakeEditor
from treebuilder import (
    predictions,
    transform_predictions_to_array_to_process,
    build_tree,
    depth_first_traversal,
    Node,
)


def parse_arguments():
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
        default="D:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example",
        help="The path to the project which will be type annotated.",
        # required=True,
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    editor = FakeEditor()

    root_uri = f"file:///{args.project_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]
    typed_subdirectory = "typed"
    typed_path = os.path.join(args.project_path, typed_subdirectory)

    editor.start(root_uri, workspace_folders)

    # Walk through project directories and type annotate all python files
    for root, dirs, files in os.walk(args.project_path):
        if typed_subdirectory in dirs:
            dirs.remove(typed_subdirectory)

        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            file_path = os.path.join(root, file)
            editor.open_file(file_path)

            # Get ML type annotation predictions
            ml_predictions = get_type4py_predictions(file_path)

            # Get already type annotationed parameters and return types
            python_code = editor.edit_document.text
            source_code_tree = cst.parse_module(python_code)
            visitor = TypingCollector()
            source_code_tree.visit(visitor)

            # Transform the predictions and filter out already type annotated parameters and return types
            search_tree_layers = transform_predictions_to_array_to_process(
                ml_predictions, visitor.type_annotated
            )

            # Build the search tree
            dummy_root_node = Node("Top level node", 1, "", "")
            search_tree = build_tree(dummy_root_node, search_tree_layers)

            # Perform depth first traversal to annotate the source code tree (most work)
            type_annotated_source_code_tree = depth_first_traversal(
                search_tree, source_code_tree, editor
            )

            # Write the type annotated source code to a file
            relative_path = os.path.relpath(root, args.project_path)
            typed_subdirectory = (
                os.path.join(typed_path, relative_path)
                if relative_path != "."
                else typed_path
            )
            os.makedirs(typed_subdirectory, exist_ok=True)
            open(os.path.join(typed_subdirectory, file), "w").write(
                type_annotated_source_code_tree.code
            )
            editor.close_file()

    editor.stop()


if __name__ == "__main__":
    main()
