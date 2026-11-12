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


def _adult_on_uc(pip_dl, lcwra_flag, year=YEAR):
    period = str(year)
    return {
        "people": {
            "adult": {
                "age": {period: 40},
                "employment_income": {period: 0},
                "is_disabled_for_benefits": {period: lcwra_flag},
                "pip_dl_category": {period: pip_dl},
                "pip_m_category": {period: "NONE"},
            }
        },
        "benunits": {
            "benunit": {"members": ["adult"], "would_claim_uc": {period: True}}
        },
        "households": {
            "household": {"members": ["adult"], "region": {period: "NORTH_WEST"}}
        },
    }


def _element(pip_dl, lcwra_flag, scenario=None, year=YEAR):
    sim = Simulation(
        situation=_adult_on_uc(pip_dl, lcwra_flag, year), scenario=scenario
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


def _drop_daily_living(sim):
    """A category move for the test: every daily living award to none."""
    holder = sim.get_holder("pip_dl_category")
    count = len(holder.get_array(YEAR))
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
