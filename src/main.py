import os
import argparse

from fake_editor import FakeEditor
from treebuilder import (
    predictions,
    transform_predictions_to_array_to_process,
    build_tree,
    depth_first_traversal,
    Node,
)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Start the Pyright language server.")
    # parser.add_argument(
    #     "--tcp",
    #     action="store_true",
    #     help="Use TCP socket to communicate with the server",
    # )
    parser.add_argument(
        "pyright_langserver",
        type=str,
        default="pyright-langserver --stdio",
        help="Start the Pyright language server on stdin/stdout.",
        nargs="?",
    )
    # Path to the project that can be set as workspace root to run the language server over.

    return parser.parse_args()


def main():
    # args = parse_arguments()

    editor = FakeEditor()

    root_path = f"{os.getcwd()}/example/"
    typed_path = f"{os.getcwd()}/typed/"
    root_uri = f"file:///{root_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    if not os.path.exists(typed_path):
        os.makedirs(typed_path)

    editor.start(root_uri, workspace_folders)

    python_files = [file for file in os.listdir(root_path) if file.endswith(".py")]
    for file in python_files:
        file_path = f"{root_path}/{file}"
        editor.open_file(file_path)

        # GET PREDICTIONS FROM TYPE4PY FOR FILE
        # ml_predictions = get_type4_py_predictions(file_path)

        arr = transform_predictions_to_array_to_process(predictions)
        dummy_root_node = Node("Top level node", 1, "", "")
        tree = build_tree(dummy_root_node, arr)

        python_code = editor.edit_document.text
        type_annotated_python_code = depth_first_traversal(tree, python_code, editor)

        open(f"{typed_path}/{file}", "w").write(type_annotated_python_code)
        editor.close_file()

    editor.stop()


if __name__ == "__main__":
    main()
