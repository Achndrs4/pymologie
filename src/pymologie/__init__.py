"""pymologie: derive the etymology tree of German words.

    >>> import pymologie
    >>> print(pymologie.tree("Haus"))
    Haus
    ├── hūs (Middle High German, 1050 n.u.Z. - 1500 n.u.Z.)
    ├── hūs (Old High German, 750 n.u.Z. - 1050 n.u.Z.)
    ├── *hūs (Proto-West Germanic, vor 500 n.u.Z. (unbestätigt))
    └── *hūsą (Proto-Germanic, 500 v.u.Z. - 500 n.u.Z.)
"""

from collections import Counter
from typing import Iterable, List, Optional

from .etymology import Etymology
from .tree import Node, Origin

__version__ = "2.0.0"
__all__ = ["Etymology", "Node", "Origin", "tree", "origins", "analyze"]

_default: Optional[Etymology] = None


def _default_etymology() -> Etymology:
    global _default
    if _default is None:
        _default = Etymology()
    return _default


def tree(word: str, max_depth: int = 10) -> Node:
    """Build the etymology tree for ``word``."""
    return _default_etymology().tree(word, max_depth=max_depth)


def origins(word: str) -> List[Origin]:
    """Direct origins of ``word``."""
    return _default_etymology().origins(word)


def analyze(words: Iterable[str]) -> Counter:
    """Count language frequency among the direct origins of ``words``."""
    return _default_etymology().analyze(words)
