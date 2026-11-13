"""Reform definition, copied in shape from the AB2026 dashboard (``uk_budget_data.models``).

Changes from the source:
- the ``Scenario`` import is lazy, so the registry and its tests load without
  policyengine-uk;
- each reform carries its route, cause class, publication status and
  placeholder flag, so the ledger and the page read them from one place.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class Route(str, Enum):
    """How a measure is handled on the day (the drill ledger's route classes)."""

    DASHBOARD_PARAM = "dashboard-param"
    DASHBOARD_STRUCTURAL = "dashboard-structural"
    LEDGER = "ledger"
    NOT_COMPUTABLE = "not-computable"
    NEEDS_PE_UK_FIRST = "needs-pe-uk-first"


class Likelihood(str, Enum):
    """Our pre-report judgement. Internal: kept for the ledger, never published."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InReport(str, Enum):
    """Whether the published report contains the measure; set at G1."""

    YES = "yes"
    NO = "no"
    NOT_YET_PUBLISHED = "not-yet-published"


class Reform(BaseModel):
    """Definition of a policy reform.

    A reform is defined by parameter changes (simple reforms) or by a
    simulation modifier from ``pip_review.measures`` (structural reforms).
    """

    id: str = Field(..., pattern=r"^[a-z0-9_]+$")
    name: str
    description: str = ""
    recommendation: str = Field(
        ..., description="The review recommendation this measure stands for"
    )
    likelihood: Likelihood
    in_report: InReport = InReport.NOT_YET_PUBLISHED
    route: Route
    route_reason: str = Field(
        ..., description="Why the measure has this route; shown on the page"
    )
    placeholder: bool = Field(
        True,
        description=(
            "Placeholder values, set before the report. A placeholder is never "
            "published as a figure."
        ),
    )
    zero_reason: str | None = Field(
        None,
        description=(
            "Why a coded measure's £0 national figure is right. Without it, a "
            "measure that scores £0 in every year fails the publication check."
        ),
    )
    data_needs: list[str] = Field(default_factory=list)
    issues: list[int] = Field(
        default_factory=list, description="Issues in this repository that block it"
    )
    parameter_changes: dict[str, dict[str, Any]] | None = None
    baseline_parameter_changes: dict[str, dict[str, Any]] | None = None
    simulation_modifier: Callable | None = None
    withdrawn_reason: str | None = Field(
        None,
        description=(
            "Set to withdraw a published measure (G5). The page then shows it "
            "as unavailable with this reason, never as £0."
        ),
    )
    england_and_wales_only: bool = Field(
        True,
        description=(
            "PIP applies in England and Wales. Until the model has a country "
            "test (issue #1), the run masks Scotland and Northern Ireland."
        ),
    )

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def _route_matches_content(self) -> "Reform":
        computable = self.route in (Route.DASHBOARD_PARAM, Route.DASHBOARD_STRUCTURAL)
        has_change = (
            self.parameter_changes is not None or self.simulation_modifier is not None
        )
        if self.route is Route.DASHBOARD_PARAM and self.parameter_changes is None:
            raise ValueError(f"{self.id}: dashboard-param needs parameter_changes")
        if (
            self.route is Route.DASHBOARD_STRUCTURAL
            and self.simulation_modifier is None
        ):
            raise ValueError(f"{self.id}: dashboard-structural needs a modifier")
        if not computable and self.simulation_modifier is not None:
            raise ValueError(f"{self.id}: only a computable route takes a modifier")
        if not computable and has_change and self.route is not Route.NOT_COMPUTABLE:
            raise ValueError(
                f"{self.id}: a {self.route.value} measure carries no model change"
            )
        return self

    @property
    def computable(self) -> bool:
        return self.route in (Route.DASHBOARD_PARAM, Route.DASHBOARD_STRUCTURAL)

    @property
    def publishable(self) -> bool:
        """A figure may be published: computable, not a placeholder, not withdrawn."""
        return self.computable and not self.placeholder and not self.withdrawn_reason

    def to_scenario(self):
        """Convert to a policyengine-uk ``Scenario`` (needs the ``model`` extra)."""
        from policyengine_uk.utils.scenario import Scenario

        kwargs: dict[str, Any] = {}
        if self.parameter_changes is not None:
            kwargs["parameter_changes"] = self.parameter_changes
        if self.simulation_modifier is not None:
            kwargs["simulation_modifier"] = self.simulation_modifier
        return Scenario(**kwargs)

    def to_baseline_scenario(self):
        if self.baseline_parameter_changes is None:
            return None
        from policyengine_uk.utils.scenario import Scenario

        return Scenario(parameter_changes=self.baseline_parameter_changes)

    def summary(self) -> dict[str, Any]:
        """The fields the page and the ledger read (no callables)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "recommendation": self.recommendation,
            "in_report": self.in_report.value,
            "route": self.route.value,
            "route_reason": self.route_reason,
            "placeholder": self.placeholder,
            "computable": self.computable,
            "publishable": self.publishable,
            "withdrawn_reason": self.withdrawn_reason,
            "zero_reason": self.zero_reason,
            "data_needs": list(self.data_needs),
            "issues": list(self.issues),
            "parameters": sorted(self.parameter_changes or {}),
        }
