"""Candidate measures for the independent review of Personal Independence Payment.

PLACEHOLDERS. These are the probable recommendations, written before the final
report from the terms of reference, the July 2026 interim report and the
September 2026 emerging recommendations. None is announced policy, and every
value below is illustrative. Every measure has ``placeholder=True``, so the
publication step holds it back (``pip_review.publication``): nothing here is
published as a figure until it is replaced by the report's own proposal and
reconciled.

Every measure is compared against current law in the installed
policyengine-uk, England and Wales only. Year Y is fiscal year Y-(Y+1).
Measures change parameters (``parameter_changes``, built from
``measure_templates``) or apply a modifier from ``pip_review.measures``, one
module each; no modifier may live here.

Routes (see ``docs/DRILL.md``): only the rate measures are computable today.
The rest are routed to the ledger, not computable (a data limit) or
needs-pe-uk-first, with the reason shown on the page.
"""

import warnings

from pip_review.measure_templates import (
    DataLimitedWarning,
    merge,
    rate_change,
    threshold_change,
)
from pip_review.measures import uc_health_gateway
from pip_review.models import Likelihood, Reform, Route
from pip_review.years import POLICY_YEARS

DL = "gov.dwp.pip.daily_living"
MOB = "gov.dwp.pip.mobility"

# 2026-27 weekly rates in policyengine-uk 2.174.1 (from 2026-04-01).
CURRENT_RATES = {
    f"{DL}.standard": 76.70,
    f"{DL}.enhanced": 114.60,
    f"{MOB}.standard": 30.30,
    f"{MOB}.enhanced": 80.00,
}


# Current-law weekly rates for each policy year in policyengine-uk 2.174.1,
# after CPI uprating (read from the installed parameters, rounded to 1p). A
# measure written as a change to current law adds to these, so it does not
# turn into a cut once uprating overtakes a cash figure. Check them at G0
# (``tests/test_model_import.py`` compares them with the installed engine).
CURRENT_LAW_RATES = {
    2027: {
        f"{DL}.standard": 79.38,
        f"{DL}.enhanced": 118.61,
        f"{MOB}.standard": 31.36,
        f"{MOB}.enhanced": 82.80,
    },
    2028: {
        f"{DL}.standard": 82.08,
        f"{DL}.enhanced": 122.64,
        f"{MOB}.standard": 32.43,
        f"{MOB}.enhanced": 85.62,
    },
    2029: {
        f"{DL}.standard": 83.73,
        f"{DL}.enhanced": 125.10,
        f"{MOB}.standard": 33.08,
        f"{MOB}.enhanced": 87.33,
    },
    2030: {
        f"{DL}.standard": 85.57,
        f"{DL}.enhanced": 127.85,
        f"{MOB}.standard": 33.80,
        f"{MOB}.enhanced": 89.25,
    },
}


def _every_year(value: float) -> dict[int, float]:
    return {year: value for year in POLICY_YEARS}


def _current_law_plus(path: str, weekly: float = 0.0, factor: float = 1.0):
    """Each policy year's current-law rate times ``factor`` plus ``weekly`` £."""
    return {
        year: round(CURRENT_LAW_RATES[year][path] * factor + weekly, 2)
        for year in POLICY_YEARS
    }


with warnings.catch_warnings():
    # The threshold placeholder is data limited by design; the warning is
    # expected and the route below records it.
    warnings.simplefilter("ignore", DataLimitedWarning)
    _THRESHOLDS = merge(
        threshold_change(f"{DL}.points_thresholds.standard", _every_year(6)),
        threshold_change(f"{MOB}.points_thresholds.standard", _every_year(6)),
    )


