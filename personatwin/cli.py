from __future__ import annotations
import argparse, json
from pathlib import Path
from .converter import convert

def main():
    parser = argparse.ArgumentParser(prog="personatwin", description="PersonaTwin AI command-line tools")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("convert", help="Convert Common Kit build-answer JSON into me.md")
    c.add_argument("answers", help="Path to build-answer JSON")
    c.add_argument("-o", "--out", default="me.md")
    c.add_argument("--review-status", default="Not yet reviewed by the person.")
    args = parser.parse_args()
    if args.command == "convert":
        result = convert(args.answers, args.out, args.review_status)
        print(json.dumps(result, indent=2))
        if result["flags"]: raise SystemExit(1)
if __name__ == "__main__": main()
