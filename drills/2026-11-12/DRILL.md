# Drill: Thursday 12 November 2026, 14:00–16:30

A mock release of the PIP review final report, run as a timed drill before the real report lands. The drill tests the path from release to a dashboard on a protected preview: coverage, coding, reconciliation against official figures, a mid-drill correction, and publication checks.

**This file holds no mock content.** The drill owner wrote the mock packet and the answer key and holds them outside this repository. Only their SHA-256 hashes are below. The integrator stays blind to the packet until each file is released.

This file sits in `drills/2026-11-12/` so it does not touch `docs/DRILL.md` in the template PR (#9). For this drill, this file is the one to follow.

## Timeline (London time)

| Time | T | Release | Gate | Owner |
|---|---|---|---|---|
| by 13:30 | T−30 | none | **G0** freeze record (below) | Integrator |
| 14:00 | T+0 | `statement.md` (mock summary of recommendations with an illustrative-parameters annex) | **G1** by 14:10: coverage ledger, every recommendation routed and given a cause class | Reconciler |
| 14:30 | T+30 | none | **G2**: provisional numbers for every coded measure, plus one hand-checked household per coded measure | Integrator, reconciler |
| 14:40 | T+40 | `documents.zip` (mock costing note, people affected, specimen households, blank scoring sheet) | **G3** to 15:10: re-base and reconcile; every gap over 10% has a written reason and a cause class | Reconciler |
| 15:15 | T+75 | `inject.md` and `inject_rows.csv` (a correction notice) | **G5**: rerun, new scoring SHA, re-run every hand-computed household row, update ledger causes | Integrator, scorer |
| 15:40 | T+100 | none | **G4**: full page on a protected preview, MOCK banner and noindex checked behind the login | Integrator |
| 15:50 | T+110 | none | stop; log the stop commit SHA | Integrator |
| 16:00 | T+120 | `answer_key.csv`, `make_key.py` and `key_meta.json` | scoring to 16:30; scorer checks the key's hash first | Drill owner, scorer |

### G0 freeze record

Write these in the drill issue before 13:30:
- start SHA of the drill branch (cut from `main` after the template PR, or from the template branch head if #9 is not merged; say which);
- `policyengine` and `policyengine-uk` versions (pinned: policyengine 6.11.1, policyengine-uk 2.151.0);
- dataset name and SHA-256 of the national file;
- "validated pair" or "unvalidated under this engine" on every figure.

## Roles (one person each; only the integrator pushes)

| Role | Owns | Does not |
|---|---|---|
| Integrator | the drill branch, the clock table, every commit, generation, re-basing | read the packet before release; score households |
| Reconciler | the coverage ledger, the reconciliation CSV, defects as PR comments within 5 minutes | push code |
| Scorer (the reconciler after T+40) | specimen households, one commit SHA per scoring run | edit reform code |
| Drill owner | the sealed packet, release times, the answer key | take part in coding |

## Route classes

Every ledger line gets one of the registry's five routes, and the route says where the work lands:

| Route | Where the work lands | Meaning |
|---|---|---|
| `dashboard-param` | dashboard repo | a parameter change, coded in this repo on the day |
| `dashboard-structural` | dashboard repo | a modifier or mask, one module per modifier in this repo |
| `ledger` | dashboard repo (ledger only) | not modelled; the official figure is recorded with its source |
| `not-computable` | data | the measure acts through an input the data lack; shown with the reason, never as £0 |
| `needs-pe-uk-first` | policyengine-uk | the engine needs a new formula or parameter; filed upstream as a draft the same day |

Every line also gets a cause class: `parameter`, `formula`, `data_calibration`, `basis`, `timing_fiscal_calendar`, `coverage`, `interaction` or `baseline_mismatch`.

Lines that go in the ledger before G1, whatever the packet says:
- Scotland and Northern Ireland are inside PIP in the model; every measure is masked to England and Wales (#1).
- Points are not held; any points or descriptor measure is `not-computable` (#3).
- Carer's Allowance does not follow the cared-for person's PIP; carer effects are a ledger line (#2).
- The model caseload is above DWP's for England and Wales and does not grow after 2024-25 (#4).

Expect trap rows: statement items that are already in the baseline. Routing one as a new measure is a defect.

## Basis, declared once

Static, cash, fiscal year, England and Wales, £ million; positive is a cost to the Exchequer. Official tables may use other conventions (sign, behavioural responses, caseload source). Re-base them to this basis at G3 and write down every conversion.

## Rubric (100)

| Item | Points |
|---|---|
| Specimen households to ±1p, after the inject | 20 |
| National figures: basis and gap class for each coded measure and year | 30 |
| Ledger: route, cause class and reason for each line, including trap rows | 25 |
| Publication path: MOCK banner, noindex, public-data guard passes, preview behind the login | 10 |
| Process: gates on time, one SHA per scoring run, inject logged, stop commit logged | 15 |

## What to time and log

Use the documents clock (T+0 is 14:00). Keep a clock table in the drill PR with one row per step:

| Step | Start | End | Machine time | People time | Commit SHA | Note |
|---|---|---|---|---|---|---|

- Split machine time (generation, tests, build) from people time (reading, coding, review).
- Log the time each release file is received and the time its hash was checked.
- Log the time each defect was posted and the time it was read.
- Log every rerun with its SHA; one SHA per scoring run.
- Log the inject: time received, what changed, which rows were re-run.

## MOCK and noindex rules

- Every page built from the drill branch carries the MOCK banner and `noindex, nofollow`.
- Check both on the protected preview behind the login, not on a local build.
- Nothing from the packet goes into a public file, issue, PR or comment until scoring ends. The drill branch is a draft PR labelled `not for merge`, never stacked on another unmerged PR.
- No deploy to a public URL. The preview stays protected.
- The repository is public and its figures come from licensed microdata: `scripts/check_public_data.py` must pass on every public file.

## Packet hashes (SHA-256)

The scorer checks each released file against this table before use.

| File | Released at | SHA-256 |
|---|---|---|
| `statement.md` | T+0 (14:00) | `14a5aecc909b1017884d7b726c33e74baabf1a3fb4c8167c962116d086c6427c` |
| `documents.zip` | T+40 (14:40) | `9b2f8088ca4518778501f53d68c7d2be745dacdc64caeb694ac17466dfb86484` |
| `inject.md` | T+75 (15:15) | `4e1e249fab79499cf143fb39dd41f73386948e959d7fe111490d24443d7a72cb` |
| `inject_rows.csv` | T+75 (15:15) | `969e787153192ec422bf5a57ff73bbe27681b6f968998ea7b5eed42504273c46` |
| `answer_key.csv` | T+120 (16:00) | `6acee539ae5a456424e74f2704dd79c4a867861ee9cec223ed9a98af5b6cd216` |
| `make_key.py` | T+120 (16:00) | `370de5ba6d761ca9f321c3e525942db3d08ae7474474f585e8cfe9d2db516039` |
| `key_meta.json` | T+120 (16:00) | `d042e453b638e54b3d6c19ac8ba7cd63f05168a4f342c1358471732c58f33821` |

## Retro

Within one working day, in the drill issue: score by rubric row, what was lost and why, defects by cause class, machine and people time per step, and fixes to file before the real report.
