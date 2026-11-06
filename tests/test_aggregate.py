"""England and Wales mask and tables, on invented arrays (no engine)."""

import numpy as np
import pytest

from pip_review import aggregate

YEARS = [2027]


def _run(change_scotland=0.0, change_england=0.0, n=60):
    # n households per nation, one person each.
    countries = ["ENGLAND"] * n + ["WALES"] * n + ["SCOTLAND"] * n
    regions = ["LONDON"] * n + ["WALES"] * n + ["SCOTLAND"] * n
    size = len(countries)
    ids = np.arange(1, size + 1)
    base = {
        "household_id": ids,
        "person_household": ids.copy(),
    }
    income = np.linspace(10_000, 60_000, size)
    y = YEARS[0]
    base.update(
        {
            f"household_weight/{y}": np.full(size, 100.0),
            f"household_count_people/{y}": np.ones(size),
            f"household_net_income/{y}": income,
            f"equiv_hbai_household_net_income/{y}": income,
            f"gov_balance/{y}": np.zeros(size),
            f"country/{y}": np.array(countries),
            f"region/{y}": np.array(regions),
            f"pip_dl/{y}": np.full(size, 4_000.0),
            f"pip_m/{y}": np.zeros(size),
            f"age/{y}": np.full(size, 40.0),
            f"carers_allowance/{y}": np.zeros(size),
            f"person_weight/{y}": np.full(size, 100.0),
            f"in_poverty_bhc/{y}": np.zeros(size, bool),
            f"in_poverty_ahc/{y}": np.zeros(size, bool),
        }
    )
    reform = {k: v.copy() for k, v in base.items()}
    delta = np.where(np.array(countries) == "SCOTLAND", change_scotland, change_england)
    reform[f"household_net_income/{y}"] = income + delta
    reform[f"gov_balance/{y}"] = -delta
    reform[f"pip_dl/{y}"] = base[f"pip_dl/{y}"] + delta
    return base, reform


def test_scottish_changes_never_reach_any_table():
    base, reform = _run(change_scotland=1_000.0)
    tables = aggregate.tables(base, reform, YEARS)
    assert tables["budgetary_impact"][0]["value_m"] == 0
    assert all(r["avg_change_gbp"] == 0 for r in tables["decile"])
    assert tables["people_affected"]["gain_k"] == 0
    assert "SCOTLAND" not in {r["region"] for r in tables["by_region"]}


def test_england_and_wales_cost_and_people():
    base, reform = _run(change_england=520.0)
    tables = aggregate.tables(base, reform, YEARS)
    # 120 households x weight 100 x £520 = £6.24m
    assert tables["budgetary_impact"][0]["value_m"] == pytest.approx(6.0, abs=0.5)
    assert tables["people_affected"]["gain_k"] == pytest.approx(12.0)
    assert tables["people_affected"]["suppressed"] is False


def test_rows_are_floored_and_counts_dropped():
    base, reform = _run(change_england=520.0, n=4)
    tables = aggregate.tables(base, reform, YEARS)
    for key in ("decile", "winners_losers", "by_region", "by_age"):
        for row in tables[key]:
            assert "n_households" not in row
            assert isinstance(row["suppressed"], bool)
    assert any(r["suppressed"] for r in tables["decile"])
