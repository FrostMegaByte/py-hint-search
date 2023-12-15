import json
import os
import argparse
import time
import libcst as cst
import colorama
from colorama import Fore
from stubs import StubTransformer

from type4py_api import Type4PyException, get_ordered_type4py_predictions
from annotations import (
    AlreadyTypeAnnotatedCollector,
    BinaryTransformer,
    PyrightTypeAnnotationCollector,
    PyrightTypeAnnotationTransformer,
    RemoveIncompleteAnnotations,
)
from fake_editor import FakeEditor
from imports import (
    add_import_to_searchtree,
    get_all_classes_in_project,
    get_all_classes_in_virtual_environment,
)
from loggers import create_evaluation_logger, create_main_logger
from searchtree import (
    transform_predictions_to_array_to_process,
    build_tree,
    depth_first_traversal,
)

colorama.init(autoreset=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python type annotator based on Pyright feedback."
    )

    def dir_path(string: str) -> str:
        normalized_path = os.path.normpath(string)
        if os.path.isdir(normalized_path):
            return normalized_path
        else:
            raise NotADirectoryError(normalized_path)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        # default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/example",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/redis-correct/fully-annotated",
        help="The path to the project which will be type annotated.",
        # required=True,
    )
    parser.add_argument(
        "--venv-path",
        type=dir_path,
        # default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/redis-correct/.venv",
        help="The path to the virtual environment.",
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


def create_pyright_config_file(project_path: str, venv_path: str | None) -> None:
    config = {"typeCheckingMode": "strict"}

    if venv_path is not None:
        config["venvPath"] = venv_path

    with open(os.path.join(project_path, "pyrightconfig.json"), "w") as f:
        json.dump(config, f)


def remove_pyright_config_file(project_path: str) -> None:
    pyright_config_file = os.path.join(project_path, "pyrightconfig.json")
    if os.path.exists(pyright_config_file):
        os.remove(pyright_config_file)


def _create_type_annotated_source_code_file(
    source_code_tree, typed_path, relative_path, file_name
) -> None:
    output_typed_directory = os.path.abspath(
        os.path.join(typed_path + "-source-code", relative_path)
    )
    os.makedirs(output_typed_directory, exist_ok=True)
    open(os.path.join(output_typed_directory, file_name), "w", encoding="utf-8").write(
        source_code_tree.code
    )


def create_stub_file(source_code_tree, typed_path, relative_path, file_name) -> None:
    _create_type_annotated_source_code_file(
        source_code_tree, typed_path, relative_path, file_name
    )

    # Create type stub for the type annotated source code tree
    transformer = StubTransformer()
    type_annotated_stub_tree = source_code_tree.visit(transformer)

    # Write the type annotated stub to a file
    output_typed_directory = os.path.abspath(os.path.join(typed_path, relative_path))
    os.makedirs(output_typed_directory, exist_ok=True)
    open(
        os.path.join(output_typed_directory, file_name + "i"), "w", encoding="utf-8"
    ).write(type_annotated_stub_tree.code)


def main(args: argparse.Namespace) -> None:
    editor = FakeEditor()
    working_directory = os.getcwd()

    root_uri = f"file:///{args.project_path}"
    workspace_folders = [{"name": "type-annotation-searcher", "uri": root_uri}]

    stubs_directory = "typings"
    stubs_path = os.path.abspath(os.path.join(working_directory, stubs_directory))
    PYRIGHT_ANNOTATIONS_EXIST = os.path.isdir(stubs_path)

    typed_directory = "type-annotated"
    typed_path = os.path.abspath(os.path.join(working_directory, typed_directory))

    print("Gathering all local classes in the project...")
    ALL_PROJECT_CLASSES = get_all_classes_in_project(args.project_path, args.venv_path)
    if args.venv_path is not None:
        venv_directory = args.venv_path.split(os.sep)[-1]
        print("Gathering all classes in the virtual environment...")
        ALL_VENV_CLASSES = get_all_classes_in_virtual_environment(args.venv_path)
        ALL_PROJECT_CLASSES = ALL_VENV_CLASSES | ALL_PROJECT_CLASSES

    editor.start(root_uri, workspace_folders)

    # Walk through project directories and type annotate all python files
    for root, dirs, files in os.walk(args.project_path):
        # Ignore the virtual environment directory
        if args.venv_path and venv_directory in dirs:
            dirs.remove(venv_directory)
        else:
            for venv_name in {"venv", ".venv", "env", ".env", "virtualenv"}:
                if venv_name in dirs:
                    dirs.remove(venv_name)
                    break

        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.project_path)
            print(f"Processing file: {os.path.join(relative_path, file)}")
            logger.info(f"Processing file: {os.path.join(relative_path, file)}")
            start_time = time.time()

            type_annotated_file = os.path.abspath(
                os.path.join(
                    working_directory, "type-annotated", relative_path, file + "i"
                )
            )
            if os.path.exists(type_annotated_file):
                print(f"{Fore.GREEN}{file} already annotated. Skipping...\n")
                logger.info(f"{file} already annotated. Skipping...")
                continue

            file_path = os.path.join(root, file)
            editor.open_file(file_path)
            editor.has_diagnostic_error(at_start=True)

            python_code = editor.edit_document.text
            if python_code == "":
                print(f"{Fore.BLUE}'{file}' is an empty file. Skipping...\n")
                logger.info(f"'{file}' is an empty file. Skipping...")
                editor.close_file()
                continue

            source_code_tree = cst.parse_module(python_code)

            # Add type annotations inferred by Pyright
            added_extra_pyright_annotations = False
            if PYRIGHT_ANNOTATIONS_EXIST:
                relative_stub_subdirectory = os.path.relpath(root, working_directory)
                stub_directory = os.path.join(stubs_path, relative_stub_subdirectory)
                stub_file = os.path.join(stub_directory, file + "i")
                try:
                    with open(stub_file, "r", encoding="utf-8") as f:
                        stub_code = f.read()
                    stub_tree = cst.parse_module(stub_code)
                    pyright_visitor = PyrightTypeAnnotationCollector()
                    stub_tree.visit(pyright_visitor)

                    all_unknown_annotations = set()
                    for (
                        pyright_type_annotation
                    ) in pyright_visitor.all_pyright_annotations:
                        # Handle imports of pyright type annotations
                        (
                            tree_with_import,
                            unknown_annotations,
                        ) = add_import_to_searchtree(
                            ALL_PROJECT_CLASSES,
                            file_path,
                            source_code_tree,
                            pyright_type_annotation,
                        )
                        source_code_tree = tree_with_import

                        if len(unknown_annotations) > 0:
                            all_unknown_annotations |= unknown_annotations
                            continue

                    pyright_transformer = PyrightTypeAnnotationTransformer(
                        pyright_visitor.annotations, all_unknown_annotations
                    )
                    source_code_tree = source_code_tree.visit(pyright_transformer)
                    editor.change_file(source_code_tree.code, None)
                    editor.has_diagnostic_error(at_start=True)
                    added_extra_pyright_annotations = True
                except FileNotFoundError:
                    print(
                        f"{Fore.YELLOW}'{file}' has no related Pyright stub file, but it should have one for better performance.\n"
                        + "Recommended: Run command to recreate Pyright stubs\n"
                    )
                    logger.warning(
                        f"'{file}' has no related Pyright stub file, but it should have one for better performance. "
                        + "Recommended: Run command to recreate Pyright stubs"
                    )

            incomplete_transformer = RemoveIncompleteAnnotations()
            source_code_tree = source_code_tree.visit(incomplete_transformer)

            binary_ops_transformer = BinaryTransformer()
            source_code_tree = source_code_tree.visit(binary_ops_transformer)

            # Get ML type annotation predictions
            try:
                ml_predictions = get_ordered_type4py_predictions(source_code_tree.code)
            except Type4PyException:
                print(
                    f"{Fore.YELLOW}'{file}' cannot be parsed by Type4Py. Skipping...\n"
                )
                logger.warning(f"'{file}' cannot be parsed by Type4Py. Skipping...")
                editor.close_file()
                continue

            # Get already type annotated parameters and return types
            pyright_visitor = AlreadyTypeAnnotatedCollector()
            source_code_tree.visit(pyright_visitor)

            # Transform the predictions and filter out already type annotated parameters and return types
            search_tree_layers = transform_predictions_to_array_to_process(
                ml_predictions, pyright_visitor.already_type_annotated
            )

            number_of_type_slots_to_fill = len(search_tree_layers)
            if number_of_type_slots_to_fill == 0:
                if added_extra_pyright_annotations:
                    create_stub_file(source_code_tree, typed_path, relative_path, file)
                    print(
                        f"{Fore.GREEN}'{file}' completed with additional Pyright annotations!\n"
                    )
                    logger.info(
                        f"'{file}' completed with additional Pyright annotations!"
                    )
                    editor.close_file()
                    continue
                else:
                    print(
                        f"{Fore.BLUE}'{file}' has no type slots to fill. Skipping...\n"
                    )
                    logger.info(f"'{file}' has no type slots to fill. Skipping...")
                    editor.close_file()
                    continue
            if number_of_type_slots_to_fill >= 100:
                print(f"{Fore.RED}'{file}' contains too many type slots. Skipping...\n")
                logger.warning(f"'{file}' contains too many type slots. Skipping...")
                editor.close_file()
                continue

            # Build the search tree
            search_tree = build_tree(search_tree_layers, args.top_k)

            # Perform depth first traversal to annotate the source code tree (most work)
            type_annotated_source_code_tree = depth_first_traversal(
                search_tree,
                source_code_tree,
                editor,
                number_of_type_slots_to_fill,
                ALL_PROJECT_CLASSES,
            )

            create_stub_file(
                type_annotated_source_code_tree, typed_path, relative_path, file
            )
            editor.close_file()

            finish_time = time.time() - start_time
            evaluation_logger.info(f"Results of {os.path.join(relative_path, file)}:")
            evaluation_logger.info(f"Total time taken:\t\t{finish_time}")
            evaluation_logger.info(
                f"# Predicted type slots:\t{number_of_type_slots_to_fill}"
            )
            evaluation_logger.info(
                f"Time per slot:\t\t\t{finish_time/number_of_type_slots_to_fill}"
            )
            evaluation_logger.info(f"=" * 15)
            print()

    editor.stop()


if __name__ == "__main__":
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.project_path, "..")))

    create_pyright_config_file(args.project_path, args.venv_path)
    logger = create_main_logger()
    evaluation_logger = create_evaluation_logger()
    main(args)
    remove_pyright_config_file(args.project_path)

    # try:
    #     create_pyright_config_file(args.project_path)
    #     logger = create_main_logger()
    #     evaluation_logger = create_evaluation_logger()
    #     main(args)
    #     remove_pyright_config_file(args.project_path)
    # except Exception as e:
    #     remove_pyright_config_file(args.project_path)
    #     print(f"{Fore.RED}An exception occurred. See logs for more details.")
    #     logger.error(e)
