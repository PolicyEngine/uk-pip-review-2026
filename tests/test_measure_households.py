"""Household checks for the UC health gateway and the Carer's Allowance link.

One household per simulation, no survey data. Skipped without the ``model``
extra.
"""

import numpy as np
import pytest

pytest.importorskip("policyengine_uk")

from policyengine_uk import Simulation  # noqa: E402
from policyengine_uk.utils.scenario import Scenario  # noqa: E402

from pip_review.household import PRESETS_BY_ID, to_situation  # noqa: E402
from pip_review.measures import carers_allowance_link, uc_health_gateway  # noqa: E402

# After the UC Act 2025 s. 4 years, inside the years the engine's UC
# rebalancing step stores the health element.
YEAR = 2030


def _adult_on_uc(pip_dl, lcwra_flag, year=YEAR, stored_lcwra=None, age=40):
    period = str(year)
    adult = {
        "age": {period: age},
        "employment_income": {period: 0},
        "is_disabled_for_benefits": {period: lcwra_flag},
        "pip_dl_category": {period: pip_dl},
        "pip_m_category": {period: "NONE"},
    }
    if stored_lcwra is not None:
        # As build 6f918b81 stores them: both limited-capability flags are
        # inputs.
        adult["uc_limited_capability_for_WRA"] = {period: stored_lcwra}
        adult["uc_limited_capability_for_work"] = {period: stored_lcwra}
    return {
        "people": {"adult": adult},
        "benunits": {
            "benunit": {"members": ["adult"], "would_claim_uc": {period: True}}
        },
        "households": {
            "household": {"members": ["adult"], "region": {period: "NORTH_WEST"}}
        },
    }


def _element(pip_dl, lcwra_flag, scenario=None, year=YEAR, **kwargs):
    sim = Simulation(
        situation=_adult_on_uc(pip_dl, lcwra_flag, year, **kwargs), scenario=scenario
    )
    return float(sim.calculate("uc_LCWRA_element", year)[0]), sim


GATEWAY = Scenario(simulation_modifier=uc_health_gateway.modifier)


def test_rebalancing_step_covers_the_test_year():
    from policyengine_uk.scenarios.uc_reform import REBALANCING_YEARS

    assert YEAR in REBALANCING_YEARS


def test_gateway_removes_element_without_qualifying_pip():
    baseline, _ = _element("NONE", True)
    reformed, _ = _element("NONE", True, GATEWAY)
    assert baseline > 0
    assert reformed == 0


def test_gateway_keeps_element_with_enhanced_daily_living():
    baseline, _ = _element("ENHANCED", True)
    reformed, sim = _element("ENHANCED", True, GATEWAY)
    assert baseline > 0
    assert reformed == pytest.approx(baseline)
    # Still the model's own value, as the rebalancing step stores it.
    from policyengine_core.periods import period
    from policyengine_uk.utils.supplied_inputs import supplied_input

    population = sim.get_variable_population("uc_LCWRA_element")
    assert supplied_input(population, "uc_LCWRA_element", period(YEAR)) is None


def test_gateway_grants_element_to_qualifying_pip_without_assessment():
    baseline, _ = _element("STANDARD", False)
    reformed, _ = _element("STANDARD", False, GATEWAY)
    assert baseline == 0
    assert reformed > 0


def test_gateway_removes_element_when_the_stored_flag_is_set_without_pip():
    # Build 6f918b81 stores uc_limited_capability_for_WRA: the gateway still
    # runs and overrides the stored flag for working-age people.
    baseline, _ = _element("NONE", False, stored_lcwra=True)
    reformed, _ = _element("NONE", False, GATEWAY, stored_lcwra=True)
    assert baseline > 0
    assert reformed == 0


def test_gateway_grants_element_over_a_stored_false_flag():
    baseline, _ = _element("STANDARD", False, stored_lcwra=False)
    reformed, _ = _element("STANDARD", False, GATEWAY, stored_lcwra=False)
    assert baseline == 0
    assert reformed > 0


