"""Move from child DLA to PIP at 18 rather than 16.

For people aged 16 or 17 in each policy year, PIP awards are replaced by
child DLA awards mapped from them (daily living enhanced to DLA care highest,
standard to middle; mobility enhanced to DLA mobility higher, standard to
lower), and their PIP awards are set to none.

Caveat: in build uk-frs-calibration-attempt-20261112T133744Z-6f918b81, 146
Microcosm rows hold PIP at 16 or 17, from only 32 distinct survey households
(rows, not survey records: the national file holds about 78k household rows
from about 16k survey households), so any figure carries a sample-size note. Placeholder until the report's own
rule is known.

Open check before any use: on a single household the move leaves net income
unchanged (DLA and PIP rates match), but a national timing run on 6 November
showed a large net saving for this measure. Find which knock-on differs
between PIP and child DLA at 16 and 17 before publishing it.
"""

AGES = (16, 17)
DL_TO_DLA_CARE = {"ENHANCED": "HIGHER", "STANDARD": "MIDDLE", "NONE": "NONE"}
M_TO_DLA_MOBILITY = {"ENHANCED": "HIGHER", "STANDARD": "LOWER", "NONE": "NONE"}


def _as_str(values):
    import numpy as np

    values = getattr(values, "values", values)
    if hasattr(values, "decode_to_str"):
        return np.asarray(values.decode_to_str())
    return np.asarray(values).astype(str)


def modifier(sim, years=None):
    import numpy as np

    from pip_review.years import POLICY_YEARS

    for year in years or POLICY_YEARS:
        age = sim.calculate("age", year)
        age = np.asarray(getattr(age, "values", age))
        young = np.isin(age, AGES)
        if not young.any():
            continue
        dl = _as_str(sim.calculate("pip_dl_category", year))
        mob = _as_str(sim.calculate("pip_m_category", year))
        care = _as_str(sim.calculate("dla_sc_category", year))
        dla_m = _as_str(sim.calculate("dla_m_category", year))
        care = np.where(young, [DL_TO_DLA_CARE[c] for c in dl], care)
        dla_m = np.where(young, [M_TO_DLA_MOBILITY[c] for c in mob], dla_m)
        sim.set_input("dla_sc_category", year, care)
        sim.set_input("dla_m_category", year, dla_m)
        sim.set_input("pip_dl_category", year, np.where(young, "NONE", dl))
        sim.set_input("pip_m_category", year, np.where(young, "NONE", mob))
