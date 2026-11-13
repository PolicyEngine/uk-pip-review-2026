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
        allow_unpinned=True,
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
    base = build(str(path), None, allow_unpinned=True)
    sim = build(str(path), None, allow_unpinned=True)
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
    sim = build(str(path), None, allow_unpinned=True)
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


def test_points_layout_scores_the_gateway_not_the_threshold_cut(tmp_path_factory):
    """A file shaped like build 6f918b81 (2024 only; points, no category; the
    UC limited-capability flag stored): the gateway runs over the stored
    flag, and the threshold cut is published as not computable, never as a
    figure."""
    os.environ["PIP_REVIEW_NO_LOCK"] = "1"
    path = write(
        tmp_path_factory.mktemp("points") / "points.h5", households=300, layout="points"
    )
    results = pipeline.build_model_results(
        dataset=str(path),
        status="mock",
        measure_ids=["uc_health_gateway"],
        households=False,
        allow_unpinned=True,
    )
    assert publication.validate_public(results) == []
    by_id = {m["id"]: m for m in results["measures"]}
    assert by_id["points_thresholds"]["status"] == "not-computable"
    assert not by_id["points_thresholds"]["budgetary_impact"]
    with pytest.raises(ValueError, match="points_thresholds"):
        pipeline.build_model_results(
            dataset=str(path),
            status="mock",
            measure_ids=["points_thresholds"],
            households=False,
            allow_unpinned=True,
        )
    gateway = by_id["uc_health_gateway"]["budgetary_impact"]
    assert any(row["value_m"] != 0 for row in gateway)


def test_a_named_file_that_is_not_the_pinned_build_is_refused(tmp_path):
    from pip_review import model_run

    path = write(tmp_path / "synthetic.h5", households=20)
    with pytest.raises(RuntimeError, match="not that of build"):
        model_run.build(str(path), None)


def test_an_unpinned_run_cannot_be_published(results):
    for status in ("provisional", "final"):
        public = {**results, "status": status, "banner": "Provisional"}
        errors = publication.validate_public(public)
        assert any(e.startswith("$.engine.certified_pair") for e in errors)


# Build 6f918b81's PIP points (María, data owner, 13 November 2026): drawn only
# for people with an award, -1 otherwise; the other component of a
# one-component recipient below 8 (daily living 4-7, mobility 0 or 4).
DL_STANDARD = "gov.dwp.pip.daily_living.points_thresholds.standard"
MOB_STANDARD = "gov.dwp.pip.mobility.points_thresholds.standard"


def test_current_law_thresholds_match_the_engine():
    from policyengine_uk import CountryTaxBenefitSystem

    from pip_review.data_limits import CURRENT_LAW_THRESHOLDS

    parameters = CountryTaxBenefitSystem().parameters
    for path, value in CURRENT_LAW_THRESHOLDS.items():
        node = parameters.get_child(path)
        assert {entry.value for entry in node.values_list} == {value}, path


def test_synthetic_points_match_the_build():
    import numpy as np

    from pip_review.synthetic_dataset import build

    person = build(households=400, layout="points").person
    dl = person["pip_dl_points"].to_numpy()
    mob = person["pip_m_points"].to_numpy()
    assessed = (dl >= 0) | (mob >= 0)
    # not assessed: both -1, never 0-7
    assert ((dl == -1) == (mob == -1)).all()
    assert set(np.unique(dl[~assessed])) == {-1}
    # every assessed person gets at least one component
    assert ((dl[assessed] >= 8) | (mob[assessed] >= 8)).all()
    dl_only = (dl >= 8) & (mob < 8) & assessed
    mob_only = (mob >= 8) & (dl < 8) & assessed
    assert set(np.unique(mob[dl_only])) <= {0, 4}
    assert set(np.unique(dl[mob_only])) == {4, 5, 6, 7}
    assert (dl[mob_only] >= 6).sum() >= 10  # the test below is not vacuous


@pytest.fixture(scope="module")
def points_file(tmp_path_factory):
    return write(
        tmp_path_factory.mktemp("cut") / "points.h5", households=400, layout="points"
    )


def _awards(path, changes=None):
    import numpy as np
    from policyengine_uk.utils.scenario import Scenario

    from pip_review.model_run import build

    scenario = Scenario(parameter_changes=changes) if changes else None
    sim = build(str(path), scenario, allow_unpinned=True)
    return {
        name: np.asarray(sim.calculate(name, 2027).values) != "NONE"
        for name in ("pip_dl_category", "pip_m_category")
    }


def test_threshold_cut_moves_no_non_recipient(points_file):
    """A daily living cut to 6 moves only mobility-only recipients drawn at
    6-7; no one holding -1 moves; a mobility cut to 6 moves no one. This is
    why a cut is not computable: the people it should reach (turned down at
    6-7) are not in the data."""
    import numpy as np

    from pip_review.synthetic_dataset import build

    person = build(households=400, layout="points").person
    dl = person["pip_dl_points"].to_numpy()
    mob = person["pip_m_points"].to_numpy()
    base = _awards(points_file)
    dl_cut = _awards(points_file, {DL_STANDARD: {"2027": 6}})
    mob_cut = _awards(points_file, {MOB_STANDARD: {"2027": 6}})
    moved = dl_cut["pip_dl_category"] & ~base["pip_dl_category"]
    assert moved.any()
    assert not moved[dl == -1].any()
    assert (mob[moved] >= 8).all() and set(np.unique(dl[moved])) <= {6, 7}
    assert (moved == ((dl >= 6) & (dl < 8) & (mob >= 8))).all()
    assert (mob_cut["pip_m_category"] == base["pip_m_category"]).all()
    # the limit applied on the pinned build keeps the cut off the page
    from pip_review import data_limits

    assert data_limits.is_only_data_limited({DL_STANDARD: {"2027": 6}})
    assert data_limits.is_only_data_limited({MOB_STANDARD: {"2027": 6}})


def test_threshold_raise_stays_computable(points_file):
    """A raise moves recipients whose drawn points fall below the new
    threshold; it is computable under the drawn-points assumption."""
    from pip_review import data_limits

    raise_ = {DL_STANDARD: {"2027": 10}}
    assert not data_limits.is_only_data_limited(raise_)
    base = _awards(points_file)
    raised = _awards(points_file, raise_)
    lost = base["pip_dl_category"] & ~raised["pip_dl_category"]
    assert lost.any()
    assert not (raised["pip_dl_category"] & ~base["pip_dl_category"]).any()
