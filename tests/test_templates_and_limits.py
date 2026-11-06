import warnings

import pytest

from pip_review import data_limits, model_limits
from pip_review.measure_templates import (
    REGISTERED_TEMPLATES,
    DataLimitedWarning,
    merge,
    rate_change,
    threshold_change,
)


def test_registered_templates():
    assert REGISTERED_TEMPLATES == ("rate_change", "threshold_change")


def test_rate_change_keys_by_bare_year():
    built = rate_change("gov.dwp.pip.mobility.standard", {2027: 31, 2028: 32.5})
    assert built == {"gov.dwp.pip.mobility.standard": {"2027": 31.0, "2028": 32.5}}


@pytest.mark.parametrize("bad", [{"2027-04-01": 1.0}, {"27": 1.0}, {}])
def test_rate_change_refuses_other_keys(bad):
    with pytest.raises(ValueError):
        rate_change("gov.dwp.pip.mobility.standard", bad)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "1"])
def test_rate_change_refuses_bad_values(bad):
    with pytest.raises((ValueError, TypeError)):
        rate_change("gov.dwp.pip.mobility.standard", {2027: bad})


def test_rate_change_refuses_bad_path():
    with pytest.raises(ValueError):
        rate_change("pip.mobility", {2027: 1})


def test_threshold_change_warns_when_data_limited():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        threshold_change(
            "gov.dwp.pip.daily_living.points_thresholds.standard", {2027: 6}
        )
    assert any(issubclass(w.category, DataLimitedWarning) for w in caught)


def test_rate_change_does_not_warn_for_rates():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DataLimitedWarning)
        rate_change("gov.dwp.pip.daily_living.standard", {2027: 80})


def test_merge_refuses_duplicates():
    a = rate_change("gov.dwp.pip.mobility.standard", {2027: 31})
    with pytest.raises(ValueError):
        merge(a, a)


def test_points_limits_live():
    keys = {limit.key for limit in data_limits.LIMITS}
    assert {"pip_daily_living_points", "pip_mobility_points"} <= keys
    assert data_limits.limits_for_paths(
        ["gov.dwp.pip.mobility.points_thresholds.enhanced"]
    )
    assert not data_limits.limits_for_paths(["gov.dwp.pip.mobility.enhanced"])
    assert not data_limits.is_only_data_limited([])


def test_model_limits_cover_pip_rates():
    found = model_limits.limits_for_paths(["gov.dwp.pip.daily_living.standard"])
    assert [limit.key for limit in found] == ["pip_no_country_test"]
    assert model_limits.limits_for_paths(
        [model_limits.variable_path("carers_allowance")]
    )
