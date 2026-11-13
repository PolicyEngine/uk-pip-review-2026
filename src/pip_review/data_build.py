"""The Microcosm build a model run uses, and the engine it was built on.

The rule (12 November 2026): use the newest published Microcosm build with
the policyengine-uk version it was built and certified on, even when no
policyengine.py release covers that pair, and never mix a build with
another engine version. ``DATA_BUILD`` is the one place that names the
build; the engine pins in ``pyproject.toml`` must match its ``engine`` and
``core`` (tests/test_engine_pin.py checks them).
"""

from dataclasses import dataclass

HF_REPO = "policyengine/populace-uk-private"
HF_REPO_TYPE = "dataset"
HF_RELEASE = "microcosm-uk-2024-25-national"
HF_FILE = "microcosm_uk_2024_25.h5"


@dataclass(frozen=True)
class DataBuild:
    """One published Microcosm build and the engine it was built on."""

    id: str
    sha256: str
    engine: str
    core: str

    @property
    def short_id(self) -> str:
        return self.id.rsplit("-", 1)[-1]

    @property
    def hf_path(self) -> str:
        return f"releases/{HF_RELEASE}/{self.id}/{HF_FILE}"

    @property
    def label(self) -> str:
        return f"build {self.id}, policyengine-uk {self.engine}, not in a policyengine.py release"


# Switched 13 November 2026 from build 9e18f010 to 6f918b81, the newest
# published build (also policyengine-uk 2.177.7).
DATA_BUILD = DataBuild(
    id="uk-frs-calibration-attempt-20261112T133744Z-6f918b81",
    sha256="e268e3af7932784ad4471f008097a5acc6c3c5bc15c4c54fbb5a489b2a0ac9ae",
    engine="2.177.7",
    core="3.34.10",
)

LABEL = DATA_BUILD.label
