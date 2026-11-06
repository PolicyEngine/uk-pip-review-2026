"""Data limits: parameters that act only through an input the data do not hold.

Pruned from the AB2026 dashboard's ``data_limits`` to the entries a PIP event
touches. The source detects limits by inspecting formulas; this template keeps
the declarative entries and the lookup, which is all the registry needs.

A measure that moves only a limited parameter is published as not computable,
with the reason, and never as £0 (``pip_review.publication``).
"""

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DataLimit:
    key: str
    parameters: tuple[str, ...]
    missing_input: str
    reason: str
    issue: int | None = None
    variables: tuple[str, ...] = field(default_factory=tuple)

    @property
    def public_reason(self) -> str:
        """The page text: the reason, which names no model variable."""
        return self.reason

    def covers(self, path: str) -> bool:
        return any(path == p or path.startswith(p + ".") for p in self.parameters)


LIMITS: tuple[DataLimit, ...] = (
    DataLimit(
        key="pip_daily_living_points",
        parameters=("gov.dwp.pip.daily_living.points_thresholds",),
        missing_input="pip_dl_points",
        reason=(
            "The data record each claimant's PIP daily living award (none, "
            "standard or enhanced), not assessment points, and a stored award "
            "overrides points. Changing a points threshold moves no one."
        ),
        issue=3,
    ),
    DataLimit(
        key="pip_mobility_points",
        parameters=("gov.dwp.pip.mobility.points_thresholds",),
        missing_input="pip_m_points",
        reason=(
            "The data record each claimant's PIP mobility award, not assessment "
            "points, and a stored award overrides points. Changing a points "
            "threshold moves no one."
        ),
        issue=3,
    ),
)

# Inputs a measure may need that no parameter path names. The registry lists
# them under ``data_needs``; the page shows the reason.
MISSING_INPUTS: dict[str, str] = {
    "pip_activity_points": (
        "No score for each assessment activity, only award categories, so a "
        "minimum score in one activity cannot be expressed (issue #3)."
    ),
    "health_condition": (
        "No main health-condition group for PIP recipients (issue #5)."
    ),
    "hospital_stay": "No hospital in-patient stays (issue #5).",
    "award_review_state": (
        "No award duration, review date or new-claim flag; the model is static."
    ),
    "cared_for_outside_household": (
        "No record of caring for someone outside the household, so Carer's "
        "Allowance cannot follow the cared-for person's award (issue #2)."
    ),
    "pip_country_test": (
        "Scottish Adult Disability Payment and Northern Ireland PIP are stored "
        "as PIP; reforms are masked to England and Wales (issue #1)."
    ),
}


def limits_for_paths(paths: Iterable[str]) -> list[DataLimit]:
    """The data limits that cover any of the given parameter paths."""
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]


def is_only_data_limited(paths: Iterable[str]) -> bool:
    """True when every path is covered by a limit: the measure cannot move anyone."""
    paths = list(paths)
    return bool(paths) and all(limits_for_paths([p]) for p in paths)
