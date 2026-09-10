"""Etymology tree data structures and construction."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

Origin = namedtuple("Origin", ["word", "language", "period"])


@dataclass
class Node:
    """A single word in an etymology tree.

    The root node's ``language``/``period`` are ``None`` since it represents
    the word that was looked up, not one of its origins.
    """

    word: str
    language: Optional[str]
    period: Optional[str]
    children: List["Node"] = field(default_factory=list)

    def render(self, prefix: str = "", is_root: bool = True) -> str:
        label = self.word if is_root else f"{self.word} ({self.language}, {self.period})"
        lines = [label]
        for i, child in enumerate(self.children):
            last = i == len(self.children) - 1
            connector = "└── " if last else "├── "
            child_prefix = prefix + ("    " if last else "│   ")
            child_lines = child.render(child_prefix, is_root=False).splitlines()
            lines.append(prefix + connector + child_lines[0])
            lines.extend(child_prefix + line for line in child_lines[1:])
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()

    __repr__ = __str__

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "language": self.language,
            "period": self.period,
            "children": [child.to_dict() for child in self.children],
        }


def map_tree(node: Node, fn: Callable[[str], str]) -> Node:
    """Return a copy of ``node`` with ``fn`` applied to every ``word`` in it."""
    return Node(
        word=fn(node.word),
        language=node.language,
        period=node.period,
        children=[map_tree(child, fn) for child in node.children],
    )


def build_tree(word: str, data: Dict[str, List[Origin]], max_depth: int = 10) -> Node:
    """Recursively expand ``word``'s origins into a tree.

    Each branch tracks its own set of already-visited words so a cycle in
    the underlying data (word A derives from B, which derives from A) stops
    that branch instead of recursing forever, while the same word is still
    free to appear again in an unrelated branch. ``max_depth`` is a
    belt-and-braces cap on top of that.
    """
    children = _expand(word, data, frozenset({word}), max_depth)
    return Node(word=word, language=None, period=None, children=children)


def _expand(
    word: str, data: Dict[str, List[Origin]], seen: frozenset, depth_left: int
) -> List[Node]:
    if depth_left <= 0 or word not in data:
        return []
    children = []
    for origin in data[word]:
        if origin.word in seen:
            grandchildren: List[Node] = []
        else:
            grandchildren = _expand(origin.word, data, seen | {origin.word}, depth_left - 1)
        children.append(
            Node(word=origin.word, language=origin.language, period=origin.period, children=grandchildren)
        )
    return children
