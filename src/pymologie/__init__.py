"""pymologie: etymology trees for German, Tamil, and Sanskrit words.

    >>> import pymologie
    >>> print(pymologie.tree("Haus"))
    Haus
    ├── hūs (Mittelhochdeutsch, 1050 n.u.Z. - 1500 n.u.Z.)
    ├── hūs (Althochdeutsch, 750 n.u.Z. - 1050)
    ├── *hūs (Westurgermanisch, nicht verfügbar)
    └── *hūsą (Urgermanisch, 500 v.u.Z. - 500 n.u.Z.)

    >>> print(pymologie.tree("मरण", language="sa"))
"""

from collections import Counter
from typing import Dict, Iterable, List, Optional

from .etymology import LANGUAGES, Etymology
from .tree import Node, Origin

__version__ = "2.0.0"
__all__ = ["Etymology", "Node", "Origin", "LANGUAGES", "tree", "origins", "analyze"]

_defaults: Dict[str, Etymology] = {}


def _default_etymology(language: str) -> Etymology:
    etymology = _defaults.get(language)
    if etymology is None:
        etymology = Etymology(language=language)
        _defaults[language] = etymology
    return etymology


def tree(word: str, language: str = "de", max_depth: int = 10) -> Node:
    """Build the etymology tree for ``word`` in ``language`` (see :data:`LANGUAGES`)."""
    return _default_etymology(language).tree(word, max_depth=max_depth)


def origins(word: str, language: str = "de") -> List[Origin]:
    """Direct origins of ``word`` in ``language`` (see :data:`LANGUAGES`)."""
    return _default_etymology(language).origins(word)


def analyze(words: Iterable[str], language: str = "de") -> Counter:
    """Count language frequency among the direct origins of ``words`` in ``language``."""
    return _default_etymology(language).analyze(words)
