"""Data limits: parameters that act only through an input the data do not hold.

Pruned from the AB2026 dashboard's ``data_limits`` to the entries a PIP event
touches. The entries are declarative; ``tests/test_model_mode.py`` (with the
model extra) checks them against the engine's formulas, as AB2026's
detection does: any measure parameter whose formulas read assessment points
must be covered here.

A measure that moves only a limited parameter is published as not computable,
with the reason, and never as £0 (``pip_review.publication``).

A limit with ``direction="cut"`` holds only for a change that brings a
component's threshold below its current-law standard threshold in some
year; a raise passes, and so does an enhanced-threshold cut that stays at
or above the standard threshold (it moves only existing standard-rate
recipients). Checks that get bare paths, with no values, cannot tell a cut
from a raise and treat a ``cut`` limit as holding.

A ``cut`` limit refuses the whole measure when it holds on any one of its
paths (``refusing_limits``): a cut bundled with a rate change or a raise
would otherwise be costed on the existing caseload only. A ``direction=
"any"`` limit (a parameter that moves no one) still refuses a measure only
when every path is limited. ``models.Reform`` and ``publication`` both
enforce this.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from pip_review.data_build import DATA_BUILD


@dataclass(frozen=True)
class DataLimit:
    key: str
    parameters: tuple[str, ...]
    missing_input: str
    reason: str
    issue: int | None = None
    variables: tuple[str, ...] = field(default_factory=tuple)
    direction: str = "any"

    def __post_init__(self):
        if self.direction not in ("any", "cut"):
            raise ValueError(f"{self.key}: direction must be 'any' or 'cut'")

    @property
    def public_reason(self) -> str:
        """The page text: the reason, which names no model variable."""
        return self.reason

    def covers(self, path: str) -> bool:
        return any(path == p or path.startswith(p + ".") for p in self.parameters)

    def holds_for(self, path: str, values: Mapping | None = None) -> bool:
        """True when the limit holds for this change (values by fiscal year).

        With no values a ``cut`` limit holds: the direction is unknown.
        """
        if not self.covers(path):
            return False
        if self.direction == "any" or values is None:
            return True
        return is_cut(path, values)


# Current-law PIP points thresholds in policyengine-uk 2.177.7, the same in
# every year from 2013 to 2041 (tests/test_model_mode.py checks them against
# the installed engine). Literal so the limits load without the engine.
DL_THRESHOLDS = "gov.dwp.pip.daily_living.points_thresholds"
MOB_THRESHOLDS = "gov.dwp.pip.mobility.points_thresholds"
CURRENT_LAW_THRESHOLDS: dict[str, float] = {
    f"{DL_THRESHOLDS}.standard": 8,
    f"{DL_THRESHOLDS}.enhanced": 12,
    f"{MOB_THRESHOLDS}.standard": 8,
    f"{MOB_THRESHOLDS}.enhanced": 12,
}


def is_cut(path: str, values: Mapping) -> bool:
    """True when any year's value is below the component's current-law
    standard threshold (8).

    A standard threshold below 8 reaches people turned down at those points,
    who are not in the data. An enhanced threshold cut to 8 or more (12 to
    10, say) moves only standard-rate recipients of the same component,
    whose points are drawn within their award: computable under the same
    drawn-points assumption as a raise. An enhanced threshold below 8 makes
    people below the standard threshold enhanced, so it counts as a cut.
    """
    if path not in CURRENT_LAW_THRESHOLDS:
        raise KeyError(
            f"No current-law value recorded for {path}: give a points "
            "threshold as its .standard or .enhanced leaf"
        )
    component = path.rsplit(".", 1)[0]
    floor = CURRENT_LAW_THRESHOLDS[f"{component}.standard"]
    return any(float(value) < floor for value in values.values())


ALL_LIMITS: tuple[DataLimit, ...] = (
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
    DataLimit(
        key="pip_daily_living_threshold_cut",
        parameters=(DL_THRESHOLDS,),
        missing_input="pip_points_of_people_turned_down",
        reason=(
            "The data hold assessment points only for people who get PIP. "
            "People turned down for daily living are not in the data, so a "
            "lower daily living standard threshold could only be costed for "
            "people who already get the mobility component, whose daily "
            "living points the data build drew below 8 (mostly 4 to 7). A cut "
            "to the standard threshold is not costed, alone or with other "
            "changes. A higher threshold, or an enhanced threshold lowered "
            "but kept at 8 or more, is costed on the assumption that the "
            "drawn points place recipients correctly within their award."
        ),
        issue=3,
        direction="cut",
    ),
    DataLimit(
        key="pip_mobility_threshold_cut",
        parameters=(MOB_THRESHOLDS,),
        missing_input="pip_points_of_people_turned_down",
        reason=(
            "The data hold assessment points only for people who get PIP. "
            "People turned down for mobility are not in the data, and people "
            "who get only the daily living component hold mobility points of "
            "0 or 4 drawn by the data build, so a mobility standard threshold "
            "of 5 to 7 moves no one (4 or lower moves only those drawn at 4). "
            "A cut to the standard threshold is not costed, alone or with "
            "other changes. A higher threshold, or an enhanced threshold "
            "lowered but kept at 8 or more, is costed on the assumption that "
            "the drawn points place recipients correctly within their award."
        ),
        issue=3,
        direction="cut",
    ),
)

# The limits that hold on each Microcosm national build (its 8-character id).
# eeb6093e stores PIP award categories and no assessment points, so a stored
# award overrides points and a threshold change moves no one. 9e18f010
# (the pin until 13 November 2026) is a single-year 2024 file whose person table
# stores pip_dl_points and pip_m_points and no PIP category column (from its
# HDFStore metadata, 13 November 2026): policyengine-uk 2.177.7 derives each
# category from the latest points against that year's thresholds, so a
# threshold change moves awards (tests/test_measure_households.py). 6f918b81
# (data_build.DATA_BUILD from 13 November 2026) stores the same: points, no
# category column (HDFStore metadata, 13 November 2026). It also stores
# cares_for_severely_disabled_person per carer, but not whom each carer cares
# for, so MISSING_INPUTS["cared_for_outside_household"] still holds there.
# On 6f918b81 the points are drawn only for people with a PIP award; everyone
# else holds -1 ("not assessed"). A recipient of one component has the other
# drawn below 8: daily living mostly over 4-7, mobility at 0 or 4 (María,
# data owner, 13 November 2026). Read from the 6f918b81 person table (14
# November 2026): of the 359 mobility-only recipient rows, 295 hold daily
# living points 4-7 and 64 hold 0-3; 152 are at 6-7. So a standard-threshold
# cut reaches only existing recipients of the other component (a daily living
# cut to 6 moves the mobility-only recipients drawn at 6-7, about 77k people
# from 88 distinct survey households; a mobility cut to 5-7 moves no one, to
# 4 or lower only daily-living-only recipients drawn at 4), and claimants
# turned down at those points are not in the data. Standard-threshold cuts
# are therefore not computable there, alone or bundled with any other change
# (the brief allows no existing-caseload-only costing). A raise, and an
# enhanced-threshold cut that stays at 8 or more (it moves only standard-rate
# recipients of the same component, all in the data), are computable under
# the drawn-points assumption. 9e18f010's draw was not checked against this
# and keeps its earlier entry.
# Only the pinned build's entries are live (``LIMITS``).
LIMITS_BY_BUILD: dict[str, tuple[str, ...]] = {
    "eeb6093e": ("pip_daily_living_points", "pip_mobility_points"),
    "9e18f010": (),
    "6f918b81": ("pip_daily_living_threshold_cut", "pip_mobility_threshold_cut"),
}


def limits_for_build(build: str) -> tuple[DataLimit, ...]:
    """The data limits that hold on a build (its 8-character id)."""
    if build not in LIMITS_BY_BUILD:
        raise KeyError(
            f"No data limits recorded for build {build}: check each entry of "
            "ALL_LIMITS against it first."
        )
    keys = LIMITS_BY_BUILD[build]
    return tuple(limit for limit in ALL_LIMITS if limit.key in keys)


LIMITS: tuple[DataLimit, ...] = limits_for_build(DATA_BUILD.short_id)

# Inputs a measure may need that no parameter path names. The registry lists
# them under ``data_needs``; the page shows the reason.
MISSING_INPUTS: dict[str, str] = {
    "pip_points_of_people_turned_down": (
        "Assessment points are held only for people who get PIP, so people "
        "turned down just below a threshold are not in the data and a "
        "threshold cut is not costed (issue #3)."
    ),
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
        "The data record whether each carer cares for someone with a "
        "qualifying disability benefit, but not who that person is or where "
        "they live. For a carer of someone in another household neither "
        "Carer's Allowance nor the UC carer element can follow the cared-for "
        "person's award. Reaching them "
        "needs a share-based adjustment or the cared-for link in "
        "policyengine-uk #2889, item 5 (issue #2)."
    ),
    "pip_country_test": (
        "Scottish Adult Disability Payment and Northern Ireland PIP are stored "
        "as PIP; reforms are masked to England and Wales (issue #1)."
    ),
}


def _changes(changes: Iterable[str] | Mapping) -> dict[str, Mapping | None]:
    if isinstance(changes, Mapping):
        return dict(changes)
    return {path: None for path in changes}


def limits_for_paths(changes: Iterable[str] | Mapping) -> list[DataLimit]:
    """The live data limits that hold for any of the given changes.

    Give parameter changes (path to values by fiscal year) to tell a cut
    from a raise; bare paths treat every ``cut`` limit as holding.
    """
    items = _changes(changes)
    return [
        limit
        for limit in LIMITS
        if any(limit.holds_for(path, values) for path, values in items.items())
    ]


def is_only_data_limited(changes: Iterable[str] | Mapping) -> bool:
    """True when a limit holds for every change."""
    items = _changes(changes)
    return bool(items) and all(
        limits_for_paths({path: values}) for path, values in items.items()
    )


def refusing_limits(changes: Iterable[str] | Mapping) -> list[DataLimit]:
    """The live limits that make a measure not computable (empty: computable).

    A ``cut`` limit that holds on any one path refuses the measure, whatever
    else it changes: the cut would be costed on the existing caseload only.
    Otherwise the measure is refused only when a limit holds on every path
    (a limited parameter alone moves no one).
    """
    held = limits_for_paths(changes)
    cuts = [limit for limit in held if limit.direction == "cut"]
    if cuts:
        return cuts
    return held if is_only_data_limited(changes) else []


def is_computable_on_data(changes: Iterable[str] | Mapping) -> bool:
    """False when a live data limit refuses the measure (``refusing_limits``)."""
    return not refusing_limits(changes)
