import argparse
import os
import re
from typing import Dict, Tuple
import libcst as cst
import csv
import colorama
from colorama import Fore

from annotations import TypeSlotsVisitor
from constants import COMMON_ANNOTATIONS
from evaluation import remove_known_dunder_methods
from type_check import PythonType, parse_type_str, AccuracyMetric

colorama.init(autoreset=True)


def parse_arguments(project_name, top_n) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the correctness of PyHintSearch determined type annotations compared to ground truth"
    )

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "-fapp",
        "--fully-annotated-project-path",
        type=dir_path,
        default=f"D:/Documents/TU Delft/Year 6/Master's Thesis/Results from GCP/{project_name}/fully_annotated",
        help="The path to the fully annotated project directory.",
        # required=True,
    )
    parser.add_argument(
        "-phspp",
        "--pyhintsearch-annotated-project-path",
        type=dir_path,
        default=f"D:/Documents/TU Delft/Year 6/Master's Thesis/Results from GCP/{project_name}/annotations-stripped/type-annotated-top{top_n}-source-code",
        help="The path to the PyHintSearch annotated project directory.",
        # required=True,
    )
    parser.add_argument(
        "-ipp",
        "--intersecting-project-path",
        type=dir_path,
        default=f"D:/Documents/TU Delft/Year 6/Master's Thesis/Results from GCP/{project_name}/annotations-stripped/pyright-annotated-source-code",
        help="The path to the project whose files are intersected with the PyHintSearch annotated project files. (This is needed for equal comparison for thesis evaluation). I.e. if PyHintSearch project is type-annotated-topn-source-code directory, this should be pyright-annotated-source-code directory. If PyHintSearch project is pyright-annotated-source-code directory, this should be type-annotated-topn-source-code directory).",
        # required=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=bool,
        default=False,
        help="Log which fully annotated type and PyHintSearch-determined type don't match.",
    )

    return parser.parse_args()


