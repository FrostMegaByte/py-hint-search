from src.treebuilder import build_search_tree, Node


def test_node_class():
    root_node = Node("Top level node", 1)

    assert root_node.typeAnnotation == "Top level node"
    assert root_node.probability == 1
    assert root_node.children == []


def test_build_search_tree():
    TOP_K = 2
    arr = [
        [
            ["A", 0.1],
            ["B", 0.2],
        ],
        [
            ["C", 0.3],
            ["D", 0.4],
        ],
    ]

    root = Node("Top level node", 1)
    tree = build_search_tree(root, arr)

    assert tree.typeAnnotation == "Top level node"
    assert tree.probability == 1
    assert len(tree.children) == TOP_K
