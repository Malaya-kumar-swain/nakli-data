"""Build labelled test messages: realistic text with fake personal data and exact positions."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Iterable

from .identifiers import Nakli
from .render import VARIANTS, render
from .templates import DIGIT_SCRIPT, LANGS, NAME_SCRIPT, TEMPLATES

_SLOT = re.compile(r"\{([A-Z]+)\}")


@dataclass
class Entity:
    type: str
    start: int
    end: int
    text: str   # exactly as it appears in the message
    value: str  # the plain ASCII value
    variant: str


@dataclass
class Record:
    id: str
    lang: str
    variant: str
    text: str
    entities: list[Entity] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @staticmethod
    def from_json(line: str) -> "Record":
        d = json.loads(line)
        return Record(d["id"], d["lang"], d["variant"], d["text"], [Entity(**e) for e in d["entities"]])


def generate(n: int = 100, seed: int = 7, langs: Iterable[str] = LANGS,
             variants: Iterable[str] = VARIANTS, safe: bool = False) -> list[Record]:
    """Make ``n`` records. Languages and variants are spread evenly; the same seed gives the same data."""
    langs, variants = list(langs), list(variants)
    for lang in langs:
        if lang not in TEMPLATES:
            raise ValueError(f"unknown language {lang!r}; choose from {', '.join(LANGS)}")
    for v in variants:
        if v not in VARIANTS:
            raise ValueError(f"unknown variant {v!r}; choose from {', '.join(VARIANTS)}")
    fake = Nakli(seed, safe=safe)
    records = []
    for i in range(n):
        variant = variants[i % len(variants)]
        lang = langs[(i // len(variants)) % len(langs)]
        template = fake.rng.choice(TEMPLATES[lang])
        person = fake.person()
        pan = fake.pan(person)
        values = {"PERSON": person.name(NAME_SCRIPT[lang]), "PAN": pan, "AADHAAR": fake.aadhaar(),
                  "GSTIN": fake.gstin(), "UPI": fake.upi(person), "IFSC": fake.ifsc(),
                  "PHONE": fake.mobile(), "EMAIL": fake.email(person), "PINCODE": fake.pincode()}
        text, entities, pos = "", [], 0
        for m in _SLOT.finditer(template):
            text += template[pos:m.start()]
            etype = m.group(1)
            shown, applied = render(values[etype], etype, variant, DIGIT_SCRIPT[lang])
            entities.append(Entity(etype, len(text), len(text) + len(shown), shown, values[etype], applied))
            text += shown
            pos = m.end()
        text += template[pos:]
        records.append(Record(f"nk-{seed}-{i:05d}", lang, variant, text, entities))
    return records


def save_jsonl(records: Iterable[Record], path: str) -> int:
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.to_json() + "\n")
            count += 1
    return count


def load_jsonl(path: str) -> list[Record]:
    with open(path, encoding="utf-8") as f:
        return [Record.from_json(line) for line in f if line.strip()]
