import pytest

from pip_review import publication
from pip_review.pipeline import build_placeholder_results


@pytest.mark.parametrize("status", ["placeholder", "mock"])
def test_placeholder_measures_allowed_on_placeholder_and_mock(status):
    results = build_placeholder_results(status=status)
    assert publication.validate_public(results) == []
    assert results["banner"]


def test_mock_banner_must_say_mock():
    results = build_placeholder_results(status="mock", banner="Drill figures")
    assert any("MOCK" in e for e in publication.validate_public(results))
    results = build_placeholder_results(status="mock")
    assert "MOCK" in results["banner"]


@pytest.mark.parametrize("status", ["provisional", "final"])
def test_placeholder_measures_refused_on_real_pages(status):
    results = build_placeholder_results(status=status)
    assert any("placeholder" in e for e in publication.validate_public(results))


def test_every_status_but_final_needs_a_banner():
    for status in ("placeholder", "mock", "provisional"):
        results = build_placeholder_results(status=status, banner="")
        assert any("banner" in e for e in publication.validate_public(results))


def test_unknown_status_refused():
    with pytest.raises(ValueError):
        publication.banner_for("draft")


def test_withdrawn_measure_carries_no_figures():
    results = build_placeholder_results()
    measure = next(m for m in results["measures"] if m["budgetary_impact"])
    measure["status"] = "withdrawn"
    errors = publication.validate_public(results)
    assert any("withdrawn" in e for e in errors)


def test_survey_rows_must_say_whether_suppressed():
    results = build_placeholder_results()
    measure = next(m for m in results["measures"] if m["decile"])
    del measure["decile"][0]["suppressed"]
    assert any("suppressed" in e for e in publication.validate_public(results))


def test_presets_must_cover_the_modelled_measures():
    results = build_placeholder_results()
    results["households"][0]["reform"].pop(
        next(iter(results["households"][0]["reform"]))
    )
    assert any("presets cover" in e for e in publication.validate_public(results))