def create_correctness_csv_file(postfix):
    headers = [
        "file",
        "metric",
        "# groundtruth annotations (excl. dunder methods)",
        "# added PyHintSearch annotations (excl. dunder methods)",
        "# correct",
        "# incorrect",
        "precision",
        "recall",
    ]
    with open(
        f"logs-evaluation/type-correctness-{postfix}.csv",
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_to_correctness_csv_file(correctness_statistics, postfix):
    with open(
        f"logs-evaluation/type-correctness-{postfix}.csv",
        "a",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(correctness_statistics)


def filter_out_Missing(annotations):
    return {k: v for k, v in annotations.items() if v != parse_type_str("Missing")}


def calculate_correctness(
    groundtruth_annotations: Dict[Tuple[str, ...], PythonType],
    pyhintsearch_annotations: Dict[Tuple[str, ...], PythonType],
    metric: AccuracyMetric,
):
    assert len(pyhintsearch_annotations) == len(groundtruth_annotations)

    groundtruth_annotations = {
        k: metric.process_type(v) for k, v in groundtruth_annotations.items()
    }
    pyhintsearch_annotations = {
        k: metric.process_type(v) for k, v in pyhintsearch_annotations.items()
    }

    if metric.filter_none_any | metric.filter_rare:
        filtered_ids = [
            i
            for i, t in enumerate(groundtruth_annotations.values())
            if metric.to_keep_type(t)
        ]
        groundtruth_annotations = {
            k: v
            for i, (k, v) in enumerate(groundtruth_annotations.items())
            if i in filtered_ids
        }
        pyhintsearch_annotations = {
            k: v
            for i, (k, v) in enumerate(pyhintsearch_annotations.items())
            if i in filtered_ids
        }

    n_correct = 0
    n_incorrect = 0
    n_pyhintsearch = 0
    n_groundtruth = 0
    incorrect_annotations = []

    for i, gt, pred in zip(
        range(len(groundtruth_annotations)),
        groundtruth_annotations.values(),
        pyhintsearch_annotations.values(),
    ):
        if pred == gt:
            n_correct += 1
        else:
            n_incorrect += 1
            type_slot = list(groundtruth_annotations.keys())[i]
            incorrect_annotations.append((type_slot, gt, pred))
        if pred != parse_type_str("Missing"):
            n_pyhintsearch += 1
        n_groundtruth += 1

    try:
        n_all = n_pyhintsearch
        precision = n_correct / n_all
    except ZeroDivisionError:
        precision = "-"
    try:
        D = n_groundtruth
        recall = n_correct / D
    except ZeroDivisionError:
        recall = "-"

    return {
        "groundtruth_annotations_count": n_groundtruth,
        "pyhintsearch_annotations_count": n_pyhintsearch,
        "correct_count": n_correct,
        "incorrect_count": n_incorrect,
        "precision": round(precision, 2) if precision != "-" else "-",
        "recall": round(recall, 2) if recall != "-" else "-",
    }, incorrect_annotations


def main(args):
    annotated_dir_name = args.pyhintsearch_annotated_project_path.split("/")[-1]
    postfix = "SOMETHING_WENT_WRONG"
    if annotated_dir_name.startswith("type-annotated-top"):
        match = re.search(r"\d+", annotated_dir_name)
        if match:
            postfix = f"top{int(match.group())}"
    elif annotated_dir_name.startswith("pyright"):
        postfix = "pyright"
    create_correctness_csv_file(postfix)

    if args.intersecting_project_path is None:
        print(
            f"{Fore.BLUE}Intersecting project path is not specified... For fair comparisons for thesis, make sure that it is. It can be ommitted if you want to check correctness of PyHintSearch annotations to the fully annotated project."
        )
        continuation = input("Want to continue without it? (y/n): ")
        if continuation.lower() not in ["y", "yes"]:
            return

    metrics = AccuracyMetric.condensed_default_metrics(
        common_type_names=COMMON_ANNOTATIONS
    )

    for root, dirs, files in os.walk(args.fully_annotated_project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.fully_annotated_project_path)
            print(f"Checking file: {os.path.join(relative_path, file)}")

            try:
                fully_annotated_file_path = os.path.join(root, file)
                fully_annotated_code = open(
                    fully_annotated_file_path, "r", encoding="utf-8"
                ).read()
                fully_annotated_tree = cst.parse_module(fully_annotated_code)
                visitor_fully_annotated = TypeSlotsVisitor()
                fully_annotated_tree.visit(visitor_fully_annotated)
            except FileNotFoundError as e:
                print(e)

            try:
                pyhintsearch_annotated_file_path = os.path.abspath(
                    os.path.join(
                        args.pyhintsearch_annotated_project_path, relative_path, file
                    )
                )
                pyhintsearch_annotated_code = open(
                    pyhintsearch_annotated_file_path, "r", encoding="utf-8"
                ).read()
                pyhintsearch_annotated_tree = cst.parse_module(
                    pyhintsearch_annotated_code
                )
                visitor_pyhintsearch_annotated = TypeSlotsVisitor()
                pyhintsearch_annotated_tree.visit(visitor_pyhintsearch_annotated)
            except FileNotFoundError as e:
                print(
                    f"{Fore.RED}No PyHintSearch annotated file found for '{file}'. Skipping..."
                )
                continue

            # Skip files that don't have a corresponding "intersecting project" annotated file as those must be used for comparison against the PyHintSearch annotations
            if os.path.exists(args.intersecting_project_path):
                try:
                    intersecting_annotated_file_path = os.path.abspath(
                        os.path.join(
                            args.intersecting_project_path, relative_path, file
                        )
                    )
                    open(intersecting_annotated_file_path, "r", encoding="utf-8").read()
                except FileNotFoundError as e:
                    print(
                        f"{Fore.RED}No intersecting project annotated file found for '{file}'. Skipping..."
                    )
                    continue

            UNANNOTATED_GROUND_TRUTHS = {
                None,
                "Incomplete",
                "Incomplete | None",
                "Optional[Incomplete]",
            }
            groundtruth_annotations = {
                k: parse_type_str(v)
                for k, v in visitor_fully_annotated.all_type_slots.items()
                if v not in UNANNOTATED_GROUND_TRUTHS
            }
            groundtruth_annotations = remove_known_dunder_methods(
                groundtruth_annotations
            )

            # Skip files with no ground truth annotations
            if len(groundtruth_annotations) == 0:
                print(f"{Fore.RED}No groundtruth annotations in '{file}'. Skipping...")
                continue

            pyhintsearch_annotations = {
                k: parse_type_str(v) if v is not None else parse_type_str("Missing")
                for k, v in visitor_pyhintsearch_annotated.all_type_slots.items()
                if k in groundtruth_annotations
            }

            for metric in metrics:
                statistics, incorrect_types = calculate_correctness(
                    groundtruth_annotations,
                    pyhintsearch_annotations,
                    metric,
                )

                if args.verbose:
                    if len(incorrect_types) > 0:
                        print(f"Incorrect types according to '{metric.name}' metric")

                    for (
                        slot,
                        groundtruth_annotation,
                        pyhintsearch_annotation,
                    ) in incorrect_types:
                        print(f"{Fore.RED}Annotation mismatch for '{slot}':")
                        print(
                            f"{Fore.RED}Groundtruth annotation: {groundtruth_annotation}"
                        )
                        print(
                            f"{Fore.RED}PyHintSearch annotation: {pyhintsearch_annotation}"
                        )
                        print()

                correctness_statistics = {
                    "file": os.path.join(relative_path, file),
                    "metric": metric.name,
                    **statistics,
                }
                append_to_correctness_csv_file(
                    list(correctness_statistics.values()), postfix
                )

            print(f"{Fore.GREEN}Successful")


if __name__ == "__main__":
    while True:
        project_name = input("Please enter the project name: ").strip()
        top_n = int(input("Enter a value (1, 3 or 5): "))
        if top_n in (1, 3, 5):
            break
        print("Invalid input. Please enter 1, 3 or 5.")

    # for project_name in [
    #     "black",
    #     "bleach",
    #     "braintree",
    #     "colorama",
    #     "dateparser",
    #     "django",
    #     "exifread",
    #     "flask",
    #     "html5lib",
    #     "matplotlib",
    #     "pandas",
    #     "Pillow",
    #     "redis",
    #     "requests",
    #     "seaborn",
    #     "stripe",
    # ]:
    #     for i in [1, 3, 5]:
    #         top_n = i

    args = parse_arguments(project_name, top_n)
    os.chdir(os.path.abspath(os.path.join(args.fully_annotated_project_path, "..")))

    main(args)
