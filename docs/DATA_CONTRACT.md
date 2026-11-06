# Data contract

- **Engine and data pair.** `policyengine[uk]==6.11.1`, which pins policyengine-uk 2.151.0 and the Microcosm UK 2024-25 national build `20261025T091414Z-a6299504` (SHA-256 `b96a8cd625b645a409c063b1de5158532708a2f0d3c3897a794a8fb0bbd5064e`). This is the bundle's certified pair; PIP-specific validation is pending (#1, #4). Model mode refuses any other installed bundle (`pipeline.CERTIFIED_BUNDLE`).
- **Microdata stay private.** No `.h5` file, record-level extract or weight is committed (`.gitignore`, `scripts/check_public_data.py`).
- **Columns the PIP measures read:** `pip_dl_category`, `pip_m_category`, `dla_sc_category`, `dla_m_category`, `age`, `region`, `carers_allowance_reported`, `is_disabled_for_benefits`, `is_severely_disabled_for_benefits`. `pip_dl`, `pip_m` and `uc_limited_capability_for_WRA` are formulas, not stored, so a modifier may wrap them.
- **England and Wales mask.** Every table keeps England and Wales households only (`pip_review.aggregate`). In a static run households do not interact, so this gives the figures a country test would.
- **Columns the PIP measures need but the data lack:** `pip_dl_points`, `pip_m_points`, a score per activity, a health-condition group, hospital stays, award duration and review dates, caring for someone outside the household.
- **Heavy runs.** One data-loading job or production build at a time, under `/tmp/pe-heavy.lock` with at least 14 GB free (`pip_review.heavy`). Model mode runs one simulation per process; its record-level arrays stay in a temporary directory and are never published.