def test_gateway_keeps_the_stored_flag_outside_working_age():
    # Over State Pension age the stored flag is the model's own value, kept.
    situation = _adult_on_uc("NONE", False, stored_lcwra=True, age=80)
    base = Simulation(situation=situation)
    sim = Simulation(situation=situation, scenario=GATEWAY)
    assert bool(sim.calculate("uc_limited_capability_for_WRA", YEAR)[0]) == bool(
        base.calculate("uc_limited_capability_for_WRA", YEAR)[0]
    )
    assert bool(sim.calculate("uc_limited_capability_for_WRA", YEAR)[0]) is True


def test_stored_pip_points_carry_forward_and_follow_the_thresholds():
    # Build 6f918b81 stores 2024 PIP points and no category: the category in a
    # scored year is derived from those points against that year's
    # thresholds, so a threshold change moves the award (data_limits).
    situation = {
        "people": {"p": {"age": {"2024": 30}, "pip_dl_points": {"2024": 9}}},
        "benunits": {"b": {"members": ["p"]}},
        "households": {"h": {"members": ["p"]}},
    }
    base = Simulation(situation=situation)
    assert str(base.calculate("pip_dl_category", YEAR)[0]) == "STANDARD"
    lower = Simulation(
        situation=situation,
        reform={
            "gov.dwp.pip.daily_living.points_thresholds.standard": {f"{YEAR}-01-01": 10}
        },
    )
    assert str(lower.calculate("pip_dl_category", YEAR)[0]) == "NONE"


def _drop_daily_living(sim):
    """A category move for the test: every daily living award to none."""
    count = sim.populations["person"].count
    sim.set_input("pip_dl_category", YEAR, np.array(["NONE"] * count))


def test_carer_link_removes_allowance_and_uc_carer_element():
    situation = to_situation(PRESETS_BY_ID["uc_enhanced_both_with_carer"], YEAR)
    baseline = Simulation(situation=situation)
    link = Scenario(
        simulation_modifier=carers_allowance_link.after(
            _drop_daily_living, years=[YEAR]
        )
    )
    reformed = Simulation(situation=situation, scenario=link)
    assert baseline.calculate("carers_allowance", YEAR).sum() > 0
    assert baseline.calculate("uc_carer_element", YEAR).sum() > 0
    assert reformed.calculate("carers_allowance", YEAR).sum() == 0
    assert reformed.calculate("uc_carer_element", YEAR).sum() == 0


def test_carer_link_keeps_uc_carer_element_when_award_kept():
    situation = to_situation(PRESETS_BY_ID["uc_enhanced_both_with_carer"], YEAR)
    baseline = Simulation(situation=situation)
    link = Scenario(
        simulation_modifier=carers_allowance_link.after(lambda sim: None, years=[YEAR])
    )
    reformed = Simulation(situation=situation, scenario=link)
    for name in ("carers_allowance", "uc_carer_element"):
        assert reformed.calculate(name, YEAR).sum() == pytest.approx(
            baseline.calculate(name, YEAR).sum()
        )


def test_carer_link_follows_awards_derived_from_stored_points():
    # As on build 6f918b81: the cared-for person's award comes from stored
    # 2024 points, with no stored category, and the link still follows it.
    situation = to_situation(PRESETS_BY_ID["uc_enhanced_both_with_carer"], YEAR)
    points = {"ENHANCED": 12, "STANDARD": 9}
    for person in situation["people"].values():
        category = person.pop("pip_dl_category")[str(YEAR)]
        if category in points:
            person["pip_dl_points"] = {"2024": points[category]}
    baseline = Simulation(situation=situation)
    assert baseline.calculate("carers_allowance", YEAR).sum() > 0
    link = Scenario(
        simulation_modifier=carers_allowance_link.after(
            _drop_daily_living, years=[YEAR]
        )
    )
    reformed = Simulation(situation=situation, scenario=link)
    assert reformed.calculate("carers_allowance", YEAR).sum() == 0
    assert reformed.calculate("uc_carer_element", YEAR).sum() == 0


POINTS = {"ENHANCED": 12, "STANDARD": 9}


