# Drill: Thursday 12 November 2026, 14:00–16:30

A mock release of the PIP review final report, run as a timed drill before the real report lands. The drill tests the path from release to a dashboard on a local production build: coverage, coding, reconciliation against official figures, a mid-drill correction, and publication checks.

**This file holds no mock content.** The drill owner wrote the mock packet and the answer key and holds them outside this repository. Only their SHA-256 hashes are below. The integrator stays blind to the packet until each file is released.

This file is the one home for this drill's plan and packet hashes; `docs/DRILL.md` and `data_inputs/packet/HASHES.md` in the template PR (#9) point here.

## Timeline (London time)

| Time | T | Release | Gate | Owner |
|---|---|---|---|---|
| by 13:30 | T−30 | none | **G0** freeze record (below) | Integrator |
| 14:00 | T+0 | `statement.md` (mock summary of recommendations with an illustrative-parameters annex) | **G1** by 14:10: coverage ledger, every recommendation routed and given a cause class | Reconciler |
| 14:30 | T+30 | none | **G2**: provisional numbers for every coded measure, plus one hand-checked household per coded measure | Integrator, reconciler |
| 14:40 | T+40 | `documents.zip` (mock costing note, people affected, specimen households, blank scoring sheet) | **G3** to 15:10: re-base and reconcile; every gap over 10% has a written reason and a cause class | Reconciler |
| 15:15 | T+75 | `inject.md` and `inject_rows.csv` (a correction notice) | **G5**: rerun, new scoring SHA, re-run every hand-computed household row, update ledger causes | Integrator, scorer |
| 15:40 | T+100 | none | **G4**: full page on a local production build from the G5 rerun SHA, MOCK banner and noindex checked in the served HTML | Integrator |
| 15:50 | T+110 | none | stop; log the stop commit SHA | Integrator |
| 16:00 | T+120 | `answer_key.csv`, `make_key.py` and `key_meta.json` | scoring to 16:30; scorer checks the hashes of all three first | Drill owner, scorer |

### G0 freeze record

