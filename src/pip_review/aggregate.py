"""Aggregate two runs (current law and a reform) into the public tables.

Pure numpy: the arrays come from ``pip_review.model_run`` and nothing here
needs policyengine, so the tables are tested on invented arrays.

England and Wales mask (issue #1). The model has no country test for PIP, so
a reform also changes the stored Scottish Adult Disability Payment and
Northern Ireland PIP awards. Every table here keeps England and Wales
households only. In a static run households do not interact, so dropping
the other nations' households gives exactly the England and Wales figures a
country test would give; their changed awards never reach any output. The
upstream fix (a country parameter read by ``pip_dl`` and ``pip_m``) remains
the long-term route.

Every row that rests on survey cells carries ``n_households`` until
``publication.apply_floor`` blanks small cells and drops the count.
"""

from typing import Any

import numpy as np

from pip_review import publication

MASK_COUNTRIES = ("ENGLAND", "WALES")
NO_CHANGE_BAND = 0.001  # |change| below 0.1% of net income is no change
AGE_BANDS = ((0, 15, "0-15"), (16, 24, "16-24"), (25, 64, "25-64"), (65, 200, "65+"))
EW_REGIONS = (
    "NORTH_EAST",
    "NORTH_WEST",
    "YORKSHIRE",
    "EAST_MIDLANDS",
    "WEST_MIDLANDS",
    "EAST_OF_ENGLAND",
    "LONDON",
    "SOUTH_EAST",
    "SOUTH_WEST",
    "WALES",
)


def ew_households(base: dict, year: int) -> np.ndarray:
    return np.isin(base[f"country/{year}"], MASK_COUNTRIES)


def _person_mask(base: dict, household_mask: np.ndarray) -> np.ndarray:
    index = {hid: i for i, hid in enumerate(base["household_id"])}
    positions = np.array([index[h] for h in base["person_household"]])
    return household_mask[positions], positions


def deciles(base: dict, year: int, mask: np.ndarray) -> np.ndarray:
    """England and Wales income deciles (1-10), people-weighted, 0 outside."""
    income = base[f"equiv_hbai_household_net_income/{year}"]
    weight = base[f"household_weight/{year}"] * base[f"household_count_people/{year}"]
    out = np.zeros(len(income), dtype=int)
    order = np.argsort(income[mask], kind="stable")
    cum = np.cumsum(weight[mask][order])
    if cum.size == 0 or cum[-1] <= 0:
        return out
    ranks = np.minimum(10, np.floor(cum / cum[-1] * 10 - 1e-9).astype(int) + 1)
    selected = np.flatnonzero(mask)[order]
    out[selected] = ranks
    return out


def budgetary_impact_m(base: dict, reform: dict, year: int, mask: np.ndarray) -> float:
    """Cost to the Exchequer, £m: minus the change in the government balance."""
    weight = base[f"household_weight/{year}"]
    change = reform[f"gov_balance/{year}"] - base[f"gov_balance/{year}"]
    return float(-(change * weight)[mask].sum() / 1e6)


def _shares(pct: np.ndarray, weight: np.ndarray, rows: np.ndarray) -> dict[str, Any]:
    bands = {
        "gain_more_5": pct >= 0.05,
        "gain_less_5": (pct >= NO_CHANGE_BAND) & (pct < 0.05),
        "no_change": np.abs(pct) < NO_CHANGE_BAND,
        "lose_less_5": (pct <= -NO_CHANGE_BAND) & (pct > -0.05),
        "lose_more_5": pct <= -0.05,
    }
    total = weight[rows].sum()
    out: dict[str, Any] = {}
    counts = []
    for key, band in bands.items():
        sel = rows & band
        out[key] = round(float(weight[sel].sum() / total * 100), 1) if total else 0.0
        if sel.any():
            counts.append(int(sel.sum()))
    out["n_households"] = min(counts) if counts else 0
    return out


