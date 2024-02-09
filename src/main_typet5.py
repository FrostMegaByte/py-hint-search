import json
import os
import argparse
import time
import libcst as cst
import colorama
from colorama import Fore
import tracemalloc

from loggers import create_evaluation_logger, create_main_logger, close_logger
from fake_editor import FakeEditor
from imports import (
    add_import_to_source_code_tree,
    get_all_classes_in_project,
    get_all_classes_in_virtual_environment,
    handle_binary_operation_imports,
)
from api_ml_model import TypeT5Exception, get_typet5_predictions
from annotations import (
    PyrightTypeAnnotationCollector,
    PyrightTypeAnnotationTransformer,
    RemoveIncompleteAnnotations,
    BinaryAnnotationTransformer,
    TypeSlotsVisitor,
)
from searchtree import (
    transform_predictions_to_slots_to_search,
    build_search_tree,
    depth_first_traversal,
)
from stubs import create_stub_file
from evaluation import (
    append_to_evaluation_csv_file,
    calculate_evaluation_statistics,
    create_evaluation_csv_file,
    gather_all_type_slots,
    has_extra_annotations,
)

colorama.init(autoreset=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Python type annotator based on Pyright feedback."
    )

    def dir_path(string: str) -> str:
        normalized_path = os.path.normpath(string)
        normalized_path = normalized_path.replace(os.sep, "/")
        if os.path.isdir(normalized_path):
            return normalized_path
        else:
            raise NotADirectoryError(normalized_path)

    parser.add_argument(
        "--project-path",
        type=dir_path,
        # default="D:/Documents/test/requests-main/src/requests",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/braintree-correct/fully-annotated",
        help="The path to the Python files directory of the project that will be type annotated.",
        # required=True,
    )
    parser.add_argument(
        "--venv-path",
        type=dir_path,
        # default="D:/Documents/test/requests-main/.venv",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/braintree-correct/.venv",
        help="The path to the virtual environment of the project that will be type annotated.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        choices=range(1, 6),
        default="1",
        help="Try the top-n type annotation predictions during search.",
    )
    parser.add_argument(
        "--only-run-pyright",
        type=bool,
        default=False,
        help="Only run Pyright and not the ML search step.",
    )
    parser.add_argument(
        "--keep-source-code-files",
        type=bool,
        default=True,
        help="Keep or discard the source code files after type annotating them.",
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


def get_pyright_stubs_path(working_directory: str) -> str:
    STUBS_DIRECTORY_PYRIGHT = "typings"
    stubs_path_pyright = os.path.abspath(
        os.path.join(working_directory, STUBS_DIRECTORY_PYRIGHT)
    )

    # If the directory doesn't exist in the current working directory, check the parent directory
    if not os.path.isdir(stubs_path_pyright):
        parent_directory = os.path.dirname(working_directory)
        stubs_path_pyright = os.path.abspath(
            os.path.join(parent_directory, STUBS_DIRECTORY_PYRIGHT)
        )

    return stubs_path_pyright


def run_pyright(
    source_code_tree,
    root,
    working_directory,
    file_path,
    file,
    all_project_classes,
):
    """
    Returns:
        source_code_tree: the source code tree to perform the ML search on
        has_performed_pyright_step: boolean indicating whether the Pyright step has been performed
    """
    stubs_path_pyright = get_pyright_stubs_path(working_directory)
    relative_stub_subdirectory = os.path.relpath(root, working_directory)
    stub_directory = os.path.join(stubs_path_pyright, relative_stub_subdirectory)
    stub_file = os.path.join(stub_directory, file + "i")
    try:
        with open(stub_file, "r", encoding="utf-8") as f:
            stub_code = f.read()
        stub_tree = cst.parse_module(stub_code)
        visitor_pyright = PyrightTypeAnnotationCollector()
        stub_tree.visit(visitor_pyright)

        all_unknown_annotations = set()
        for pyright_type_annotation in visitor_pyright.all_pyright_annotations:
            # Handle imports of pyright type annotations
            tree_with_import, unknown_annotations = add_import_to_source_code_tree(
                source_code_tree,
                pyright_type_annotation,
                all_project_classes,
                file_path,
            )
            source_code_tree = tree_with_import

            if len(unknown_annotations) > 0:
                all_unknown_annotations |= unknown_annotations
                continue

        transformer_pyright = PyrightTypeAnnotationTransformer(
            visitor_pyright.annotations, all_unknown_annotations
        )
        source_code_tree = source_code_tree.visit(transformer_pyright)
        return source_code_tree, True
    except FileNotFoundError:
        print(
            f"{Fore.YELLOW}'{file}' has no related Pyright stub file, but it should have one for better performance.\n"
            + "Recommended: Run command to recreate Pyright stubs\n"
        )
        logger.warning(
            f"'{file}' has no related Pyright stub file, but it should have one for better performance. "
            + "Recommended: Run command to recreate Pyright stubs"
        )
        return source_code_tree, False


def run_ml_search(
    source_code_tree,
    file,
    added_extra_pyright_annotations,
    editor,
    all_project_classes,
    ml_predictions_per_file,
    relative_path,
):
    """
    Returns:
        source_code_tree: the source code tree to perform the ML search on
        has_performed_ml_search: boolean indicating whether the ML search has been performed
        should_skip_file: boolean indicating whether the file should be skipped
        number_of_ml_evaluated_type_slots: integer value of the number of type slots evaluated by the ML model
    """
    # Get available and already type annotated parameters and return types
    visitor_type_slots = TypeSlotsVisitor()
    source_code_tree.visit(visitor_type_slots)

    relative_file_name = os.path.normpath(os.path.join(relative_path, file)).replace(
        os.sep, "/"
    )
    if relative_file_name not in ml_predictions_per_file:
        print(
            f"{Fore.YELLOW}'{file}' doesn't have TypeT5 type annotation predictions. Skipping...\n"
        )
        logger.warning(
            f"'{file}' doesn't have TypeT5 type annotation predictions. Skipping..."
        )
        return source_code_tree, False, True, 0

    ml_predictions = ml_predictions_per_file[relative_file_name]

    # Transform the predictions and filter out already type annotated parameters and return types
    search_tree_layers = transform_predictions_to_slots_to_search(
        ml_predictions, visitor_type_slots.available_slots
    )

    number_of_type_slots_to_fill = len(search_tree_layers)
    if number_of_type_slots_to_fill == 0:
        if added_extra_pyright_annotations:
            print(f"{Fore.GREEN}'{file}' completed fully with Pyright annotations!")
            logger.info(f"'{file}' completed fully with Pyright annotations!")
            return source_code_tree, False, False, 0
        else:
            print(f"{Fore.BLUE}'{file}' has no type slots to fill. Skipping...\n")
            logger.info(f"'{file}' has no type slots to fill. Skipping...")
            return source_code_tree, False, True, 0

    if number_of_type_slots_to_fill >= 100:
        print(f"{Fore.RED}'{file}' contains too many type slots. Skipping...\n")
        logger.warning(f"'{file}' contains too many type slots. Skipping...")
        return source_code_tree, False, True, 0

    search_tree = build_search_tree(search_tree_layers, args.top_n)

    type_annotated_source_code_tree = depth_first_traversal(
        search_tree,
        source_code_tree,
        editor,
        number_of_type_slots_to_fill,
        all_project_classes,
    )
    return type_annotated_source_code_tree, True, False, number_of_type_slots_to_fill


def main(args: argparse.Namespace) -> None:
    working_directory = os.getcwd()
    project_path = (
        args.project_path.lstrip("/")
        if args.project_path.startswith("/")
        else args.project_path
    )
    root_uri = f"file:///{project_path}"

    print("Gathering all local classes in the project...")
    ALL_PROJECT_CLASSES = get_all_classes_in_project(args.project_path, args.venv_path)
    if args.venv_path is not None:
        venv_directory = args.venv_path.split(os.sep)[-1]
        print("Gathering all classes in the virtual environment...")
        ALL_VENV_CLASSES = get_all_classes_in_virtual_environment(args.venv_path)
        ALL_PROJECT_CLASSES = ALL_VENV_CLASSES | ALL_PROJECT_CLASSES

    if not args.only_run_pyright:
        try:
            print(
                "Predicting type annotations with TypeT5. This will take a long time..."
            )
            ml_predictions_per_file = get_typet5_predictions()
        except TypeT5Exception:
            print(f"{Fore.RED}Project cannot be parsed by TypeT5...\n")
            logger.error("Project cannot be parsed by TypeT5...")

    stubs_path_pyright = get_pyright_stubs_path(working_directory)
    pyright_annotations_exist = os.path.isdir(stubs_path_pyright)
    if not pyright_annotations_exist:
        print(
            f"{Fore.YELLOW}No Pyright stubs found. Skipping Pyright annotations...\n"
            + "Recommended: Run Pyright command from README to create Pyright stubs\n"
        )
        logger.warning(
            "No Pyright stubs found. Skipping Pyright annotations... "
            + "Recommended: Run Pyright command from README to create Pyright stubs"
        )

    typed_directory = (
        f"type-annotated-top{args.top_n}"
        if not args.only_run_pyright
        else "pyright-annotated"
    )
    typed_path = os.path.abspath(os.path.join(working_directory, typed_directory))

    editor = FakeEditor()
    editor.start(root_uri)

    postfix = "pyright" if args.only_run_pyright else f"top{args.top_n}"
    create_evaluation_csv_file(postfix)

    # Walk through project directories and type annotate all Python files
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
            logger.info("=" * 15)
            evaluation_logger.info("=" * 15)

            relative_path = os.path.relpath(root, args.project_path)
            print(f"Processing file: {os.path.join(relative_path, file)}")
            logger.info(f"Processing file: {os.path.join(relative_path, file)}")
            start_time_total = time.perf_counter()

            type_annotated_file = os.path.abspath(
                os.path.join(typed_path, relative_path, file + "i")
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
            type_slots_groundtruth = gather_all_type_slots(source_code_tree)

            #####################
            # Pyright step      #
            #####################
            # Add type annotations inferred by Pyright
            if pyright_annotations_exist:
                tracemalloc.start()
                start_time_pyright = time.perf_counter()

                source_code_tree, has_performed_pyright_step = run_pyright(
                    source_code_tree,
                    root,
                    working_directory,
                    file_path,
                    file,
                    ALL_PROJECT_CLASSES,
                )
                editor.change_file(source_code_tree.code, None)
                editor.has_diagnostic_error(at_start=True)

                finish_time_pyright = time.perf_counter() - start_time_pyright
                if not has_performed_pyright_step:
                    finish_time_pyright = 0

                _, peak_memory_usage_pyright = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            type_slots_after_pyright = gather_all_type_slots(source_code_tree)
            added_extra_pyright_annotations = has_extra_annotations(
                type_slots_groundtruth, type_slots_after_pyright
            )

            if args.only_run_pyright:
                if added_extra_pyright_annotations:
                    print(f"{Fore.GREEN}'{file}' has extra Pyright annotations added!")
                    logger.info(f"'{file}' has extra Pyright annotations added!")
                else:
                    print(
                        f"{Fore.BLUE}'{file}' has no Pyright annotations. Skipping...\n"
                    )
                    logger.info(f"'{file}' has no Pyright annotations. Skipping...")
                    editor.close_file()
                    continue

            transformer_remove_incomplete = RemoveIncompleteAnnotations()
            source_code_tree = source_code_tree.visit(transformer_remove_incomplete)

            transformer_binary_ops = BinaryAnnotationTransformer()
            source_code_tree = source_code_tree.visit(transformer_binary_ops)
            source_code_tree = handle_binary_operation_imports(
                source_code_tree,
                transformer_binary_ops.should_import_optional,
                transformer_binary_ops.should_import_union,
            )

            #####################
            # ML search step    #
            #####################
            tracemalloc.start()
            start_time_ml_search = time.perf_counter()

            has_performed_ml_search = False
            should_skip_file = False
            number_of_ml_evaluated_type_slots = 0
            if not args.only_run_pyright:
                (
                    source_code_tree,
                    has_performed_ml_search,
                    should_skip_file,
                    number_of_ml_evaluated_type_slots,
                ) = run_ml_search(
                    source_code_tree,
                    file,
                    added_extra_pyright_annotations,
                    editor,
                    ALL_PROJECT_CLASSES,
                    ml_predictions_per_file,
                    relative_path,
                )

            if should_skip_file:
                editor.close_file()
                continue

            finish_time_ml_search = time.perf_counter() - start_time_ml_search
            if not has_performed_ml_search:
                finish_time_ml_search = 0

            type_slots_after_ml_search = gather_all_type_slots(source_code_tree)

            create_stub_file(
                source_code_tree,
                typed_path,
                relative_path,
                file,
                args.keep_source_code_files,
            )
            editor.close_file()

            finish_time_total = time.perf_counter() - start_time_total
            _, peak_memory_usage_ml_search = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            evaluation_statistics = calculate_evaluation_statistics(
                os.path.join(relative_path, file),
                type_slots_groundtruth,
                type_slots_after_pyright,
                type_slots_after_ml_search,
                number_of_ml_evaluated_type_slots,
                has_performed_pyright_step,
                has_performed_ml_search,
                finish_time_pyright,
                finish_time_ml_search,
                finish_time_total,
                peak_memory_usage_pyright if has_performed_pyright_step else 0,
                peak_memory_usage_ml_search if has_performed_ml_search else 0,
            )
            append_to_evaluation_csv_file(list(evaluation_statistics.values()), postfix)

            for k, v in evaluation_statistics.items():
                evaluation_logger.info(f"{k}: {v}")
            print()

    editor.stop()


if __name__ == "__main__":
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.project_path, "..")))

    create_pyright_config_file(args.project_path, args.venv_path)
    logger = create_main_logger()
    evaluation_logger = create_evaluation_logger()
    main(args)
    close_logger(logger)
    close_logger(evaluation_logger)
    remove_pyright_config_file(args.project_path)

    # try:
    #     create_pyright_config_file(args.project_path, args.venv_path)
    #     logger = create_main_logger()
    #     evaluation_logger = create_evaluation_logger()
    #     main(args)
    #     remove_pyright_config_file(args.project_path)
    # except Exception as e:
    #     remove_pyright_config_file(args.project_path)
    #     print(f"{Fore.RED}An exception occurred. See logs for more details.")
    #     logger.error(e)
