"""Check-digit algorithms for Indian identifiers.

- Aadhaar uses the Verhoeff algorithm (not Luhn).
- GSTIN uses a base-36 weighted check character.
"""

from __future__ import annotations

_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_valid(digits: str) -> bool:
    """True if a string of ASCII digits passes the Verhoeff check."""
    if not digits.isascii() or not digits.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(digits: str) -> str:
    """The digit to append so that the whole number passes the Verhoeff check."""
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


_B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_check_char(first14: str) -> str:
    """Check character for the first 14 characters of a GSTIN."""
    total = 0
    for i, ch in enumerate(first14):
        product = _B36.index(ch) * (1 if i % 2 == 0 else 2)
        total += product // 36 + product % 36
    return _B36[(36 - total % 36) % 36]


def gstin_valid(gstin: str) -> bool:
    return len(gstin) == 15 and all(ch in _B36 for ch in gstin) and gstin_check_char(gstin[:14]) == gstin[14]


def aadhaar_valid(number: str) -> bool:
    """Format and checksum rules: 12 ASCII digits, first digit 2-9, Verhoeff-valid."""
    return len(number) == 12 and number[:1] in "23456789" and verhoeff_valid(number)
