"""G3 reconciliation: our figures against official costings.

``pip-review reconcile --out reconciliation.csv`` reads ``results.json`` and
official costing CSVs, one schema for all of them::

    measure_id,fiscal_year,value_m,basis,source

``value_m`` must already be re-based to our basis (static, cash, fiscal year,
England and Wales, £m, positive is a cost); write each conversion in
``basis``. A reasons CSV (``measure_id,fiscal_year,cause_class,reason``)
gives the written reason for a gap.

It writes one row per official figure with the gap, and reports a problem
for any gap over ``GAP_LIMIT`` without a reason, any figure for a measure we
do not model, and any of our figures whose sign contradicts
``data_inputs/expected_effects.csv``.
"""

import csv
import json
from pathlib import Path

from pip_review.pipeline import REPO_ROOT

GAP_LIMIT = 0.10
CAUSE_CLASSES = (
    "parameter",
    "formula",
    "data_calibration",
    "basis",
    "timing_fiscal_calendar",
    "coverage",
    "interaction",
    "baseline_mismatch",
)
OFFICIAL_DIR = REPO_ROOT / "data_inputs" / "official"
EXPECTED = REPO_ROOT / "data_inputs" / "expected_effects.csv"
COLUMNS = (
    "measure_id",
    "fiscal_year",
    "ours_m",
    "official_m",
    "gap_m",
    "gap_pct",
    "official_basis",
    "official_source",
    "expected_direction",
    "sign_ok",
    "cause_class",
    "reason",
    "flag",
)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def sign_ok(direction: str, value: float | None) -> bool:
    if value is None or direction in ("", "either"):
        return True
    if direction == "cost":
        return value >= 0
    if direction == "saving":
        return value <= 0
    return True


def run(
    results_path: Path,
    official_paths: list[Path] | None,
    reasons_path: Path | None,
    out_path: Path,
    expected_path: Path = EXPECTED,
):
    results = json.loads(Path(results_path).read_text())
    ours = {}
    for measure in results["measures"]:
        for row in measure.get("budgetary_impact") or []:
            ours[(measure["id"], row["fiscal_year"])] = row["value_m"]
    modelled = {m["id"] for m in results["measures"] if m.get("budgetary_impact")}
    expected = {r["measure_id"]: r for r in _read(expected_path)}
    reasons = {
        (r["measure_id"], r["fiscal_year"]): r
        for r in (_read(reasons_path) if reasons_path else [])
    }
    paths = (
        official_paths
        if official_paths
        else sorted(OFFICIAL_DIR.glob("costings_*.csv"))
    )

    problems: list[str] = []
    rows: list[dict[str, object]] = []
    for path in paths:
        for official in _read(path):
            key = (official["measure_id"], official["fiscal_year"])
            mine = ours.get(key)
            value = float(official["value_m"])
            gap = None if mine is None else mine - value
            gap_pct = None if gap is None or value == 0 else round(gap / abs(value), 4)
            direction = expected.get(official["measure_id"], {}).get(
                "expected_direction", ""
            )
            reason = reasons.get(key, {})
            cause = reason.get("cause_class", "")
            flag = ""
            if official["measure_id"] not in modelled:
                flag = "not modelled: record as a ledger line"
            elif (
                gap_pct is not None
                and abs(gap_pct) > GAP_LIMIT
                and not (reason.get("reason", "").strip() and cause in CAUSE_CLASSES)
            ):
                flag = "gap over 10% without a reason and cause class"
            if cause and cause not in CAUSE_CLASSES:
                flag = f"unknown cause class {cause!r}"
            ok = sign_ok(direction, mine)
            if not ok:
                flag = flag or f"sign contradicts expected {direction}"
            if flag and not flag.startswith("not modelled"):
                problems.append(f"{key[0]} {key[1]}: {flag}")
            rows.append(
                {
                    "measure_id": key[0],
                    "fiscal_year": key[1],
                    "ours_m": mine,
                    "official_m": value,
                    "gap_m": gap,
                    "gap_pct": gap_pct,
                    "official_basis": official.get("basis", ""),
                    "official_source": official.get("source", ""),
                    "expected_direction": direction,
                    "sign_ok": ok,
                    "cause_class": cause,
                    "reason": reason.get("reason", ""),
                    "flag": flag,
                }
            )
    for (measure_id, year), value in ours.items():
        direction = expected.get(measure_id, {}).get("expected_direction", "")
        if not sign_ok(direction, value) and not any(
            r["measure_id"] == measure_id and r["fiscal_year"] == year for r in rows
        ):
            problems.append(
                f"{measure_id} {year}: our sign contradicts expected {direction}"
            )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows, problems
