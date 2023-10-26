import os
import argparse
import time
import libcst as cst

from fake_editor import FakeEditor


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
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/communication",
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


def main():
    args = parse_arguments()
    editor = FakeEditor()

    root_uri = f"file:///{args.project_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    editor.start(root_uri, workspace_folders)

    # Walk through project directories and type annotate all python files
    for root, dirs, files in os.walk(args.project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            file_path = os.path.join(root, file)
            editor.open_file(file_path)

            python_code = editor.edit_document.text
            source_code_tree = cst.parse_module(python_code)

            editor.show_completions()

            time.sleep(3)

            # modified_tree = (
            #     insert_return_annotation(
            #         modified_trees[layer_index],
            #         type_annotation,
            #         type_slot["func_name"],
            #     )
            #     if type_slot["param_name"] == "return"
            #     else insert_parameter_annotation(
            #         modified_trees[layer_index],
            #         type_annotation,
            #         type_slot["func_name"],
            #         type_slot["param_name"],
            #     )
            # )

            # editor.change_file(modified_tree.code)
            print(source_code_tree.code)

            editor.close_file()

    editor.stop()


if __name__ == "__main__":
    main()
