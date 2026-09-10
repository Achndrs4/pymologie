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
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .etymology import LANGUAGES, Etymology
from .transliteration import transliterate_text as transliterate
from .tree import Node, Origin

__version__ = "2.1.0"
__all__ = [
    "Etymology",
    "Node",
    "Origin",
    "LANGUAGES",
    "tree",
    "origins",
    "analyze",
    "transliterate",
]

_defaults: Dict[Tuple[str, bool], Etymology] = {}


def _default_etymology(language: str, transliterate_output: bool) -> Etymology:
    key = (language, transliterate_output)
    etymology = _defaults.get(key)
    if etymology is None:
        etymology = Etymology(language=language, transliterate=transliterate_output)
        _defaults[key] = etymology
    return etymology


def tree(
    word: str,
    language: str = "de",
    *,
    transliterate: bool = False,
    max_depth: int = 10,
    settings: Optional[Etymology] = None,
) -> Union[Node, List[Node]]:
    """Build the etymology tree for ``word`` in ``language`` (see :data:`LANGUAGES`).

    Pass a preconfigured :class:`Etymology` as ``settings`` to reuse its
    ``language``/``transliterate`` instead of repeating them on every call.
    """
    etymology = settings if settings is not None else _default_etymology(language, transliterate)
    return etymology.tree(word, max_depth=max_depth)


def origins(
    word: str,
    language: str = "de",
    *,
    transliterate: bool = False,
    settings: Optional[Etymology] = None,
) -> Union[List[Origin], List[List[Origin]]]:
    """Direct origins of ``word`` in ``language`` (see :data:`LANGUAGES`)."""
    etymology = settings if settings is not None else _default_etymology(language, transliterate)
    return etymology.origins(word)


def analyze(
    words: Iterable[str],
    language: str = "de",
    *,
    transliterate: bool = False,
    settings: Optional[Etymology] = None,
) -> Counter:
    """Count language frequency among the direct origins of ``words`` in ``language``."""
    etymology = settings if settings is not None else _default_etymology(language, transliterate)
    return etymology.analyze(words)
