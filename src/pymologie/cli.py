"""Command-line interface for pymologie."""

from __future__ import annotations

import argparse
import json
import sys

from .etymology import LANGUAGES, Etymology


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pymologie", description="Show a word's etymology tree.")
    parser.add_argument("word", help="the word to look up (native script or Latin transliteration)")
    parser.add_argument(
        "--language",
        "-l",
        default="de",
        choices=sorted(LANGUAGES),
        help="language dataset to use (default: de)",
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

    etymology = Etymology(language=args.language, transliterate=args.transliterate)
    result = etymology.tree(args.word, max_depth=args.max_depth)
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
