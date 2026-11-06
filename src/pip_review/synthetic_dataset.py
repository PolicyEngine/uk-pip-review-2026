"""A small, invented dataset for testing model mode end to end.

Copied in shape from the AB2026 dashboard's ``synthetic_dataset``, with PIP
awards and households in every nation, so the England and Wales mask and
the tables can be tested without the licensed national file. No survey
record is in it: every value is drawn here from a fixed seed. Its figures
mean nothing and are never published (an unmanaged file is never
certified).
"""

from pathlib import Path

import numpy as np

DEFAULT_HOUSEHOLDS = 400
DEFAULT_SEED = 2026
FISCAL_YEAR = 2026
REGIONS = (
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
    "SCOTLAND",
    "NORTHERN_IRELAND",
)
CATEGORIES = ("NONE", "STANDARD", "ENHANCED")


def build(households: int = DEFAULT_HOUSEHOLDS, seed: int = DEFAULT_SEED):
    import pandas as pd
    from policyengine_uk.data import UKSingleYearDataset

    rng = np.random.default_rng(seed)
    people, benunits, rows = [], [], []
    person_id = 0
    for household in range(1, households + 1):
        adults = 1 + int(rng.random() < 0.5)
        children = int(rng.integers(0, 3)) if rng.random() < 0.4 else 0
        pensioner = rng.random() < 0.2
        for index in range(adults + children):
            person_id += 1
            adult = index < adults
            if adult and pensioner:
                age = int(rng.integers(67, 85))
            elif adult:
                age = int(rng.integers(17, 66))
            else:
                age = int(rng.integers(0, 16))
            earnings = (
                float(round(rng.lognormal(9.8, 0.8), -2))
                if adult and not pensioner and rng.random() < 0.6
                else 0.0
            )
            has_pip = adult and rng.random() < 0.35
            people.append(
                {
                    "person_id": person_id,
                    "person_benunit_id": household,
                    "person_household_id": household,
                    "age": age,
                    "employment_income": earnings,
                    "state_pension": 11_973.0 if adult and pensioner else 0.0,
                    "pip_dl_category": (
                        CATEGORIES[int(rng.integers(1, 3))] if has_pip else "NONE"
                    ),
                    "pip_m_category": (
                        CATEGORIES[int(rng.integers(0, 3))] if has_pip else "NONE"
                    ),
                }
            )
        benunits.append({"benunit_id": household})
        rows.append(
            {
                "household_id": household,
                "household_weight": float(rng.integers(50_000, 150_000)),
                "region": REGIONS[(household - 1) % len(REGIONS)],
                "tenure_type": "RENT_PRIVATELY",
                "rent": float(round(rng.uniform(6_000, 14_000), -1)),
                "council_tax": float(round(rng.uniform(1_400, 3_200), -1)),
            }
        )
    return UKSingleYearDataset(
        person=pd.DataFrame(people),
        benunit=pd.DataFrame(benunits),
        household=pd.DataFrame(rows),
        fiscal_year=FISCAL_YEAR,
    )


def write(path: Path, households: int = DEFAULT_HOUSEHOLDS, seed: int = DEFAULT_SEED):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    build(households, seed).save(str(path))
    return path
