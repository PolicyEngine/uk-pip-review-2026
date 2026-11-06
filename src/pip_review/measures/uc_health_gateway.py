"""PIP as the gateway to the UC health element (issue #6).

Working-age people (16 to below State Pension age) are treated as having
limited capability for work-related activity exactly when they hold a
qualifying PIP daily living award, in place of the Work Capability
Assessment flag. Other people keep the model's own determination.

``uc_limited_capability_for_WRA`` is a formula variable and is not stored in
the national file, so it can be wrapped here. The award that qualifies is a
literal default; change it in this module only. Placeholder until the
report's own rule is known.
"""

QUALIFYING_AWARDS = ("STANDARD", "ENHANCED")
VARIABLE = "uc_limited_capability_for_WRA"


def modifier(sim, qualifying_awards=QUALIFYING_AWARDS):
    import numpy as np

    from pip_review.formula_override import replace_formula

    def formula(person, period, parameters, previous):
        category = person("pip_dl_category", period).decode_to_str()
        qualifies = np.isin(category, list(qualifying_awards))
        working_age = (person("age", period) >= 16) & ~person("is_SP_age", period)
        return np.where(working_age, qualifies, previous)

    replace_formula(sim, VARIABLE, formula)
