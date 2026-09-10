"""pymologie: etymology trees for English (bundled) plus German, Tamil,
Sanskrit, Telugu, Malayalam, and Kannada words (downloaded on demand).

    >>> import pymologie
    >>> print(pymologie.tree("house"))
    house
    ├── hous (Middle English, 1150 CE - 1500 CE)
    ├── hūs (Old English, 450 CE - 1150 CE)
    ├── *hūsą (Proto-Germanic, 500 BCE - 500 CE)
    └── *(s)kews- (Proto-Indo-European, 4500 BCE - 2500 BCE)

    >>> pymologie.download_language("sa")   # one-time, per language
    >>> print(pymologie.tree("मरण", language="sa"))
"""

from collections import Counter
from importlib.metadata import version as _pkg_version
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .etymology import LANGUAGES, Etymology
from .etymology import download_language as download_language
from .packs import LanguagePackNotFoundError
from .transliteration import transliterate_text as transliterate
from .tree import Node, Origin

__version__ = _pkg_version("pymologie")
__all__ = [
    "Etymology",
    "Node",
    "Origin",
    "LANGUAGES",
    "tree",
    "origins",
    "analyze",
    "transliterate",
    "download_language",
    "LanguagePackNotFoundError",
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
    language: str = "en",
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
    language: str = "en",
    *,
    transliterate: bool = False,
    settings: Optional[Etymology] = None,
) -> Union[List[Origin], List[List[Origin]]]:
    """Direct origins of ``word`` in ``language`` (see :data:`LANGUAGES`)."""
    etymology = settings if settings is not None else _default_etymology(language, transliterate)
    return etymology.origins(word)


def analyze(
    words: Iterable[str],
    language: str = "en",
    *,
    transliterate: bool = False,
    settings: Optional[Etymology] = None,
) -> Counter:
    """Count language frequency among the direct origins of ``words`` in ``language``."""
    etymology = settings if settings is not None else _default_etymology(language, transliterate)
    return etymology.analyze(words)
