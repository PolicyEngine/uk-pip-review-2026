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

On policyengine-uk 2.177.7 the caring-hours route to Carer's Allowance and
to ``is_carer_for_benefits`` also needs ``cares_for_severely_disabled_person``
(default true), and a reported award counts whatever it says. Build 6f918b81
stores that flag, true for carers, and it does not follow the cared-for
person's award, so it would keep both payments. The link therefore overrides
the two outputs above, not the flag: for the people it reaches, a stored true
flag no longer pays either.

On a build that stores assessment points and no category, a measure can move
awards through a points threshold, a parameter that is already reformed when
the snapshot is taken. The snapshot therefore derives the current-law award
from the stored points against current-law thresholds.

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


# Category variables policyengine-uk derives from stored assessment points
# when no category is stored, and the component each belongs to.
POINTS_COMPONENT = {"pip_dl_category": "dl", "pip_m_category": "m"}


def _current_law_from_points(sim, name, year):
    """The category in ``year`` derived from the stored points against
    current-law thresholds (``policyengine_uk``'s default parameters), not
    the simulation's: a measure that moves a points threshold has already
    changed the simulation's parameters when the snapshot is taken, and the
    category derived from them would be the reformed one."""
    import numpy as np
    from policyengine_core.periods import period as as_period
    from policyengine_uk import tax_benefit_system as current_law
    from policyengine_uk.utils.pip import pip_category
    from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory

    component = POINTS_COMPONENT[name]
    branch = "daily_living" if component == "dl" else "mobility"
    when = as_period(str(year))
    thresholds = getattr(
        current_law.parameters(when).gov.dwp.pip, branch
    ).points_thresholds
    index = np.asarray(
        pip_category(sim.populations["person"], when, thresholds, component)
    )
    return np.array([c.name for c in PIPCategory])[index]


def _stored(sim, name, year):
    """The category in ``year`` under current law: the stored input, or, on
    a build that stores assessment points and no category (6f918b81), the
    category policyengine-uk derives from them against current-law
    thresholds. Read before any category modifier runs, so it is the
    current-law category."""
    import numpy as np

    from pip_review.formula_override import stored_input_periods

    if name not in sim.tax_benefit_system.variables:
        return None
    if str(year) in {str(p) for p in stored_input_periods(sim, name)}:
        array = sim.get_holder(name).get_array(year)
    elif name in POINTS_COMPONENT:
        return _current_law_from_points(sim, name, year)
    else:
        array = sim.calculate(name, year)
        array = getattr(array, "values", array)
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