def _carer_on_points(route="hours"):
    """The preset carer household shaped like build 6f918b81: 2024 PIP points
    and no category, and ``cares_for_severely_disabled_person`` stored true
    for everyone. ``route`` is how the carer qualifies: caring hours, or a
    reported award they would claim with no hours recorded."""
    situation = to_situation(PRESETS_BY_ID["uc_enhanced_both_with_carer"], YEAR)
    period = str(YEAR)
    for person in situation["people"].values():
        category = person.pop("pip_dl_category")[period]
        if category in POINTS:
            person["pip_dl_points"] = {"2024": POINTS[category]}
        person["cares_for_severely_disabled_person"] = {period: True}
    if route == "reported":
        carer = situation["people"]["carer"]
        carer.pop("care_hours")
        carer["carers_allowance_reported"] = {period: 4_000}
        carer["would_claim_carers_allowance"] = {period: True}
    return situation


def _link_after(category_modifier, parameter_changes=None):
    return Scenario(
        parameter_changes=parameter_changes,
        simulation_modifier=carers_allowance_link.after(
            category_modifier, years=[YEAR]
        ),
    )


@pytest.mark.parametrize("route", ["hours", "reported"])
def test_carer_link_overrides_a_stored_cared_for_flag(route):
    # The stored flag stays true after the award goes, and a reported award
    # counts whatever the flag says, so the link zeroes the outputs, not the
    # flag: Carer's Allowance and the UC carer element both go.
    situation = _carer_on_points(route)
    baseline = Simulation(situation=situation)
    reformed = Simulation(situation=situation, scenario=_link_after(_drop_daily_living))
    assert baseline.calculate("carers_allowance", YEAR).sum() > 0
    assert baseline.calculate("uc_carer_element", YEAR).sum() > 0
    assert bool(reformed.calculate("cares_for_severely_disabled_person", YEAR)[1])
    assert reformed.calculate("carers_allowance", YEAR).sum() == 0
    assert reformed.calculate("uc_carer_element", YEAR).sum() == 0


# Every threshold above the cared-for person's 12 points: the award goes.
_ABOVE_ALL_POINTS = {
    "gov.dwp.pip.daily_living.points_thresholds.standard": {str(YEAR): 13},
    "gov.dwp.pip.daily_living.points_thresholds.enhanced": {str(YEAR): 14},
}


def test_carer_link_follows_a_points_threshold_change():
    # On a points build an award moves through the thresholds, which are
    # already reformed when the link takes its snapshot: the snapshot derives
    # the current-law award from current-law thresholds.
    situation = _carer_on_points()
    without_link = Simulation(
        situation=situation, scenario=Scenario(parameter_changes=_ABOVE_ALL_POINTS)
    )
    assert str(without_link.calculate("pip_dl_category", YEAR)[0]) == "NONE"
    assert without_link.calculate("carers_allowance", YEAR).sum() > 0
    reformed = Simulation(
        situation=situation,
        scenario=_link_after(lambda sim: None, _ABOVE_ALL_POINTS),
    )
    assert reformed.calculate("carers_allowance", YEAR).sum() == 0
    assert reformed.calculate("uc_carer_element", YEAR).sum() == 0


def test_carer_link_keeps_carers_when_a_threshold_change_leaves_the_award():
    situation = _carer_on_points()
    baseline = Simulation(situation=situation)
    reformed = Simulation(
        situation=situation,
        scenario=_link_after(
            lambda sim: None,
            {"gov.dwp.pip.daily_living.points_thresholds.standard": {str(YEAR): 10}},
        ),
    )
    for name in ("carers_allowance", "uc_carer_element"):
        assert reformed.calculate(name, YEAR).sum() == pytest.approx(
            baseline.calculate(name, YEAR).sum()
        )


def test_severe_disability_flag_follows_the_daily_living_award():
    # Build 6f918b81 does not store is_severely_disabled_for_benefits: the
    # formula derives it from the award, so it follows a category move.
    situation = _carer_on_points()
    baseline = Simulation(situation=situation)
    moved = Simulation(
        situation=situation,
        scenario=Scenario(simulation_modifier=_drop_daily_living),
    )
    flag = "is_severely_disabled_for_benefits"
    assert list(baseline.calculate(flag, YEAR)) == [True, False]
    assert list(moved.calculate(flag, YEAR)) == [False, False]