def tables(base: dict, reform: dict, years: list[int]) -> dict[str, Any]:
    """The public tables for one measure (or package) against current law."""
    last = years[-1]
    mask = ew_households(base, last)
    decile = deciles(base, last, mask)
    weight = base[f"household_weight/{last}"]
    people = base[f"household_count_people/{last}"]
    before = base[f"household_net_income/{last}"]
    change = reform[f"household_net_income/{last}"] - before
    pct = np.where(np.abs(before) > 1, change / np.maximum(np.abs(before), 1), 0.0)

    decile_rows = []
    wl_rows = []
    for d in range(1, 11):
        rows = mask & (decile == d)
        w = weight[rows]
        avg = float((change[rows] * w).sum() / w.sum()) if w.sum() else 0.0
        base_income = float((before[rows] * w).sum())
        decile_rows.append(
            {
                "decile": d,
                "avg_change_gbp": round(avg, 0),
                "pct_change": round(
                    float((change[rows] * w).sum() / base_income * 100), 2
                )
                if base_income
                else 0.0,
                "n_households": int(rows.sum()),
            }
        )
        wl_rows.append({"decile": d, **_shares(pct, weight * people, rows)})
    all_row = {"decile": "all", **_shares(pct, weight * people, mask)}

    region = base[f"region/{last}"]
    region_rows = []
    for name in EW_REGIONS:
        rows = mask & (region == name)
        w = weight[rows]
        region_rows.append(
            {
                "region": name,
                "avg_change_gbp": round(float((change[rows] * w).sum() / w.sum()), 0)
                if w.sum()
                else 0.0,
                "n_households": int(rows.sum()),
            }
        )

    pmask, positions = _person_mask(base, mask)
    pw = base[f"person_weight/{last}"]
    pip_before = base[f"pip_dl/{last}"] + base[f"pip_m/{last}"]
    pip_after = reform[f"pip_dl/{last}"] + reform[f"pip_m/{last}"]
    pip_change = pip_after - pip_before
    gain = pmask & (pip_change > 0.5)
    lose = pmask & (pip_change < -0.5)
    ca_change = reform[f"carers_allowance/{last}"] - base[f"carers_allowance/{last}"]

    def _people_k(sel):
        return round(float(pw[sel].sum() / 1e3), 0)

    gain_households = len(set(positions[gain]))
    lose_households = len(set(positions[lose]))
    nonzero = [n for n in (gain_households, lose_households) if n]
    people_affected = {
        "gain_k": _people_k(gain),
        "lose_k": _people_k(lose),
        "n_households": min(nonzero) if nonzero else 0,
    }

    age = base[f"age/{last}"]
    hh_change_person = change[positions]
    age_rows = []
    for low, high, label in AGE_BANDS:
        sel = pmask & (age >= low) & (age <= high)
        w = pw[sel]
        age_rows.append(
            {
                "age_band": label,
                "avg_household_change_gbp": round(
                    float((hh_change_person[sel] * w).sum() / w.sum()), 0
                )
                if w.sum()
                else 0.0,
                "n_households": int(len(set(positions[sel]))),
            }
        )

    poverty = {}
    for basis in ("bhc", "ahc"):
        b = base[f"in_poverty_{basis}/{last}"]
        r = reform[f"in_poverty_{basis}/{last}"]
        denom = pw[pmask].sum()
        poverty[basis] = {
            "baseline_pct": round(float(pw[pmask & b].sum() / denom * 100), 2)
            if denom
            else 0.0,
            "change_pp": round(
                float((pw[pmask & r].sum() - pw[pmask & b].sum()) / denom * 100), 2
            )
            if denom
            else 0.0,
        }

    knock_ons = {
        "carers_allowance_m": round(float((ca_change * pw)[pmask].sum() / 1e6), 0),
    }

    return {
        "budgetary_impact": [
            {
                "year": year,
                "value_m": round(
                    budgetary_impact_m(base, reform, year, ew_households(base, year)),
                    0,
                )
                + 0.0,
            }
            for year in years
        ],
        "decile": publication.apply_floor(
            decile_rows, ["avg_change_gbp", "pct_change"]
        ),
        "winners_losers": publication.apply_floor(
            wl_rows,
            ["gain_more_5", "gain_less_5", "no_change", "lose_less_5", "lose_more_5"],
        ),
        "winners_losers_all": publication.apply_floor(
            [all_row],
            ["gain_more_5", "gain_less_5", "no_change", "lose_less_5", "lose_more_5"],
        )[0],
        "by_region": publication.apply_floor(region_rows, ["avg_change_gbp"]),
        "by_age": publication.apply_floor(age_rows, ["avg_household_change_gbp"]),
        "people_affected": publication.apply_floor(
            [people_affected], ["gain_k", "lose_k"]
        )[0],
        "poverty": poverty,
        "knock_ons": knock_ons,
    }
