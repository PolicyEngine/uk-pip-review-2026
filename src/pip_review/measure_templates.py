"""Parameter builders and modifier templates, copied from the AB2026 dashboard's ``measure_templates``.

Kept: ``rate_change`` and ``threshold_change`` (the PIP rate measures),
``uc_health_element_change`` (UC health element amounts, for any knock-on
on the UC health element, #6) and ``apply_benefit_receipt_payment`` (a lump
sum to households receiving a benefit). Builders key every value by its bare
fiscal year in ASCII digits and refuse anything else, as in the source. The
other five AB2026 templates (``allowance_uprating``, ``pension_uprating``,
``apply_vat_base_change``, ``apply_age_conditioned_allowance``,
``apply_property_band_surcharge``) touch nothing a PIP measure moves and are
copied when a measure needs one. A measure built only from templates needs
no attestation.

A parameter covered by a data limit (``pip_review.data_limits``) still builds,
with a ``DataLimitedWarning``: the measure is published as not computable,
never as a figure.
"""

import math
import re
import warnings
from collections.abc import Mapping

REGISTERED_TEMPLATES = (
    "rate_change",
    "threshold_change",
    "uc_health_element_change",
    "apply_benefit_receipt_payment",
)

UC_LCWRA_AMOUNT = "gov.dwp.universal_credit.elements.disabled.amount"
UC_PROTECTED_HEALTH = "gov.dwp.universal_credit.rebalancing.protected_health_element"
UC_NEW_CLAIMANT_HEALTH = (
    "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
)
UC_REBALANCING_ACTIVE = "gov.dwp.universal_credit.rebalancing.active"
# The years policyengine-uk 2.174.1's (and 2.177.7's) UC rebalancing runs
# (policyengine_uk.scenarios.uc_reform.REBALANCING_YEARS). Literal so the
# builders load without the engine; tests/test_model_mode.py checks it
# against the installed engine.
UC_REBALANCED_YEARS = range(2026, 2033)
UC_HEALTH_ADVICE = (
    "build a UC health measure with uc_health_element_change(), which sets "
    f"{UC_PROTECTED_HEALTH} (pre-2026 claimants) and {UC_NEW_CLAIMANT_HEALTH} "
    "(new claimants)"
)
_YEAR_KEY = re.compile(r"^[0-9]{4}$")
_PATH = re.compile(r"^gov(\.[a-z0-9_]+)+$")


class DataLimitedWarning(UserWarning):
    """The parameter acts only through an input the data do not hold."""


def _validate_path(path: str) -> None:
    if not isinstance(path, str) or not _PATH.match(path):
        raise ValueError(f"Not a parameter path: {path!r}")


def _annual_values(values: Mapping) -> dict[str, float]:
    if not values:
        raise ValueError("Give at least one year")
    out: dict[str, float] = {}
    for key, value in values.items():
        key_text = str(key)
        if not _YEAR_KEY.match(key_text) or not key_text.isascii():
            raise ValueError(f"Key each value by a bare fiscal year, not {key!r}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{key}: value must be a number")
        if not math.isfinite(value):
            raise ValueError(f"{key}: value must be finite")
        out[key_text] = float(value)
    return dict(sorted(out.items()))


def _warn_if_data_limited(path: str) -> None:
    from pip_review.data_limits import limits_for_paths

    for limit in limits_for_paths([path]):
        warnings.warn(f"{path}: {limit.reason}", DataLimitedWarning, stacklevel=3)


def _refuse_uc_health_traps(path: str, years) -> None:
    """Refuse UC health changes that score nothing or the wrong thing.

    In the rebalanced years the rebalancing overwrites every claimant's
    LCWRA element, so a change to the element's own amount moves no award;
    switching the rebalancing off pays everyone the new claimants' rate.
    """
    rebalanced = [str(y) for y in years if int(y) in UC_REBALANCED_YEARS]
    if path == UC_LCWRA_AMOUNT and rebalanced:
        raise ValueError(
            f"{UC_LCWRA_AMOUNT} in {', '.join(rebalanced)} is not what UC "
            "health awards pay: the engine's UC rebalancing overwrites each "
            "claimant's element, so a change to it scores nothing; " + UC_HEALTH_ADVICE
        )
    if path == UC_REBALANCING_ACTIVE:
        raise ValueError(
            f"{UC_REBALANCING_ACTIVE} switched off is not the law before the "
            "Universal Credit Act 2025; " + UC_HEALTH_ADVICE
        )


def rate_change(path: str, values: Mapping) -> dict[str, dict[str, float]]:
    """A rate or amount set for each fiscal year, for example a PIP weekly rate."""
    _validate_path(path)
    built = {path: _annual_values(values)}
    _refuse_uc_health_traps(path, built[path])
    _warn_if_data_limited(path)
    return built


