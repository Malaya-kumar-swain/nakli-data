# Nakli-Data

**Safe fake Indian personal data, labelled for testing PII detectors.**

Realistic bank chats, KYC requests and call-centre notes in English, Hindi, Hinglish and Odia, with fake Aadhaar, PAN, GSTIN, UPI, IFSC, phone, email and PIN code values inside. Every value is labelled with its exact position, so you can measure what your privacy tool catches and what it misses.

[![PyPI](https://img.shields.io/pypi/v/nakli-data)](https://pypi.org/project/nakli-data/) ![python](https://img.shields.io/badge/python-3.10%2B-blue) ![license](https://img.shields.io/badge/license-Apache--2.0-green) ![deps](https://img.shields.io/badge/core%20dependencies-0-brightgreen)

*Nakli* (नकली) means "fake" in Hindi.

## Why

Under India's DPDP Act, teams mask personal data before it reaches logs, analytics and AI models. To trust that masking, you need test data that looks like what Indian users actually type. Two problems get in the way:

- **Fake numbers that fail real checks.** Real Aadhaar numbers use the Verhoeff check digit and never start with 0 or 1. Validating detectors such as Presidio reject numbers that break these rules, so tests built on them say nothing. In our check, only 214 of 2,000 Aadhaar numbers from Faker 40.54.0's `en_IN` provider (11%) passed the Verhoeff check, about what chance alone gives.
- **Clean test data hides real-world failures.** Indian users write numbers in their own scripts (२३४५), copy-paste brings invisible characters, and attackers use look-alike letters. A detector that only sees tidy ASCII looks better than it is.

## 30-second demo

```bash
pip install nakli-data
nakli demo
```

From source: `git clone https://github.com/Malaya-kumar-swain/nakli-data && cd nakli-data && pip install -e .`

## Benchmark: how three detectors do on 700 Indian messages

700 messages, seed 7, spread evenly over 4 languages and 7 writing styles. Each detector is scored only on the types it says it supports. Run on 13 Nov 2026.

| Detector | Recall | Precision | Aadhaar | PAN | GSTIN | Phone | Indian-script digits | Invisible characters | Look-alike letters | Split across lines |
|---|---|---|---|---|---|---|---|---|---|---|
| Naive regex (ASCII-only) | 66% | 100% | 60% | 58% | 57% | 71% | 0% | 6% | 18% | 0% |
| [Vismriti](https://github.com/Malaya-kumar-swain/vismriti) 0.1.0 | 81% | 100% | 75% | 74% | 69% | 84% | 100% | 18% | 30% | 0% |
| [Vismriti](https://github.com/Malaya-kumar-swain/vismriti) 0.1.1 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| Presidio 2.2.366, default | 80% | 81% | 60% | 72% | 57% | 100% | 37% | 46% | 70% | 0% |
| Presidio 2.2.366, very weak matches dropped | 77% | 99.9% | 60% | 58% | 57% | 100% | 37% | 46% | 25% | 0% |

What it shows:

- **Every detector misses a number split across two lines.**
- **Invisible characters beat Aadhaar detection in all of them.**
- **Presidio misses Aadhaar and PAN written in Indian-script digits.** Its 37% on Indian digits comes from phone numbers alone. Reported upstream as [presidio#2481](https://github.com/data-privacy-stack/presidio/issues/2481).
- **Presidio's default settings flag ordinary 10-letter words as PAN.** For example, "Registered" is flagged with a very low score (0.01). That causes 224 false alarms here; dropping matches below 0.1 removes them. Its "hits" on look-alike PANs also come from that weak pattern.
- **Vismriti 0.1.0 handled Indian-script digits but not invisible characters, look-alike letters or line breaks.** Version 0.1.1 fixed all three after this benchmark found them. Both projects have the same author, and the benchmark was used while making the fixes, so read the 0.1.1 row as a regression test rather than an independent result.

How it was run: Presidio's pattern recognisers (Aadhaar, PAN, GSTIN, email, phone) were called directly, without an NLP model, so names were not scored for Presidio. Its context words, which can raise scores, also need that model. Results with a full Presidio setup may differ.

Reproduce:

```bash
nakli generate --n 700 --seed 7 --out bench.jsonl
nakli score --data bench.jsonl --detector regex
nakli score --data bench.jsonl --detector vismriti          # pip install vismriti
nakli score --data bench.jsonl --detector presidio          # pip install presidio-analyzer
nakli score --data bench.jsonl --detector presidio-strict
```

## What it generates

| Type | Rules followed |
|---|---|
| AADHAAR | 12 digits, first digit 2 to 9, Verhoeff check digit, no palindromes |
| PAN | 5 letters, 4 digits, 1 letter; 4th letter P (individual), 5th letter the surname's first letter |
| GSTIN | State code, PAN, entity number, Z, and the correct check character |
| UPI | `name.surname42@okaxis` style IDs on common handles |
| IFSC | Bank code, 0, then a 6-character branch code |
| PHONE | Indian mobile, starting 6 to 9 |
| EMAIL | Only reserved example domains (`example.com`, `example.org`, `example.net`) |
| PINCODE | 6 digits, first digit 1 to 8 |
| PERSON | Fictional combinations of common Indian first names and surnames, in Latin, Devanagari or Odia script |

**Languages:** English, Hinglish, Hindi (Devanagari) and Odia.
**Writing styles:** `plain`, `compact`, `hyphen`, `indic_digits`, `zero_width`, `homoglyph` (look-alike letters), `line_break`.

Each record looks like this:

```json
{"id": "nk-7-00012", "lang": "hi", "variant": "indic_digits",
 "text": "नमस्ते, मैं प्रिया दास हूँ। मेरा आधार नंबर २३४५ ६७८९ ०१२४ है ...",
 "entities": [{"type": "AADHAAR", "start": 43, "end": 57, "text": "२३४५ ६७८९ ०१२४",
               "value": "234567890124", "variant": "indic_digits"}]}
```

## Use it from Python

```python
from nakli import generate, score

records = generate(n=280, seed=7)                 # same seed, same data

def my_detector(text):                             # return (start, end, type) for each finding
    ...

report = score(records, my_detector, "my-detector", types=["AADHAAR", "PAN", "PHONE"])
print(report.to_markdown())
```

You can also score from the command line with `nakli score --detector mypackage.module:my_detector`. Add `--fail-below 0.9` to fail a CI pipeline when recall drops.

## Safety

- **Valid mode** (the default) makes values that pass the format and checksum rules, so validating detectors recognise them. A value can, by chance, equal a real person's number. Generate data on your own machine and do not publish large generated lists. This repository contains none.
- **Safe mode** (`--safe`) makes values that can never be real: Aadhaar numbers starting with 1 and a wrong check digit, an invalid PAN holder type, phone numbers starting with 5, and a fake UPI handle. Use it for demos and screenshots. Safe values fail validation, so they are not useful for testing validating detectors.
- Names are random pairings of common first names and surnames, and emails use reserved example domains.

## Limits

- PAN's last character is a check letter whose algorithm is not public, so PAN values follow the structure rules only.
- Five message templates per language is a starting point, not full coverage. Hindi, Hinglish and Odia templates welcome review by native speakers.
- Names are scored only for detectors that claim to find them.

## Related

- [Vismriti](https://github.com/Malaya-kumar-swain/vismriti): DPDP consent and erasure for RAG and AI agents, with an Indian PII masker
- [Kavach-Eval](https://github.com/Malaya-kumar-swain/kavach-eval): prompt-injection and data-leak tests in Indian languages
- [Agent-Pariksha](https://github.com/Malaya-kumar-swain/agent-pariksha): reliability tests for AI agents that take actions

## License

Apache-2.0
