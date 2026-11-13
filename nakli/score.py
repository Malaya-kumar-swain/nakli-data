"""Score any PII detector against labelled Nakli-Data records."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from .generate import Record

# Common detector label names mapped to Nakli's types.
DEFAULT_TYPE_MAP = {
    "IN_AADHAAR": "AADHAAR", "AADHAAR": "AADHAAR", "IN_PAN": "PAN", "PAN": "PAN",
    "IN_GSTIN": "GSTIN", "GSTIN": "GSTIN", "IFSC": "IFSC", "IN_IFSC": "IFSC",
    "PHONE_NUMBER": "PHONE", "PHONE_IN": "PHONE", "PHONE": "PHONE",
    "EMAIL_ADDRESS": "EMAIL", "EMAIL": "EMAIL", "UPI": "UPI", "IN_UPI": "UPI",
    "PERSON": "PERSON", "PINCODE": "PINCODE",
}

Prediction = tuple[int, int, str]
Detector = Callable[[str], Iterable[Any]]


def _as_prediction(p: Any, type_map: dict[str, str]) -> Prediction | None:
    if isinstance(p, (tuple, list)):
        start, end, kind = p[0], p[1], p[2]
    else:
        start, end = p.start, p.end
        kind = getattr(p, "type", None) or getattr(p, "kind", None) or getattr(p, "entity_type", None)
    kind = type_map.get(str(kind), str(kind))
    return (int(start), int(end), kind)


@dataclass
class Tally:
    found: int = 0
    total: int = 0

    @property
    def recall(self) -> float:
        return self.found / self.total if self.total else 0.0


@dataclass
class Report:
    detector: str
    records: int
    types: tuple[str, ...]
    by_type: dict[str, Tally] = field(default_factory=dict)
    by_lang: dict[str, Tally] = field(default_factory=dict)
    by_variant: dict[str, Tally] = field(default_factory=dict)
    overall: Tally = field(default_factory=Tally)
    false_positives: int = 0
    false_positives_by_type: dict[str, int] = field(default_factory=dict)
    predictions: int = 0
    errored: int = 0
    missed_examples: list[dict] = field(default_factory=list)

    @property
    def precision(self) -> float:
        true_hits = self.predictions - self.false_positives
        return true_hits / self.predictions if self.predictions else 0.0

    def to_dict(self) -> dict:
        tab = lambda d: {k: {"found": v.found, "total": v.total, "recall": round(v.recall, 3)} for k, v in sorted(d.items())}
        return {"detector": self.detector, "records": self.records, "types": list(self.types),
                "recall": round(self.overall.recall, 3), "precision": round(self.precision, 3),
                "found": self.overall.found, "total": self.overall.total,
                "false_positives": self.false_positives, "false_positives_by_type": dict(sorted(self.false_positives_by_type.items())),
                "errored_records": self.errored,
                "by_type": tab(self.by_type), "by_language": tab(self.by_lang),
                "by_variant": tab(self.by_variant), "missed_examples": self.missed_examples}

    def to_markdown(self) -> str:
        pct = lambda t: f"{t.recall:.0%} ({t.found}/{t.total})"
        lines = [f"## Nakli-Data score: `{self.detector}`", "",
                 f"**Recall: {self.overall.recall:.0%}** ({self.overall.found} of {self.overall.total} fake identifiers found)  ",
                 f"**Precision: {self.precision:.1%}** ({self.false_positives} false alarm{'' if self.false_positives == 1 else 's'} out of {self.predictions} detections)", ""]
        if self.false_positives:
            lines += ["False alarms by detected type: " + ", ".join(f"{k} {v}" for k, v in sorted(self.false_positives_by_type.items())), ""]
        if self.errored:
            lines += [f"> Warning: the detector crashed on {self.errored} records; their identifiers count as missed.", ""]
        for title, table in (("Type", self.by_type), ("Language", self.by_lang), ("How it was written", self.by_variant)):
            lines += [f"| {title} | Found |", "|---|---|"]
            lines += [f"| {k} | {pct(v)} |" for k, v in sorted(table.items())]
            lines.append("")
        return "\n".join(lines)


def score(records: Iterable[Record], detector: Detector, name: str = "custom",
          types: Iterable[str] | None = None, type_map: dict[str, str] | None = None,
          keep_examples: int = 5) -> Report:
    """A labelled identifier counts as found when the detector returns a span of the same
    type that overlaps it. Detections of a scored type that overlap nothing are false alarms."""
    type_map = {**DEFAULT_TYPE_MAP, **(type_map or {})}
    records = list(records)
    # Score only the types asked for, else the types the detector says it supports, else every type.
    wanted = tuple(types or getattr(detector, "types", None) or sorted({e.type for r in records for e in r.entities}))
    rep = Report(name, len(records), wanted)
    for r in records:
        try:
            preds = [p for p in (_as_prediction(x, type_map) for x in detector(r.text)) if p and p[2] in wanted]
        except Exception as e:  # a crash is never a pass
            rep.errored += 1
            preds = []
            if len(rep.missed_examples) < keep_examples:
                rep.missed_examples.append({"id": r.id, "error": f"{type(e).__name__}: {e}"})
        gold = [e for e in r.entities if e.type in wanted]
        used = set()
        for g in gold:
            hit = next((i for i, p in enumerate(preds) if p[2] == g.type and p[0] < g.end and g.start < p[1]), None)
            ok = hit is not None
            if ok:
                used.add(hit)
            for table, key in ((rep.by_type, g.type), (rep.by_lang, r.lang), (rep.by_variant, g.variant)):
                t = table.setdefault(key, Tally())
                t.total += 1
                t.found += ok
            rep.overall.total += 1
            rep.overall.found += ok
            if not ok and len(rep.missed_examples) < keep_examples:
                rep.missed_examples.append({"id": r.id, "type": g.type, "variant": g.variant, "text": g.text})
        rep.predictions += len(preds)
        for i, p in enumerate(preds):
            if i not in used and not any(g.type == p[2] and p[0] < g.end and g.start < p[1] for g in gold):
                rep.false_positives += 1
                rep.false_positives_by_type[p[2]] = rep.false_positives_by_type.get(p[2], 0) + 1
    return rep


def save_report(report: Report, out_prefix: str) -> tuple[str, str]:
    md, js = out_prefix + ".md", out_prefix + ".json"
    with open(md, "w", encoding="utf-8") as f:
        f.write(report.to_markdown() + "\n")
    with open(js, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    return md, js
