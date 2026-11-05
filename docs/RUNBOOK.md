# Runbook for the day the report is published

The publication date is not announced. The government response is due before the end of 2026, with a White Paper early in 2027; the OBR will cost the response, not the report.

1. **G0 (as soon as the date is known).** Freeze the engine and data pair; record versions and the dataset SHA-256 in the PR. Run one data-loading job at a time.
2. **G1 (within 30 minutes of publication).** Read the report. Write the coverage ledger: one line per recommendation with route and cause. Replace the placeholder measures in `reforms.py` with the report's own, keeping `placeholder=True` until reconciled.
3. **G2.** Generate in model mode for the computable measures, England and Wales mask on. Hand-check one household per measure.
4. **G3.** Reconcile against any official figure in `data_inputs/official/`. Write a reason for each gap over 10%.
5. **G4.** Protected preview with banner and noindex, checked behind the login. Sign-off rows for every public file (`sign_off.REQUIRED` is on).
6. **G5.** Re-run after any correction or new official figure; update the ledger causes.

Nothing deploys from this repository until the team chooses a target (`.github/workflows/deploy.yml`).
