import os
import libcst as cst
from evaluation import gather_all_type_slots, create_evaluation_csv_file


def test_gather_all_type_slots():
    source_code_tree = cst.parse_module("def function(a, b: int, c: List[str]): pass")
    all_type_slots = gather_all_type_slots(source_code_tree)
    assert all_type_slots == {
        ("function", "a"): None,
        ("function", "b"): "int",
        ("function", "c"): "List[str]",
        ("function", "return"): None,
    }


def test_gather_all_type_slots_with_incomplete_type_annotations():
    source_code_tree = cst.parse_module(
        "def function(a: Incomplete, b: int, c: List[str]) -> float: pass"
    )
    all_type_slots = gather_all_type_slots(source_code_tree)
    assert all_type_slots == {
        ("function", "a"): None,
        ("function", "b"): "int",
        ("function", "c"): "List[str]",
        ("function", "return"): "float",
    }
