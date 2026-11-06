"""Model limits: places where the installed policyengine-uk mis-costs a PIP measure.

Pruned from the AB2026 dashboard's ``model_limits``. A measure that touches a
model limit is held at provisional and never approved until the limit is
fixed upstream or handled in this repository.
"""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelLimit:
    key: str
    paths: tuple[str, ...]
    reason: str
    public_reason: str
    issue: int | None = None

    def covers(self, path: str) -> bool:
        return any(path == p or path.startswith(p + ".") for p in self.paths)


LIMITS: tuple[ModelLimit, ...] = (
    ModelLimit(
        key="pip_no_country_test",
        paths=("gov.dwp.pip", "variable:pip", "variable:pip_dl", "variable:pip_m"),
        reason=(
            "pip_dl and pip_m have no country test, and Scottish Adult "
            "Disability Payment is stored as PIP. Mask to England and Wales."
        ),
        public_reason=(
            "The model counts Scottish Adult Disability Payment and Northern "
            "Ireland PIP as PIP. Figures cover England and Wales households only."
        ),
        issue=1,
    ),
    ModelLimit(
        key="carers_allowance_ignores_pip",
        paths=(
            "gov.dwp.carers_allowance.qualifying_disability_benefits",
            "variable:carers_allowance",
        ),
        reason=(
            "carers_allowance_pre_overlap never reads the cared-for person's "
            "award, so a PIP change leaves Carer's Allowance unchanged."
        ),
        public_reason=(
            "Carer's Allowance in the model does not depend on the cared-for "
            "person's award, so a change to PIP awards leaves carers' "
            "payments unchanged."
        ),
        issue=2,
    ),
    ModelLimit(
        key="uc_health_proxy",
        paths=(
            "gov.dwp.universal_credit.rebalancing",
            "variable:uc_limited_capability_for_WRA",
        ),
        reason=(
            "UC limited capability for work-related activity follows the "
            "stored flag is_disabled_for_benefits, not PIP."
        ),
        public_reason=(
            "The Universal Credit health element follows a recorded disability "
            "status, not PIP, so a change to PIP does not change it."
        ),
        issue=6,
    ),
    ModelLimit(
        key="stored_disability_flags",
        paths=(
            "variable:is_disabled_for_benefits",
            "variable:is_severely_disabled_for_benefits",
        ),
        reason=(
            "Disability flags are stored columns and do not follow a PIP "
            "reform; disability premiums and elements stay unchanged."
        ),
        public_reason=(
            "Recorded disability status does not follow a PIP change, so "
            "disability premiums and elements in other benefits stay the same."
        ),
        issue=7,
    ),
    ModelLimit(
        key="caseload_grows_with_population",
        paths=(),
        reason=(
            "Projected years copy the base-year inputs forward and grow weights "
            "with population (extend_single_year_dataset), so the caseload does "
            "not follow DWP's forecast path (policyengine-uk #2889, item 6)."
        ),
        public_reason=(
            "The PIP caseload is calibrated to the OBR's PIP forecast for "
            "2025-26, which is close to DWP's figures. In later years it grows "
            "with the population, not with DWP's caseload "
            "forecast, so it falls further below DWP's forecast in each later "
            "year."
        ),
        issue=4,
    ),
)


def variable_path(name: str) -> str:
    return f"variable:{name}"


def limits_for_paths(paths: Iterable[str]) -> list[ModelLimit]:
    paths = list(paths)
    return [limit for limit in LIMITS if any(limit.covers(p) for p in paths)]
