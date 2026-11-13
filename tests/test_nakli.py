import json

import pytest

from nakli import (VARIANTS, Nakli, aadhaar_valid, generate, gstin_check_char, gstin_valid, load_jsonl, normalise,
                   render, save_jsonl, score, verhoeff_check_digit, verhoeff_valid)
from nakli.__main__ import main
from nakli.adapters import load_detector, regex_baseline


def test_verhoeff_and_gstin_known_values():
    assert verhoeff_check_digit("23456789012") == "4"
    assert verhoeff_valid("234567890124") and not verhoeff_valid("234567890125")
    assert gstin_valid("27AAPFU0939F1ZV")  # widely published sample GSTIN
    assert not gstin_valid("27AAPFU0939F1ZW")
    assert gstin_check_char("27AAPFU0939F1Z") == "V"


def test_valid_mode_identifiers_pass_their_rules():
    fake = Nakli(seed=1)
    for _ in range(200):
        a = fake.aadhaar()
        assert aadhaar_valid(a) and a != a[::-1]
        assert gstin_valid(fake.gstin())
        p = fake.person()
        pan = fake.pan(p)
        assert len(pan) == 10 and pan[3] == "P" and pan[4] == p.last[0][0]
        assert fake.mobile()[0] in "6789"


def test_safe_mode_values_can_never_be_real():
    fake = Nakli(seed=1, safe=True)
    for _ in range(200):
        assert not aadhaar_valid(fake.aadhaar())
        assert not gstin_valid(fake.gstin())
        assert fake.pan()[3] == "X"
        assert fake.mobile()[0] == "5"
        assert fake.upi().endswith("@nakli")


def test_same_seed_same_data():
    assert [r.text for r in generate(20, seed=5)] == [r.text for r in generate(20, seed=5)]
    assert [r.text for r in generate(20, seed=5)] != [r.text for r in generate(20, seed=6)]


def test_labels_point_at_the_exact_text():
    for r in generate(280, seed=9):
        for e in r.entities:
            assert r.text[e.start:e.end] == e.text
            if e.type != "PERSON":
                assert normalise(e.text).replace(" ", "").replace("-", "").replace("\n", "").replace("+91", "") \
                    == e.value


def test_languages_and_variants_are_all_covered():
    records = generate(len(VARIANTS) * 4, seed=2)
    assert {r.lang for r in records} == {"en", "hinglish", "hi", "or"}
    assert {r.variant for r in records} == set(VARIANTS)


def test_render_tricks():
    assert render("234567890124", "AADHAAR", "indic_digits", "odia")[0] == "୨୩୪୫ ୬୭୮୯ ୦୧୨୪"
    shown, applied = render("ABCPE1234F", "PAN", "homoglyph")
    assert shown != "ABCPE1234F" and normalise(shown) == "ABCPE1234F" and applied == "homoglyph"
    assert render("ABCPE1234F", "PAN", "line_break") == ("ABCPE1234F", "plain")  # not applicable: falls back


def test_unknown_language_or_variant_is_rejected():
    with pytest.raises(ValueError):
        generate(5, langs=["xx"])
    with pytest.raises(ValueError):
        generate(5, variants=["nope"])


def test_perfect_detector_scores_100_and_empty_detector_scores_0():
    records = generate(70, seed=4)
    by_text = {r.text: r for r in records}
    perfect = lambda text: [(e.start, e.end, e.type) for e in by_text[text].entities]
    rep = score(records, perfect, "perfect")
    assert rep.overall.recall == 1.0 and rep.precision == 1.0 and rep.false_positives == 0
    rep = score(records, lambda text: [], "empty")
    assert rep.overall.recall == 0.0 and rep.overall.total > 0


def test_false_alarms_and_wrong_types_are_counted():
    records = generate(14, seed=4)
    rep = score(records, lambda text: [(0, 3, "AADHAAR")], "noisy", types=["AADHAAR"])
    assert rep.false_positives > 0 and rep.precision < 1.0
    by_text = {r.text: r for r in records}
    swapped = lambda text: [(e.start, e.end, "PAN") for e in by_text[text].entities if e.type == "AADHAAR"]
    assert score(records, swapped, "swapped", types=["AADHAAR"]).overall.found == 0


def test_a_crashing_detector_is_never_a_pass():
    def boom(text):
        raise RuntimeError("detector down")
    rep = score(generate(10, seed=1), boom, "boom")
    assert rep.errored == 10 and rep.overall.found == 0
    assert "crashed" in rep.to_markdown()


def test_regex_baseline_misses_indian_digits_and_is_scored_on_its_own_types():
    rep = score(generate(140, seed=3), regex_baseline, "regex")
    assert set(rep.types) == set(regex_baseline.types)
    assert rep.by_variant["indic_digits"].recall == 0.0
    assert rep.by_variant["compact"].recall == 1.0


def test_jsonl_round_trip(tmp_path):
    records = generate(12, seed=8)
    path = str(tmp_path / "d.jsonl")
    assert save_jsonl(records, path) == 12
    back = load_jsonl(path)
    assert [r.to_json() for r in back] == [r.to_json() for r in records]
    json.loads(open(path, encoding="utf-8").readline())


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "d.jsonl")
    assert main(["generate", "--n", "28", "--out", out]) == 0
    assert main(["score", "--data", out, "--detector", "regex", "--out", str(tmp_path / "r")]) == 0
    assert (tmp_path / "r.md").exists() and (tmp_path / "r.json").exists()
    assert main(["score", "--data", out, "--fail-below", "0.99"]) == 1
    assert main(["validate", "2345 6789 0124"]) == 0 and "valid" in capsys.readouterr().out
    assert main(["demo"]) == 0
    with pytest.raises(ValueError):
        load_detector("unknown-detector")
