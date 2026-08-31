"""Loading and querying etymology data."""

from __future__ import annotations

import csv
from collections import Counter
from importlib import resources
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

from .tree import Node, Origin, build_tree

_DEFAULT_RESOURCE = "de.csv"


class Etymology:
    """Looks up word origins and builds etymology trees.

    By default, data is loaded from the bundled German dataset. Pass
    ``data_path`` to load a different dataset instead (e.g. in tests).
    """

    def __init__(self, data_path: Optional[Union[str, Path]] = None) -> None:
        self._data: Dict[str, List[Origin]] = self._load(data_path)

    @staticmethod
    def _load(data_path: Optional[Union[str, Path]]) -> Dict[str, List[Origin]]:
        data: Dict[str, List[Origin]] = {}
        if data_path is not None:
            context = open(data_path, "r", encoding="utf-8", newline="")
        else:
            context = resources.files("pymologie.resources").joinpath(_DEFAULT_RESOURCE).open(
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
