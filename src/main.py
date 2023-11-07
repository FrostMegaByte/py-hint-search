import os
import argparse
import libcst as cst
from datetime import datetime
import logging

from api import Type4PyException, get_type4py_predictions
from annotation_inserter import TypingCollector
from classes_gatherer import get_all_classes_in_project
from fake_editor import FakeEditor
from treebuilder import (
    transform_predictions_to_array_to_process,
    build_tree,
    depth_first_traversal,
)
from typestubs_creator import create_typestubs
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
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/example",
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
    ENABLE_PYRIGHT_ANNOTATIONS = False  # TODO: Doesn't work yet, since create_typestubs() has issues with finding imports

    args = parse_arguments()
    editor = FakeEditor()

    os.chdir(os.path.abspath(os.path.join(args.project_path, "..")))
    working_directory = os.getcwd()

    logs_path = os.path.abspath(os.path.join(working_directory, "logs"))
    os.makedirs(logs_path, exist_ok=True)
    logging.basicConfig(
        filename=f"logs/{datetime.today().strftime('%Y-%m-%d %H_%M_%S')}.txt",
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG,
    )
    logger = logging.getLogger(__name__)

    root_uri = f"file:///{args.project_path}"
    workspace_folders = [{"name": "python-lsp", "uri": root_uri}]

    stubs_directory = "typings"
    stubs_path = os.path.abspath(os.path.join(working_directory, stubs_directory))

    typed_directory = "type-annotated"
    typed_path = os.path.abspath(os.path.join(working_directory, typed_directory))

    all_project_classes = get_all_classes_in_project(args.project_path)

    create_pyright_config_file(args.project_path)
    if ENABLE_PYRIGHT_ANNOTATIONS:
        create_typestubs(args.project_path)
    editor.start(root_uri, workspace_folders)

    # Walk through project directories and type annotate all python files
    for root, dirs, files in os.walk(args.project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.project_path)
            print(f"Processing file: {os.path.join(relative_path, file)}")
            logger.info(f"Processing file: {os.path.join(relative_path, file)}")

            type_annotated_file = os.path.abspath(
                os.path.join(working_directory, "type-annotated", relative_path, file)
            )
            if os.path.exists(type_annotated_file):
                print(f"{file} already annotated. Skipping...\n")
                logger.info(f"{file} already annotated. Skipping...")
                continue

            file_path = os.path.join(root, file)
            editor.open_file(file_path)

            if editor.has_diagnostic_error():
                print(f"'{file}' contains Pyright error at the start. Skipping...\n")
                logger.info(
                    f"'{file}' contains Pyright error at the start. Skipping..."
                )
                # TODO: Can make this more specific by checking line and column positions of the error
                editor.close_file()
                continue

            python_code = editor.edit_document.text
            source_code_tree = cst.parse_module(python_code)

            # Add type annotations inferred by Pyright
            if ENABLE_PYRIGHT_ANNOTATIONS:
                relative_stub_subdirectory = os.path.relpath(root, working_directory)
                stub_directory = os.path.join(stubs_path, relative_stub_subdirectory)
                stub_file = os.path.join(stub_directory, file + "i")
                with open(stub_file, "r") as f:
                    stub_code = f.read()
                stub_tree = cst.parse_module(stub_code)
                visitor = PyrightAnnotationCollector()
                stub_tree.visit(visitor)
                transformer = PyrightAnnotationTransformer(visitor.annotations)
                source_code_tree = source_code_tree.visit(transformer)

            # Get already type annotated parameters and return types
            visitor = TypingCollector()
            source_code_tree.visit(visitor)

            # Get ML type annotation predictions
            try:
                ml_predictions = get_type4py_predictions(source_code_tree.code)
            except Type4PyException:
                print(f"'{file}' cannot be parsed by Type4Py. Skipping...\n")
                logger.info(f"'{file}' cannot be parsed by Type4Py. Skipping...")
                editor.close_file()
                continue

            # Transform the predictions and filter out already type annotated parameters and return types
            search_tree_layers = transform_predictions_to_array_to_process(
                ml_predictions, visitor.type_annotated
            )

            number_of_type_slots = len(search_tree_layers)
            if number_of_type_slots >= 100:
                print(f"'{file}' contains too many type slots. Skipping...\n")
                logger.info(f"'{file}' contains too many type slots. Skipping...")
                editor.close_file()
                continue

            # Build the search tree
            search_tree = build_tree(search_tree_layers, args.top_k)

            # Perform depth first traversal to annotate the source code tree (most work)
            type_annotated_source_code_tree = depth_first_traversal(
                search_tree,
                source_code_tree,
                editor,
                number_of_type_slots,
                all_project_classes,
            )

            # Write the type annotated source code to a file
            output_typed_directory = os.path.abspath(
                os.path.join(typed_path, relative_path)
            )
            os.makedirs(output_typed_directory, exist_ok=True)
            open(
                os.path.join(output_typed_directory, file), "w", encoding="utf-8"
            ).write(type_annotated_source_code_tree.code)

            editor.close_file()
            print()

    editor.stop()
    remove_pyright_config_file(args.project_path)


if __name__ == "__main__":
    main()
