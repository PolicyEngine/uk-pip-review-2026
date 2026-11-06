"""Model mode end to end on a small invented file (needs the model extra).

Skipped without policyengine-uk. Runs one simulation per process on a
400-household synthetic file, so it skips the heavy-run lock.
"""

import json
import os

import pytest

pytest.importorskip("policyengine_uk")

from pip_review import pipeline, publication  # noqa: E402
from pip_review.reforms import CURRENT_LAW_RATES  # noqa: E402
from pip_review.synthetic_dataset import write  # noqa: E402


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    os.environ["PIP_REVIEW_NO_LOCK"] = "1"
    path = write(tmp_path_factory.mktemp("data") / "synthetic.h5")
    return pipeline.build_model_results(
        dataset=str(path),
        status="mock",
        measure_ids=["standard_daily_living_rate", "uc_health_gateway"],
        households=False,
    )


def test_model_results_pass_the_gate(results):
    assert publication.validate_public(results) == []
    assert results["engine"]["certified_pair"] is False
    assert "MOCK" in results["banner"]
    json.dumps(results)


def test_rate_rise_is_a_cost_with_gainers_only(results):
    measure = next(
        m for m in results["measures"] if m["id"] == "standard_daily_living_rate"
    )
    assert all(row["value_m"] > 0 for row in measure["budgetary_impact"])
    affected = measure["people_affected"]
    assert affected["suppressed"] or affected["lose_k"] == 0


def test_package_runs_both_measures(results):
    assert results["package"]["measure_ids"] == [
        "standard_daily_living_rate",
        "uc_health_gateway",
    ]


def test_provenance_records_run(results):
    provenance = results["provenance"]
    assert provenance["commit"]
    assert set(provenance["machine_seconds"]) >= {"baseline", "package"}


def test_current_law_rates_match_engine():
    from policyengine_uk import CountryTaxBenefitSystem

    parameters = CountryTaxBenefitSystem().parameters
    for year, rates in CURRENT_LAW_RATES.items():
        for path, value in rates.items():
            leaf = parameters.get_child(path)(f"{year}-04-01")
            assert leaf == pytest.approx(value, abs=0.006), (year, path)


def test_certified_bundle_matches_install():
    from policyengine.tax_benefit_models.uk.model import uk_latest

    bundle = uk_latest.release_bundle
    for key, value in pipeline.CERTIFIED_BUNDLE.items():
        assert bundle[key] == value


def test_uc_rebalanced_years_match_engine():
    from policyengine_uk.scenarios import uc_reform

    from pip_review.measure_templates import UC_REBALANCED_YEARS

    assert list(UC_REBALANCED_YEARS) == list(uc_reform.REBALANCING_YEARS)


def test_benefit_receipt_payment_reaches_pip_households_in_england_and_wales(
    tmp_path,
):
    from policyengine.tax_benefit_models.uk.model import managed_microsimulation

    from pip_review.measure_templates import apply_benefit_receipt_payment

    path = write(tmp_path / "small.h5", households=60)
    base = managed_microsimulation(dataset=str(path), allow_unmanaged=True)
    sim = managed_microsimulation(dataset=str(path), allow_unmanaged=True)
    apply_benefit_receipt_payment(
        sim,
        amount=100,
        eligible_benefits=["pip"],
        geography="EW",
        channel="cost_of_living_support_payment",
        year=2027,
    )
    change = (
        sim.calculate("household_net_income", 2027).values
        - base.calculate("household_net_income", 2027).values
    )
    country = base.calculate("country", 2027).values
    pip = base.calculate("pip", 2027, map_to="household").values
    ew = (country == "ENGLAND") | (country == "WALES")
    assert (change[~ew] == 0).all()
    assert change[ew & (pip > 0)] == pytest.approx(100, abs=1)
