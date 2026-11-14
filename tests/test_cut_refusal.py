"""A points-threshold cut is never costed, alone or bundled (REVIEW2 P1).

On build 6f918b81 assessment points are held only for PIP recipients, so a
standard-threshold cut could be costed only on the existing caseload. The
model validator and the publication gate both refuse any computable measure
where a cut limit holds on any of its paths.
"""

import warnings

import pytest

from pip_review import data_limits, publication
from pip_review.measure_templates import DataLimitedWarning, merge, threshold_change
from pip_review.models import Reform, Route
from pip_review.reforms import get_reform
from pip_review.years import POLICY_YEARS

DL_STANDARD = "gov.dwp.pip.daily_living.points_thresholds.standard"
MOB_STANDARD = "gov.dwp.pip.mobility.points_thresholds.standard"


def _every_year(value):
    return {year: value for year in POLICY_YEARS}


def _threshold(path, value):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DataLimitedWarning)
        return threshold_change(path, _every_year(value))


def _bundled_with_rate(path, value):
    """The registered standard daily living rate measure plus a threshold."""
    rate = get_reform("standard_daily_living_rate")
    changes = merge(rate.parameter_changes, _threshold(path, value))
    fields = rate.model_dump(exclude={"parameter_changes", "id"})
    return fields, changes


def test_cut_bundled_with_a_rate_change_is_refused():
    # The reviewer's case: DL standard threshold to 6 plus the standard DL
    # rate change, as a dashboard-param measure.
    fields, changes = _bundled_with_rate(DL_STANDARD, 6)
    assert fields["route"] is Route.DASHBOARD_PARAM
    assert not data_limits.is_only_data_limited(changes)
    assert [x.key for x in data_limits.refusing_limits(changes)] == [
        "pip_daily_living_threshold_cut"
    ]
    with pytest.raises(ValueError, match="pip_daily_living_threshold_cut"):
        Reform(id="rate_and_cut", parameter_changes=changes, **fields)


def test_cut_bundled_with_a_raise_is_refused():
    changes = merge(_threshold(DL_STANDARD, 6), _threshold(MOB_STANDARD, 10))
    assert not data_limits.is_computable_on_data(changes)
    fields = get_reform("standard_daily_living_rate").model_dump(
        exclude={"parameter_changes", "id"}
    )
    with pytest.raises(ValueError, match="not computable"):
        Reform(id="cut_and_raise", parameter_changes=changes, **fields)


def test_pure_cut_is_refused_by_the_validator():
    fields = get_reform("standard_daily_living_rate").model_dump(
        exclude={"parameter_changes", "id"}
    )
    for path in (DL_STANDARD, MOB_STANDARD):
        with pytest.raises(ValueError, match="threshold_cut"):
            Reform(id="pure_cut", parameter_changes=_threshold(path, 6), **fields)


def test_cut_still_builds_as_not_computable():
    # The registered placeholder is a cut routed not-computable: it builds.
    reform = get_reform("points_thresholds")
    assert reform.route is Route.NOT_COMPUTABLE
    assert not data_limits.is_computable_on_data(reform.parameter_changes)


def test_raise_stays_computable():
    fields, changes = _bundled_with_rate(DL_STANDARD, 10)
    assert data_limits.is_computable_on_data(changes)
    reform = Reform(id="rate_and_raise", parameter_changes=changes, **fields)
    assert reform.computable
    raise_only = Reform(
        id="raise_only", parameter_changes=_threshold(MOB_STANDARD, 9), **fields
    )
    assert raise_only.computable
    assert publication.data_limit_problems([reform, raise_only]) == []


def test_publication_gate_refuses_a_cut_that_bypassed_the_validator():
    # model_construct skips the validator, so only the gate can catch it.
    fields, changes = _bundled_with_rate(DL_STANDARD, 6)
    sneaked = Reform.model_construct(
        id="rate_and_cut", parameter_changes=changes, **fields
    )
    assert sneaked.computable
    problems = publication.data_limit_problems([sneaked])
    assert len(problems) == 1 and "pip_daily_living_threshold_cut" in problems[0]
    with pytest.raises(ValueError, match="Publication check failed"):
        publication.manifest([sneaked])
    from pip_review import pipeline

    with pytest.raises(ValueError, match="Publication check failed"):
        pipeline._measure_entry(sneaked)


def test_publication_gate_refuses_when_reforms_hold_a_cut(monkeypatch):
    from pip_review import pipeline

    fields, changes = _bundled_with_rate(DL_STANDARD, 6)
    sneaked = Reform.model_construct(
        id="rate_and_cut", parameter_changes=changes, **fields
    )
    monkeypatch.setattr(pipeline, "REFORMS", [*pipeline.REFORMS, sneaked])
    with pytest.raises(ValueError, match="rate_and_cut"):
        pipeline.build_placeholder_results()
    with pytest.raises(ValueError, match="rate_and_cut"):
        pipeline.build_model_results(dataset="unused.h5", allow_unpinned=True)


def test_any_limits_keep_the_every_path_rule(monkeypatch):
    # On an awards-only build a limited parameter moves no one, so a rate
    # change beside it is still computable (the AB2026 rule).
    monkeypatch.setattr(data_limits, "LIMITS", data_limits.limits_for_build("eeb6093e"))
    fields, changes = _bundled_with_rate(DL_STANDARD, 6)
    assert data_limits.limits_for_paths(changes)
    assert data_limits.is_computable_on_data(changes)
    assert not data_limits.is_computable_on_data(_threshold(DL_STANDARD, 6))
