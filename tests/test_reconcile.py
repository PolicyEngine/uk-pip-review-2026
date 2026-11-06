import csv
import json

from pip_review import reconcile
from pip_review.pipeline import build_placeholder_results


def _write(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_gap_over_ten_percent_needs_a_reason(tmp_path):
    results = build_placeholder_results()
    (tmp_path / "results.json").write_text(json.dumps(results))
    measure = next(m for m in results["measures"] if m["budgetary_impact"])
    ours = measure["budgetary_impact"][0]
    official = tmp_path / "costings_test.csv"
    _write(
        official,
        [
            {
                "measure_id": measure["id"],
                "fiscal_year": ours["fiscal_year"],
                "value_m": ours["value_m"] * 1.5,
                "basis": "re-based to static cash E&W",
                "source": "invented fixture",
            }
        ],
    )
    out = tmp_path / "reconciliation.csv"
    rows, problems = reconcile.run(tmp_path / "results.json", [official], None, out)
    assert len(rows) == 1 and problems
    assert out.exists()

    reasons = tmp_path / "reasons.csv"
    _write(
        reasons,
        [
            {
                "measure_id": measure["id"],
                "fiscal_year": ours["fiscal_year"],
                "cause_class": "basis",
                "reason": "official figure includes behaviour",
            }
        ],
    )
    rows, problems = reconcile.run(tmp_path / "results.json", [official], reasons, out)
    assert problems == []


def test_sign_check_against_expected_effects():
    assert reconcile.sign_ok("cost", 10)
    assert not reconcile.sign_ok("cost", -10)
    assert not reconcile.sign_ok("saving", 10)
    assert reconcile.sign_ok("either", -10)
