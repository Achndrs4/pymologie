"""pymologie: etymology trees for German, Tamil, Sanskrit, Telugu, Malayalam, and Kannada words.

    >>> import pymologie
    >>> print(pymologie.tree("Haus"))
    Haus
    ├── hūs (Middle High German, 1050 CE - 1500 CE)
    ├── hūs (Old High German, 750 CE - 1050 CE)
    ├── *hūs (Proto-West Germanic, before 500 CE (unconfirmed))
    └── *hūsą (Proto-Germanic, 500 BCE - 500 CE)

    >>> print(pymologie.tree("मरण", language="sa"))
"""

from collections import Counter
from typing import Dict, Iterable, List, Optional

from .etymology import LANGUAGES, Etymology
from .tree import Node, Origin

__version__ = "2.1.0"
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
