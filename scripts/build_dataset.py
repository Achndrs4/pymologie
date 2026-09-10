"""Filter an etymology-db dump down to just the languages pymologie ships.

Source dataset: https://github.com/droher/etymology-db (Wiktionary-derived,
CC BY-SA 3.0) -- a graph of ~4M etymological relationships across ~2900
languages. This script throws away everything except what's reachable from
German, Tamil, and Sanskrit terms, and writes the result straight into
src/pymologie/resources/ as the small per-language CSVs the pip package
actually ships.

Usage:
    python scripts/build_dataset.py <etymology-db.csv>

    # only rebuild a subset, or add a new language:
    python scripts/build_dataset.py <etymology-db.csv> --languages Tamil
    python scripts/build_dataset.py <etymology-db.csv> --languages Hindi --code hi

Only "descent" relation types are kept (inherited_from, borrowed_from,
derived_from, compound_of, calques, blends, clippings, etc.) -- sideways
relations like cognate_of/doublet_with/etymologically_related_to and the
internal group_* bookkeeping rows are dropped, since they don't represent
"this word comes from that word".
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DESCENT_RELTYPES = {
    "inherited_from",
    "derived_from",
    "borrowed_from",
    "learned_borrowing_from",
    "unadapted_borrowing_from",
    "orthographic_borrowing_from",
    "semi_learned_borrowing_from",
    "calque_of",
    "semantic_loan_of",
    "phono-semantic_matching_of",
    "blend_of",
    "clipping_of",
    "back-formation_from",
    "abbreviation_of",
    "initialism_of",
    "compound_of",
}

#: etymology-db "lang" value -> pymologie language code, for the languages
#: bundled by default. Extend this (or pass --languages/--code) to add more.
DEFAULT_LANGUAGES = {
    "German": "de",
    "Tamil": "ta",
    "Sanskrit": "sa",
}

RESOURCES_DIR = Path(__file__).resolve().parent.parent / "src" / "pymologie" / "resources"

Node = Tuple[str, str]  # (term, lang)
Edge = Tuple[str, str, str]  # (related_term, related_lang, reltype)


def load_edges(dump_path: Path) -> Dict[Node, List[Edge]]:
    edges: Dict[Node, List[Edge]] = {}
    with dump_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["reltype"] not in DESCENT_RELTYPES:
                continue
            related_term = row["related_term"]
            related_lang = row["related_lang"]
            if not related_term or not related_lang:
                continue
            node = (row["term"], row["lang"])
            edges.setdefault(node, []).append((related_term, related_lang, row["reltype"]))
    return edges


def bfs_reachable(edges: Dict[Node, List[Edge]], start_lang: str) -> Dict[Node, List[Edge]]:
    visited: Dict[Node, List[Edge]] = {}
    queue = deque(node for node in edges if node[1] == start_lang)
    seen = set(queue)
    while queue:
        node = queue.popleft()
        outgoing = edges.get(node, [])
        visited[node] = outgoing
        for related_term, related_lang, _ in outgoing:
            child = (related_term, related_lang)
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return visited


def write_dataset(visited: Dict[Node, List[Edge]], periods: Dict[str, str], out_path: Path) -> int:
    rows_written = 0
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Term", "Stamm", "Sprache", "Zeitraum"])
        for (term, _lang), outgoing in visited.items():
            seen_targets = set()
            for related_term, related_lang, _reltype in outgoing:
                key = (related_term, related_lang)
                if key in seen_targets:
                    continue
                seen_targets.add(key)
                period = periods.get(related_lang, "not available")
                writer.writerow([term, related_term, related_lang, period])
                rows_written += 1
    return rows_written


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dump", type=Path, help="path to the etymology-db CSV dump")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help='exact "lang" column value(s) to keep, e.g. "German" "Tamil" "Sanskrit" '
        f"(default: {', '.join(DEFAULT_LANGUAGES)})",
    )
    parser.add_argument(
        "--code",
        default=None,
        help="pymologie language code for the output filename, when --languages names exactly one language "
        "not already in the default map (e.g. --languages Hindi --code hi)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=RESOURCES_DIR,
        help=f"directory to write <code>.csv into (default: {RESOURCES_DIR})",
    )
    parser.add_argument(
        "--periods",
        type=Path,
        default=None,
        help="optional JSON file mapping language name -> period string, for languages missing from the built-in table",
    )
    args = parser.parse_args(argv)

    languages = args.languages or list(DEFAULT_LANGUAGES)
    if args.code:
        if len(languages) != 1:
            parser.error("--code requires exactly one --languages value")
        code_map = {languages[0]: args.code}
    else:
        try:
            code_map = {lang: DEFAULT_LANGUAGES[lang] for lang in languages}
        except KeyError as exc:
            parser.error(f"no known pymologie code for {exc.args[0]!r}; pass --code to specify one")
            return 2  # unreachable, parser.error exits

    periods = dict(DEFAULT_PERIODS)
    if args.periods:
        periods.update(json.loads(args.periods.read_text(encoding="utf-8")))

    print(f"Loading descent edges from {args.dump} ...", file=sys.stderr)
    edges = load_edges(args.dump)
    print(f"{len(edges)} nodes with outgoing descent edges", file=sys.stderr)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    all_missing: set = set()
    for language, code in code_map.items():
        print(f"Walking reachable graph from lang={language!r} ...", file=sys.stderr)
        visited = bfs_reachable(edges, language)
        out_path = args.out_dir / f"{code}.csv"
        rows_written = write_dataset(visited, periods, out_path)
        print(f"  {len(visited)} nodes reachable, {rows_written} rows -> {out_path}", file=sys.stderr)
        all_missing |= {lang for outgoing in visited.values() for _, lang, _ in outgoing if lang not in periods}

    if all_missing:
        print(
            "No period on file for these languages (they'll show 'not available'): "
            + ", ".join(sorted(all_missing)),
            file=sys.stderr,
        )
    return 0


# Rough, approximate era estimates for the historical language stages this
# script is expected to encounter. Dates for ancient/reconstructed languages
# (especially Proto-Dravidian, Proto-Indo-European, Vedic Sanskrit) are
# contested among historical linguists -- treat these as ballpark, not fact.
DEFAULT_PERIODS: Dict[str, str] = {
    "Sanskrit": "1500 BCE - present (liturgical/classical)",
    "Vedic Sanskrit": "1500 BCE - 500 BCE",
    "Classical Sanskrit": "500 BCE - 1000 CE",
    "Prakrit": "500 BCE - 1000 CE",
    "Ashokan Prakrit": "300 BCE - 100 BCE",
    "Sauraseni Prakrit": "1 CE - 700 CE",
    "Maharastri Prakrit": "1 CE - 700 CE",
    "Kamarupi Prakrit": "600 CE - 1200 CE",
    "Niya Prakrit": "200 CE - 400 CE",
    "Pali": "500 BCE - 1 CE",
    "Proto-Indo-Aryan": "2000 BCE - 1500 BCE",
    "Proto-Indo-Iranian": "2200 BCE - 1800 BCE",
    "Proto-Indo-European": "4500 BCE - 2500 BCE",
    "Tamil": "300 BCE - present",
    "Old Tamil": "300 BCE - 700 CE",
    "Middle Tamil": "700 CE - 1600 CE",
    "Proto-Dravidian": "3000 BCE - 1500 BCE (disputed)",
    "Proto-South Dravidian": "1500 BCE - 500 BCE",
    "German": "750 CE - present",
    "Old High German": "750 CE - 1050 CE",
    "Middle High German": "1050 CE - 1500 CE",
    "Middle Low German": "1200 CE - 1600 CE",
    "Low German": "1200 CE - present",
    "Proto-West Germanic": "before 500 CE (unconfirmed)",
    "Proto-Germanic": "500 BCE - 500 CE",
    # Common loanword-source languages that show up when tracing Tamil,
    # Sanskrit, or German outward. Reusing the same real-world date ranges
    # already curated for the German dataset where they overlap.
    "Latin": "700 BCE - 500 CE",
    "Late Latin": "200 CE - 600 CE",
    "Vulgar Latin": "100 BCE - 600 CE",
    "Medieval Latin": "600 CE - 1400 CE",
    "Ancient Greek": "1500 BCE - 300 BCE",
    "Greek": "1453 CE - present",
    "Proto-Hellenic": "2200 BCE - 1800 BCE",
    "Old English": "450 CE - 1150 CE",
    "Middle English": "1150 CE - 1500 CE",
    "English": "1550 CE - present",
    "Old French": "800 CE - 1400 CE",
    "Middle French": "1340 CE - 1610 CE",
    "French": "1600 CE - present",
    "Old Dutch": "600 CE - 1200 CE",
    "Middle Dutch": "1150 CE - 1500 CE",
    "Dutch": "1500 CE - present",
    "Old Norse": "700 CE - 1350 CE",
    "Old Portuguese": "870 CE - 1400 CE",
    "Portuguese": "1516 CE - present",
    "Spanish": "1600 CE - present",
    "Italian": "1400 CE - present",
    "Arabic": "600 CE - present",
    "Old Persian": "600 BCE - 300 BCE",
    "Middle Persian": "300 BCE - 651 CE",
    "Classical Persian": "800 CE - 1900 CE",
    "Persian": "1000 CE - present",
    "Hebrew": "900 BCE - 500 CE",
    "Biblical Hebrew": "1000 BCE - 500 BCE",
    "Proto-Celtic": "1000 BCE - 500 BCE (disputed)",
    "Proto-Italic": "1000 BCE - 700 BCE (disputed)",
    "Proto-Slavic": "500 CE - 1000 CE (disputed)",
}


if __name__ == "__main__":
    sys.exit(main())
