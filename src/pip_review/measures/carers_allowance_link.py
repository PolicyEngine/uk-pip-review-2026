"""Carer's Allowance follows the cared-for person's award (issue #2).

A knock-on for measures that move award categories, not a measure on its
own: chain it after a category modifier with ``after(modifier)``. In
policyengine-uk 2.174.1 and 2.177.7 ``carers_allowance_pre_overlap`` (through
``carers_allowance_pre_couple_limit``, as 2.151.0 did directly) tests reported
receipt, age, hours, earnings and country, never the cared-for person's
award. This wraps it: a carer's allowance is set to zero when their
household had a qualifying person (``is_severely_disabled_for_carers_allowance``)
under the stored, current-law categories and has none after the measure.
Carers with no qualifying person in the household are left unchanged; the
DWP figure for carers of someone outside the household stays a ledger line.

``carers_allowance_pre_overlap`` is a formula variable and is not stored in
the national file, so it can be wrapped.

The UC carer element does not follow Carer's Allowance by itself. It is
included for a claimant with ``is_carer_for_benefits``
(``uc_carer_element_included_for_claimant``), which is true for anyone with 35
or more hours of care (``care_hours``), or a reported Carer's Allowance award
they would claim, as well as for anyone paid or entitled to a carer benefit.
Zeroing the allowance leaves the hours and reported-award limbs, so the
element would stay. The link therefore also wraps ``is_carer_for_benefits``
and sets it to false for the same people, so the UC carer element (and the
other rules that read it) follows the cared-for person's award too.

Known limit: only carers in the same household as the person whose award
changes are reached. A carer of someone in another household keeps both the
allowance and the UC carer element; reaching them needs a share-based
adjustment or the cared-for link proposed in policyengine-uk#2889 (item 5).
A carer in a household that loses its last qualifying person is treated as
caring for that person, even if they also care for someone elsewhere.
"""

VARIABLE = "carers_allowance_pre_overlap"
CARER_FLAG = "is_carer_for_benefits"
# Stored inputs that decide the qualifying benefits under current law.
CATEGORY_INPUTS = ("pip_dl_category", "dla_sc_category")
QUALIFYING = {
    "pip_dl_category": ("STANDARD", "ENHANCED"),
    "dla_sc_category": ("MIDDLE", "HIGHER"),
}
OTHER_QUALIFYING = ("attendance_allowance", "afcs")


def _stored(sim, name, year):
    """The category in ``year`` under current law: the stored input, or, on
    a build that stores assessment points and no category (9e18f010), the
    category policyengine-uk derives from them. Read before any category
    modifier runs, so it is the current-law category."""
    import numpy as np

    holder = sim.get_holder(name)
    array = holder.get_array(year)
    if array is None and name in sim.tax_benefit_system.variables:
        array = sim.calculate(name, year)
        array = getattr(array, "values", array)
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

    def lost(person, period):
        """Per person: their household had a qualifying person and has none."""
        stored = before.get(period.start.year)
        if stored is None:
            return None
        other = np.zeros(person.count, dtype=bool)
        for name in OTHER_QUALIFYING:
            if name in person.simulation.tax_benefit_system.variables:
                other |= person(name, period) > 0
        household = person.simulation.populations["household"]
        had = household.any(stored | other)
        has = household.any(person("is_severely_disabled_for_carers_allowance", period))
        return household.project(had & ~has)

    def allowance(person, period, parameters, previous):
        hit = lost(person, period)
        return previous if hit is None else np.where(hit, 0.0, previous)

    def carer_flag(person, period, parameters, previous):
        hit = lost(person, period)
        return previous if hit is None else previous & ~hit

    replace_formula(sim, VARIABLE, allowance)
    replace_formula(sim, CARER_FLAG, carer_flag)


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
