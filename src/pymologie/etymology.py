"""Loading and querying etymology data for a given language."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

from .packs import LanguagePackNotFoundError, download_language as _download_pack, resolve_resource
from .transliteration import annotate_transliteration, transliterate_text
from .tree import Node, Origin, build_tree, map_tree

#: Supported language codes and the CSV each one loads. Only "en" ships
#: inside the pip package (see packs.BUNDLED_LANGUAGES) -- the rest are
#: fetched on demand via download_language().
LANGUAGES: Dict[str, str] = {
    "en": "en.csv",
    "de": "de.csv",
    "ta": "ta.csv",
    "sa": "sa.csv",
    "te": "te.csv",
    "ml": "ml.csv",
    "kn": "kn.csv",
}

#: Languages whose script is already Latin, so no reverse transliteration
#: index or output romanization applies to them.
_LATIN_SCRIPT_LANGUAGES = {"de", "en"}


def download_language(language: str, *, force: bool = False) -> Path:
    """Download and cache the CSV for ``language`` (see :data:`LANGUAGES`).

    Raises :class:`ValueError` for an unknown language code, or
    :class:`~pymologie.packs.LanguagePackNotFoundError` if the download
    itself fails (e.g. no matching tag for the installed version).
    """
    try:
        filename = LANGUAGES[language]
    except KeyError:
        available = ", ".join(sorted(LANGUAGES))
        raise ValueError(f"unknown language {language!r}; available: {available}") from None
    return _download_pack(language, filename, force=force)


class Etymology:
    """Looks up word origins in one language and builds etymology trees.

    Construct once and reuse — this instance is itself the reusable
    "settings" object, so ``language``/``transliterate`` don't need to be
    passed again on every call. By default, data is loaded from the bundled
    CSV for ``language`` (one of :data:`LANGUAGES`). Pass ``data_path`` to
    load a different dataset instead (e.g. in tests, or a dataset for a
    language not bundled here).

    When ``transliterate`` is ``True``, every non-Latin word in the results
    gets its Latin romanization (ISO 15919) shown alongside it, e.g.
    ``"गुरु (guru)"`` — the original script is kept, not replaced, since
    losing it would make the etymology harder to cross-reference against
    other sources. Words already in Latin script (German, reconstructed
    Proto-Indo-European forms, etc.) are left untouched. Regardless of this
    setting, lookups also accept a word's Latin transliteration as input
    (e.g. ``"guru"`` as well as ``"குரு"``) for any bundled non-German
    language.
    """

    def __init__(
        self,
        language: str = "en",
        data_path: Optional[Union[str, Path]] = None,
        transliterate: bool = False,
    ) -> None:
        self.language = language
        self.transliterate = transliterate
        self._data: Dict[str, List[Origin]] = self._load(language, data_path)
        self._latin_index: Dict[str, List[str]] = self._build_latin_index(self._data, language)

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
            context = resolve_resource(language, filename)
        with context as file:
            reader = csv.reader(file)
            next(reader, None)  # header
            for row in reader:
                term = row[0]
                data.setdefault(term, []).append(Origin(*row[1:]))
        return data

    @staticmethod
    def _build_latin_index(data: Dict[str, List[Origin]], language: str) -> Dict[str, List[str]]:
        if language in _LATIN_SCRIPT_LANGUAGES:
            return {}
        index: Dict[str, List[str]] = {}
        for term in data:
            latin = transliterate_text(term).lower()
            if latin != term.lower():
                index.setdefault(latin, []).append(term)
        return index

    def _resolve(self, word: str) -> List[str]:
        """Native term(s) matching ``word`` when it was given as a Latin spelling."""
        return self._latin_index.get(word.lower(), [])

    def _finalize_origins(self, origins: List[Origin]) -> List[Origin]:
        if not self.transliterate:
            return origins
        return [Origin(annotate_transliteration(o.word), o.language, o.period) for o in origins]

    def _finalize_node(self, node: Node) -> Node:
        if not self.transliterate:
            return node
        return map_tree(node, annotate_transliteration)

    def origins(self, word: str) -> Union[List[Origin], List[List[Origin]]]:
        """Direct origins of ``word``.

        A direct native-script match (or an unknown word) returns a flat
        list, exactly as before (``[]`` when unknown). A Latin spelling
        always resolves to a list of lists — one per matching native word —
        even when there's only a single match.
        """
        if word in self._data:
            return self._finalize_origins(list(self._data[word]))
        matches = self._resolve(word)
        if not matches:
            return []
        return [self._finalize_origins(list(self._data[term])) for term in matches]

    def tree(self, word: str, max_depth: int = 10) -> Union[Node, List[Node]]:
        """Build the full etymology tree for ``word``.

        A direct native-script match (or an unknown word) returns a single
        :class:`Node`, exactly as before. A Latin spelling always resolves
        to a list of trees — one per matching native word — even when
        there's only a single match.
        """
        if word in self._data:
            return self._finalize_node(build_tree(word, self._data, max_depth=max_depth))
        matches = self._resolve(word)
        if not matches:
            return self._finalize_node(build_tree(word, self._data, max_depth=max_depth))
        return [
            self._finalize_node(build_tree(term, self._data, max_depth=max_depth))
            for term in matches
        ]

    def analyze(self, words: Iterable[str]) -> Counter:
        """Count how often each language appears among the direct origins of ``words``."""
        language_counts: Counter = Counter()
        for word in words:
            terms = [word] if word in self._data else self._resolve(word)
            for term in terms:
                language_counts.update(origin.language for origin in self._data.get(term, []))
        return language_counts
