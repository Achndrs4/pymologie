"""Command-line interface for pymologie."""

from __future__ import annotations

import argparse
import json
import sys

from .etymology import LANGUAGES, Etymology, download_language
from .packs import LanguagePackNotFoundError


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pymologie", description="Show a word's etymology tree.")
    parser.add_argument(
        "word",
        nargs="?",
        help="the word to look up (native script or Latin transliteration)",
    )
    parser.add_argument(
        "--download",
        metavar="LANGUAGE",
        choices=sorted(LANGUAGES),
        help="download and cache a language pack (see --language choices), then exit",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="en",
        choices=sorted(LANGUAGES),
        help="language dataset to use (default: en). Every language but en must be "
        "downloaded first via --download",
    )
    parser.add_argument("--max-depth", type=int, default=10, help="maximum tree depth (default: 10)")
    parser.add_argument(
        "--transliterate",
        "-t",
        action="store_true",
        help="romanize output to Latin script (ISO 15919)",
    )
    parser.add_argument("--json", action="store_true", help="print the tree as JSON instead of ASCII art")
    args = parser.parse_args(argv)

    if args.download:
        path = download_language(args.download)
        print(f"downloaded {args.download!r} language pack to {path}")
        return 0

    if not args.word:
        parser.error("the following arguments are required: word (unless --download is used)")

    try:
        etymology = Etymology(language=args.language, transliterate=args.transliterate)
        result = etymology.tree(args.word, max_depth=args.max_depth)
    except LanguagePackNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    nodes = result if isinstance(result, list) else [result]

    if not any(node.children for node in nodes):
        print(f"no results for: {args.word}", file=sys.stderr)
        return 1

    if args.json:
        payload = [node.to_dict() for node in nodes] if isinstance(result, list) else nodes[0].to_dict()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for i, node in enumerate(nodes):
            if len(nodes) > 1:
                print(f"=== match {i + 1}: {node.word} ===")
            print(node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
