import pytest

from pip_review.household import PRESETS, PRESETS_BY_ID, pip_award, to_situation
from pip_review.reforms import CURRENT_RATES


def test_five_presets_with_unique_ids():
    assert len(PRESETS) == 5
    assert len(PRESETS_BY_ID) == 5


def test_presets_are_england_and_wales():
    for preset in PRESETS:
        assert preset["region"] not in {"SCOTLAND", "NORTHERN_IRELAND"}


@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p["id"])
def test_situation_shape(preset):
    situation = to_situation(preset, 2027)
    names = [p["name"] for p in preset["people"]]
    assert list(situation["people"]) == names
    assert situation["benunits"]["benunit"]["members"] == names
    assert situation["households"]["household"]["members"] == names
    for person in situation["people"].values():
        assert set(person["pip_dl_category"]) == {"2027"}


def test_pip_award_maximum():
    # Both components enhanced: (114.60 + 80.00) x 52 = £10,119.20.
    preset = PRESETS_BY_ID["uc_enhanced_both_with_carer"]
    assert pip_award(preset) == pytest.approx(10_119.20, abs=0.01)


def test_pip_award_follows_rates():
    preset = PRESETS_BY_ID["single_standard_dl_part_time"]
    base = pip_award(preset)
    raised = pip_award(preset, {"gov.dwp.pip.daily_living.standard": CURRENT_RATES["gov.dwp.pip.daily_living.standard"] + 1})
    assert raised - base == pytest.approx(52.0)
