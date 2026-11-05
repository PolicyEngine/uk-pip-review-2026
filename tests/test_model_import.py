"""The engine pin imports, when the ``model`` extra is installed (skipped otherwise)."""

import pytest

from pip_review.reforms import get_reform


def test_scenario_builds_with_engine():
    pytest.importorskip("policyengine_uk")
    scenario = get_reform("standard_daily_living_rate").to_scenario()
    assert scenario is not None
