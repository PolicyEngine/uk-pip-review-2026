"""Model mode end to end on a small invented file (needs the model extra).

Skipped without policyengine-uk. Runs one simulation per process on a
400-household synthetic file, so it skips the heavy-run lock.
"""

import json
import os

import pytest

pytest.importorskip("policyengine_uk")

from pip_review import pipeline, publication  # noqa: E402
from pip_review.reforms import CURRENT_LAW_RATES  # noqa: E402
from pip_review.synthetic_dataset import write  # noqa: E402


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    os.environ["PIP_REVIEW_NO_LOCK"] = "1"
    path = write(tmp_path_factory.mktemp("data") / "synthetic.h5")
    return pipeline.build_model_results(
        dataset=str(path),
        status="mock",
        measure_ids=["standard_daily_living_rate", "uc_health_gateway"],
        households=False,
    )


def test_model_results_pass_the_gate(results):
    assert publication.validate_public(results) == []
    assert results["engine"]["certified_pair"] is False
    assert "MOCK" in results["banner"]
    json.dumps(results)


def test_rate_rise_is_a_cost_with_gainers_only(results):
    measure = next(
        m for m in results["measures"] if m["id"] == "standard_daily_living_rate"
    )
    assert all(row["value_m"] > 0 for row in measure["budgetary_impact"])
    affected = measure["people_affected"]
    assert affected["suppressed"] or affected["lose_k"] == 0


def test_package_runs_both_measures(results):
    assert results["package"]["measure_ids"] == [
        "standard_daily_living_rate",
        "uc_health_gateway",
    ]


def test_provenance_records_run(results):
    provenance = results["provenance"]
    assert provenance["commit"]
    assert set(provenance["machine_seconds"]) >= {"baseline", "package"}


def test_current_law_rates_match_engine():
    from policyengine_uk import CountryTaxBenefitSystem

    parameters = CountryTaxBenefitSystem().parameters
    for year, rates in CURRENT_LAW_RATES.items():
        for path, value in rates.items():
            leaf = parameters.get_child(path)(f"{year}-04-01")
            assert leaf == pytest.approx(value, abs=0.006), (year, path)


def test_pinned_engine_matches_install():
    from importlib import metadata

    from pip_review.data_build import DATA_BUILD

    assert pipeline.CERTIFIED_BUNDLE["model_version"] == DATA_BUILD.engine
    assert metadata.version("policyengine-uk") == DATA_BUILD.engine
    assert metadata.version("policyengine-core") == DATA_BUILD.core


def test_uc_rebalanced_years_match_engine():
    from policyengine_uk.scenarios import uc_reform

    from pip_review.measure_templates import UC_REBALANCED_YEARS

    assert list(UC_REBALANCED_YEARS) == list(uc_reform.REBALANCING_YEARS)


def test_benefit_receipt_payment_reaches_pip_households_in_england_and_wales(
    tmp_path,
):
    from pip_review.measure_templates import apply_benefit_receipt_payment
    from pip_review.model_run import build

    path = write(tmp_path / "small.h5", households=60)
    base = build(str(path), None)
    sim = build(str(path), None)
    apply_benefit_receipt_payment(
        sim,
        amount=100,
        eligible_benefits=["pip"],
        geography="EW",
        channel="cost_of_living_support_payment",
        year=2027,
    )
    change = (
        sim.calculate("household_net_income", 2027).values
        - base.calculate("household_net_income", 2027).values
    )
    country = base.calculate("country", 2027).values
    pip = base.calculate("pip", 2027, map_to="household").values
    ew = (country == "ENGLAND") | (country == "WALES")
    assert (change[~ew] == 0).all()
    assert change[ew & (pip > 0)] == pytest.approx(100, abs=1)


