import argparse
import os
import subprocess
from typing import List


def create_pyright_typestubs(project_path: str) -> None:
    os.chdir(os.path.abspath(os.path.join(project_path, "..")))
    working_directory = os.getcwd()

    python_subdirectories = get_subdirectories(project_path)
    python_subdirectories.reverse()

    for subdirectory in python_subdirectories:
        subdirectory_path = os.path.join(working_directory, subdirectory)
        init_file_path = os.path.join(subdirectory_path, "__init__.py")
        init_file_exists = os.path.exists(init_file_path)

        # Create __init__.py file if it doesn't exist yet
        if not init_file_exists:
            with open(init_file_path, "w") as f:
                f.write("")

        # Create type stubs for all python files in subdirectory
        subprocess.run(["pyright", "--createstub", subdirectory])

        # Remove __init__.py and __init__.pyi file if it didn't exist before
        if not init_file_exists:
            os.remove(init_file_path)
            init_stub_file_path = os.path.join(
                working_directory, "typings", subdirectory, "__init__.pyi"
            )
            if os.path.exists(init_stub_file_path):
                os.remove(init_stub_file_path)


def get_subdirectories(project_path: str) -> List[str]:
    subdirectories = []
    base_dir = project_path.rsplit("/", 1)[0]
    for root, dirs, files in os.walk(project_path):
        contains_python_files = False
        for file in files:
            if file.endswith(".py"):
                contains_python_files = True
                break

        if contains_python_files:
            subdirectory = os.path.relpath(root, base_dir)
            subdirectories.append(subdirectory)

    return subdirectories


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python type annotator based on Pyright feedback."
    )

    def dir_path(string: str) -> str:
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/Rope-main/rope",
        help="The path to the project which will be type annotated.",
        # required=True,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    create_pyright_typestubs(args.project_path)
