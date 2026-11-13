"""Fake Indian identifiers that follow the real format and check-digit rules.

``valid`` mode (the default) produces values that pass format and checksum checks, so
PII detectors that validate checksums will recognise them. Such a value can, by chance,
equal a real person's number, so generate test data locally and do not publish large
generated lists. ``safe`` mode produces values that deliberately break a rule and can
never be real (useful for demos and screenshots).
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass

from .checksums import gstin_check_char, verhoeff_check_digit

# Fictional people: common first names and surnames, combined at random.
# (latin, devanagari, odia). Odia and Hindi spellings should be reviewed by native speakers.
FIRST_NAMES = [
    ("Aarav", "आरव", "ଆରବ"), ("Priya", "प्रिया", "ପ୍ରିୟା"), ("Rohan", "रोहन", "ରୋହନ"),
    ("Ananya", "अनन्या", "ଅନନ୍ୟା"), ("Vikram", "विक्रम", "ବିକ୍ରମ"), ("Sneha", "स्नेहा", "ସ୍ନେହା"),
    ("Arjun", "अर्जुन", "ଅର୍ଜୁନ"), ("Kavya", "काव्या", "କାବ୍ୟା"), ("Manoj", "मनोज", "ମନୋଜ"),
    ("Ritika", "रितिका", "ରିତିକା"), ("Sanjay", "संजय", "ସଞ୍ଜୟ"), ("Pooja", "पूजा", "ପୂଜା"),
    ("Debasish", "देबाशीष", "ଦେବାଶିଷ"), ("Smita", "स्मिता", "ସ୍ମିତା"),
]
SURNAMES = [
    ("Sharma", "शर्मा", "ଶର୍ମା"), ("Patel", "पटेल", "ପଟେଲ"), ("Das", "दास", "ଦାସ"),
    ("Mohanty", "मोहंती", "ମହାନ୍ତି"), ("Singh", "सिंह", "ସିଂହ"), ("Nayak", "नायक", "ନାୟକ"),
    ("Gupta", "गुप्ता", "ଗୁପ୍ତା"), ("Mishra", "मिश्रा", "ମିଶ୍ର"), ("Rao", "राव", "ରାଓ"),
]
_SCRIPT_INDEX = {"latin": 0, "devanagari": 1, "odia": 2}

UPI_HANDLES = ("okaxis", "oksbi", "okhdfcbank", "okicici", "ybl", "paytm", "ibl", "axl")
IFSC_BANKS = ("SBIN", "HDFC", "ICIC", "UTIB", "PUNB", "BARB", "CNRB", "UBIN", "KKBK", "IDIB")
PAN_INDIVIDUAL = "P"
GST_STATE_CODES = [f"{i:02d}" for i in range(1, 38)]
EMAIL_DOMAINS = ("example.com", "example.org", "example.net")  # reserved for examples (RFC 2606)


@dataclass(frozen=True)
class Person:
    first: tuple[str, str, str]
    last: tuple[str, str, str]

    def name(self, script: str = "latin") -> str:
        i = _SCRIPT_INDEX[script]
        return f"{self.first[i]} {self.last[i]}"


class Nakli:
    """Seeded generator, so the same seed always gives the same data."""

    def __init__(self, seed: int | None = None, safe: bool = False):
        self.rng = random.Random(seed)
        self.safe = safe

    def _digits(self, n: int) -> str:
        return "".join(self.rng.choice(string.digits) for _ in range(n))

    def person(self) -> Person:
        return Person(self.rng.choice(FIRST_NAMES), self.rng.choice(SURNAMES))

    def aadhaar(self) -> str:
        if self.safe:  # first digit 1 is never issued, and the check digit is deliberately wrong
            body = "1" + self._digits(10)
            return body + str((int(verhoeff_check_digit(body)) + 1) % 10)
        while True:
            body = self.rng.choice("23456789") + self._digits(10)
            number = body + verhoeff_check_digit(body)
            if number != number[::-1]:  # validators reject palindromes
                return number

    def pan(self, person: Person | None = None) -> str:
        letters = string.ascii_uppercase
        first3 = "".join(self.rng.choice(letters) for _ in range(3))
        holder_type = "X" if self.safe else PAN_INDIVIDUAL  # X is not a valid holder type
        initial = (person.last[0][0] if person else self.rng.choice(letters)).upper()
        return f"{first3}{holder_type}{initial}{self._digits(4)}{self.rng.choice(letters)}"

    def gstin(self, pan: str | None = None) -> str:
        pan = pan or self.pan()
        first14 = self.rng.choice(GST_STATE_CODES) + pan + self.rng.choice("123456789") + "Z"
        check = gstin_check_char(first14)
        if self.safe:
            check = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(check) + 1) % 36]
        return first14 + check

    def mobile(self) -> str:
        return ("5" if self.safe else self.rng.choice("6789")) + self._digits(9)  # Indian mobiles start 6-9

    def upi(self, person: Person | None = None) -> str:
        handle = "nakli" if self.safe else self.rng.choice(UPI_HANDLES)
        user = (person.first[0].lower() + "." + person.last[0].lower()) if person else "user"
        return f"{user}{self._digits(2)}@{handle}"

    def ifsc(self) -> str:
        return self.rng.choice(IFSC_BANKS) + "0" + self._digits(6)

    def email(self, person: Person | None = None) -> str:
        user = (person.first[0].lower() + "." + person.last[0].lower()) if person else "user"
        return f"{user}{self._digits(2)}@{self.rng.choice(EMAIL_DOMAINS)}"

    def pincode(self) -> str:
        return self.rng.choice("12345678") + self._digits(5)
