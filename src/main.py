import os
import argparse

from fake_editor import FakeEditor


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

    root_path = f"{os.getcwd()}/src/example/"
    root_uri = f"file:///{root_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    editor.start(root_uri, workspace_folders)

    python_files = [file for file in os.listdir(root_path) if file.endswith(".py")]
    for file in python_files:
        file_path = f"{root_path}/{file}"
        editor.open_file(file_path)

        # GET PREDICTIONS FROM TYPE4PY FOR FILE
        # ml_predictions = get_type4_py_predictions(file_path)

        # BUILD SEARCH TREE
        # search_tree = build_tree(Node("Top level node", 1), ml_predictions)
        # depth_first_traversal(search_tree, python_code)

        # PERFORM CHANGE
        # for annotation in ml_predictions:
        #     print("ANNOTATION:", annotation)

        # new_text = AnnotationInserter.insert_annotations(text)

        file_path_wrong = "d:\Documents\TU Delft\Year 6\Master's Thesis\lsp-mark-python\src\example\example-wrong.py"
        new_python_code = open(file_path_wrong, "r").read()
        editor.change_file(new_python_code)
        editor.close_file()

    editor.stop()


if __name__ == "__main__":
    main()
