"""Apply a category measure at award review, not to everyone at once (issue #7).

``phase(category_modifier, shares)`` wraps a modifier that changes PIP award
categories. In each policy year only a seeded share of the people whose
award it changes take the new award; the rest keep the current-law award.
``shares`` maps a fiscal year to the cumulative share reached by then (new
claims plus award reviews), for example from DWP's review schedule.

The draw is policyengine-uk's deterministic hash of the person id
(``splitmix64_uniform``, salt ``SALT``), so a person who moves in one year
stays moved in later years when the share does not fall. This phases award
categories, so every knock-on that reads them follows; the engine's own
``pip_reform`` scenario overwrites ``pip`` and bypasses them.

Build 6f918b81 does not store ``is_severely_disabled_for_benefits``, so its
formula follows the phased categories. Not done here: recomputing the stored
flags (``is_enhanced_disabled_for_benefits`` and ``is_disabled_for_benefits``)
from the new categories. That needs the same change in the current-law run as
well, and ``is_disabled_for_benefits`` has no formula at all, so it stays
fixed.
"""

CATEGORIES = ("pip_dl_category", "pip_m_category")
SALT = 1_407


def _strings(values):
    import numpy as np

    values = getattr(values, "values", values)
    if hasattr(values, "decode_to_str"):
        return np.asarray(values.decode_to_str())
    return np.asarray(values).astype(str)


def phase(category_modifier, shares):
    for year, share in shares.items():
        if type(year) is not int or not 0 <= float(share) <= 1:
            raise ValueError("shares maps int years to a share between 0 and 1")

    def modifier(sim):
        import numpy as np
        from policyengine_uk.utils.stochastic import splitmix64_uniform

        before = {
            (name, year): _strings(sim.calculate(name, year))
            for name in CATEGORIES
            for year in shares
        }
        category_modifier(sim)
        ids = np.asarray(getattr(sim.calculate("person_id", min(shares)), "values"))
        draw = splitmix64_uniform(ids.astype(np.uint64), salt=SALT)
        for year, share in shares.items():
            moves = draw < float(share)
            for name in CATEGORIES:
                after = _strings(sim.calculate(name, year))
                kept = np.where(moves, after, before[(name, year)])
                if (kept != after).any():
                    sim.set_input(name, year, kept)

    return modifier
