"""Publication gate, scaled down from the AB2026 dashboard's ``publication`` package.

Kept: a manifest of what may be published, a receipt binding each measure's
definition, the disclosure floor and validation of the public results file.
Dropped: release index, area-code routing, attestations and responsiveness
(no constituency map in this template).

Page status, defined once here (``STATUSES``) and read by the generator,
``validate_public``, ``dashboard/scripts/validate-results.mjs`` and the page:

- ``placeholder``: template figures before the report; banner required.
- ``mock``: a drill branch; banner required and must contain ``MOCK``.
- ``provisional``: the real day before G4 sign-off; banner required.
- ``final``: signed off; no banner. No placeholder measure is allowed.
"""

import hashlib
import inspect
import json
import sys
from collections.abc import Iterable
from typing import Any

from pip_review import sign_off
from pip_review.models import Reform

STATUSES = ("placeholder", "mock", "provisional", "final")
# Statuses under which a placeholder measure may still be in the file.
PLACEHOLDER_STATUSES = frozenset({"placeholder", "mock"})
DEFAULT_BANNERS = {
    "placeholder": (
        "Pre-release template: placeholder figures, not PolicyEngine estimates"
    ),
    "mock": "MOCK: drill figures for a made-up report, not PolicyEngine estimates",
    "provisional": "Provisional: figures are being checked and may change",
}

# Fewest unweighted survey households behind any published cell.
DISCLOSURE_FLOOR = 10

# Keys that must never appear in a public file: record identifiers and weights.
FORBIDDEN_KEYS = frozenset(
    {
        "household_id",
        "person_id",
        "benunit_id",
        "household_weight",
        "person_weight",
        "benunit_weight",
        "weight",
        "weights",
    }
)

# Row lists that come from survey cells and so must say whether the floor
# blanked them (``suppressed``), so the public file shows that apply_floor ran.
FLOORED_ROWS = ("decile", "winners_losers", "by_region", "by_age")


def banner_for(status: str) -> str:
    if status not in STATUSES:
        raise ValueError(f"Unknown status {status!r}; use one of {STATUSES}")
    return DEFAULT_BANNERS.get(status, "")


def _modifier_source(modifier) -> str | None:
    """The exact source of the module that holds a modifier, if any."""
    if modifier is None:
        return None
    module = sys.modules.get(modifier.__module__)
    try:
        return inspect.getsource(module) if module else None
    except (OSError, TypeError):
        return None


def receipt(reform: Reform) -> str:
    """SHA-256 of a measure's definition, so a published figure binds its exact inputs.

    Binds the summary, both sets of parameter changes, the modifier's dotted
    name and the exact source of its module. Run-level provenance (commit,
    clean tree, engine versions, dataset SHA-256) lives in the results file's
    ``provenance`` block, so a receipt stays the same across commits that do
    not change the measure.
    """
    modifier = reform.simulation_modifier
    payload = {
        "summary": reform.summary(),
        "parameter_changes": reform.parameter_changes,
        "baseline_parameter_changes": reform.baseline_parameter_changes,
        "modifier": (
            None
            if modifier is None
            else f"{modifier.__module__}.{modifier.__qualname__}"
        ),
        "modifier_source_sha256": (
            None
            if (source := _modifier_source(modifier)) is None
            else hashlib.sha256(source.encode()).hexdigest()
        ),
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode()).hexdigest()


def status_of(reform: Reform) -> str:
    """What the page may show for a measure."""
    if reform.withdrawn_reason:
        return "withdrawn"
    if not reform.computable:
        return reform.route.value
    if reform.placeholder:
        return "held-placeholder"
    if sign_off.REQUIRED:
        return "held-sign-off"
    return "published"


def manifest(reforms: Iterable[Reform]) -> list[dict[str, Any]]:
    return [
        {
            "id": reform.id,
            "status": status_of(reform),
            "receipt": receipt(reform),
        }
        for reform in reforms
    ]


def apply_floor(
    rows: list[dict[str, Any]],
    value_keys: Iterable[str],
    count_key: str = "n_households",
) -> list[dict[str, Any]]:
    """Blank the values of any row with fewer survey households than the floor.

    Every row gets ``suppressed`` (true or false). A count of zero is not
    suppressed: no household is behind the cell, so its zero discloses
    nothing. The count itself is dropped from the output, so the public file
    does not carry record counts.
    """
    value_keys = list(value_keys)
    out = []
    for row in rows:
        row = dict(row)
        count = row.pop(count_key, None)
        suppressed = count is None or 0 < count < DISCLOSURE_FLOOR
        if suppressed:
            for key in value_keys:
                row[key] = None
        row["suppressed"] = suppressed
        out.append(row)
    return out


