import argparse
from datetime import datetime
import logging
import os
from typing import Dict, List, Optional, Tuple
import libcst as cst
import csv

import colorama
from colorama import Fore

from utils import node_to_code, transform_binary_operations_to_unions

colorama.init(autoreset=True)


class TypeAnnotationsCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.stack: List[Tuple[str, ...]] = []
        self.all_type_slots: Dict[Tuple[str, ...], str] = {}

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.stack.append(node.name.value)
        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.stack.append(node.name.value)
        for param in node.params.params:
            if param.name.value == "self":
                continue
            self.stack.append(param.name.value)
            annotation = (
                node_to_code(param.annotation.annotation)
                if param.annotation is not None
                else None
            )
            self.all_type_slots[tuple(self.stack)] = annotation
            self.stack.pop()

        self.stack.append("return")
        return_annotation = (
            node_to_code(node.returns.annotation) if node.returns is not None else None
        )
        self.all_type_slots[tuple(self.stack)] = return_annotation
        self.stack.pop()
        return True

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.stack.pop()


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
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/braintree-correct/type-annotated-source-code-stripped-run",
        help="The path to the ML annotated project directory.",
        # required=True,
    )
    parser.add_argument(
        "-fapp",
        "--fully-annotated-project-path",
        type=dir_path,
        # default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/projects/example",
        default="D:/Documents/TU Delft/Year 6/Master's Thesis/lsp-mark-python/src/typeshed-mergings/braintree-correct/fully-annotated",
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
        "# correct",
        "# incorrect",
        "# groundtruth annotations",
        # "# available type slots",
        "precision",
        "recall",
        # "# total type slots",
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


def main():
    args = parse_arguments()
    os.chdir(os.path.abspath(os.path.join(args.fully_annotated_project_path, "..")))
    create_correctness_csv_file()

    for root, dirs, files in os.walk(args.fully_annotated_project_path):
        python_files = [file for file in files if file.endswith(".py")]
        for file in python_files:
            relative_path = os.path.relpath(root, args.fully_annotated_project_path)
            print(f"Checking file: {os.path.join(relative_path, file)}")
            n_correct = 0
            n_incorrect = 0

            try:
                fully_annotated_file_path = os.path.join(root, file)
                fully_annotated_code = open(
                    fully_annotated_file_path, "r", encoding="utf-8"
                ).read()
                fully_annotated_tree = cst.parse_module(fully_annotated_code)
                visitor_fully_annotated = TypeAnnotationsCollector()
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
                visitor_ml_annotated = TypeAnnotationsCollector()
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
                k: v
                for k, v in visitor_fully_annotated.all_type_slots.items()
                if v not in UNANNOTATED_GROUND_TRUTHS
            }
            ml_annotations = {
                k: v
                for k, v in visitor_ml_annotated.all_type_slots.items()
                if k in groundtruth_annotations
            }
            # available_type_slots = {
            #     k: v
            #     for k, v in visitor_fully_annotated.all_type_slots.items()
            #     if v in UNANNOTATED_GROUND_TRUTHS
            # }

            assert len(groundtruth_annotations) == len(ml_annotations)

            for slot, groundtruth_annotation in groundtruth_annotations.items():
                ml_annotation = ml_annotations[slot]

                # Parse binary operations to unions
                if "|" in groundtruth_annotation:
                    groundtruth_annotation = transform_binary_operations_to_unions(
                        cst.parse_expression(groundtruth_annotation)
                    )
                if ml_annotation is not None and "|" in ml_annotation:
                    ml_annotation = transform_binary_operations_to_unions(
                        cst.parse_expression(ml_annotation)
                    )

                if ml_annotation == groundtruth_annotation:
                    n_correct += 1
                # TODO: elif check for partial match
                else:
                    n_incorrect += 1
                    if args.verbose:
                        print(f"{Fore.RED}Annotation mismatch for '{slot}':")
                        print(f"{Fore.RED}Fully annotated: {groundtruth_annotation}")
                        print(f"{Fore.RED}ML annotated: {ml_annotation}")
                        print()

            try:
                n_all = len([v for v in ml_annotations.values() if v is not None])
                precision = n_correct / n_all
            except ZeroDivisionError:
                precision = "-"
            try:
                D = len(groundtruth_annotations)
                recall = n_correct / D
            except ZeroDivisionError:
                recall = "-"

            correctness_statistics = {
                "file": os.path.join(relative_path, file),
                "correct_count": n_correct,
                "incorrect_count": n_incorrect,
                "groundtruth_annotations_count": n_correct + n_incorrect,
                # "available_slots_count": len(available_type_slots),
                "precision": precision,
                "recall": recall,
                # "total_type_slots_count": len(visitor_fully_annotated.all_type_slots),
            }
            append_to_correctness_csv_file(list(correctness_statistics.values()))


if __name__ == "__main__":
    main()
