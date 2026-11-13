"""Nakli-Data: safe fake Indian personal data, labelled for testing PII detectors."""

from .checksums import aadhaar_valid, gstin_check_char, gstin_valid, verhoeff_check_digit, verhoeff_valid
from .generate import Entity, Record, generate, load_jsonl, save_jsonl
from .identifiers import Nakli, Person
from .render import VARIANTS, normalise, render
from .score import Report, save_report, score
from .templates import LANGS

__version__ = "0.1.0"
__all__ = ["Nakli", "Person", "Entity", "Record", "generate", "save_jsonl", "load_jsonl", "score", "save_report",
           "Report", "render", "normalise", "VARIANTS", "LANGS", "aadhaar_valid", "gstin_valid", "gstin_check_char",
           "verhoeff_valid", "verhoeff_check_digit", "__version__"]
