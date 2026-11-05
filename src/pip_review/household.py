"""Household calculator: presets and the situation each one builds.

The calculator runs locally (``pip-review household``) or in the page from
precomputed presets. Nothing here deploys. ``calculate`` needs the ``model``
extra and builds a single-household simulation; it never loads survey data.

The presets cover the cases the day's coverage usually turns on: standard
daily living only, both components enhanced with a carer, enhanced mobility,
a pensioner who claimed before State Pension age and a young person moving
from child DLA.
"""

from typing import Any

from pip_review.reforms import CURRENT_RATES
from pip_review.years import BASE_YEAR

WEEKS_IN_YEAR = 52

PRESETS: list[dict[str, Any]] = [
    {
        "id": "single_standard_dl_part_time",
        "label": "Single adult, part-time work, standard daily living only",
        "region": "NORTH_WEST",
        "people": [
            {
                "name": "adult",
                "age": 38,
                "employment_income": 12_000,
                "pip_dl_category": "STANDARD",
                "pip_m_category": "NONE",
            }
        ],
        "claims_uc": True,
    },
    {
        "id": "uc_enhanced_both_with_carer",
        "label": "Adult on UC with both components enhanced, partner on Carer's Allowance",
        "region": "WALES",
        "people": [
            {
                "name": "claimant",
                "age": 45,
                "employment_income": 0,
                "pip_dl_category": "ENHANCED",
                "pip_m_category": "ENHANCED",
            },
            {
                "name": "carer",
                "age": 47,
                "employment_income": 0,
                "pip_dl_category": "NONE",
                "pip_m_category": "NONE",
                "is_carer": True,
            },
        ],
        "claims_uc": True,
    },
    {
        "id": "couple_standard_dl_enhanced_mobility",
        "label": "Working couple, one with standard daily living and enhanced mobility",
        "region": "WEST_MIDLANDS",
        "people": [
            {
                "name": "claimant",
                "age": 52,
                "employment_income": 18_000,
                "pip_dl_category": "STANDARD",
                "pip_m_category": "ENHANCED",
            },
            {
                "name": "partner",
                "age": 50,
                "employment_income": 30_000,
                "pip_dl_category": "NONE",
                "pip_m_category": "NONE",
            },
        ],
        "claims_uc": False,
    },
    {
        "id": "pensioner_claimed_before_spa",
        "label": "Pensioner who claimed PIP before State Pension age",
        "region": "YORKSHIRE",
        "people": [
            {
                "name": "pensioner",
                "age": 70,
                "employment_income": 0,
                "pip_dl_category": "ENHANCED",
                "pip_m_category": "STANDARD",
            }
        ],
        "claims_uc": False,
    },
    {
        "id": "young_person_from_child_dla",
        "label": "Young person aged 17 moving from child DLA, living with a parent",
        "region": "SOUTH_WEST",
        "people": [
            {
                "name": "young_person",
                "age": 17,
                "employment_income": 0,
                "pip_dl_category": "STANDARD",
                "pip_m_category": "STANDARD",
            },
            {
                "name": "parent",
                "age": 46,
                "employment_income": 26_000,
                "pip_dl_category": "NONE",
                "pip_m_category": "NONE",
            },
        ],
        "claims_uc": True,
    },
]

PRESETS_BY_ID = {preset["id"]: preset for preset in PRESETS}

_RATE_KEY = {
    ("dl", "STANDARD"): "gov.dwp.pip.daily_living.standard",
    ("dl", "ENHANCED"): "gov.dwp.pip.daily_living.enhanced",
    ("m", "STANDARD"): "gov.dwp.pip.mobility.standard",
    ("m", "ENHANCED"): "gov.dwp.pip.mobility.enhanced",
}


def to_situation(preset: dict[str, Any], year: int = BASE_YEAR) -> dict[str, Any]:
    """A policyengine-uk situation for one preset household (one benefit unit)."""
    period = str(year)
    people = {}
    for person in preset["people"]:
        values = {
            "age": {period: person["age"]},
            "employment_income": {period: person["employment_income"]},
            "pip_dl_category": {period: person["pip_dl_category"]},
            "pip_m_category": {period: person["pip_m_category"]},
        }
        if person.get("is_carer"):
            values["care_hours"] = {period: 40}
        people[person["name"]] = values
    names = list(people)
    return {
        "people": people,
        "benunits": {
            "benunit": {
                "members": names,
                "would_claim_uc": {period: preset["claims_uc"]},
            }
        },
        "households": {
            "household": {"members": names, "region": {period: preset["region"]}}
        },
    }


def pip_award(
    preset: dict[str, Any], rates: dict[str, float] | None = None
) -> float:
    """Annual PIP for the household at the given weekly rates (arithmetic only).

    Used for the template's placeholder cards. The real calculator runs the
    full model (``calculate``), so knock-ons on UC and Carer's Allowance show.
    """
    rates = {**CURRENT_RATES, **(rates or {})}
    total = 0.0
    for person in preset["people"]:
        for component in ("dl", "m"):
            key = _RATE_KEY.get((component, person[f"pip_{component}_category"]))
            if key:
                total += rates[key] * WEEKS_IN_YEAR
    return round(total, 2)


def calculate(preset_id: str, reform=None, year: int = BASE_YEAR) -> dict[str, float]:
    """Net income and PIP for one preset under current law or a reform.

    Needs the ``model`` extra. Builds one household, not a survey simulation.
    """
    from policyengine_uk import Simulation

    situation = to_situation(PRESETS_BY_ID[preset_id], year)
    scenario = None if reform is None else reform.to_scenario()
    simulation = Simulation(situation=situation, scenario=scenario)
    return {
        "household_net_income": float(
            simulation.calculate("household_net_income", year).sum()
        ),
        "pip": float(simulation.calculate("pip", year).sum()),
    }
