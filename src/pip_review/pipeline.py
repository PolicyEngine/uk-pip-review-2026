"""Generate ``data/results.json``, the one file the page reads.

Two modes:
- ``placeholder``: writes the full schema with illustrative figures for the
  computable measures, ``null`` for every measure that is not computable and
  for the tables only a model run fills, and the banner. No data are loaded
  and no simulation is built.
- ``model``: runs current law, each computable measure and the package of
  all of them through ``policyengine_uk.Microsimulation`` on the pinned
  Microcosm build (``data_build.DATA_BUILD``; or a named file for tests), one simulation per process
  (``pip_review.model_run``), inside the heavy-run lock. ``pip_review.aggregate``
  builds the England and Wales tables and applies the disclosure floor.

Status and banner come from ``publication.STATUSES``. Basis, declared once
(``BASIS``): static, cash, fiscal year, England and Wales, £m, positive is a
cost to the Exchequer.
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np

from pip_review import data_limits, model_limits, publication
from pip_review.data_build import DATA_BUILD, LABEL
from pip_review.household import PRESETS, pip_award
from pip_review.reforms import CURRENT_LAW_RATES, REFORMS
from pip_review.years import BASE_YEAR, POLICY_YEARS, fiscal_label

SCHEMA_VERSION = 2
# Kept for callers of the template: the placeholder banner text.
BANNER = publication.DEFAULT_BANNERS["placeholder"]

BASIS = {
    "cost": "Static, cash, fiscal year, England and Wales, £ million; positive is a cost to the Exchequer",
    "distribution": "Average change in household net income by equivalised household income decile, England and Wales, in the last policy year",
    "behaviour": "No behavioural response",
}

# The pinned pair (data_build.DATA_BUILD): the Microcosm build and the
# policyengine-uk version it was built and certified on. No policyengine.py
# release covers it. Model mode records what each run loaded and refuses to
# run if it differs from this record.
CERTIFIED_BUNDLE = {
    "model_version": DATA_BUILD.engine,
    "dataset_build_id": DATA_BUILD.id,
    "runtime_dataset_sha256": DATA_BUILD.sha256,
}
PIP_VALIDATION = "pending (#1, #4)"

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SPENDING = (
    REPO_ROOT / "data_inputs" / "official" / "dwp_pip_spending_spring_2026.csv"
)
LOCK_FILE = REPO_ROOT / "uv.lock"

# Placeholder only: illustrative England and Wales recipients by award, in
# thousands, roughly in proportion to the DWP caseload. Not DWP figures; used
# so placeholder costs have the right sign and order of magnitude.
PLACEHOLDER_RECIPIENTS_K = {
    "gov.dwp.pip.daily_living.standard": 1_700,
    "gov.dwp.pip.daily_living.enhanced": 2_100,
    "gov.dwp.pip.mobility.standard": 1_000,
    "gov.dwp.pip.mobility.enhanced": 1_500,
}
# Placeholder only: share of each decile's people with PIP (lower deciles more).
PLACEHOLDER_DECILE_SHAPE = (1.4, 1.6, 1.5, 1.3, 1.1, 0.9, 0.8, 0.6, 0.5, 0.3)
WEEKS = 52


def locked_versions() -> dict[str, str | None]:
    """policyengine, policyengine-uk and policyengine-core versions in uv.lock
    (policyengine is None: no policyengine.py release covers the pair)."""
    text = LOCK_FILE.read_text()
    out = {}
    for package in ("policyengine", "policyengine-uk", "policyengine-core"):
        match = re.search(rf'name = "{re.escape(package)}"\nversion = "([^"]+)"', text)
        out[package.replace("-", "_")] = match.group(1) if match else None
    return out


def _installed(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def engine_record(installed: bool = False) -> dict[str, Any]:
    """The engine block. Placeholder mode reads uv.lock; model mode the install."""
    if installed:
        versions = {
            key: _installed(key.replace("_", "-"))
            for key in ("policyengine", "policyengine_uk", "policyengine_core")
        }
    else:
        versions = locked_versions()
    return {
        **versions,
        "dataset": DATA_BUILD.id,
        "dataset_sha256": DATA_BUILD.sha256,
        "certified_pair": True,
        "label": LABEL,
        "pip_validation": PIP_VALIDATION,
    }


def _rate_deltas(reform, year: int) -> dict[str, float]:
    """Weekly change against current law in one year, for each rate moved."""
    law = CURRENT_LAW_RATES[year]
    return {
        path: values[str(year)] - law[path]
        for path, values in (reform.parameter_changes or {}).items()
        if path in law
    }


def _placeholder_figures(reform) -> dict[str, Any]:
    """Illustrative numbers that follow each measure's signs. Not estimates.

    Cost is recipients x change in the weekly rate x 52 for each rate the
    measure moves; gains and losses follow the sign of each rate change.
    """

    def cost_m(year):
        return sum(
            PLACEHOLDER_RECIPIENTS_K[path] * 1e3 * delta * WEEKS / 1e6
            for path, delta in _rate_deltas(reform, year).items()
        )

    budgetary = [
        {"year": year, "value_m": round(cost_m(year), 0)} for year in POLICY_YEARS
    ]
    last = POLICY_YEARS[-1]
    deltas = _rate_deltas(reform, last)
    total_m = cost_m(last)
    shape = np.array(PLACEHOLDER_DECILE_SHAPE)
    shape = shape / shape.sum()
    households_k_per_decile = 2_600  # illustrative: about 26m households
    decile = []
    for d in range(10):
        avg = total_m * 1e6 * shape[d] / (households_k_per_decile * 1e3)
        decile.append(
            {
                "decile": d + 1,
                "avg_change_gbp": round(float(avg), 0),
                "pct_change": round(float(avg / (20_000 + 6_000 * d) * 100), 2),
                "suppressed": False,
            }
        )
    gain_k = sum(PLACEHOLDER_RECIPIENTS_K[p] for p, x in deltas.items() if x > 0)
    lose_k = sum(PLACEHOLDER_RECIPIENTS_K[p] for p, x in deltas.items() if x < 0)
    people_k = 56_000  # illustrative England and Wales population, thousands
    winners_losers = []
    for d in range(10):
        weight = float(shape[d]) * 10
        gain = gain_k / people_k * 100 * weight * 2  # people in their households
        lose = lose_k / people_k * 100 * weight * 2
        row = {
            "decile": d + 1,
            "gain_more_5": round(gain * 0.3, 1),
            "gain_less_5": round(gain * 0.7, 1),
            "lose_less_5": round(lose * 0.8, 1),
            "lose_more_5": round(lose * 0.2, 1),
        }
        row["no_change"] = round(
            100
            - row["gain_more_5"]
            - row["gain_less_5"]
            - row["lose_less_5"]
            - row["lose_more_5"],
            1,
        )
        row["suppressed"] = False
        winners_losers.append(
            {
                k: row[k]
                for k in (
                    "decile",
                    "gain_more_5",
                    "gain_less_5",
                    "no_change",
                    "lose_less_5",
                    "lose_more_5",
                    "suppressed",
                )
            }
        )
    return {
        "budgetary_impact": budgetary,
        "decile": decile,
        "winners_losers": winners_losers,
        "people_affected": {
            "gain_k": float(gain_k),
            "lose_k": float(lose_k),
            "suppressed": False,
        },
    }


# Tables only a model run fills; null in placeholder mode, and for any measure
# without figures.
MODEL_ONLY_TABLES = (
    "winners_losers_all",
    "by_region",
    "by_age",
    "poverty",
    "knock_ons",
)
FIGURE_TABLES = ("budgetary_impact", "decile", "winners_losers", "people_affected")


def _empty_tables() -> dict[str, None]:
    return {key: None for key in (*FIGURE_TABLES, *MODEL_ONLY_TABLES)}


def _with_fiscal_labels(rows):
    return [{**row, "fiscal_year": fiscal_label(row["year"])} for row in rows]


def _official_spending() -> list[dict[str, Any]]:
    with OFFICIAL_SPENDING.open() as handle:
        return [
            {
                "year": int(row["year"]),
                "fiscal_year": row["fiscal_year"],
                "dwp_m": float(row["pip_spend_m"]),
                "dwp_caseload_k": float(row["pip_caseload_k"]),
            }
            for row in csv.DictReader(handle)
        ]


def _spending_path(measures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    with_figures = [m for m in measures if m["budgetary_impact"]]
    totals = {
        year: sum(
            next(r["value_m"] for r in m["budgetary_impact"] if r["year"] == year)
            for m in with_figures
        )
        for year in POLICY_YEARS
    }
    return [
        {**row, "reformed_m": round(row["dwp_m"] + totals.get(row["year"], 0.0), 0)}
        for row in _official_spending()
    ]


def _limits() -> dict[str, list[dict[str, Any]]]:
    return {
        "data_limits": [
            {
                "key": limit.key,
                "missing_input": limit.missing_input,
                "reason": limit.public_reason,
                "issue": limit.issue,
            }
            for limit in data_limits.LIMITS
        ],
        "model_limits": [
            {"key": limit.key, "reason": limit.public_reason, "issue": limit.issue}
            for limit in model_limits.LIMITS
        ],
    }


def _has_figures(reform) -> bool:
    return reform.computable and not reform.withdrawn_reason


def _measure_entry(reform) -> dict[str, Any]:
    entry = reform.summary()
    entry["status"] = publication.status_of(reform)
    entry["receipt"] = publication.receipt(reform)
    entry.update(_empty_tables())
    return entry


def _placeholder_households(reforms) -> list[dict[str, Any]]:
    """PIP only, by arithmetic (rate x 52), in the first policy year."""
    year = POLICY_YEARS[0]
    law = CURRENT_LAW_RATES[year]
    rates = {
        reform.id: {
            path: values[str(year)]
            for path, values in (reform.parameter_changes or {}).items()
            if path in law
        }
        for reform in reforms
        if _has_figures(reform) and _rate_deltas(reform, year)
    }
    return [
        {
            "id": preset["id"],
            "label": preset["label"],
            "baseline": {"pip": pip_award(preset, law), "net_income": None},
            "reform": {
                mid: {"pip": pip_award(preset, {**law, **r}), "net_income": None}
                for mid, r in rates.items()
            },
        }
        for preset in PRESETS
    ]


def _assemble(measures, households, status, banner, engine, extra=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "banner": banner,
        "engine": engine,
        "basis": BASIS,
        "base_year": BASE_YEAR,
        "years": POLICY_YEARS,
        "distribution_year": POLICY_YEARS[-1],
        "measures": measures,
        "package": None,
        "spending_path": _spending_path(measures),
        "households": households,
        **_limits(),
        **(extra or {}),
    }


def _banner(status: str, banner: str | None) -> str:
    return publication.banner_for(status) if banner is None else banner


def build_placeholder_results(
    status: str = "placeholder", banner: str | None = None
) -> dict[str, Any]:
    measures = []
    for reform in REFORMS:
        entry = _measure_entry(reform)
        # Structural measures have no rate path to illustrate: their tables
        # stay null until a model run.
        if _has_figures(reform) and _rate_deltas(reform, POLICY_YEARS[0]):
            figures = _placeholder_figures(reform)
            figures["budgetary_impact"] = _with_fiscal_labels(
                figures["budgetary_impact"]
            )
            entry.update(figures)
        measures.append(entry)
    return _assemble(
        measures,
        _placeholder_households(REFORMS),
        status,
        _banner(status, banner),
        engine_record(installed=False),
    )


# --- model mode -------------------------------------------------------------


def git_state() -> dict[str, Any]:
    def run(*args):
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
        ).stdout.strip()

    return {
        "commit": run("rev-parse", "HEAD") or None,
        "clean_tree": run("status", "--porcelain", "--untracked-files=no") == "",
    }


def _spawn(reform_ids: list[str], dataset: str | None, out: Path) -> dict:
    from pip_review.heavy import MIN_FREE_GB, free_gb

    if os.environ.get("PIP_REVIEW_NO_LOCK") != "1":
        import time

        while (free := free_gb()) is not None and free < MIN_FREE_GB:
            print(f"Waiting for memory: {free:.1f} GB free", file=sys.stderr)
            time.sleep(15)
    command = [
        sys.executable,
        "-m",
        "pip_review.model_run",
        "--years",
        ",".join(str(y) for y in POLICY_YEARS),
        "--out",
        str(out),
    ]
    if reform_ids:
        command += ["--reform", ",".join(reform_ids)]
    if dataset:
        command += ["--dataset", dataset]
    subprocess.run(command, check=True)
    with np.load(out, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


def _check_bundle(bundle: dict[str, str], dataset: str | None) -> None:
    if dataset is not None:
        return
    for key, expected in CERTIFIED_BUNDLE.items():
        if bundle.get(key) != expected:
            raise RuntimeError(
                f"The run loaded {key} {bundle.get(key)!r}, not the pinned "
                f"{expected!r}. Update data_build.DATA_BUILD at G0 and "
                "regenerate, or install the pinned engine."
            )


def _model_households(reforms) -> list[dict[str, Any]]:
    """Preset households through the full model (single-household runs)."""
    from pip_review.household import calculate

    year = POLICY_YEARS[0]
    out = []
    for preset in PRESETS:
        base = calculate(preset["id"], None, year=year)
        out.append(
            {
                "id": preset["id"],
                "label": preset["label"],
                "baseline": {
                    "pip": round(base["pip"], 2),
                    "net_income": round(base["household_net_income"], 2),
                },
                "reform": {
                    reform.id: {
                        key: round(value, 2)
                        for key, value in (
                            ("pip", r["pip"]),
                            ("net_income", r["household_net_income"]),
                        )
                    }
                    for reform in reforms
                    for r in [calculate(preset["id"], reform, year=year)]
                },
            }
        )
    return out


def build_model_results(
    dataset: str | None = None,
    status: str = "provisional",
    banner: str | None = None,
    measure_ids: list[str] | None = None,
    households: bool = True,
) -> dict[str, Any]:
    """Model figures for every computable, non-withdrawn measure.

    ``dataset=None`` runs the pinned national build inside the
    heavy-run lock. A placeholder measure may run only under status
    'placeholder' or 'mock' (``validate_public`` refuses it otherwise).
    """
    from pip_review import aggregate
    from pip_review.heavy import heavy_lock

    chosen = [
        r
        for r in REFORMS
        if _has_figures(r) and (measure_ids is None or r.id in measure_ids)
    ]
    if measure_ids is not None:
        missing = set(measure_ids) - {r.id for r in chosen}
        if missing:
            raise ValueError(f"Not computable or unknown: {sorted(missing)}")
    seconds: dict[str, float] = {}
    with heavy_lock(), tempfile.TemporaryDirectory(prefix="pip-review-") as tmp:
        tmp = Path(tmp)
        base = _spawn([], dataset, tmp / "baseline.npz")
        bundle = json.loads(str(base.pop("bundle_json")))
        seconds["baseline"] = float(base.pop("seconds"))
        _check_bundle(bundle, dataset)
        tables_by_id = {}
        for reform in chosen:
            run = _spawn([reform.id], dataset, tmp / f"{reform.id}.npz")
            run.pop("bundle_json")
            seconds[reform.id] = float(run.pop("seconds"))
            tables_by_id[reform.id] = aggregate.tables(base, run, POLICY_YEARS)
            del run
        package = None
        if len(chosen) > 1:
            ids = [r.id for r in chosen]
            run = _spawn(ids, dataset, tmp / "package.npz")
            run.pop("bundle_json")
            seconds["package"] = float(run.pop("seconds"))
            package = {"measure_ids": ids, **aggregate.tables(base, run, POLICY_YEARS)}
            package["budgetary_impact"] = _with_fiscal_labels(
                package["budgetary_impact"]
            )
            del run
        # --no-households leaves the example households out (faster runs).
        house = _model_households(chosen) if households else []

    measures = []
    for reform in REFORMS:
        entry = _measure_entry(reform)
        if reform.id in tables_by_id:
            figures = tables_by_id[reform.id]
            figures["budgetary_impact"] = _with_fiscal_labels(
                figures["budgetary_impact"]
            )
            entry.update(figures)
        measures.append(entry)
    engine = engine_record(installed=True)
    if dataset is not None:
        engine.update(
            {
                "dataset": "unmanaged test file",
                "dataset_sha256": bundle.get("runtime_dataset_sha256"),
                "certified_pair": False,
                "label": None,
            }
        )
    results = _assemble(
        measures,
        house,
        status,
        _banner(status, banner),
        engine,
        extra={
            "provenance": {
                **git_state(),
                "bundle": bundle,
                "machine_seconds": {k: round(v, 1) for k, v in seconds.items()},
            }
        },
    )
    results["package"] = package
    return results


def write_results(results: dict[str, Any], *paths: Path) -> None:
    errors = publication.validate_public(results)
    if errors:
        raise ValueError("Results fail the publication check:\n" + "\n".join(errors))
    text = json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


__all__ = [
    "BANNER",
    "BASIS",
    "build_model_results",
    "build_placeholder_results",
    "engine_record",
    "write_results",
]
