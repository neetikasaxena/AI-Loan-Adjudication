"""Adjudicate a single free-text application and print the structured decision as JSON.

Examples:
  python scripts/predict.py "Hi, I'm 34, I earn $52,000 a year ..."
  python scripts/predict.py --file application.txt --extractor regex --explainer template
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loan_adjudication.pipeline import build_adjudicator

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("narrative", nargs="?", help="Application text (reads stdin if omitted)")
    parser.add_argument("--file", help="Read the application text from a file")
    parser.add_argument("--extractor", choices=["auto", "llm", "regex"], default="auto")
    parser.add_argument("--explainer", choices=["auto", "llm", "template"], default="auto")
    parser.add_argument("--debug", action="store_true", help="Include extracted fields in the output")
    args = parser.parse_args()

    text = Path(args.file).read_text() if args.file else args.narrative or sys.stdin.read()
    if not text.strip():
        parser.error("empty application text")

    result = build_adjudicator(args.extractor, args.explainer).run(text.strip())
    if not args.debug:
        result = {k: result[k] for k in ("decision", "failed_rules", "missing_information", "reasoning")}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