def threshold_change(path: str, values: Mapping) -> dict[str, dict[str, float]]:
    """A threshold set for each fiscal year, for example a points threshold."""
    return rate_change(path, values)


def merge(*changes: Mapping[str, Mapping[str, float]]) -> dict[str, dict[str, float]]:
    """Merge builder outputs, refusing two values for one parameter."""
    merged: dict[str, dict[str, float]] = {}
    for change in changes:
        for path, years in change.items():
            if path in merged:
                raise ValueError(f"{path} is set twice")
            merged[path] = dict(years)
    return merged


def uc_health_element_change(
    *, protected: Mapping | None = None, new_claimant: Mapping | None = None
) -> dict[str, dict[str, float]]:
    """Change Universal Credit's health (LCWRA) element as the model pays it.

    In the rebalanced years the engine sets each claimant's element from the
    rebalancing amounts: ``protected`` for pre-2026 claimants and
    ``new_claimant`` for those who claim from April 2026. Values are monthly
    amounts in pounds by fiscal year, only for the rebalanced years.
    """
    changes = {}
    for path, values in (
        (UC_PROTECTED_HEALTH, protected),
        (UC_NEW_CLAIMANT_HEALTH, new_claimant),
    ):
        if values is None:
            continue
        annual = _annual_values(values)
        outside = [y for y in annual if int(y) not in UC_REBALANCED_YEARS]
        if outside:
            raise ValueError(
                f"{path} is used only in {UC_REBALANCED_YEARS.start}-"
                f"{UC_REBALANCED_YEARS.stop - 1}; a value for "
                f"{', '.join(outside)} would score nothing"
            )
        changes[path] = annual
    if not changes:
        raise ValueError("Supply protected or new_claimant amounts")
    return changes


# Receipt selectors for apply_benefit_receipt_payment, as in AB2026. The two
# Pension Credit components are entitlement amounts, so they also need the
# native receipt gate.
BENEFIT_RECEIPT_GATES = {
    "universal_credit": None,
    "guarantee_credit": "in_receipt_of_guarantee_credit",
    "savings_credit": "pension_credit",
    "housing_benefit": None,
    "esa_income": None,
    "pip": None,
}


def apply_benefit_receipt_payment(
    sim, *, amount, eligible_benefits, geography, channel, year
):
    """Add a lump sum once per household that receives an eligible benefit.

    Receipt on a payment date is approximated by annual receipt. ``geography``
    is ``GB`` (excludes Northern Ireland), ``UK`` or ``EW`` (England and
    Wales, for PIP). ``channel`` is an existing annual household variable
    with a formula; its native value is kept in every year. Ported from
    AB2026 without the receipt-rate draw; add it from there if a measure
    pays only a share of eligible households.
    """
    import numpy as np

    from pip_review.formula_override import replace_formula

    if type(year) is not int:
        raise ValueError("year must be an int")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")
    if not math.isfinite(amount) or amount < 0:
        raise ValueError("amount must be finite and nonnegative")
    if geography not in ("GB", "UK", "EW"):
        raise ValueError("geography must be GB, UK or EW")
    if (
        isinstance(eligible_benefits, str)
        or not isinstance(eligible_benefits, (list, tuple))
        or not eligible_benefits
    ):
        raise ValueError("Select a nonempty list of eligible benefit variables")
    native = sim.tax_benefit_system.get_variable(channel, check_existence=True)
    if native.entity.key != "household" or not native.formulas:
        raise ValueError("Payment channel must have a household formula")
    benefits = {}
    for name in eligible_benefits:
        if name not in BENEFIT_RECEIPT_GATES:
            raise ValueError(
                f"Unsupported receipt selector: {name}; choose "
                + ", ".join(BENEFIT_RECEIPT_GATES)
            )
        variable = sim.tax_benefit_system.get_variable(name, check_existence=True)
        benefits[name] = variable.entity.key

    def formula(household, period, parameters, previous):
        if period.start.year != year:
            return previous
        eligible = np.zeros(household.count, dtype=bool)
        for name, entity in benefits.items():
            if entity == "household":
                positive = household(name, period) > 0
            elif entity == "person":
                positive = household.any(household.members(name, period) > 0)
            else:
                received = household.members.benunit(name, period) > 0
                gate = BENEFIT_RECEIPT_GATES[name]
                if gate is not None:
                    received &= household.members.benunit(gate, period) > 0
                positive = household.any(received)
            eligible |= positive
        country = household("country", period)
        values = country.possible_values
        if geography == "GB":
            eligible &= country != values.NORTHERN_IRELAND
        elif geography == "EW":
            eligible &= (country == values.ENGLAND) | (country == values.WALES)
        return previous + eligible * amount

    replace_formula(sim, channel, formula)
    return sim
