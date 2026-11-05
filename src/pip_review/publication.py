"""Publication gate, scaled down from the AB2026 dashboard's ``publication`` package.

Kept: a manifest of what may be published, a receipt binding each measure's
definition, the disclosure floor and validation of the public results file.
Dropped: release index, area-code routing, attestations and responsiveness
(no constituency map in this template).
"""

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from pip_review import sign_off
from pip_review.models import Reform

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


def receipt(reform: Reform) -> str:
    """SHA-256 of a measure's definition, so a published figure binds its exact inputs."""
    payload = {
        "summary": reform.summary(),
        "parameter_changes": reform.parameter_changes,
        "baseline_parameter_changes": reform.baseline_parameter_changes,
        "modifier": (
            None
            if reform.simulation_modifier is None
            else f"{reform.simulation_modifier.__module__}."
            f"{reform.simulation_modifier.__qualname__}"
        ),
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode()).hexdigest()


def status_of(reform: Reform) -> str:
    """What the page may show for a measure."""
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

    The count itself is dropped from the output, so the public file does not
    carry record counts.
    """
    value_keys = list(value_keys)
    out = []
    for row in rows:
        row = dict(row)
        count = row.pop(count_key, None)
        if count is None or count < DISCLOSURE_FLOOR:
            for key in value_keys:
                row[key] = None
            row["suppressed"] = True
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


def validate_public(results: dict[str, Any]) -> list[str]:
    """Problems that block publishing the results file. Empty means it passes."""
    errors: list[str] = []
    for key, where in _walk_keys(results):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{where}: record identifier or weight in a public file")
        if key == "n_households":
            errors.append(f"{where}: record counts are not published")
    measures = results.get("measures", [])
    any_placeholder = any(m.get("placeholder") for m in measures)
    if any_placeholder and results.get("status") != "placeholder":
        errors.append("$.status: a placeholder measure needs status 'placeholder'")
    if results.get("status") == "placeholder" and not results.get("banner"):
        errors.append("$.banner: placeholder figures need the banner text")
    for measure in measures:
        mid = measure.get("id", "?")
        if not measure.get("computable"):
            for field in ("budgetary_impact", "decile", "winners_losers"):
                if measure.get(field) is not None:
                    errors.append(
                        f"{mid}.{field}: a measure that is not computable carries "
                        "no figure (never £0)"
                    )
            if not measure.get("route_reason"):
                errors.append(f"{mid}: give the reason it is not computable")
    return errors
