"""Loading and querying etymology data for a given language."""

from __future__ import annotations

import csv
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

from .tree import Node, Origin, build_tree

#: Supported language codes and the bundled CSV each one loads.
LANGUAGES: Dict[str, str] = {
    "de": "de.csv",
    "ta": "ta.csv",
    "sa": "sa.csv",
    "te": "te.csv",
    "ml": "ml.csv",
    "kn": "kn.csv",
}


class Etymology:
    """Looks up word origins in one language and builds etymology trees.

    By default, data is loaded from the bundled CSV for ``language`` (one of
    :data:`LANGUAGES`). Pass ``data_path`` to load a different dataset
    instead (e.g. in tests, or a dataset for a language not bundled here).
    """

    def __init__(
        self,
        language: str = "de",
        data_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.language = language
        self._data: Dict[str, List[Origin]] = self._load(language, data_path)

    @staticmethod
    def _load(language: str, data_path: Optional[Union[str, Path]]) -> Dict[str, List[Origin]]:
        data: Dict[str, List[Origin]] = {}
        if data_path is not None:
            context = open(data_path, "r", encoding="utf-8", newline="")
        else:
            try:
                filename = LANGUAGES[language]
            except KeyError:
                available = ", ".join(sorted(LANGUAGES))
                raise ValueError(f"unknown language {language!r}; available: {available}") from None
            context = resources.files("pymologie.resources").joinpath(filename).open(
                "r", encoding="utf-8", newline=""
            )
        with context as file:
            reader = csv.reader(file)
            next(reader, None)  # header
            for row in reader:
                term = row[0]
                data.setdefault(term, []).append(Origin(*row[1:]))
        return data

    def origins(self, word: str) -> List[Origin]:
        """Direct origins of ``word``, or an empty list if unknown."""
        return list(self._data.get(word, []))

    def tree(self, word: str, max_depth: int = 10) -> Node:
        """Build the full etymology tree for ``word``."""
        return build_tree(word, self._data, max_depth=max_depth)

    def analyze(self, words: Iterable[str]) -> Counter:
        """Count how often each language appears among the direct origins of ``words``."""
        language_counts: Counter = Counter()
        for word in words:
            language_counts.update(origin.language for origin in self._data.get(word, []))
        return language_counts
