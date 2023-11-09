import os
import argparse

from remove_type_annotations import remove_type_hints


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
        help="The path to the project which will be type annotated.",
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
