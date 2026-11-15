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
from pip_review.measures import mock6_uc_health_gateway, uc_health_gateway  # noqa: F401
from pip_review.models import InReport, Likelihood, Reform, Route
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
    # Drill 6 (mock): the template placeholders are replaced by the mock
    # statement's measures. Every id starts mock6_. Rates are cash levels by
    # fiscal year: the stated 2027-28 rate, then the previous year's rate times
    # the installed CPI uprating factor, rounded to the nearest 5p.
    Reform(
        id="mock6_dl_standard_rate",
        name="Raise the standard daily living rate (mock R6)",
        description="Standard daily living £84.00 a week from April 2027, then CPI uprated and rounded to 5p.",
        recommendation="R6 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.DASHBOARD_PARAM,
        route_reason="A rate is a parameter; modelled directly.",
        parameter_changes=rate_change(
            f"{DL}.standard", {2027: 84.00, 2028: 86.85, 2029: 88.60, 2030: 90.55}
        ),
        issues=[1, 4],
    ),
    Reform(
        id="mock6_m_standard_rate",
        name="Raise the standard mobility rate (mock R7)",
        description="Standard mobility £34.50 a week from April 2027 (corrected at 15:15), then CPI uprated and rounded to 5p.",
        recommendation="R7 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.DASHBOARD_PARAM,
        route_reason="A rate is a parameter; modelled directly.",
        parameter_changes=rate_change(
            f"{MOB}.standard", {2027: 34.50, 2028: 35.65, 2029: 36.35, 2030: 37.15}
        ),
        issues=[1, 4],
    ),
    Reform(
        id="mock6_dl_enhanced_hold",
        name="Hold the enhanced daily living rate in 2027-28 and 2028-29 (mock R10)",
        description="Enhanced daily living held at £114.60 in 2027-28 and 2028-29 (corrected at 15:15); CPI uprating from April 2029 on £114.60, rounded to 5p.",
        recommendation="R10 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.DASHBOARD_PARAM,
        route_reason="A rate is a parameter; modelled directly.",
        parameter_changes=rate_change(
            f"{DL}.enhanced", {2027: 114.60, 2028: 114.60, 2029: 116.90, 2030: 119.45}
        ),
        issues=[1, 4],
    ),
    Reform(
        id="mock6_uc_health_gateway",
        name="Enhanced daily living as the UC health element test (mock R11)",
        description="From April 2029, only an enhanced daily living award (or the fast track) gives the UC health element.",
        recommendation="R11 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.DASHBOARD_STRUCTURAL,
        route_reason=(
            "Modelled by setting limited capability for work-related activity, "
            "for working-age people from 2029-30, to whether they hold an "
            "enhanced daily living award. The fast-track route is not modelled "
            "(no condition data); disability premiums in other benefits do not follow."
        ),
        simulation_modifier=mock6_uc_health_gateway.modifier,
        issues=[5, 6, 7],
    ),
    Reform(
        id="mock6_fluctuating",
        name="Fluctuating conditions test (mock R1)",
        recommendation="R1 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.NOT_COMPUTABLE,
        route_reason="Acts through descriptors and the share of days they apply; the data hold awards, not points.",
        data_needs=['pip_dl_points', 'pip_m_points'],
        issues=[3],
    ),
    Reform(
        id="mock6_aids_points",
        name="Aids and appliances score 1 point (mock R2)",
        recommendation="R2 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.NOT_COMPUTABLE,
        route_reason="A points measure; the data hold awards, not points.",
        data_needs=['pip_dl_points', 'pip_m_points'],
        issues=[3],
    ),
    Reform(
        id="mock6_fast_track",
        name="Fast track for serious conditions (mock R3)",
        recommendation="R3 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.NOT_COMPUTABLE,
        route_reason="The data have no health-condition group to select people by.",
        data_needs=['health_condition'],
        issues=[5],
    ),
    Reform(
        id="mock6_ongoing_awards",
        name="Ongoing awards for lifelong conditions (mock R4)",
        recommendation="R4 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="Changes flows on and off PIP over time; the model is static.",
        data_needs=[],
        issues=[],
    ),
    Reform(
        id="mock6_hospital_84_days",
        name="PIP for 84 days in hospital (mock R5)",
        recommendation="R5 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="No hospital stays in the data or the model.",
        data_needs=[],
        issues=[5],
    ),
    Reform(
        id="mock6_carers_either_component",
        name="Carer's Allowance for either component (mock R8)",
        recommendation="R8 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="Carer's Allowance in the model does not test the cared-for person's award, so carer effects are a ledger line.",
        data_needs=[],
        issues=[2],
    ),
    Reform(
        id="mock6_advocacy",
        name="Independent advocacy service (mock R9)",
        recommendation="R9 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="Departmental spending on a service, not a benefit rule.",
        data_needs=[],
        issues=[],
    ),
    Reform(
        id="mock6_existing_claimants",
        name="Existing claimants at award review (mock R12)",
        recommendation="R12 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="A rule for how other measures apply; the assessment measures it phases are not computable.",
        data_needs=[],
        issues=[7],
    ),
    Reform(
        id="mock6_transitional_protection",
        name="52-week transitional protection (mock R13)",
        recommendation="R13 (mock)",
        likelihood=Likelihood.HIGH,
        in_report=InReport.YES,
        route=Route.LEDGER,
        route_reason="Protects award falls from the assessment measures, which are not computable; the model holds no review dates.",
        data_needs=[],
        issues=[7],
    ),
]

REFORMS_BY_ID: dict[str, Reform] = {reform.id: reform for reform in REFORMS}


def get_reform(reform_id: str) -> Reform:
    try:
        return REFORMS_BY_ID[reform_id]
    except KeyError as error:
        raise KeyError(f"No measure {reform_id!r}") from error