REFORMS: list[Reform] = [
    Reform(
        id="fluctuating_conditions",
        name="Assess fluctuating conditions over time",
        description=(
            "Replace the rule that a descriptor must apply on more than half of "
            "days with a test of fluctuating and cumulative impact."
        ),
        recommendation="Change how fluctuating conditions are assessed",
        likelihood=Likelihood.HIGH,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "Acts through assessment points and the share of days a descriptor "
            "applies; the data hold neither."
        ),
        data_needs=["pip_dl_points", "pip_m_points", "pip_activity_points"],
        issues=[3],
    ),
    Reform(
        id="fewer_award_reviews",
        name="Fewer award reviews for lifelong conditions",
        description=(
            "Longer or ongoing awards for lifelong and degenerative conditions."
        ),
        recommendation="Fewer award reviews for lifelong or degenerative conditions",
        likelihood=Likelihood.HIGH,
        route=Route.LEDGER,
        route_reason=(
            "Changes flows on and off PIP over time; the model is static. Recorded "
            "as a fiscal line from any official figure."
        ),
        data_needs=["award_review_state"],
    ),
    Reform(
        id="fast_track_serious_conditions",
        name="Fast track for serious conditions",
        description=(
            "A fast-track pathway, paying both components at the enhanced rate, "
            "for well-evidenced serious conditions and end-of-life care."
        ),
        recommendation="A fast-track pathway for well-evidenced serious conditions",
        likelihood=Likelihood.HIGH,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "The data have no health-condition group to select people by. "
            "Recorded as a fiscal line from any official figure."
        ),
        data_needs=["health_condition"],
        issues=[5],
    ),
    Reform(
        id="hospital_rule",
        name="Change the 28-day hospital rule",
        description=(
            "Lengthen or remove the period after which PIP stops during an "
            "in-patient hospital stay."
        ),
        recommendation="Review the 28-day hospitalisation rule",
        likelihood=Likelihood.HIGH,
        route=Route.LEDGER,
        route_reason="No hospital stays in the data or the model.",
        data_needs=["hospital_stay"],
        issues=[5],
    ),
    Reform(
        id="cost_category_tiers",
        name="Re-tier awards (illustrative)",
        description=(
            "Illustrative stand-in for awards set by cost categories: the "
            "standard daily living rate £8.30 a week above current law and the "
            "enhanced rate £4.60 a week below it. The values are placeholders, "
            "not a proposal."
        ),
        recommendation="Awards that reflect the extra costs of disability",
        likelihood=Likelihood.MEDIUM,
        route=Route.DASHBOARD_PARAM,
        route_reason=(
            "The cash part can be approximated by changing the four rates; any "
            "non-cash support is not modelled."
        ),
        parameter_changes=merge(
            rate_change(f"{DL}.standard", _current_law_plus(f"{DL}.standard", 8.30)),
            rate_change(f"{DL}.enhanced", _current_law_plus(f"{DL}.enhanced", -4.60)),
        ),
        issues=[1],
    ),
    Reform(
        id="points_thresholds",
        name="Lower the standard-rate points threshold (illustrative)",
        description=(
            "Illustrative: the standard rate of each component from 6 points "
            "rather than 8."
        ),
        recommendation="Recalibrate activities, descriptors and points",
        likelihood=Likelihood.MEDIUM,
        route=Route.NOT_COMPUTABLE,
        route_reason=(
            "The parameter exists but moves no one: the data hold awards, not "
            "points, and a stored award overrides points."
        ),
        parameter_changes=_THRESHOLDS,
        data_needs=["pip_dl_points", "pip_m_points"],
        issues=[3],
    ),
    Reform(
        id="single_activity_minimum",
        name="Minimum score in one daily living activity",
        description=(
            "Daily living paid only to people who score at least 4 points in one "
            "activity."
        ),
        recommendation="A minimum score in one daily living activity",
        likelihood=Likelihood.LOW,
        route=Route.NOT_COMPUTABLE,
        route_reason="Needs a score for each activity, which the data do not hold.",
        data_needs=["pip_activity_points"],
        issues=[3],
    ),
    Reform(
        id="standard_daily_living_rate",
        name="Raise the standard daily living rate (illustrative)",
        description=(
            "Illustrative: standard daily living 5% above its current-law rate "
            "in each year from 2027-28."
        ),
        recommendation="Rates that contribute fairly to extra costs",
        likelihood=Likelihood.LOW,
        route=Route.DASHBOARD_PARAM,
        route_reason="A rate is a parameter; modelled directly.",
        parameter_changes=rate_change(
            f"{DL}.standard", _current_law_plus(f"{DL}.standard", factor=1.05)
        ),
        issues=[1, 4],
    ),
    Reform(
        id="uc_health_gateway",
        name="PIP as the gateway to the UC health element",
        description=(
            "A PIP daily living award, rather than a Work Capability Assessment, "
            "unlocks the Universal Credit health element."
        ),
        recommendation="PIP as the single gateway to health-related support",
        likelihood=Likelihood.MEDIUM,
        route=Route.DASHBOARD_STRUCTURAL,
        route_reason=(
            "Modelled by treating working-age people as having limited "
            "capability for work-related activity when they hold a PIP daily "
            "living award. Disability premiums in other benefits do not follow."
        ),
        simulation_modifier=uc_health_gateway.modifier,
        issues=[6, 7],
    ),
    Reform(
        id="carers_allowance_link",
        name="Carer's Allowance follows the PIP award",
        description=(
            "Carer's Allowance and the UC carer element follow the cared-for "
            "person's daily living award."
        ),
        recommendation="Knock-on to passported support",
        likelihood=Likelihood.MEDIUM,
        route=Route.LEDGER,
        route_reason=(
            "A knock-on, not a measure on its own: any measure that moves award "
            "levels applies the link (carers in the same household lose "
            "Carer's Allowance when no one there qualifies any more). Carers "
            "of someone outside the household are a fiscal line from the "
            "official figure."
        ),
        data_needs=["cared_for_outside_household"],
        issues=[2],
    ),
    Reform(
        id="existing_claimants_phasing",
        name="Apply changes at award review",
        description=(
            "New rules apply to new claims at once and to existing claimants at "
            "their next award review."
        ),
        recommendation="How recommendations apply to people already claiming",
        likelihood=Likelihood.HIGH,
        route=Route.LEDGER,
        route_reason=(
            "A rule for how other measures apply, not a measure on its own: a "
            "measure that moves award levels can be phased in at award review, "
            "with the yearly shares taken from official figures. Disability "
            "premiums in other benefits do not follow the new awards."
        ),
        issues=[7],
    ),
    Reform(
        id="transition_age_18",
        name="Move from child DLA to PIP at 18",
        description="Young people stay on child DLA until 18 rather than 16.",
        recommendation="Move from child DLA to PIP at 18",
        likelihood=Likelihood.LOW,
        # Held: measures/transition_age_18.py is written, but a national run
        # gives a net saving that a single-household check does not. Restore
        # route=DASHBOARD_STRUCTURAL and the modifier once the knock-on is found.
        route=Route.NEEDS_PE_UK_FIRST,
        route_reason=(
            "Held until a check is done: moving people aged 16 and 17 from PIP "
            "to the matching child DLA awards should leave their income "
            "unchanged, but a national run does not, and the cause is not yet "
            "found. About 133 survey records hold PIP at those ages in the "
            "certified build (eeb6093e), 146 in the newer 6f918b81 build."
        ),
    ),
]

REFORMS_BY_ID: dict[str, Reform] = {reform.id: reform for reform in REFORMS}


def get_reform(reform_id: str) -> Reform:
    try:
        return REFORMS_BY_ID[reform_id]
    except KeyError as error:
        raise KeyError(f"No measure {reform_id!r}") from error
