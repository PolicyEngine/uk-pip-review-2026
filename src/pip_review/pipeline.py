"""Generate ``data/results.json``, the one file the page reads.

Two modes:
- ``placeholder`` (the only mode in this template): writes the full schema
  with illustrative figures for the computable measures, ``null`` for every
  measure that is not computable, ``status: "placeholder"`` and the banner
  text. No data are loaded and no simulation is built.
- ``model``: wired on the day. It will run each publishable measure through
  ``policyengine.tax_benefit_models.uk.managed_microsimulation`` on the
  frozen dataset, masked to England and Wales (issue #1). It is not
  implemented in the template and raises.

Basis, declared once (``BASIS``): static, cash, fiscal year, England and
Wales, £m, positive is a cost to the Exchequer.
"""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from pip_review import data_limits, model_limits, publication
from pip_review.household import PRESETS, pip_award
from pip_review.reforms import REFORMS
from pip_review.years import BASE_YEAR, POLICY_YEARS, fiscal_label

SCHEMA_VERSION = 1
BANNER = "Pre-release template: placeholder figures, not PolicyEngine estimates"

BASIS = {
    "cost": "Static, cash, fiscal year, England and Wales, £ million; positive is a cost to the Exchequer",
    "distribution": "Average change in household net income by equivalised household income decile, England and Wales",
    "behaviour": "No behavioural response",
}

ENGINE = {
    "policyengine": "6.11.1",
    "policyengine_uk": "2.151.0",
    "dataset": "microcosm-uk-2024-25-national-20261025T091414Z-a6299504",
    "validated_pair": False,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SPENDING = REPO_ROOT / "data_inputs" / "official" / "dwp_pip_spending_spring_2026.csv"


def _rng(measure_id: str) -> np.random.Generator:
    seed = int(hashlib.sha256(measure_id.encode()).hexdigest()[:8], 16)
    return np.random.default_rng(seed)


def _placeholder_figures(measure_id: str) -> dict[str, Any]:
    """Illustrative numbers of the right shape. Not estimates."""
    rng = _rng(measure_id)
    scale = float(rng.uniform(200, 900))
    budgetary = [
        {"year": year, "fiscal_year": fiscal_label(year), "value_m": round(scale * (1 + 0.06 * i), 0)}
        for i, year in enumerate(POLICY_YEARS)
    ]
    shape = np.array([0.6, 1.0, 1.1, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.3])
    decile = [
        {
            "decile": d + 1,
            "avg_change_gbp": round(float(shape[d] * rng.uniform(40, 60)), 0),
            "pct_change": round(float(shape[d] * rng.uniform(0.1, 0.3)), 2),
        }
        for d in range(10)
    ]
    winners_losers = [
        {
            "decile": d + 1,
            "gain_more_5": round(float(rng.uniform(0, 4)), 1),
            "gain_less_5": round(float(rng.uniform(2, 10)), 1),
            "no_change": 0.0,
            "lose_less_5": 0.0,
            "lose_more_5": 0.0,
        }
        for d in range(10)
    ]
    for row in winners_losers:
        row["no_change"] = round(100 - row["gain_more_5"] - row["gain_less_5"], 1)
    return {
        "budgetary_impact": budgetary,
        "decile": decile,
        "winners_losers": winners_losers,
        "people_affected_k": round(scale * 1.4, 0),
    }


def _official_spending() -> list[dict[str, Any]]:
    with OFFICIAL_SPENDING.open() as handle:
        return [
            {"year": int(row["year"]), "fiscal_year": row["fiscal_year"], "dwp_m": float(row["pip_spend_m"])}
            for row in csv.DictReader(handle)
        ]


def build_placeholder_results() -> dict[str, Any]:
    measures = []
    for reform in REFORMS:
        entry = reform.summary()
        entry["status"] = publication.status_of(reform)
        entry["receipt"] = publication.receipt(reform)
        if reform.computable:
            entry.update(_placeholder_figures(reform.id))
        else:
            entry.update(
                {
                    "budgetary_impact": None,
                    "decile": None,
                    "winners_losers": None,
                    "people_affected_k": None,
                }
            )
        measures.append(entry)

    computable = [m for m in measures if m["computable"]]
    totals = {
        year: sum(
            next(r["value_m"] for r in m["budgetary_impact"] if r["year"] == year)
            for m in computable
        )
        for year in POLICY_YEARS
    }
    spending_path = []
    for row in _official_spending():
        reformed = row["dwp_m"] + totals.get(row["year"], 0.0)
        spending_path.append({**row, "reformed_m": round(reformed, 0)})

    rates_by_measure = {
        reform.id: {
            path: values[str(POLICY_YEARS[0])]
            for path, values in (reform.parameter_changes or {}).items()
            if path.endswith(("standard", "enhanced")) and "points" not in path
        }
        for reform in REFORMS
        if reform.computable
    }
    households = [
        {
            "id": preset["id"],
            "label": preset["label"],
            "baseline_pip": pip_award(preset),
            "reform_pip": {mid: pip_award(preset, rates) for mid, rates in rates_by_measure.items()},
        }
        for preset in PRESETS
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "placeholder",
        "banner": BANNER,
        "engine": ENGINE,
        "basis": BASIS,
        "base_year": BASE_YEAR,
        "years": POLICY_YEARS,
        "measures": measures,
        "spending_path": spending_path,
        "households": households,
        "data_limits": [
            {"key": limit.key, "missing_input": limit.missing_input, "reason": limit.reason, "issue": limit.issue}
            for limit in data_limits.LIMITS
        ],
        "model_limits": [
            {"key": limit.key, "reason": limit.reason, "issue": limit.issue}
            for limit in model_limits.LIMITS
        ],
    }


def build_model_results() -> dict[str, Any]:
    raise NotImplementedError(
        "Model mode is wired on the day: freeze the engine and data pair (G0), "
        "take the heavy-run lock, and run each publishable measure through "
        "managed_microsimulation masked to England and Wales."
    )


def write_results(results: dict[str, Any], *paths: Path) -> None:
    errors = publication.validate_public(results)
    if errors:
        raise ValueError("Results fail the publication check:\n" + "\n".join(errors))
    text = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


