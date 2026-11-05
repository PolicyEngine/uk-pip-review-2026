"""Base year and policy years, shared by the pipeline, the household calculator and the page.

Year Y is fiscal year Y-(Y+1): 2027 is 2027-28. Copied in shape from the AB2026
dashboard's ``budget_years``.
"""

import json
from importlib.resources import files

_CONFIG = json.loads(files("pip_review").joinpath("years.json").read_text())
BASE_YEAR: int = _CONFIG["base_year"]
POLICY_YEARS: list[int] = list(_CONFIG["policy_years"])
TERMINAL_CALENDAR_YEAR: int = _CONFIG["terminal_calendar_year"]
HOUSEHOLD_YEARS: list[int] = [BASE_YEAR, *POLICY_YEARS]


def fiscal_label(year: int) -> str:
    """Return the fiscal-year label for a start year, for example 2027 -> '2027-28'."""
    if type(year) is not int:
        raise TypeError("year must be an int")
    return f"{year}-{(year + 1) % 100:02d}"
