"""PIP as the gateway to the UC health element (issue #6).

Working-age people (16 to below State Pension age) are treated as having
limited capability for work-related activity exactly when they hold a
qualifying PIP daily living award, in place of the Work Capability
Assessment flag. Other people keep the model's own determination.

``uc_limited_capability_for_WRA`` is a formula variable. Microcosm build
9e18f010 stores it as an input (eeb6093e did not), so the wrapper takes the
stored values out of the simulation and uses them as the model's own
determination for the people it does not override (``keep_stored``); on a
file without it, the formula gives that value as before. The award that
qualifies is a literal default; change it in this module only. Placeholder
until the report's own rule is known.

On 9e18f010 ``pip_dl_category`` is not stored either: it is derived from the
stored assessment points, which the wrapper reads in the same way.

The UC rebalancing step in policyengine-uk 2.174.1 and 2.177.7
(``policyengine_uk/scenarios/uc_reform.py``, ``add_universal_credit_reform``)
runs while the simulation is built, before this modifier. For every year in
``REBALANCING_YEARS`` (2026 to the end of the projection) it calculates
``uc_LCWRA_element`` and stores the result as an input, so a later change to
the limited-capability flag would not reach those years' awards. The modifier
therefore drops the element the step stored (the model's own value, not a
user's entry) and runs the step again over the wrapped flag. The step reads
back the new-claimant status it stored the first time and redraws the same
seed, so each benefit unit keeps its protected or new-claimant amount; only
who has the element changes. The scenario file is the same in
policyengine-uk 2.177.7, and the household tests pass on both versions.

Order matters: the rerun stores the element again, so a modifier that runs
after this one and moves ``pip_dl_category`` would not reach the stored
element. Chain this modifier last, or call ``rerun_uc_rebalancing`` again
after any later category move.
"""

QUALIFYING_AWARDS = ("STANDARD", "ENHANCED")
VARIABLE = "uc_limited_capability_for_WRA"
ELEMENT = "uc_LCWRA_element"


def modifier(sim, qualifying_awards=QUALIFYING_AWARDS):
    import numpy as np

    from pip_review.formula_override import replace_formula

    def formula(person, period, parameters, previous):
        category = person("pip_dl_category", period).decode_to_str()
        qualifies = np.isin(category, list(qualifying_awards))
        working_age = (person("age", period) >= 16) & ~person("is_SP_age", period)
        return np.where(working_age, qualifies, previous)

    replace_formula(sim, VARIABLE, formula, keep_stored=True)
    rerun_uc_rebalancing(sim)


def rerun_uc_rebalancing(sim):
    """Recompute the UC health element the rebalancing step stored.

    Without this the gateway moves no award in the rebalanced years. A
    year whose element was supplied by the user keeps that entry, as the
    step itself does.
    """
    from policyengine_core.periods import period
    from policyengine_uk.scenarios.uc_reform import (
        REBALANCING_YEARS,
        add_universal_credit_reform,
    )
    from policyengine_uk.utils.supplied_inputs import supplied_input

    population = sim.get_variable_population(ELEMENT)
    for year in REBALANCING_YEARS:
        if supplied_input(population, ELEMENT, period(year)) is None:
            sim.delete_arrays(ELEMENT, year)
    add_universal_credit_reform(sim)
