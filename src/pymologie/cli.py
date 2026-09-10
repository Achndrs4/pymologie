"""Command-line interface for pymologie."""

from __future__ import annotations

import argparse
import json
import sys

from .etymology import LANGUAGES, Etymology


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="pymologie", description="Show a word's etymology tree.")
    parser.add_argument("word", help="the word to look up")
    parser.add_argument(
        "--language",
        "-l",
        default="de",
        choices=sorted(LANGUAGES),
        help="language dataset to use (default: de)",
    )
    parser.add_argument("--max-depth", type=int, default=10, help="maximum tree depth (default: 10)")
    parser.add_argument("--json", action="store_true", help="print the tree as JSON instead of ASCII art")
    args = parser.parse_args(argv)

    node = Etymology(language=args.language).tree(args.word, max_depth=args.max_depth)

    if not node.children:
        print(f"no results for: {args.word}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(node.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
