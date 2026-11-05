import json
from pathlib import Path

from pip_review import publication, sign_off
from pip_review.pipeline import BANNER, build_placeholder_results
from pip_review.reforms import REFORMS

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_holds_every_placeholder():
    entries = publication.manifest(REFORMS)
    assert len(entries) == len(REFORMS)
    assert not any(entry["status"] == "published" for entry in entries)
    for entry, reform in zip(entries, REFORMS):
        expected = "held-placeholder" if reform.computable else reform.route.value
        assert entry["status"] == expected


def test_sign_off_required_before_the_event():
    assert sign_off.REQUIRED is True


def test_receipt_is_stable_and_specific():
    a, b = REFORMS[4], REFORMS[7]
    assert publication.receipt(a) == publication.receipt(a)
    assert publication.receipt(a) != publication.receipt(b)
    assert len(publication.receipt(a)) == 64


def test_floor_blanks_small_cells_and_drops_counts():
    rows = [{"decile": 1, "value": 5.0, "n_households": 9}, {"decile": 2, "value": 6.0, "n_households": 40}]
    out = publication.apply_floor(rows, ["value"])
    assert out[0]["value"] is None and out[0]["suppressed"] is True
    assert out[1]["value"] == 6.0
    assert all("n_households" not in row for row in out)


def test_placeholder_results_pass_validation():
    results = build_placeholder_results()
    assert publication.validate_public(results) == []
    assert results["status"] == "placeholder"
    assert results["banner"] == BANNER


def test_not_computable_measures_never_carry_zero():
    results = build_placeholder_results()
    for measure in results["measures"]:
        if not measure["computable"]:
            assert measure["budgetary_impact"] is None
            assert measure["decile"] is None


def test_validation_catches_identifiers_and_zero_for_limited():
    results = build_placeholder_results()
    results["households"][0]["household_id"] = 1
    limited = next(m for m in results["measures"] if not m["computable"])
    limited["budgetary_impact"] = [{"year": 2027, "value_m": 0}]
    errors = publication.validate_public(results)
    assert any("identifier" in e for e in errors)
    assert any("never £0" in e for e in errors)


def test_validation_requires_status_and_banner():
    results = build_placeholder_results()
    results["status"] = "final"
    assert publication.validate_public(results)
    results["status"] = "placeholder"
    results["banner"] = ""
    assert publication.validate_public(results)


def test_committed_results_match_generator():
    generated = build_placeholder_results()
    for path in (ROOT / "data" / "results.json", ROOT / "dashboard" / "public" / "data" / "results.json"):
        assert json.loads(path.read_text()) == generated, f"{path} is stale: run pip-review generate"
