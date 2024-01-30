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
        f"% extra Pyright annotations",
        f"% extra ML annotations",
        f"% extra annotations (all)",
        "# available type slots after Pyright",
        f"% extra ML annotations after Pyright",
        "# ML evaluated type slots",
        "Average time per slot (s)",
        "ML search time (s)",
        "Total time (s)",
        "Peak memory usage Pyright (mb)",
        "Peak memory usage ML (mb)",
        "# ubiquitous annotations arguments (groundtruth)",
        "# ubiquitous annotations returns (groundtruth)",
        "# common annotations arguments (groundtruth)",
        "# common annotations returns (groundtruth)",
        "# rare annotations arguments (groundtruth)",
        "# rare annotations returns (groundtruth)",
        "# ubiquitous annotations arguments (extra Pyright)",
        "# ubiquitous annotations returns (extra Pyright)",
        "# common annotations arguments (extra Pyright)",
        "# common annotations returns (extra Pyright)",
        "# rare annotations arguments (extra Pyright)",
        "# rare annotations returns (extra Pyright)",
        "# ubiquitous annotations arguments (extra ML)",
        "# ubiquitous annotations returns (extra ML)",
        "# common annotations arguments (extra ML)",
        "# common annotations returns (extra ML)",
        "# rare annotations arguments (extra ML)",
        "# rare annotations returns (extra ML)",
        "# ubiquitous annotations arguments (all)",
        "# ubiquitous annotations returns (all)",
        "# common annotations arguments (all)",
        "# common annotations returns (all)",
        "# rare annotations arguments (all)",
        "# rare annotations returns (all)",
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
    initial_type_slots,
    updated_type_slots,
):
    extra_annotations = {
        k: v
        for k, v in updated_type_slots.items()
        if (k, None) in initial_type_slots.items() and v is not None
    }
    return extra_annotations


def has_extra_annotations(
    initial_type_slots,
    updated_type_slots,
):
    none_type_slots = {
        key: updated_type_slots[key]
        for key in updated_type_slots
        if initial_type_slots.get(key) is None
    }
    all_values_none = any(value is not None for value in none_type_slots.values())
    return all_values_none


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


def split_arguments_and_return_types(type_slots):
    arguments_dict = {}
    return_dict = {}
    for slot, annotation in type_slots.items():
        if slot[-1] != "return":
            arguments_dict[slot] = annotation
        else:
            return_dict[slot] = annotation
    return arguments_dict, return_dict


