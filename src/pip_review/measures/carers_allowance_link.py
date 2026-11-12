"""Carer's Allowance follows the cared-for person's award (issue #2).

A knock-on for measures that move award categories, not a measure on its
own: chain it after a category modifier with ``after(modifier)``. In
policyengine-uk 2.174.1 ``carers_allowance_pre_overlap`` (through
``carers_allowance_pre_couple_limit``, as 2.151.0 did directly) tests reported
receipt, age, hours, earnings and country, never the cared-for person's
award. This wraps it: a carer's allowance is set to zero when their
household had a qualifying person (``is_severely_disabled_for_carers_allowance``)
under the stored, current-law categories and has none after the measure.
Carers with no qualifying person in the household are left unchanged; the
DWP figure for carers of someone outside the household stays a ledger line.

``carers_allowance_pre_overlap`` is a formula variable and is not stored in
the national file, so it can be wrapped.
"""

VARIABLE = "carers_allowance_pre_overlap"
# Stored inputs that decide the qualifying benefits under current law.
CATEGORY_INPUTS = ("pip_dl_category", "dla_sc_category")
QUALIFYING = {
    "pip_dl_category": ("STANDARD", "ENHANCED"),
    "dla_sc_category": ("MIDDLE", "HIGHER"),
}
OTHER_QUALIFYING = ("attendance_allowance", "afcs")


def _stored(sim, name, year):
    import numpy as np

    holder = sim.get_holder(name)
    array = holder.get_array(year)
    if array is None:
        return None
    if hasattr(array, "decode_to_str"):
        return np.asarray(array.decode_to_str())
    return np.asarray(array)


def snapshot(sim, years):
    """Per person and year: qualifying under the stored categories."""
    import numpy as np

    out = {}
    for year in years:
        qualifies = None
        for name in CATEGORY_INPUTS:
            values = _stored(sim, name, year)
            if values is None:
                continue
            hit = np.isin(values, QUALIFYING[name])
            qualifies = hit if qualifies is None else qualifies | hit
        out[year] = qualifies
    return out


def _apply_with(sim, before):
    import numpy as np

    from pip_review.formula_override import replace_formula

    def formula(person, period, parameters, previous):
        stored = before.get(period.start.year)
        if stored is None:
            return previous
        other = np.zeros(person.count, dtype=bool)
        for name in OTHER_QUALIFYING:
            if name in person.simulation.tax_benefit_system.variables:
                other |= person(name, period) > 0
        household = person.simulation.populations["household"]
        had = household.any(stored | other)
        has = household.any(person("is_severely_disabled_for_carers_allowance", period))
        lost = household.project(had & ~has)
        return np.where(lost, 0.0, previous)

    replace_formula(sim, VARIABLE, formula)


def modifier(sim, years=None):
    """The link on its own: the stored categories at application time."""
    from pip_review.years import POLICY_YEARS

    _apply_with(sim, snapshot(sim, years or POLICY_YEARS))


def after(category_modifier, years=None):
    """A modifier that runs ``category_modifier`` with this link applied.

    The snapshot is taken before the category modifier runs, so it records
    current-law categories.
    """

    def chained(sim):
        from pip_review.years import POLICY_YEARS

        before = snapshot(sim, years or POLICY_YEARS)
        category_modifier(sim)
        _apply_with(sim, before)

    return chained
