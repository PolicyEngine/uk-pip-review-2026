# Data contract

- **Engine and data pair.** `policyengine[uk]==6.11.1`, which pins policyengine-uk 2.151.0 and the Microcosm UK 2024-25 national build `20261025T091414Z-a6299504`. Not yet a validated pair for PIP: every figure carries "unvalidated under this engine" until G0 names a certified pair.
- **Microdata stay private.** No `.h5` file, record-level extract or weight is committed (`.gitignore`, `scripts/check_public_data.py`).
- **Columns the PIP measures read:** `pip_dl_category`, `pip_m_category`, `age`, `region`/`country`, `carers_allowance_reported`, `is_disabled_for_benefits`, `is_severely_disabled_for_benefits`.
- **Columns the PIP measures need but the data lack:** `pip_dl_points`, `pip_m_points`, a score per activity, a health-condition group, hospital stays, award duration and review dates, caring for someone outside the household.
- **Heavy runs.** Run one data-loading job at a time and check available memory first. Prefer reading the needed columns to full simulations.
