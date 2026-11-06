import pytest

from pip_review import data_limits
from pip_review.models import Likelihood, Reform, Route
from pip_review.reforms import (
    CURRENT_LAW_RATES,
    CURRENT_RATES,
    REFORMS,
    REFORMS_BY_ID,
    get_reform,
)
from pip_review.years import POLICY_YEARS


def test_ids_unique_and_complete():
    assert len(REFORMS) == 12
    assert len(REFORMS_BY_ID) == len(REFORMS)


def test_every_measure_is_a_placeholder():
    # Template rule: nothing is published before the report.
    assert all(reform.placeholder for reform in REFORMS)
    assert not any(reform.publishable for reform in REFORMS)


@pytest.mark.parametrize("reform", REFORMS, ids=lambda r: r.id)
def test_every_measure_has_a_route_and_reason(reform):
    assert isinstance(reform.route, Route)
    assert reform.route_reason.strip()
    assert reform.recommendation.strip()


@pytest.mark.parametrize("reform", REFORMS, ids=lambda r: r.id)
def test_parameter_years_cover_policy_years(reform):
    for path, values in (reform.parameter_changes or {}).items():
        assert sorted(values) == [str(y) for y in POLICY_YEARS], path


def test_points_threshold_measures_are_not_computable():
    # The brief's one concrete PIP rule: a points measure is never costed.
    for reform in REFORMS:
        paths = list(reform.parameter_changes or {})
        if any("points_thresholds" in p for p in paths):
            assert data_limits.is_only_data_limited(paths)
            assert reform.route is Route.NOT_COMPUTABLE
            assert not reform.computable


def test_computable_measures():
    computable = {r.id: r for r in REFORMS if r.computable}
    assert set(computable) == {
        "cost_category_tiers",
        "standard_daily_living_rate",
        "uc_health_gateway",
    }
    for reform in computable.values():
        if reform.route is Route.DASHBOARD_PARAM:
            assert set(reform.parameter_changes) <= set(CURRENT_RATES)
        else:
            assert reform.simulation_modifier.__module__.startswith(
                "pip_review.measures."
            )


def test_rate_measures_follow_current_law():
    # Written against each year's current-law rate, so uprating never turns
    # an illustrative rise into a cut.
    standard = get_reform("standard_daily_living_rate").parameter_changes
    path = "gov.dwp.pip.daily_living.standard"
    for year in POLICY_YEARS:
        law = CURRENT_LAW_RATES[year][path]
        assert standard[path][str(year)] == pytest.approx(law * 1.05, abs=0.01)


def test_public_text_has_no_prep_notes():
    for reform in REFORMS:
        text = " ".join([reform.description, reform.recommendation])
        assert "Not expected" not in text and "Not in the emerging" not in text
        assert "likelihood" not in reform.summary()


def test_route_validation_rejects_param_route_without_change():
    with pytest.raises(ValueError):
        Reform(
            id="bad",
            name="Bad",
            recommendation="x",
            likelihood=Likelihood.LOW,
            route=Route.DASHBOARD_PARAM,
            route_reason="x",
        )


def test_ledger_route_carries_no_change():
    with pytest.raises(ValueError):
        Reform(
            id="bad",
            name="Bad",
            recommendation="x",
            likelihood=Likelihood.LOW,
            route=Route.LEDGER,
            route_reason="x",
            parameter_changes={"gov.dwp.pip.mobility.standard": {"2027": 31.0}},
        )


def test_get_reform_unknown():
    with pytest.raises(KeyError):
        get_reform("nope")


def test_summary_has_no_callables():
    for reform in REFORMS:
        summary = reform.summary()
        assert all(not callable(v) for v in summary.values())