def gather_ubiquitous_common_rare(annotations):
    annotations_filtered = remove_known_dunder_methods(annotations)
    annotations_normalized = normalize_annotations(annotations_filtered)
    ubiquitous, common, rare = split_into_ubiquitous_common_rare(annotations_normalized)
    ubiquitous_args, ubiquitous_returns = split_arguments_and_return_types(ubiquitous)
    common_args, common_returns = split_arguments_and_return_types(common)
    rare_args, rare_returns = split_arguments_and_return_types(rare)
    return (
        ubiquitous_args,
        ubiquitous_returns,
        common_args,
        common_returns,
        rare_args,
        rare_returns,
    )


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
    annotations_groundtruth = gather_annotated_slots(type_slots_groundtruth)
    annotations_after_pyright = gather_annotated_slots(type_slots_after_pyright)
    annotations_after_ml_search = gather_annotated_slots(type_slots_after_ml_search)
    available_slots = gather_available_slots(type_slots_groundtruth)

    extra_pyright_annotations = {
        key_pyright: value_pyright
        for key_pyright, value_pyright in annotations_after_pyright.items()
        if key_pyright not in annotations_groundtruth
    }
    extra_ml_annotations = {
        key_ml: value_ml
        for key_ml, value_ml in annotations_after_ml_search.items()
        if key_ml not in annotations_after_pyright
    }

    added_extra_pyright_annotations = len(extra_pyright_annotations) > 0
    added_extra_ml_annotations = len(extra_ml_annotations) > 0

    # Pyright's percentage of filled-in slots of all available slots
    try:
        if added_extra_pyright_annotations:
            extra_pyright_annotations_percentage = (
                len(extra_pyright_annotations) / len(available_slots) * 100
            )
        else:
            extra_pyright_annotations_percentage = 0.0
        extra_pyright_annotations_percentage = round(
            extra_pyright_annotations_percentage, 2
        )
    except ZeroDivisionError:
        extra_pyright_annotations_percentage = "-"

    # ML's percentage of filled-in slots of all available slots
    try:
        if added_extra_ml_annotations:
            extra_ml_annotations_percentage = (
                len(extra_ml_annotations) / len(available_slots) * 100
            )
        else:
            extra_ml_annotations_percentage = 0.0
        extra_ml_annotations_percentage = round(extra_ml_annotations_percentage, 2)
    except ZeroDivisionError:
        extra_ml_annotations_percentage = "-"

    # Percentage of all available slots filled in
    try:
        if added_extra_ml_annotations:
            new_annotations_percentage = (
                (len(annotations_after_ml_search) - len(annotations_groundtruth))
                / len(available_slots)
                * 100
            )
        elif added_extra_pyright_annotations:
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

    # ML's percentage of filled-in slots of all still available slots after Pyright
    try:
        available_slots_after_pyright_count = len(available_slots) - len(
            extra_pyright_annotations
        )
        if added_extra_ml_annotations:
            extra_ml_annotations_after_pyright_percentage = (
                len(extra_ml_annotations) / available_slots_after_pyright_count * 100
            )
        else:
            extra_ml_annotations_after_pyright_percentage = 0.0
        extra_ml_annotations_after_pyright_percentage = round(
            extra_ml_annotations_after_pyright_percentage, 2
        )
    except ZeroDivisionError:
        extra_ml_annotations_after_pyright_percentage = "-"

    try:
        avg_time_per_slot = round(ml_search_time / number_of_ml_evaluated_type_slots, 2)
    except ZeroDivisionError:
        avg_time_per_slot = "-"

    (
        groundtruth_annotations_ubiquitous_args,
        groundtruth_annotations_ubiquitous_returns,
        groundtruth_annotations_common_args,
        groundtruth_annotations_common_returns,
        groundtruth_annotations_rare_args,
        groundtruth_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(annotations_groundtruth)
    (
        extra_pyright_annotations_ubiquitous_args,
        extra_pyright_annotations_ubiquitous_returns,
        extra_pyright_annotations_common_args,
        extra_pyright_annotations_common_returns,
        extra_pyright_annotations_rare_args,
        extra_pyright_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(extra_pyright_annotations)
    (
        extra_ml_annotations_ubiquitous_args,
        extra_ml_annotations_ubiquitous_returns,
        extra_ml_annotations_common_args,
        extra_ml_annotations_common_returns,
        extra_ml_annotations_rare_args,
        extra_ml_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(extra_ml_annotations)

    annotations_all = (
        annotations_after_ml_search
        or annotations_after_pyright
        or annotations_groundtruth
        or {}
    )
    (
        all_annotations_ubiquitous_args,
        all_annotations_ubiquitous_returns,
        all_annotations_common_args,
        all_annotations_common_returns,
        all_annotations_rare_args,
        all_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(annotations_all)

    evaluation_statistics = {
        "file": file,
        "annotations_groundtruth_count": len(annotations_groundtruth),
        "annotations_after_pyright_count": len(annotations_after_pyright)
        if added_extra_pyright_annotations
        else "-",
        "annotations_after_ml_search_count": len(annotations_after_ml_search)
        if number_of_ml_evaluated_type_slots > 0
        else "-",
        "available_type_slots_count": len(available_slots),
        "total_type_slots_count": len(type_slots_groundtruth),
        "extra_pyright_annotations_count": len(extra_pyright_annotations)
        if added_extra_pyright_annotations
        else "-",
        "extra_ml_annotations_count": len(extra_ml_annotations)
        if number_of_ml_evaluated_type_slots > 0
        else "-",
        "extra_pyright_annotations_percentage": extra_pyright_annotations_percentage,
        "extra_ml_annotations_percentage": extra_ml_annotations_percentage,
        "extra_annotations_percentage": new_annotations_percentage,
        "available_type_slots_after_pyright_count": available_slots_after_pyright_count,
        "extra_ml_annotations_after_pyright_percentage": extra_ml_annotations_after_pyright_percentage,
        "ml_evaluated_type_slots_count": number_of_ml_evaluated_type_slots,
        "avg_time_per_slot": avg_time_per_slot,
        "ml_search_time": round(ml_search_time, 2),
        "total_time": round(total_time, 2),
        "peak_memory_usage_pyright_mb": round(
            peak_memory_usage_pyright / (1024 * 1024), 2
        ),
        "peak_memory_usage_ml_mb": round(peak_memory_usage_ml / (1024 * 1024), 2),
        "ubiquitous_annotations_groundtruth_args_count": len(
            groundtruth_annotations_ubiquitous_args
        ),
        "ubiquitous_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_ubiquitous_returns
        ),
        "common_annotations_groundtruth_args_count": len(
            groundtruth_annotations_common_args
        ),
        "common_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_common_returns
        ),
        "rare_annotations_groundtruth_args_count": len(
            groundtruth_annotations_rare_args
        ),
        "rare_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_rare_returns
        ),
        "ubiquitous_annotations_pyright_args_count": len(
            extra_pyright_annotations_ubiquitous_args
        ),
        "ubiquitous_annotations_pyright_returns_count": len(
            extra_pyright_annotations_ubiquitous_returns
        ),
        "common_annotations_pyright_args_count": len(
            extra_pyright_annotations_common_args
        ),
        "common_annotations_pyright_returns_count": len(
            extra_pyright_annotations_common_returns
        ),
        "rare_annotations_pyright_args_count": len(extra_pyright_annotations_rare_args),
        "rare_annotations_pyright_returns_count": len(
            extra_pyright_annotations_rare_returns
        ),
        "ubiquitous_annotations_ml_args_count": len(
            extra_ml_annotations_ubiquitous_args,
        ),
        "ubiquitous_annotations_ml_returns_count": len(
            extra_ml_annotations_ubiquitous_returns,
        ),
        "common_annotations_ml_args_count": len(extra_ml_annotations_common_args),
        "common_annotations_ml_returns_count": len(extra_ml_annotations_common_returns),
        "rare_annotations_ml_args_count": len(extra_ml_annotations_rare_args),
        "rare_annotations_ml_returns_count": len(extra_ml_annotations_rare_returns),
        "ubiquitous_annotations_all_args_count": len(all_annotations_ubiquitous_args),
        "ubiquitous_annotations_all_returns_count": len(
            all_annotations_ubiquitous_returns
        ),
        "common_annotations_all_args_count": len(all_annotations_common_args),
        "common_annotations_all_returns_count": len(all_annotations_common_returns),
        "rare_annotations_all_args_count": len(all_annotations_rare_args),
        "rare_annotations_all_returns_count": len(all_annotations_rare_returns),
    }
    return evaluation_statistics
