"""Drill 6 (mock): enhanced daily living as the only test for the UC health element from 2029-30.

From fiscal year ``FROM_YEAR`` working-age people (16 to below State Pension
age) have limited capability for work-related activity exactly when they hold
an enhanced daily living award; everyone else of working age loses it, so the
UC health element (protected and new-claimant amounts) follows the award.
Before ``FROM_YEAR`` and above State Pension age the model's own
determination is kept. The fast-track route is not modelled (no condition
data). Literal defaults, no runtime state.

policyengine-uk's UC rebalancing stores ``uc_LCWRA_element`` as an input in
each rebalanced year when the simulation is built, so a change to the flag
alone moves no award. For each policy year from ``FROM_YEAR`` this
recomputes the element through its formula with the new flag, then pays a
benefit unit that had an element its stored (rebalanced) amount and a benefit
unit that newly gains one the new-claimant amount; units that lose the test
get nothing.
"""

QUALIFYING_AWARDS = ("ENHANCED",)
FROM_YEAR = 2029
VARIABLE = "uc_limited_capability_for_WRA"


def modifier(sim, qualifying_awards=QUALIFYING_AWARDS, from_year=FROM_YEAR):
    import numpy as np

    from pip_review.formula_override import replace_formula

    def formula(person, period, parameters, previous):
        if period.start.year < from_year:
            return previous
        category = person("pip_dl_category", period).decode_to_str()
        qualifies = np.isin(category, list(qualifying_awards))
        working_age = (person("age", period) >= 16) & ~person("is_SP_age", period)
        return np.where(working_age, qualifies, previous)

    replace_formula(sim, VARIABLE, formula)

    from policyengine_uk.scenarios.uc_reform import REBALANCING_YEARS
    from policyengine_uk.utils.supplied_inputs import set_model_value

    from pip_review.years import POLICY_YEARS

    rebalancing = sim.tax_benefit_system.parameters.gov.dwp.universal_credit.rebalancing
    for year in POLICY_YEARS:
        if year < from_year or year not in REBALANCING_YEARS:
            continue
        before = np.array(sim.calculate("uc_LCWRA_element", year))
        sim.delete_arrays(VARIABLE, year)
        sim.delete_arrays("uc_LCWRA_element", year)
        has = np.array(sim.calculate("uc_LCWRA_element", year)) > 0
        new_amount = float(rebalancing.new_claimant_health_element(year)) * 12
        after = np.where(has, np.where(before > 0, before, new_amount), 0.0)
        set_model_value(sim, "uc_LCWRA_element", year, after)
