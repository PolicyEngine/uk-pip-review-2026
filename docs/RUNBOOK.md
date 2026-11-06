# Runbook for the day the report is published

The review reports in November 2026 (written answer UIN 38956, 3 November 2026); no date has been announced. The government response is due before the end of 2026, with a White Paper early in 2027; the OBR will cost the response, not the report. From 9 November, check the GOV.UK collection page for the review and GOV.UK search each morning.

The one-page checklist is [`event-day-checklist.md`](event-day-checklist.md). Drill plans live in `drills/<date>/DRILL.md`.

## Freeze rule

From G0 until the stop commit, nothing that changes the calculation path merges or lands on the event branch except through the integrator: `src/pip_review/` (reforms, measures, aggregate, pipeline, publication), `pyproject.toml`, `uv.lock` and `data_inputs/official/`. Page text and layout may still change. Do not adopt a new policyengine release after G0.

## Commands

```sh
uv sync --locked --extra dev --extra model
(cd dashboard && bun install --frozen-lockfile)

# heavy-run lock: one data-loading job or production build at a time
until mkdir /tmp/pe-heavy.lock 2>/dev/null; do sleep 15; done; trap 'rmdir /tmp/pe-heavy.lock' EXIT

uv run pip-review generate --mode model --status provisional     # takes the lock itself
uv run pip-review household <preset> --reform <id>                # one household, light
uv run pip-review reconcile --out reconciliation.csv --reasons gap_reasons.csv
uv run python scripts/check_public_data.py                        # data/ and dashboard/public/data/
uv run python scripts/check_public_data.py ledger.csv reconciliation.csv   # any other public file

cd dashboard && bun run data && bun run build && bun run smoke    # build under the lock
```

`generate --mode model` runs current law, each computable measure and the package, one simulation per process, inside the lock, and refuses an installed bundle other than the one recorded in `pipeline.CERTIFIED_BUNDLE`. It records machine time per run in `provenance.machine_seconds`.

## Gates

1. **G0 (as soon as the date is known).** Record the start SHA, policyengine and policyengine-uk versions, dataset build id and SHA-256 (`pipeline.CERTIFIED_BUNDLE`, from the bundle manifest), and "certified bundle pair; PIP-specific validation pending (#1, #4)". If DWP's autumn 2026 benefit expenditure and caseload tables are out, swap them into `data_inputs/official/` and regenerate.
2. **G1 (within 30 minutes of publication).** Read the report. Write the coverage ledger: one line per recommendation with route and cause class. Replace the placeholder measures in `reforms.py` with the report's own, set `in_report`, and keep `placeholder=True` until reconciled. A measure that moves award levels wraps its modifier in `carers_allowance_link.after(...)` so Carer's Allowance follows the cared-for person's award (#2).
3. **G2.** `generate --mode model --status provisional`. Hand-check one household per measure.
4. **G3.** Put each official costing in `data_inputs/official/costings_<source>.csv` (`measure_id,fiscal_year,value_m,basis,source`, re-based to our basis) and run `reconcile`. Every gap over 10% needs a reason and a cause class in the reasons CSV.
5. **G4.** Sign-off rows for every public file in `data_inputs/public_data_review.csv` (`path,sha256,reviewer,reviewed_on`); the build refuses a provisional or final page without them. Local build and `bun run smoke`. On the real day, also check the protected Vercel preview behind the login once the project exists. Set `--status final` only after sign-off; noindex stays until then.
6. **G5: corrections.** See below.

## G5: corrections and withdrawals

1. **Withdraw** a wrong measure at once: set `withdrawn_reason` on it in `reforms.py`. The page shows it as unavailable with the reason, never as £0.
2. **Fix** the measure or the data on the event branch (one commit, through the integrator).
3. **Regenerate** in model mode; the results file records the new commit.
4. **Re-reconcile** and update the ledger causes; refresh the sign-off rows.
5. **Redeploy**: the page imports `results.json` at build time, so every correction is regenerate, commit, rebuild and redeploy. Log the new SHA in the clock table.

## Rollback

- Vercel Instant Rollback to the deployment ID recorded in the clock table.
- Then `git revert -m 1 <merge>` through a PR, never a push to main.
- Once the fix is reviewed, `vercel promote` the fixed deployment.

## Clock table

Keep one row per event in the event PR:

| Event | Time | Commit SHA | results.json SHA-256 | Vercel deployment ID or rollback target | Note |
|---|---|---|---|---|---|

## Before the event (needs the team)

- Vercel project with root `dashboard/`, framework Next.js, build `bun run build`; protection on previews.
- The route under policyengine.org (basePath) and the app-v2 zone rewrite and `apps.json` entry.
- Required checks on main and a certified-data CI job (the repository secret needs an org admin).
- `deploy.yml` stays `workflow_dispatch` only until then.
