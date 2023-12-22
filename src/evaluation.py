import csv
from typing import Dict, List, Optional, Tuple
import libcst as cst

from annotations import TypeSlotsVisitor


INCOMPLETE_TYPE_ANNOTATIONS = {
    "Incomplete",
    "Incomplete | None",
    "Optional[Incomplete]",
}


def gather_all_type_slots(source_code_tree: cst.Module):
    visitor = TypeSlotsVisitor()
    source_code_tree.visit(visitor)
    all_type_slots = {
        k: v if v not in INCOMPLETE_TYPE_ANNOTATIONS else None
        for k, v in visitor.all_type_slots.items()
    }
    return all_type_slots


def create_evaluation_csv_file():
    headers = [
        "file",
        "# groundtruth annotations",
        "# annotations after Pyright",
        "# annotations after ML",
        "# available type slots",
        "# total type slots",
        "# extra Pyright annotations",
        "# extra ML annotations",
        f"% extra annotations",
        "# ML evaluated type slots",
        "Average time per slot (s)",
        "ML search time (s)",
        "Total time (s)",
    ]
    with open(
        "logs-evaluation/evaluation statistics.csv",
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_to_evaluation_csv_file(statistics):
    with open(
        "logs-evaluation/evaluation statistics.csv",
        "a",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(statistics)


def calculate_extra_annotations(
    original_type_annotations,
    updated_type_annotations,
):
    extra_annotations = {
        k: v
        for k, v in updated_type_annotations.items()
        if v is not None and (k, None) in original_type_annotations.items()
    }
    return extra_annotations


def gather_annotated_slots(type_slots):
    if type_slots is None:
        return {}
    annotations = {k: v for k, v in type_slots.items() if v is not None}
    return annotations


def gather_available_slots(type_slots):
    annotations = {k: v for k, v in type_slots.items() if v is None}
    return annotations


def calculate_evaluation_statistics(
    file,
    type_slots_groundtruth,
    type_slots_after_pyright,
    type_slots_after_ml_search,
    number_of_ml_evaluated_type_slots,
    ml_search_time,
    total_time,
):
    if type_slots_after_pyright is not None and type_slots_after_ml_search is not None:
        extra_pyright_annotations = calculate_extra_annotations(
            type_slots_groundtruth, type_slots_after_pyright
        )
        extra_ml_annotations = calculate_extra_annotations(
            type_slots_after_pyright, type_slots_after_ml_search
        )
    elif type_slots_after_pyright is not None:
        extra_pyright_annotations = calculate_extra_annotations(
            type_slots_groundtruth, type_slots_after_pyright
        )
        extra_ml_annotations = {}
    elif type_slots_after_ml_search is not None:
        extra_pyright_annotations = {}
        extra_ml_annotations = calculate_extra_annotations(
            type_slots_groundtruth, type_slots_after_ml_search
        )
    else:
        extra_pyright_annotations = {}
        extra_ml_annotations = {}

    annotations_groundtruth = gather_annotated_slots(type_slots_groundtruth)
    annotations_after_pyright = gather_annotated_slots(type_slots_after_pyright)
    annotations_after_ml_search = gather_annotated_slots(type_slots_after_ml_search)
    available_slots = gather_available_slots(type_slots_groundtruth)

    try:
        if len(extra_ml_annotations) > 0:
            new_annotations_percentage = (
                (len(annotations_after_ml_search) - len(annotations_groundtruth))
                / len(available_slots)
                * 100
            )
        elif len(extra_pyright_annotations) > 0:
            new_annotations_percentage = (
                (len(annotations_after_pyright) - len(annotations_groundtruth))
                / len(available_slots)
                * 100
            )
        else:
            new_annotations_percentage = 0.0
    except ZeroDivisionError:
        new_annotations_percentage = "-"

    try:
        avg_time_per_slot = round(ml_search_time / number_of_ml_evaluated_type_slots, 2)
    except ZeroDivisionError:
        avg_time_per_slot = "-"

    evaluation_statistics = {
        "file": file,
        "annotations_groundtruth_count": len(annotations_groundtruth),
        "annotations_after_pyright_count": len(annotations_after_pyright)
        if len(annotations_after_pyright) > 0
        else "-",
        "annotations_after_ml_search_count": len(annotations_after_ml_search)
        if len(annotations_after_ml_search) > 0
        else "-",
        "available_type_slots_count": len(available_slots),
        "total_type_slots_count": len(type_slots_groundtruth),
        "extra_pyright_annotations_count": len(extra_pyright_annotations)
        if len(available_slots) > 0
        else "-",
        "extra_ml_annotations_count": len(extra_ml_annotations)
        if len(available_slots) > 0
        else "-",
        "extra_annotations_percentage": new_annotations_percentage,
        "ml_evaluated_type_slots_count": number_of_ml_evaluated_type_slots,
        "avg_time_per_slot": avg_time_per_slot,
        "ml_search_time": round(ml_search_time, 2),
        "total_time": round(total_time, 2),
    }
    return evaluation_statistics