def test_carers_allowance_link_follows_the_cared_for_award():
    import numpy as np
    from policyengine_uk import Simulation

    from pip_review.measures import carers_allowance_link

    year = "2027"
    situation = {
        "people": {
            "cared": {
                "age": {year: 50},
                "pip_dl_category": {year: "STANDARD"},
                "pip_m_category": {year: "NONE"},
            },
            "carer": {
                "age": {year: 48},
                "care_hours": {year: 40},
                "carers_allowance_reported": {year: 4_000},
            },
        },
        "benunits": {"b": {"members": ["cared", "carer"]}},
        "households": {
            "h": {"members": ["cared", "carer"], "region": {year: "NORTH_WEST"}}
        },
    }

    def remove_award(sim):
        sim.set_input("pip_dl_category", 2027, np.array(["NONE", "NONE"]))

    def carer_ca(modifier):
        sim = Simulation(situation=situation)
        modifier(sim)
        return float(sim.calculate("carers_allowance_pre_overlap", 2027)[1])

    assert carer_ca(lambda sim: None) > 0
    assert carer_ca(remove_award) > 0  # the model's own gap (#2)
    assert carer_ca(carers_allowance_link.after(remove_award, years=[2027])) == 0
    assert carer_ca(lambda sim: carers_allowance_link.modifier(sim, years=[2027])) > 0


def test_phasing_moves_only_the_share(tmp_path):
    import numpy as np

    from pip_review.measures.phasing import phase
    from pip_review.model_run import build

    def remove_all_awards(sim):
        for year in (2027, 2028):
            n = len(sim.calculate("age", year))
            sim.set_input("pip_dl_category", year, np.array(["NONE"] * n))

    path = write(tmp_path / "phase.h5", households=150)
    sim = build(str(path), None)
    before = {
        y: np.asarray(sim.calculate("pip_dl_category", y).values) != "NONE"
        for y in (2027, 2028)
    }
    phase(remove_all_awards, {2027: 0.25, 2028: 0.75})(sim)
    after = {
        y: np.asarray(sim.calculate("pip_dl_category", y).values) != "NONE"
        for y in (2027, 2028)
    }
    moved = {y: (before[y] & ~after[y]).sum() / before[y].sum() for y in after}
    assert 0.1 < moved[2027] < 0.4
    assert 0.6 < moved[2028] < 0.9
    # anyone moved in 2027 is still moved in 2028
    assert not (before[2027] & ~after[2027] & after[2028]).any()


def test_parameters_that_act_through_points_are_data_limited():
    """Formula-based detection, cut down from AB2026's data-limit detection.

    For each parameter path a registered measure changes, find the engine
    source files that read it; if any of them also reads assessment points,
    the path must be covered by a declared DataLimit (``ALL_LIMITS``),
    which is live only on a build without points (``LIMITS_BY_BUILD``).
    """
    from pathlib import Path

    import policyengine_uk

    from pip_review import data_limits
    from pip_review.reforms import REFORMS

    sources = {
        path: path.read_text()
        for path in Path(policyengine_uk.__file__).parent.rglob("*.py")
    }
    import re

    points = ("pip_dl_points", "pip_m_points")
    paths = {p for r in REFORMS for p in (r.parameter_changes or {})}
    flagged = set()
    for path in paths:
        # The node a formula reads: the path without its leaf, not followed
        # by a deeper node.
        node = re.escape(path.rsplit(".", 1)[0]) + r"(?![.\w])"
        readers = [f for f, text in sources.items() if re.search(node, text)]
        if any(any(p in sources[f] for p in points) for f in readers):
            flagged.add(path)
            assert any(limit.covers(path) for limit in data_limits.ALL_LIMITS), path
    # The check is live: the points thresholds are found to act through points
    assert any("points_thresholds" in p for p in flagged)
    assert not any(
        p.endswith(("daily_living.standard", "daily_living.enhanced")) for p in flagged
    )


def test_points_layout_scores_the_gateway_and_thresholds(tmp_path_factory):
    """A file shaped like build 9e18f010 (2024 only; points, no category; the
    UC limited-capability flag stored): the gateway runs over the stored
    flag and a lower points threshold moves awards in the scored years."""
    os.environ["PIP_REVIEW_NO_LOCK"] = "1"
    path = write(
        tmp_path_factory.mktemp("points") / "points.h5", households=300, layout="points"
    )
    results = pipeline.build_model_results(
        dataset=str(path),
        status="mock",
        measure_ids=["uc_health_gateway", "points_thresholds"],
        households=False,
    )
    assert publication.validate_public(results) == []
    by_id = {m["id"]: m for m in results["measures"]}
    thresholds = by_id["points_thresholds"]["budgetary_impact"]
    assert all(row["value_m"] > 0 for row in thresholds)  # more awards: a cost
    gateway = by_id["uc_health_gateway"]["budgetary_impact"]
    assert any(row["value_m"] != 0 for row in gateway)
