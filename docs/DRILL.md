# Drill: Thursday 12 November 2026, 14:00-16:30

A mock release of the final report, run on the compressed clock (two drills that day; this is the afternoon one). The packet is mock: invented recommendations and costings, written by the drill owner and held outside this repository. Only their hashes are committed (`data_inputs/packet/HASHES.md`).

## Clock

| Time | T | Release | Gate |
|---|---|---|---|
| by 13:30 | | none | **G0** freeze record: start SHA, policyengine and policyengine-uk versions, dataset name and SHA-256, validated pair or "unvalidated" label |
| 14:00 | T+0 | statement (mock report summary) | **G1** by 14:10: coverage ledger, every recommendation routed |
| 14:30 | T+30 | none | **G2**: provisional numbers against the statement, plus one hand-checked household per coded measure |
| 14:40 | T+40 | documents (mock costings table, mock DWP figures, specimen households, blank scoring sheet) | **G3** to 15:10: re-base and reconcile; each gap over 10% has a written reason |
| 15:15 | T+75 | inject (a correction notice) | **G5**: rerun, new scoring SHA, re-run hand-computed rows |
| 15:40 | T+100 | none | **G4**: full page on a protected preview with the banner and noindex, checked behind the login |
| 15:50 | T+110 | none | stop; log the stop commit |
| 16:00 | T+120 | answer key | scoring, to 16:30 |

## Roles (one person each; only the integrator pushes)

| Role | Owns | Does not |
|---|---|---|
| Integrator | the branch, the clock table, every commit, generation, re-basing | score households |
| Reconciler | the ledger, the reconciliation CSV, defects as PR comments within 5 minutes | push code |
| Scorer (the reconciler after T+40) | specimen households, one commit SHA per scoring run | edit reform code |

## Ledger

Every line gets a route (`dashboard-param`, `dashboard-structural`, `ledger`, `not-computable`, `needs-pe-uk-first`) and a cause class (`parameter`, `formula`, `data_calibration`, `basis`, `timing_fiscal_calendar`, `coverage`, `interaction`, `baseline_mismatch`).

Lines that must be in the ledger before G1, whatever the packet says:
- Scotland and Northern Ireland are inside PIP; reforms are masked to England and Wales (#1).
- Points are not held; any points or descriptor measure is `not-computable` (#3).
- Carer's Allowance does not follow PIP; carer effects are a ledger line (#2).

## Rubric (100)

| Item | Points |
|---|---|
| Households to ±1p | 20 |
| National figures: basis and gap class | 30 |
| Ledger class, route and cause | 25 |
| Publication path (banner, noindex, guard passes) | 10 |
| Process: gates on time, one SHA per run, inject logged | 15 |

The packet includes trap rows: statement items already in the baseline (for example the April 2026 rates and the UC health element split for new claims).

## Hygiene

- Draft PR from `main`, labelled `not for merge`, never stacked on another unmerged PR.
- Code in waves: parameters, then modifiers, then new variables.
- Time each step on the documents clock; record machine time and people time separately.
