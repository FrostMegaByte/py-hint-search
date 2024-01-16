import argparse
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional, Tuple
import libcst as cst
import csv
import colorama
from colorama import Fore

from annotations import TypeSlotsVisitor
from constants import COMMON_ANNOTATIONS
from evaluation import remove_known_dunder_methods, split_into_ubiquitous_common_rare
from type_check import PythonType, parse_type_str, AccuracyMetric

colorama.init(autoreset=True)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the correctness of ML determined type annotations compared to ground truth"
    )

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument(
        "-mlpp",
        "--ml-annotated-project-path",
        type=dir_path,
        # default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/type-annotated-source-code",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/colorama-correct/type-annotated-source-code-stripped",
        help="The path to the ML annotated project directory.",
        # required=True,
    )
    parser.add_argument(
        "-fapp",
        "--fully-annotated-project-path",
        type=dir_path,
        # default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/example",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/colorama-correct/fully-annotated",
        help="The path to the fully annotated project directory.",
        # required=True,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=bool,
        default=True,
        help="Log which fully annotated type and ML-determined type don't match.",
    )

    return parser.parse_args()


def create_correctness_csv_file():
    headers = [
        "file",
        "metric",
        "# correct",
        "# incorrect",
        "# groundtruth annotations",
        "precision",
        "recall",
        "# ML annotations",
        "# ubiquitous annotations (excl. dunder methods)",
        "# common annotations (excl. dunder methods)",
        "# rare annotations (excl. dunder methods)",
    ]
    with open(
        "logs-evaluation/type correctness.csv",
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_to_correctness_csv_file(correctness_statistics):
    with open(
        "logs-evaluation/type correctness.csv",
        "a",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(correctness_statistics)


def filter_out_Missing(annotations):
    return {k: v for k, v in annotations.items() if v != parse_type_str("Missing")}


def calculate_correctness(
    ml_annotations: Dict[Tuple[str, ...], PythonType],
    groundtruth_annotations: Dict[Tuple[str, ...], PythonType],
    metric: AccuracyMetric,
):
    assert len(ml_annotations) == len(groundtruth_annotations)

    label_types = list(map(metric.process_type, groundtruth_annotations.values()))
    pred_types = list(map(metric.process_type, ml_annotations.values()))

    if metric.filter_none_any | metric.filter_rare:
        filtered_ids = [i for i, t in enumerate(label_types) if metric.to_keep_type(t)]
        pred_types = [pred_types[i] for i in filtered_ids]
        label_types = [label_types[i] for i in filtered_ids]

    n_correct = 0
    n_incorrect = 0
    n_total = 0
    incorrect_annotations = []

    for i, p, l in zip(range(len(pred_types)), pred_types, label_types):
        if p == l:
            n_correct += 1
        else:
            n_incorrect += 1
            incorrect_annotations.append(
                (list(groundtruth_annotations.keys())[i], p, l)
            )
        n_total += 1

    try:
        n_all = len(
            [v for v in ml_annotations.values() if v != parse_type_str("Missing")]
        )
        precision = n_correct / n_all
    except ZeroDivisionError:
        precision = "-"
    try:
        D = len(groundtruth_annotations)
        recall = n_correct / D
    except ZeroDivisionError:
        recall = "-"

    return {
        "correct_count": n_correct,
        "incorrect_count": n_incorrect,
        "groundtruth_annotations_count": n_total,
        "precision": precision,
        "recall": recall,
    }, incorrect_annotations


def main():
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.fully_annotated_project_path, "..")))
    create_correctness_csv_file()

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
                ml_annotated_file_path = os.path.abspath(
                    os.path.join(args.ml_annotated_project_path, relative_path, file)
                )
                ml_annotated_code = open(
                    ml_annotated_file_path, "r", encoding="utf-8"
                ).read()
                ml_annotated_tree = cst.parse_module(ml_annotated_code)
                visitor_ml_annotated = TypeSlotsVisitor()
                ml_annotated_tree.visit(visitor_ml_annotated)
            except FileNotFoundError as e:
                print(f"{Fore.RED}No ML annotated file found for '{file}'")
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

            ml_annotations = {
                k: parse_type_str(v) if v is not None else parse_type_str("Missing")
                for k, v in visitor_ml_annotated.all_type_slots.items()
                if k in groundtruth_annotations
            }

            for metric in metrics:
                statistics, incorrect_types = calculate_correctness(
                    ml_annotations, groundtruth_annotations, metric
                )

                if args.verbose:
                    if len(incorrect_types) > 0:
                        print(f"Incorrect types according to '{metric.name}' metric")
                    for slot, ml_annotation, groundtruth_annotation in incorrect_types:
                        print(f"{Fore.RED}Annotation mismatch for '{slot}':")
                        print(f"{Fore.RED}Fully annotated: {groundtruth_annotation}")
                        print(f"{Fore.RED}ML annotated: {ml_annotation}")
                        print()

                ml_annotations_without_missing = filter_out_Missing(ml_annotations)
                (
                    annotations_ubiquitous,
                    annotations_common,
                    annotations_rare,
                ) = split_into_ubiquitous_common_rare(ml_annotations_without_missing)

                correctness_statistics = {
                    "file": os.path.join(relative_path, file),
                    "metric": metric.name,
                    **statistics,
                    "ml_annotations_count": len(ml_annotations_without_missing),
                    "ubiquitous_annotations_count": len(annotations_ubiquitous),
                    "common_annotations_count": len(annotations_common),
                    "rare_annotations_count": len(annotations_rare),
                }
                append_to_correctness_csv_file(list(correctness_statistics.values()))


if __name__ == "__main__":
    main()
