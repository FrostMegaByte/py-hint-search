import os
import csv
from typing import Tuple
import libcst as cst

from annotations import TypeSlotsVisitor
from constants import UBIQUITOUS_ANNOTATIONS, COMMON_ANNOTATIONS
from type_check import AccuracyMetric, PythonType, normalize_type, parse_type_str


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


def create_evaluation_csv_file(top_n: int) -> None:
    csv_file = f"logs-evaluation/evaluation-statistics-top{top_n}.csv"
    if os.path.exists(csv_file):
        return

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
        "Peak memory usage Pyright (mb)",
        "Peak memory usage ML (mb)",
        "# ubiquitous annotations (extra Pyright)",
        "# common annotations (extra Pyright)",
        "# rare annotations (extra Pyright)",
        "# ubiquitous annotations (extra ML)",
        "# common annotations (extra ML)",
        "# rare annotations (extra ML)",
        "# ubiquitous annotations (all)",
        "# common annotations (all)",
        "# rare annotations (all)",
    ]
    with open(
        csv_file,
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_to_evaluation_csv_file(statistics, top_n: int) -> None:
    with open(
        f"logs-evaluation/evaluation-statistics-top{top_n}.csv",
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
    annotations = {k: v for k, v in type_slots.items() if v is not None}
    return annotations


def gather_available_slots(type_slots):
    annotations = {k: v for k, v in type_slots.items() if v is None}
    return annotations


def remove_known_dunder_methods(type_slots):
    def contains_dunder_string(slot: Tuple[str, ...]) -> bool:
        return any(s.startswith("__") and s.endswith("__") for s in slot)

    annotations = {
        k: v
        for k, v in type_slots.items()
        if not (contains_dunder_string(k) and "return" in k)
    }
    return annotations


def normalize_annotations(annotations):
    normalized_annotations = {
        k: normalize_type(parse_type_str(v)) for k, v in annotations.items()
    }
    return normalized_annotations


def split_into_ubiquitous_common_rare(type_slots):
    def is_ubiquitous_type(t: PythonType) -> bool:
        return t.head_name() in UBIQUITOUS_ANNOTATIONS and all(
            map(is_ubiquitous_type, t.args)
        )

    def is_common_type(t: PythonType) -> bool:
        return t.head_name() in COMMON_ANNOTATIONS and all(map(is_common_type, t.args))

    ubiquitous, common, rare = {}, {}, {}
    for k, v in type_slots.items():
        if is_ubiquitous_type(v):
            ubiquitous[k] = v
        elif is_common_type(v):
            common[k] = v
        else:
            rare[k] = v
    return ubiquitous, common, rare


def gather_ubiquitous_common_rare(annotations):
    annotations_filtered = remove_known_dunder_methods(annotations)
    annotations_normalized = normalize_annotations(annotations_filtered)
    ubiquitous, common, rare = split_into_ubiquitous_common_rare(annotations_normalized)
    return ubiquitous, common, rare


def calculate_evaluation_statistics(
    file,
    type_slots_groundtruth,
    type_slots_after_pyright,
    type_slots_after_ml_search,
    number_of_ml_evaluated_type_slots,
    ml_search_time,
    total_time,
    peak_memory_usage_pyright,
    peak_memory_usage_ml,
):
    if len(type_slots_after_pyright) > 0 and len(type_slots_after_ml_search) > 0:
        extra_pyright_annotations = calculate_extra_annotations(
            type_slots_groundtruth, type_slots_after_pyright
        )
        extra_ml_annotations = calculate_extra_annotations(
            type_slots_after_pyright, type_slots_after_ml_search
        )
    elif len(type_slots_after_pyright) > 0:
        extra_pyright_annotations = calculate_extra_annotations(
            type_slots_groundtruth, type_slots_after_pyright
        )
        extra_ml_annotations = {}
    elif len(type_slots_after_ml_search) > 0:
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
        new_annotations_percentage = round(new_annotations_percentage, 2)
    except ZeroDivisionError:
        new_annotations_percentage = "-"

    try:
        avg_time_per_slot = round(ml_search_time / number_of_ml_evaluated_type_slots, 2)
    except ZeroDivisionError:
        avg_time_per_slot = "-"

    (
        extra_pyright_annotations_ubiquitous,
        extra_pyright_annotations_common,
        extra_pyright_annotations_rare,
    ) = gather_ubiquitous_common_rare(extra_pyright_annotations)
    (
        extra_ml_annotations_ubiquitous,
        extra_ml_annotations_common,
        extra_ml_annotations_rare,
    ) = gather_ubiquitous_common_rare(extra_ml_annotations)

    annotations_all = (
        annotations_after_ml_search
        or annotations_after_pyright
        or annotations_groundtruth
        or {}
    )
    (
        all_annotations_ubiquitous,
        all_annotations_common,
        all_annotations_rare,
    ) = gather_ubiquitous_common_rare(annotations_all)

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
        "peak_memory_usage_pyright_mb": round(
            peak_memory_usage_pyright / (1024 * 1024), 2
        ),
        "peak_memory_usage_ml_mb": round(peak_memory_usage_ml / (1024 * 1024), 2),
        "ubiquitous_annotations_pyright_count": len(
            extra_pyright_annotations_ubiquitous
        ),
        "common_annotations_pyright_count": len(extra_pyright_annotations_common),
        "rare_annotations_pyright_count": len(extra_pyright_annotations_rare),
        "ubiquitous_annotations_ml_count": len(
            extra_ml_annotations_ubiquitous,
        ),
        "common_annotations_ml_count": len(extra_ml_annotations_common),
        "rare_annotations_ml_count": len(extra_ml_annotations_rare),
        "ubiquitous_annotations_all_count": len(all_annotations_ubiquitous),
        "common_annotations_all_count": len(all_annotations_common),
        "rare_annotations_all_count": len(all_annotations_rare),
    }
    return evaluation_statistics
