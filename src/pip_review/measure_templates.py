"""Parameter builders, pruned from the AB2026 dashboard's ``measure_templates``.

Only the two builders the PIP measures use are kept: ``rate_change`` and
``threshold_change``. Both key every value by its bare fiscal year in ASCII
digits and refuse anything else, as in the source. The other seven registered
templates (``uc_health_element_change``, ``allowance_uprating``,
``pension_uprating``, ``apply_vat_base_change``,
``apply_benefit_receipt_payment``, ``apply_age_conditioned_allowance``,
``apply_property_band_surcharge``) are copied from the AB2026 repository when
a measure needs one. A measure built only from templates needs no attestation.

A parameter covered by a data limit (``pip_review.data_limits``) still builds,
with a ``DataLimitedWarning``: the measure is published as not computable,
never as a figure.
"""

import math
import re
import warnings
from collections.abc import Mapping

REGISTERED_TEMPLATES = ("rate_change", "threshold_change")
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
        warnings.warn(
            f"{path}: {limit.reason}", DataLimitedWarning, stacklevel=3
        )


def rate_change(path: str, values: Mapping) -> dict[str, dict[str, float]]:
    """A rate or amount set for each fiscal year, for example a PIP weekly rate."""
    _validate_path(path)
    built = {path: _annual_values(values)}
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
