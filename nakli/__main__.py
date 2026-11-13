"""Command line: python -m nakli (or the ``nakli`` command once installed)."""

from __future__ import annotations

import argparse
import sys

from .adapters import load_detector
from .checksums import aadhaar_valid, gstin_valid
from .generate import generate, load_jsonl, save_jsonl
from .render import VARIANTS, normalise
from .score import save_report, score
from .templates import LANGS


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nakli", description="Safe fake Indian personal data for testing PII detectors.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="write labelled test messages to a JSONL file")
    g.add_argument("--n", type=int, default=280)
    g.add_argument("--seed", type=int, default=7)
    g.add_argument("--langs", type=_csv, default=list(LANGS), help=f"comma list from {','.join(LANGS)}")
    g.add_argument("--variants", type=_csv, default=list(VARIANTS), help=f"comma list from {','.join(VARIANTS)}")
    g.add_argument("--safe", action="store_true", help="values that can never be real (they also fail validation)")
    g.add_argument("--out", required=True)

    s = sub.add_parser("score", help="score a PII detector on labelled data")
    s.add_argument("--detector", default="regex", help="regex, vismriti, presidio, presidio-strict, or module:function")
    s.add_argument("--data", help="JSONL from `nakli generate`; if left out, data is generated in memory")
    s.add_argument("--n", type=int, default=280)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--types", type=_csv, help="only score these types, e.g. AADHAAR,PAN,PHONE")
    s.add_argument("--out", help="write <out>.md and <out>.json")
    s.add_argument("--fail-below", type=float, help="exit with code 1 if recall is below this (0 to 1)")

    sub.add_parser("demo", help="show a few safe sample messages and score the naive regex baseline")

    v = sub.add_parser("validate", help="check an Aadhaar or GSTIN against the format and checksum rules")
    v.add_argument("value")

    args = ap.parse_args(argv)

    if args.cmd == "generate":
        n = save_jsonl(generate(args.n, args.seed, args.langs, args.variants, safe=args.safe), args.out)
        print(f"Wrote {n} labelled records to {args.out}. Keep generated files local; do not publish large lists.")
        return 0

    if args.cmd == "score":
        records = load_jsonl(args.data) if args.data else generate(args.n, args.seed)
        report = score(records, load_detector(args.detector), args.detector, types=args.types)
        print(report.to_markdown())
        if args.out:
            md, js = save_report(report, args.out)
            print(f"Saved {md} and {js}")
        if args.fail_below is not None and (report.overall.recall < args.fail_below or report.errored):
            print(f"FAIL: recall {report.overall.recall:.0%} is below {args.fail_below:.0%}", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "demo":
        print("Sample messages (safe mode: these values can never be real):\n")
        samples = [generate(1, seed=11 + i, langs=[lang], variants=[variant], safe=True)[0]
                   for i, (lang, variant) in enumerate([("en", "plain"), ("hinglish", "homoglyph"),
                                                         ("hi", "indic_digits"), ("or", "zero_width")])]
        for r in samples:
            print(f"[{r.lang}, {r.variant}] {r.text}")
            print("   labels: " + ", ".join(f"{e.type}={e.text!r}" for e in r.entities) + "\n")
        report = score(generate(280, seed=7), load_detector("regex"), "regex-baseline (ASCII-only patterns)")
        print(report.to_markdown())
        return 0

    if args.cmd == "validate":
        value = normalise(args.value).replace(" ", "").replace("-", "").upper()
        if value.isdigit():
            print(f"Aadhaar rules (12 digits, starts 2-9, Verhoeff check): {'valid' if aadhaar_valid(value) else 'not valid'}")
        elif len(value) == 15:
            print(f"GSTIN check character: {'valid' if gstin_valid(value) else 'not valid'}")
        else:
            print("Give a 12-digit Aadhaar-style number or a 15-character GSTIN.")
            return 2
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
