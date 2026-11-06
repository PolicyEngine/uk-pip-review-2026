"""One simulation per process: the worker behind ``pip-review generate --mode model``.

``python -m pip_review.model_run --reform ID[,ID...] --out run.npz`` builds one
``managed_microsimulation`` (current law when ``--reform`` is omitted), reads
the household and person arrays the pipeline aggregates, saves them to a
private ``.npz`` and exits, so its memory is returned before the next run.

The ``.npz`` holds record-level arrays and weights. It is written to a
temporary directory and never published; only the aggregates the pipeline
builds from it, after the disclosure floor, reach ``results.json``.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

HOUSEHOLD_VARIABLES = (
    "household_weight",
    "household_count_people",
    "household_net_income",
    "equiv_hbai_household_net_income",
    "gov_balance",
)
HOUSEHOLD_ENUMS = ("country", "region")
PERSON_VARIABLES = ("pip_dl", "pip_m", "age", "carers_allowance")
PERSON_HOUSEHOLD_FLAGS = ("in_poverty_bhc", "in_poverty_ahc")


def scenario_for(reform_ids: list[str]):
    """The scenario for one or more registry measures (summed), or None."""
    from pip_review.reforms import get_reform

    scenario = None
    for reform_id in reform_ids:
        part = get_reform(reform_id).to_scenario()
        scenario = part if scenario is None else scenario + part
    return scenario


def build(dataset: str | None, scenario):
    """A simulation pinned to the installed policyengine bundle.

    ``dataset=None`` uses the bundle's certified national file. Any other path
    is an unmanaged run (tests use a synthetic file) and its figures are never
    certified.
    """
    import os

    from policyengine.tax_benefit_models.uk.model import managed_microsimulation

    if dataset is None and not os.environ.get("HUGGING_FACE_TOKEN"):
        # The certified file is private: use the saved Hugging Face login,
        # if any (never printed).
        from huggingface_hub import get_token

        token = get_token()
        if token:
            os.environ["HUGGING_FACE_TOKEN"] = token
    return managed_microsimulation(
        dataset=dataset,
        allow_unmanaged=dataset is not None,
        scenario=scenario,
    )


def _values(series):
    return np.asarray(getattr(series, "values", series))


def read_arrays(sim, years: list[int]) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    first = years[0]
    out["person_household"] = _values(
        sim.calculate("household_id", first, map_to="person")
    )
    out["household_id"] = _values(sim.calculate("household_id", first))
    for year in years:
        for name in HOUSEHOLD_VARIABLES:
            out[f"{name}/{year}"] = _values(sim.calculate(name, year)).astype(float)
        for name in HOUSEHOLD_ENUMS:
            out[f"{name}/{year}"] = _values(sim.calculate(name, year)).astype(str)
        for name in PERSON_VARIABLES:
            out[f"{name}/{year}"] = _values(sim.calculate(name, year)).astype(float)
        for name in PERSON_HOUSEHOLD_FLAGS:
            out[f"{name}/{year}"] = _values(
                sim.calculate(name, year, map_to="person")
            ).astype(bool)
        out[f"person_weight/{year}"] = _values(
            sim.calculate("person_weight", year)
        ).astype(float)
    return out


def bundle_record(sim) -> dict[str, str]:
    """The bundle fields the provenance block records (strings only)."""
    bundle = getattr(sim, "policyengine_bundle", {}) or {}
    keep = (
        "bundle_id",
        "policyengine_version",
        "model_version",
        "certified_data_build_id",
        "certified_data_artifact_sha256",
        "default_dataset_uri",
        "dataset_sha256",
        "runtime_dataset_sha256",
        "runtime_dataset_uri",
    )
    return {key: str(bundle[key]) for key in keep if key in bundle}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pip_review.model_run")
    parser.add_argument("--reform", default="", help="Comma-separated measure ids")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--years", required=True, help="Comma-separated years")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    import json

    reform_ids = [r for r in args.reform.split(",") if r]
    years = [int(y) for y in args.years.split(",")]
    start = time.monotonic()
    sim = build(args.dataset, scenario_for(reform_ids))
    arrays = read_arrays(sim, years)
    arrays["bundle_json"] = np.array(json.dumps(bundle_record(sim)))
    arrays["seconds"] = np.array(time.monotonic() - start)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, **arrays)
    print(
        f"{args.reform or 'baseline'}: {time.monotonic() - start:.0f} s",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
