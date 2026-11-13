"""Ready-made detectors to score: a naive regex baseline, Vismriti and Presidio.

Vismriti and Presidio are optional; install them only if you want to score them.
"""

from __future__ import annotations

import importlib
import re
from typing import Callable, Iterable

_BASELINE = {
    "AADHAAR": re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", re.ASCII),
    "PAN": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.ASCII),
    "GSTIN": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", re.ASCII),
    "IFSC": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", re.ASCII),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", re.ASCII),
    "PHONE": re.compile(r"(?:\+91[ -]?)?\b[6-9]\d{4}[ -]?\d{5}\b", re.ASCII),
}


def regex_baseline(text: str) -> list[tuple[int, int, str]]:
    """A typical first attempt: ASCII-only patterns, no checksums, no normalisation."""
    return [(m.start(), m.end(), kind) for kind, pattern in _BASELINE.items() for m in pattern.finditer(text)]


regex_baseline.types = tuple(_BASELINE)  # the types this detector claims to find; only these are scored


def vismriti_detector() -> Callable[[str], Iterable]:
    from vismriti.pii import IndianPIIDetector  # pip install vismriti

    detector = IndianPIIDetector()

    def detect(text: str):
        return [(f.start, f.end, f.kind) for f in detector.detect(text)]

    detect.types = ("AADHAAR", "PAN", "GSTIN", "IFSC", "EMAIL", "UPI", "PHONE")
    return detect


def presidio_patterns(min_score: float = 0.0) -> Callable[[str], Iterable]:
    """Presidio's pattern-based recognisers for these types, run directly (no NLP model needed).
    PERSON detection in Presidio needs a spaCy model, so PERSON is not scored with this adapter.
    ``min_score`` drops low-confidence matches; Presidio's own default keeps everything (0.0).
    Without an NLP model, Presidio's context words cannot raise scores, so weak patterns stay weak."""
    from presidio_analyzer.predefined_recognizers import (  # pip install presidio-analyzer
        EmailRecognizer, InAadhaarRecognizer, InGstinRecognizer, InPanRecognizer, PhoneRecognizer)

    recognisers = [InAadhaarRecognizer(), InPanRecognizer(), InGstinRecognizer(), EmailRecognizer(),
                   PhoneRecognizer(supported_regions=("IN",))]

    def detect(text: str):
        out = []
        for rec in recognisers:
            for res in rec.analyze(text, rec.supported_entities, None) or []:
                if res.score >= min_score:
                    out.append((res.start, res.end, res.entity_type))
        return out

    detect.types = ("AADHAAR", "PAN", "GSTIN", "EMAIL", "PHONE")
    return detect


BUILT_IN = {"regex": lambda: regex_baseline, "vismriti": vismriti_detector, "presidio": presidio_patterns,
            "presidio-strict": lambda: presidio_patterns(min_score=0.1)}


def load_detector(spec: str) -> Callable[[str], Iterable]:
    """``regex``, ``vismriti``, ``presidio``, ``presidio-strict`` (drops Presidio's very weak matches, score below 0.1), or ``package.module:function``."""
    if spec in BUILT_IN:
        return BUILT_IN[spec]()
    if ":" in spec:
        module, func = spec.split(":", 1)
        return getattr(importlib.import_module(module), func)
    raise ValueError(f"unknown detector {spec!r}: use {', '.join(BUILT_IN)} or module:function")
