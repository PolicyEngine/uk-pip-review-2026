"""One simulation per process: the worker behind ``pip-review generate --mode model``.

``python -m pip_review.model_run --reform ID[,ID...] --out run.npz`` builds one
``policyengine_uk.Microsimulation`` on the pinned Microcosm build
(``data_build.DATA_BUILD``; current law when ``--reform`` is omitted), reads
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


def fetch_dataset() -> Path:
    """The pinned build's file, downloaded once into the Hugging Face cache
    with HUGGING_FACE_TOKEN or the saved login (never printed)."""
    import os

    from huggingface_hub import hf_hub_download

    from pip_review.data_build import DATA_BUILD, HF_REPO, HF_REPO_TYPE

    return Path(
        hf_hub_download(
            repo_id=HF_REPO,
            filename=DATA_BUILD.hf_path,
            repo_type=HF_REPO_TYPE,
            token=os.environ.get("HUGGING_FACE_TOKEN") or None,
        )
    )


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _runtime_dataset(path: Path):
    """The dataset object policyengine_uk reads, as policyengine.py's managed
    helper builds it from a local file."""
    from policyengine_uk.data.dataset_schema import (
        UKMultiYearDataset,
        UKSingleYearDataset,
    )

    if UKMultiYearDataset.validate_file_path(str(path), False):
        return UKMultiYearDataset(str(path))
    if UKSingleYearDataset.validate_file_path(str(path), False):
        return UKSingleYearDataset(str(path))
    return str(path)


def build(dataset: str | None, scenario, allow_unpinned: bool = False):
    """A simulation on the pinned build, with the engine it was built on.

    policyengine_uk is loaded directly: no policyengine.py release covers the
    pair (``data_build.DATA_BUILD``). It refuses an installed policyengine-uk
    other than the build's. ``dataset=None`` downloads the pinned build. Any
    file, downloaded or named, must have the build's SHA-256; only
    ``allow_unpinned`` (tests on a synthetic file) lets another file run, and
    its figures are then marked ``certified_pair: false``, which the
    publication check refuses for a provisional or final page.
    """
    from importlib import metadata

    from policyengine_uk import Microsimulation

    from pip_review.data_build import DATA_BUILD, HF_REPO, LABEL

    installed = metadata.version("policyengine-uk")
    if installed != DATA_BUILD.engine:
        raise RuntimeError(
            f"policyengine-uk {installed} is installed, but build {DATA_BUILD.id} "
            f"was made on {DATA_BUILD.engine}. Never mix a build with another "
            "engine version."
        )
    path = Path(dataset) if dataset is not None else fetch_dataset()
    sha = file_sha256(path)
    if sha != DATA_BUILD.sha256 and not (dataset is not None and allow_unpinned):
        raise RuntimeError(
            f"{path.name} has SHA-256 {sha}, not that of build {DATA_BUILD.id} "
            f"({DATA_BUILD.sha256}). Name the pinned file, or pass "
            "--allow-unpinned for a test file whose figures are never published."
        )
    sim = Microsimulation(dataset=_runtime_dataset(path), scenario=scenario)
    pinned = sha == DATA_BUILD.sha256
    sim.pip_review_provenance = {
        "model_version": installed,
        "dataset_build_id": DATA_BUILD.id if pinned else "unpinned file",
        "runtime_dataset_sha256": sha,
        "runtime_dataset_uri": (
            f"hf://{HF_REPO}/{DATA_BUILD.hf_path}" if pinned else "local file"
        ),
        "label": LABEL if pinned else "",
        "managed_by": "pip_review.model_run (policyengine_uk directly)",
    }
    return sim


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
    """The engine and dataset fields the provenance block records (strings)."""
    record = getattr(sim, "pip_review_provenance", {}) or {}
    return {key: str(value) for key, value in record.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pip_review.model_run")
    parser.add_argument("--reform", default="", help="Comma-separated measure ids")
    parser.add_argument("--dataset", default=None)
    parser.add_argument(
        "--allow-unpinned",
        action="store_true",
        help="Run a --dataset file that is not the pinned build (tests only)",
    )
    parser.add_argument("--years", required=True, help="Comma-separated years")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    import json

    reform_ids = [r for r in args.reform.split(",") if r]
    years = [int(y) for y in args.years.split(",")]
    start = time.monotonic()
    sim = build(args.dataset, scenario_for(reform_ids), args.allow_unpinned)
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