Write these in the drill issue before 13:30:
- start SHA of the drill branch. The default is a local run branch cut from the head of `bump-policyengine-6.17.2` (PR #14, which branches from the template branch #9); drills never merge, so the unmerged bump branch is allowed as the base. Say which commit it was cut from;
- `policyengine`, `policyengine-uk` and `policyengine-core` versions (pinned: policyengine 6.17.2, policyengine-uk 2.174.1, policyengine-core 3.33.3);
- dataset name and SHA-256 of the national file (certified by policyengine 6.17.2: `microcosm-uk-2024-25-national-20261107T020434Z-eeb6093e`, SHA-256 `0a9b77db1c0dee2693cb2d47bad68da34cb662916eee4829942bcd45de581f25`);
- "certified bundle pair; PIP-specific validation pending (#1, #4)" on every figure.
- The pin moved from policyengine 6.11.1 (policyengine-uk 2.151.0) to 6.17.2 on 12 November. PIP current-law rates for 2028-29 onwards and the 2027-28 minimum wage differ between the two (see PR #14). The drill owner regenerated the key, `inject_rows.csv` and the T+40 tables on 6.17.2 at 13:00 on 12 November (single-household simulations; the national cell counts are unchanged) and updated the four hashes below; `statement.md`, `inject.md` and `make_key.py` are unchanged.

## Roles (one person each; only the integrator pushes)

| Role | Owns | Does not |
|---|---|---|
| Integrator | the drill branch, the clock table, every commit, generation, re-basing | read the packet before release; score households |
| Reconciler | the coverage ledger, the reconciliation CSV, defects as PR comments within 5 minutes | push code |
| Scorer (the reconciler after T+40) | specimen households, one commit SHA per scoring run | edit reform code |
| Drill owner | the sealed packet, release times, the answer key | take part in coding |

### Load on the clock

The scorer is also the reconciler after T+40, so household scoring starts only after G3 closes at 15:10, unless a third person can score. Start the G4 production build as soon as the G5 rerun SHA exists rather than at 15:40: the build waits for the heavy-run lock and 14 GB free. Log its machine time.

## Commands

Run from the drill branch (the template's machinery must be on it).

```sh
# setup, before G0
uv sync --locked --extra dev --extra model
(cd dashboard && bun install --frozen-lockfile)

# G2 and G5: every drill measure id starts with mock6_; status mock forces the MOCK banner
uv run pip-review generate --mode model --status mock             # takes the heavy-run lock
uv run pip-review household <preset> --reform <id>

# G3
uv run pip-review reconcile --out drills/2026-11-12/reconciliation.csv --reasons drills/2026-11-12/gap_reasons.csv

# public-data guard, with the drill files named explicitly
uv run python scripts/check_public_data.py data/results.json dashboard/public/data/results.json drills/2026-11-12/ledger.csv drills/2026-11-12/reconciliation.csv

# G4: local production build, in a subshell that holds the lock and waits for 14 GB free+inactive
(
  until mkdir /tmp/pe-heavy.lock 2>/dev/null; do sleep 15; done
  trap 'rmdir /tmp/pe-heavy.lock' EXIT
  free_gb() { vm_stat | awk '/Pages free/ {f=$3} /Pages inactive/ {i=$3} END {print int((f+i)*16384/1e9)}'; }
  until [ "$(free_gb)" -ge 14 ]; do sleep 30; done
  cd dashboard && bun run data && bun run build && bun run smoke   # serves, checks noindex and the MOCK banner, stops the server
)
git rev-parse HEAD                                                 # record the build SHA in the clock table
```

The coverage ledger is `drills/2026-11-12/ledger.csv` and the reconciliation is `drills/2026-11-12/reconciliation.csv`. Whether they sit on the public draft PR during the drill or in a private channel until scoring ends is still to be decided (see the drill issue); the guard runs on them either way.

## Preflight, by Wednesday 11 November

- [ ] The drill branch has the template's CI, pipeline and dashboard on it, and CI runs on it.
- [x] `generate --mode model` timed end to end on the national file with the four template measures (no mock content), under the lock, on 6 November at template commit `0aadc8c`: baseline 45 s, about 80 s per measure and 79 s for the package, about 9 minutes in all with the example households. G2 needs about 2 minutes plus 80 s per coded measure once the lock is free.
- [x] One local production build timed: `bun run build` 10 s, and `bun run smoke` passed (noindex and banner in the served HTML).
- [ ] Roles named in the drill issue.

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
- The model caseload is below DWP's for England and Wales, by 5% to 26% over 2026-27 to 2030-31, because it grows only with population after 2024-25 (#4). Carry a modelled ÷ DWP caseload ratio per year in the ledger, and a "baseline below DWP by X%" note on any proportional measure.

Expect trap rows: statement items that are already in the baseline. Routing one as a new measure is a defect.

## Basis, declared once

Static, cash, fiscal year, England and Wales, £ million; positive is a cost to the Exchequer. Official tables may use other conventions (sign, behavioural responses, caseload source). Re-base them to this basis at G3 and write down every conversion.

## Rubric (100)

| Item | Points |
|---|---|
| Specimen households to ±1p, after the inject | 20 |
| National figures: basis and gap class for each coded measure and year | 30 |
| Ledger: route, cause class and reason for each line, including trap rows | 25 |
| Publication path: MOCK banner, noindex, public-data guard passes, on the local production build | 10 |
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
- Check both in the served HTML of a local production build (`bun run smoke`). On the real day, check them again on the protected Vercel preview behind the login, once that project exists.
- Nothing from the packet goes into a public file, issue, PR or comment until scoring ends. The drill branch is a draft PR labelled `not for merge`, never stacked on another unmerged PR.
- No deploy to any URL. The drill page is a local build only; kill the server after the check.
- The repository is public and its figures come from licensed microdata: `scripts/check_public_data.py` must pass on every public file.

## Packet hashes (SHA-256)

The scorer checks each released file against this table before use.

| File | Released at | SHA-256 |
|---|---|---|
| `statement.md` | T+0 (14:00) | `14a5aecc909b1017884d7b726c33e74baabf1a3fb4c8167c962116d086c6427c` |
| `documents.zip` | T+40 (14:40) | `d2a6a6f0e5d2131f3498f35b2d15d02700e18eb4de7a068b3a73a3c0406bd686` |
| `inject.md` | T+75 (15:15) | `4e1e249fab79499cf143fb39dd41f73386948e959d7fe111490d24443d7a72cb` |
| `inject_rows.csv` | T+75 (15:15) | `8550cdb2e1610e648ac2dee280bf5c1388007ba20ac727ac6a00e6c0b59b49fe` |
| `answer_key.csv` | T+120 (16:00) | `6d726e7d04947b7a1b58b08236b711f799c5e2c6a96f3ec3306821f1b13ea524` |
| `make_key.py` | T+120 (16:00) | `370de5ba6d761ca9f321c3e525942db3d08ae7474474f585e8cfe9d2db516039` |
| `key_meta.json` | T+120 (16:00) | `b25dec449c4dc90392f8a2fe640eecaad12645c64a875935e31f247efa755277` |

## Retro

Within one working day, in the drill issue: score by rubric row, what was lost and why, defects by cause class, machine and people time per step, and fixes to file before the real report.
