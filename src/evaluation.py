import os
import csv
from typing import Tuple
import libcst as cst

from annotations import TypeSlotsVisitor
from constants import UBIQUITOUS_ANNOTATIONS, COMMON_ANNOTATIONS
from type_check import PythonType, normalize_type, parse_type_str


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


def create_evaluation_csv_file(postfix) -> None:
    csv_file = f"logs-evaluation/evaluation-statistics-{postfix}.csv"
    if os.path.exists(csv_file):
        return

    headers = [
        "file",
        "# groundtruth annotations",
        "# annotations after Pyright",
        "# annotations after ML search",
        "# fillable type slots",
        "# unfilled type slots",
        "# total type slots",
        "# extra Pyright annotations",
        "# extra ML search annotations",
        f"% extra Pyright annotations",
        f"% extra ML search annotations",
        f"% extra annotations (all)",
        "# ML search evaluated type slots",
        f"% extra ML search annotations after Pyright",
        "Pyright time (s)",
        "Average time per ML search slot (s)",
        "ML search time (s)",
        "Total time (s)",
        "Peak memory usage Pyright (mb)",
        "Peak memory usage ML search (mb)",
        "# ubiquitous annotations parameters (groundtruth)",
        "# ubiquitous annotations returns (groundtruth)",
        "# common annotations parameters (groundtruth)",
        "# common annotations returns (groundtruth)",
        "# rare annotations parameters (groundtruth)",
        "# rare annotations returns (groundtruth)",
        "# ubiquitous annotations parameters (extra Pyright)",
        "# ubiquitous annotations returns (extra Pyright)",
        "# common annotations parameters (extra Pyright)",
        "# common annotations returns (extra Pyright)",
        "# rare annotations parameters (extra Pyright)",
        "# rare annotations returns (extra Pyright)",
        "# ubiquitous annotations parameters (extra ML)",
        "# ubiquitous annotations returns (extra ML)",
        "# common annotations parameters (extra ML)",
        "# common annotations returns (extra ML)",
        "# rare annotations parameters (extra ML)",
        "# rare annotations returns (extra ML)",
        "# ubiquitous annotations parameters (all)",
        "# ubiquitous annotations returns (all)",
        "# common annotations parameters (all)",
        "# common annotations returns (all)",
        "# rare annotations parameters (all)",
        "# rare annotations returns (all)",
    ]
    with open(
        csv_file,
        "w",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def append_to_evaluation_csv_file(statistics, postfix) -> None:
    with open(
        f"logs-evaluation/evaluation-statistics-{postfix}.csv",
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


def gather_fillable_slots(type_slots):
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


def split_parameters_and_return_types(type_slots):
    parameters_dict = {}
    return_dict = {}
    for slot, annotation in type_slots.items():
        if slot[-1] != "return":
            parameters_dict[slot] = annotation
        else:
            return_dict[slot] = annotation
    return parameters_dict, return_dict


def gather_ubiquitous_common_rare(annotations):
    annotations_filtered = remove_known_dunder_methods(annotations)
    annotations_normalized = normalize_annotations(annotations_filtered)
    ubiquitous, common, rare = split_into_ubiquitous_common_rare(annotations_normalized)
    ubiquitous_params, ubiquitous_returns = split_parameters_and_return_types(
        ubiquitous
    )
    common_params, common_returns = split_parameters_and_return_types(common)
    rare_params, rare_returns = split_parameters_and_return_types(rare)
    return (
        ubiquitous_params,
        ubiquitous_returns,
        common_params,
        common_returns,
        rare_params,
        rare_returns,
    )


def calculate_evaluation_statistics(
    file,
    type_slots_groundtruth,
    type_slots_after_pyright,
    type_slots_after_ml_search,
    number_of_ml_evaluated_type_slots,
    has_performed_pyright_step,
    has_performed_ml_search,
    pyright_time,
    ml_search_time,
    total_time,
    peak_memory_usage_pyright,
    peak_memory_usage_ml_search,
):
    annotations_groundtruth = gather_annotated_slots(type_slots_groundtruth)
    annotations_after_pyright = gather_annotated_slots(type_slots_after_pyright)
    annotations_after_ml_search = gather_annotated_slots(type_slots_after_ml_search)
    fillable_slots = gather_fillable_slots(type_slots_groundtruth)
    if has_performed_ml_search:
        unfilled_slots = gather_fillable_slots(type_slots_after_ml_search)
    elif has_performed_pyright_step:
        unfilled_slots = gather_fillable_slots(type_slots_after_pyright)
    else:
        unfilled_slots = fillable_slots

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

    # Pyright's percentage of filled-in slots of all fillable slots
    try:
        if added_extra_pyright_annotations:
            extra_pyright_annotations_percentage = (
                len(extra_pyright_annotations) / len(fillable_slots) * 100
            )
        else:
            extra_pyright_annotations_percentage = 0.0
        extra_pyright_annotations_percentage = round(
            extra_pyright_annotations_percentage, 2
        )
    except ZeroDivisionError:
        extra_pyright_annotations_percentage = "-"

    # ML's percentage of filled-in slots of all fillable slots
    try:
        if added_extra_ml_annotations:
            extra_ml_annotations_percentage = (
                len(extra_ml_annotations) / len(fillable_slots) * 100
            )
        else:
            extra_ml_annotations_percentage = 0.0
        extra_ml_annotations_percentage = round(extra_ml_annotations_percentage, 2)
    except ZeroDivisionError:
        extra_ml_annotations_percentage = "-"

    # Percentage of all fillable slots filled in
    try:
        if added_extra_ml_annotations:
            new_annotations_percentage = (
                (len(annotations_after_ml_search) - len(annotations_groundtruth))
                / len(fillable_slots)
                * 100
            )
        elif added_extra_pyright_annotations:
            new_annotations_percentage = (
                (len(annotations_after_pyright) - len(annotations_groundtruth))
                / len(fillable_slots)
                * 100
            )
        else:
            new_annotations_percentage = 0.0
        new_annotations_percentage = round(new_annotations_percentage, 2)
    except ZeroDivisionError:
        new_annotations_percentage = "-"

    # ML's percentage of filled-in slots of all still fillable slots after Pyright
    try:
        if added_extra_ml_annotations:
            extra_ml_annotations_after_pyright_percentage = (
                len(extra_ml_annotations) / number_of_ml_evaluated_type_slots * 100
            )
        else:
            extra_ml_annotations_after_pyright_percentage = 0.0
        extra_ml_annotations_after_pyright_percentage = round(
            extra_ml_annotations_after_pyright_percentage, 2
        )
    except ZeroDivisionError:
        extra_ml_annotations_after_pyright_percentage = "-"

    try:
        avg_time_per_ml_search_slot = round(
            ml_search_time / number_of_ml_evaluated_type_slots, 2
        )
    except ZeroDivisionError:
        avg_time_per_ml_search_slot = "-"

    (
        groundtruth_annotations_ubiquitous_params,
        groundtruth_annotations_ubiquitous_returns,
        groundtruth_annotations_common_params,
        groundtruth_annotations_common_returns,
        groundtruth_annotations_rare_params,
        groundtruth_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(annotations_groundtruth)
    (
        extra_pyright_annotations_ubiquitous_params,
        extra_pyright_annotations_ubiquitous_returns,
        extra_pyright_annotations_common_params,
        extra_pyright_annotations_common_returns,
        extra_pyright_annotations_rare_params,
        extra_pyright_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(extra_pyright_annotations)
    (
        extra_ml_annotations_ubiquitous_params,
        extra_ml_annotations_ubiquitous_returns,
        extra_ml_annotations_common_params,
        extra_ml_annotations_common_returns,
        extra_ml_annotations_rare_params,
        extra_ml_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(extra_ml_annotations)

    annotations_all = (
        annotations_after_ml_search
        or annotations_after_pyright
        or annotations_groundtruth
        or {}
    )
    (
        all_annotations_ubiquitous_params,
        all_annotations_ubiquitous_returns,
        all_annotations_common_params,
        all_annotations_common_returns,
        all_annotations_rare_params,
        all_annotations_rare_returns,
    ) = gather_ubiquitous_common_rare(annotations_all)

    evaluation_statistics = {
        "file": file,
        "annotations_groundtruth_count": len(annotations_groundtruth),
        "annotations_after_pyright_count": (
            len(annotations_after_pyright) if has_performed_pyright_step else "-"
        ),
        "annotations_after_ml_search_count": (
            len(annotations_after_ml_search) if has_performed_ml_search else "-"
        ),
        "fillable_type_slots_count": len(fillable_slots),
        "unfilled_type_slots_count": len(unfilled_slots),
        "total_type_slots_count": len(type_slots_groundtruth),
        "extra_pyright_annotations_count": (
            len(extra_pyright_annotations) if has_performed_pyright_step else "-"
        ),
        "extra_ml_annotations_count": (
            len(extra_ml_annotations) if has_performed_ml_search else "-"
        ),
        "extra_pyright_annotations_percentage": extra_pyright_annotations_percentage,
        "extra_ml_annotations_percentage": (
            extra_ml_annotations_percentage if has_performed_ml_search else "-"
        ),
        "extra_annotations_percentage": new_annotations_percentage,
        "ml_evaluated_type_slots_count": number_of_ml_evaluated_type_slots,
        "extra_ml_annotations_after_pyright_percentage": (
            extra_ml_annotations_after_pyright_percentage
            if has_performed_ml_search
            else "-"
        ),
        "pyright_time": round(pyright_time, 2),
        "avg_time_per_ml_search_slot": avg_time_per_ml_search_slot,
        "ml_search_time": round(ml_search_time, 2),
        "total_time": round(total_time, 2),
        "peak_memory_usage_pyright_mb": round(peak_memory_usage_pyright / 1024**2, 2),
        "peak_memory_usage_ml_search_mb": round(
            peak_memory_usage_ml_search / 1024**2, 2
        ),
        "ubiquitous_annotations_groundtruth_params_count": len(
            groundtruth_annotations_ubiquitous_params
        ),
        "ubiquitous_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_ubiquitous_returns
        ),
        "common_annotations_groundtruth_params_count": len(
            groundtruth_annotations_common_params
        ),
        "common_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_common_returns
        ),
        "rare_annotations_groundtruth_params_count": len(
            groundtruth_annotations_rare_params
        ),
        "rare_annotations_groundtruth_returns_count": len(
            groundtruth_annotations_rare_returns
        ),
        "ubiquitous_annotations_pyright_params_count": len(
            extra_pyright_annotations_ubiquitous_params
        ),
        "ubiquitous_annotations_pyright_returns_count": len(
            extra_pyright_annotations_ubiquitous_returns
        ),
        "common_annotations_pyright_params_count": len(
            extra_pyright_annotations_common_params
        ),
        "common_annotations_pyright_returns_count": len(
            extra_pyright_annotations_common_returns
        ),
        "rare_annotations_pyright_params_count": len(
            extra_pyright_annotations_rare_params
        ),
        "rare_annotations_pyright_returns_count": len(
            extra_pyright_annotations_rare_returns
        ),
        "ubiquitous_annotations_ml_params_count": len(
            extra_ml_annotations_ubiquitous_params,
        ),
        "ubiquitous_annotations_ml_returns_count": len(
            extra_ml_annotations_ubiquitous_returns,
        ),
        "common_annotations_ml_params_count": len(extra_ml_annotations_common_params),
        "common_annotations_ml_returns_count": len(extra_ml_annotations_common_returns),
        "rare_annotations_ml_params_count": len(extra_ml_annotations_rare_params),
        "rare_annotations_ml_returns_count": len(extra_ml_annotations_rare_returns),
        "ubiquitous_annotations_all_params_count": len(
            all_annotations_ubiquitous_params
        ),
        "ubiquitous_annotations_all_returns_count": len(
            all_annotations_ubiquitous_returns
        ),
        "common_annotations_all_params_count": len(all_annotations_common_params),
        "common_annotations_all_returns_count": len(all_annotations_common_returns),
        "rare_annotations_all_params_count": len(all_annotations_rare_params),
        "rare_annotations_all_returns_count": len(all_annotations_rare_returns),
    }
    return evaluation_statistics
