from pathlib import Path

import pytest

from pymologie import Etymology, Node

FIXTURE = Path(__file__).parent / "fixtures" / "mini_etymologie.csv"


@pytest.fixture
def etymology() -> Etymology:
    return Etymology(data_path=FIXTURE)


def test_tree_chains_through_multiple_hops(etymology: Etymology) -> None:
    node = etymology.tree("Haus")
    assert node.word == "Haus"
    assert node.language is None

    mhd_child = next(c for c in node.children if c.language == "Mittelhochdeutsch")
    assert mhd_child.word == "hus"
    assert [c.word for c in mhd_child.children] == ["urhus"]
    assert mhd_child.children[0].children == []

    ahd_child = next(c for c in node.children if c.language == "Althochdeutsch")
    assert ahd_child.children == []


def test_tree_stops_on_leaf_word(etymology: Etymology) -> None:
    node = etymology.tree("Nichtvorhanden")
    assert node.word == "Nichtvorhanden"
    assert node.children == []


def test_tree_handles_direct_cycle(etymology: Etymology) -> None:
    node = etymology.tree("A")
    assert node.word == "A"
    b_child = node.children[0]
    assert b_child.word == "B"
    # B's origin is A again, but A is already in this branch, so it stops.
    a_grandchild = b_child.children[0]
    assert a_grandchild.word == "A"
    assert a_grandchild.children == []


def test_tree_max_depth_caps_recursion(etymology: Etymology) -> None:
    node = etymology.tree("A", max_depth=1)
    assert node.children[0].word == "B"
    assert node.children[0].children == []


def test_to_dict_roundtrip_structure(etymology: Etymology) -> None:
    node = etymology.tree("Haus")
    as_dict = node.to_dict()
    assert as_dict["word"] == "Haus"
    assert as_dict["language"] is None
    assert {c["word"] for c in as_dict["children"]} == {"hus", "hus_alt"}


def test_render_produces_ascii_tree(etymology: Etymology) -> None:
    node = etymology.tree("Haus")
    text = str(node)
    assert text.splitlines()[0] == "Haus"
    assert "├── hus (Mittelhochdeutsch, 1050-1500)" in text
    assert "└── hus_alt (Althochdeutsch, 750-1050)" in text
    assert "urhus (Urgermanisch, vor 500)" in text


def test_node_is_dataclass_instance() -> None:
    node = Node(word="x", language=None, period=None)
    assert node.children == []
