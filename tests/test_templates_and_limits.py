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
    assert REGISTERED_TEMPLATES == (
        "rate_change",
        "threshold_change",
        "uc_health_element_change",
        "apply_benefit_receipt_payment",
    )


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


def test_threshold_change_warns_when_data_limited(monkeypatch):
    # On a build without points (eeb6093e) a threshold change warns.
    monkeypatch.setattr(data_limits, "LIMITS", data_limits.limits_for_build("eeb6093e"))
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


def test_points_limits_live(monkeypatch):
    # The pinned build (9e18f010) stores points: no points limit is live.
    assert data_limits.LIMITS == ()
    assert not data_limits.limits_for_paths(
        ["gov.dwp.pip.mobility.points_thresholds.enhanced"]
    )
    monkeypatch.setattr(data_limits, "LIMITS", data_limits.limits_for_build("eeb6093e"))
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


def test_uc_health_element_change_builds_only_rebalanced_years():
    from pip_review.measure_templates import (
        UC_LCWRA_AMOUNT,
        UC_NEW_CLAIMANT_HEALTH,
        rate_change,
        uc_health_element_change,
    )

    assert uc_health_element_change(new_claimant={2027: 300}) == {
        UC_NEW_CLAIMANT_HEALTH: {"2027": 300.0}
    }
    with pytest.raises(ValueError, match="would score nothing"):
        uc_health_element_change(new_claimant={2040: 300})
    with pytest.raises(ValueError, match="is not what UC"):
        rate_change(UC_LCWRA_AMOUNT, {2027: 300})
    with pytest.raises(ValueError):
        uc_health_element_change()


def test_registered_templates_are_the_four_kept():
    from pip_review import measure_templates

    for name in measure_templates.REGISTERED_TEMPLATES:
        assert callable(getattr(measure_templates, name))