def _walk_keys(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key, f"{path}.{key}"
            yield from _walk_keys(inner, f"{path}.{key}")
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _walk_keys(inner, f"{path}[{index}]")


def _check_status(results: dict[str, Any], errors: list[str]) -> None:
    status = results.get("status")
    banner = results.get("banner") or ""
    if status not in STATUSES:
        errors.append(f"$.status: {status!r} is not one of {list(STATUSES)}")
        return
    measures = results.get("measures", [])
    if (
        any(m.get("placeholder") for m in measures)
        and status not in PLACEHOLDER_STATUSES
    ):
        errors.append(
            "$.status: a placeholder measure needs status 'placeholder' or 'mock'"
        )
    if status != "final" and not banner.strip():
        errors.append(f"$.banner: status {status!r} needs the banner text")
    if status == "mock" and "MOCK" not in banner:
        errors.append("$.banner: a mock page's banner must contain 'MOCK'")
    if status == "final" and banner:
        errors.append("$.banner: a final page carries no banner")


def _check_floored_rows(mid: str, measure: dict[str, Any], errors: list[str]):
    for field in FLOORED_ROWS:
        rows = measure.get(field)
        if rows is None:
            continue
        for index, row in enumerate(rows):
            if "suppressed" not in row:
                errors.append(
                    f"{mid}.{field}[{index}]: every survey row says whether "
                    "it is suppressed"
                )


def validate_public(results: dict[str, Any]) -> list[str]:
    """Problems that block publishing the results file. Empty means it passes."""
    errors: list[str] = []
    for key, where in _walk_keys(results):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{where}: record identifier or weight in a public file")
        if key == "n_households":
            errors.append(f"{where}: record counts are not published")
    _check_status(results, errors)
    if results.get("status") in ("provisional", "final") and (
        (results.get("engine") or {}).get("certified_pair") is not True
    ):
        errors.append(
            "$.engine.certified_pair: a provisional or final page needs the "
            "pinned build and engine (data_build.DATA_BUILD)"
        )
    measures = results.get("measures", [])
    if results.get("status") not in PLACEHOLDER_STATUSES:
        for measure in measures:
            if (
                measure.get("computable")
                and measure.get("status") != "withdrawn"
                and not measure.get("budgetary_impact")
            ):
                errors.append(
                    f"{measure.get('id')}: a modelled measure needs its figures "
                    "outside placeholder and mock pages; withdraw it instead"
                )
    for measure in measures:
        mid = measure.get("id", "?")
        has_figures = measure.get("computable") and measure.get("status") != (
            "withdrawn"
        )
        if not has_figures:
            for field in ("budgetary_impact", "decile", "winners_losers"):
                if measure.get(field) is not None:
                    errors.append(
                        f"{mid}.{field}: a measure that is not computable or "
                        "is withdrawn carries no figure (never £0)"
                    )
            if not measure.get("route_reason"):
                errors.append(f"{mid}: give the reason it is not computable")
        if measure.get("status") == "withdrawn" and not measure.get("withdrawn_reason"):
            errors.append(f"{mid}: a withdrawn measure needs its reason")
        _check_floored_rows(mid, measure, errors)
    if results.get("package"):
        _check_floored_rows("package", results["package"], errors)
    _check_page_measures(results, errors)
    return errors


def _check_page_measures(results: dict[str, Any], errors: list[str]) -> None:
    """The page's presets and package cover exactly the measures in the file.

    A light version of AB2026's ``page_measures_check``: a stale preset or a
    package built from another measure list fails here, not on the page.
    """
    with_figures = {
        m["id"] for m in results.get("measures", []) if m.get("budgetary_impact")
    }
    for household in results.get("households", []):
        keys = set(household.get("reform", {}))
        if keys != with_figures:
            errors.append(
                f"households.{household.get('id')}: presets cover "
                f"{sorted(keys)}, the file's modelled measures are "
                f"{sorted(with_figures)}"
            )
    package = results.get("package")
    if package is not None and set(package.get("measure_ids", [])) != with_figures:
        errors.append("$.package: built from a different measure list than the file")
