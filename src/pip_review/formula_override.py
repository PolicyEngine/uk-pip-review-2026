"""Replace one variable's formula on one simulation, as AB2026's templates do.

Ported from the AB2026 dashboard's ``measure_templates`` (``_replace_formula``,
``_call_formula``, ``_ensure_not_stored``). A wrapper is refused when core
would not run the formula: a stored input (the data would bypass it), a
neutralised variable, or one built from ``adds`` or ``subtracts``.

Needs the ``model`` extra; imported only by modifiers at run time.
"""


def stored_input_periods(sim, variable: str) -> set:
    """Periods with a supplied input, excluding cached formula results."""
    return set(sim.get_holder(variable).get_input_periods(sim.branch_name))


def ensure_not_stored(sim, variable: str) -> None:
    if stored_input_periods(sim, variable):
        raise ValueError(
            f"{variable} is a stored input; a formula override would be bypassed"
        )


def call_formula(variable, entity, period, parameters):
    """A variable's previous value, computed as policyengine-core does."""
    formula = variable.get_formula(period)
    if formula is None:
        return entity.filled_array(variable.default_value)
    if formula.__code__.co_argcount == 2:
        return formula(entity, period)
    return formula(entity, period, parameters)


def take_stored(sim, name: str) -> dict:
    """Remove ``name``'s stored inputs from the simulation and return them,
    by period string, so a wrapper can use them as the previous value."""
    import numpy as np

    holder = sim.get_holder(name)
    taken = {}
    for period in sorted(stored_input_periods(sim, name), key=str):
        taken[str(period)] = np.asarray(holder.get_array(period, sim.branch_name))
        sim.delete_arrays(name, period)
    return taken


def replace_formula(sim, name: str, formula, keep_stored: bool = False) -> None:
    """Replace ``name``'s formula on this simulation only.

    ``formula(entity, period, parameters, previous)`` receives the previous
    variable's value as ``previous``. A stored input is refused, as the data
    would bypass the formula, unless ``keep_stored``: then the stored values
    are taken out of the simulation and passed as ``previous`` in the periods
    they cover, and the old formula gives ``previous`` elsewhere.
    """
    from policyengine_core.reforms import Reform as CoreReform
    from policyengine_uk.model_api import Variable
    from policyengine_uk.utils.scenario import _apply_reform_class

    stored = take_stored(sim, name) if keep_stored else {}
    ensure_not_stored(sim, name)
    current = sim.tax_benefit_system.get_variable(name)
    if getattr(current, "is_neutralized", False):
        raise ValueError(f"{name} is neutralised; a template cannot wrap it")
    if current.adds or current.subtracts:
        raise ValueError(f"{name} is built from adds or subtracts; cannot wrap it")

    def wrapped(entity, period, parameters):
        if str(period) in stored:
            previous = stored[str(period)]
        else:
            previous = call_formula(current, entity, period, parameters)
        return formula(entity, period, parameters, previous)

    replacement = type(name, (Variable,), {"formula": wrapped, "__module__": __name__})

    class FormulaReform(CoreReform):
        def apply(self):
            self.update_variable(replacement)

    _apply_reform_class(FormulaReform, sim)
