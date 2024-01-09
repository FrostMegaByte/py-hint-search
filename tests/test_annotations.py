import libcst as cst
from src.annotations import node_to_code


def test_node_to_code_with_empty_module():
    node = cst.Module([])
    result = node_to_code(node)
    assert result == ""


def test_node_to_code_with_union():
    node = cst.Subscript(
        value=cst.Name("Union"),
        slice=[
            cst.SubscriptElement(slice=cst.Index(value=cst.Name("str"))),
            cst.SubscriptElement(slice=cst.Index(value=cst.Name("float"))),
        ],
    )
    result = node_to_code(node)
    assert result == "Union[str, float]"


def test_node_to_code_with_function_def():
    node = cst.FunctionDef(
        name=cst.Name("test"),
        params=cst.Parameters([]),
        body=cst.SimpleStatementSuite([cst.Pass()]),
    )
    result = node_to_code(node)
    assert result == "def test(): pass"
