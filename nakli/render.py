"""How an identifier is written inside text: the plain form and the tricky real-world forms."""

from __future__ import annotations

ZWSP = "​"  # zero-width space: invisible, but breaks naive pattern matching
DIGIT_ZERO = {"devanagari": 0x0966, "bengali": 0x09E6, "odia": 0x0B66, "tamil": 0x0BE6,
              "telugu": 0x0C66, "kannada": 0x0CE6, "gujarati": 0x0AE6, "gurmukhi": 0x0A66}
# Cyrillic letters that look identical to Latin ones.
HOMOGLYPHS = {"A": "А", "B": "В", "C": "С", "E": "Е", "H": "Н", "K": "К", "M": "М", "O": "О",
              "P": "Р", "T": "Т", "X": "Х", "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х"}

VARIANTS = ("plain", "compact", "hyphen", "indic_digits", "zero_width", "homoglyph", "line_break")


def to_script_digits(text: str, script: str) -> str:
    zero = DIGIT_ZERO[script]
    return "".join(chr(zero + int(ch)) if ch.isascii() and ch.isdigit() else ch for ch in text)


def _homoglyph(text: str) -> str:
    """Swap up to two letters for look-alikes, so the text still reads the same."""
    out, swapped = [], 0
    for ch in text:
        if swapped < 2 and ch in HOMOGLYPHS:
            out.append(HOMOGLYPHS[ch])
            swapped += 1
        else:
            out.append(ch)
    return "".join(out)


def _middle(text: str, insert: str) -> str:
    mid = len(text) // 2
    return text[:mid] + insert + text[mid:]


def render(value: str, etype: str, variant: str, digit_script: str = "devanagari") -> tuple[str, str]:
    """Return (text as written, variant actually applied). Variants that make no sense
    for a type (for example look-alike letters in an all-digit number) fall back to plain."""
    if etype == "AADHAAR":
        groups = [value[0:4], value[4:8], value[8:12]]
        forms = {
            "plain": " ".join(groups),
            "compact": value,
            "hyphen": "-".join(groups),
            "indic_digits": to_script_digits(" ".join(groups), digit_script),
            "zero_width": ZWSP.join(groups),
            "line_break": f"{groups[0]} {groups[1]}\n{groups[2]}",
        }
    elif etype == "PHONE":
        forms = {
            "plain": f"+91 {value[:5]} {value[5:]}",
            "compact": value,
            "hyphen": f"{value[:5]}-{value[5:]}",
            "indic_digits": to_script_digits(f"{value[:5]} {value[5:]}", digit_script),
            "zero_width": _middle(value, ZWSP),
        }
    elif etype in ("PAN", "GSTIN", "IFSC"):
        forms = {
            "plain": value,
            "indic_digits": to_script_digits(value, digit_script),
            "zero_width": _middle(value, ZWSP),
            "homoglyph": _homoglyph(value),
        }
    elif etype in ("UPI", "EMAIL"):
        forms = {"plain": value, "homoglyph": _homoglyph(value), "zero_width": _middle(value, ZWSP)}
    elif etype == "PINCODE":
        forms = {"plain": value, "hyphen": f"{value[:3]} {value[3:]}",
                 "indic_digits": to_script_digits(value, digit_script)}
    else:  # PERSON and anything else stays as written
        forms = {"plain": value}
    if variant in forms:
        return forms[variant], variant
    return forms["plain"], "plain"


def normalise(text: str) -> str:
    """Undo every trick above: what a robust detector should see."""
    out = []
    reverse = {v: k for k, v in HOMOGLYPHS.items()}
    zeros = list(DIGIT_ZERO.values())
    for ch in text:
        if ch == ZWSP:
            continue
        code = ord(ch)
        digit = next((str(code - z) for z in zeros if z <= code <= z + 9), None)
        out.append(digit or reverse.get(ch, ch))
    return "".join(out)
