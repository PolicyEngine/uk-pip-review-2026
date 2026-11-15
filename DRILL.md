# Drill: Sunday 15 November 2026, 22:05–00:35

A timed rehearsal of the day the independent review of Personal Independence Payment publishes its final report and the government responds, run on a mock release before the real one. It tests the path from release to a dashboard on a local production build: coverage, coding, reconciliation against official figures, a mid-drill correction, freezing the scored files at the stop, and publication checks. All times are London time; times after midnight are Monday 16 November.

**This file holds the plan only. It says nothing about the mock content.** The drill owner wrote the mock packet and the answer key and holds them outside this repository; only their SHA-256 hashes are below. The integrator stays blind to the packet until each file is released. This file is the one home for this drill's clock and packet hashes; `docs/DRILL.md` and `data_inputs/packet/HASHES.md` point here.

The drill runs on a local run branch cut from the head of `engine-2.177.7-microcosm-9e18f010` (the branch name keeps the old build id; its head is on build 6f918b81). Before G0 the integrator cuts it, merges the drill PR's branch into it for this file, and records the start SHA and the engine-branch SHA it was cut from. Drills never merge, so the unmerged engine branch is allowed as the base.

## Clock

Four drills share this machine tonight, staggered so heavy runs never overlap. A heavy run (any national `generate`, any production build) takes `/tmp/pe-heavy.lock` only inside this drill's own slots. A run that cannot finish inside its slot is not started; an overrun is logged, and the next slot owner logs the wait as lock wait.

| Time | T | Release | Gate |
|---|---|---|---|
| by 21:35 | T−30 | none | **G0**: pair record, by hand (below) |
| 22:05 | T+0 | statement | **G1** by 22:15: coverage ledger, every line routed, given a cause class, and flagged if already in the baseline |
| 22:15–22:35 | | heavy slot 1 | **G2** by 22:35: provisional numbers for every coded measure, one hand-checked household per coded measure |
| 22:45 | T+40 | documents: costings, example households, blank scoring sheet | **G3** by 23:15: re-base and reconcile; every gap over 10% has a written reason and a gap class |
| 23:20 | T+75 | correction notice | **G5** by 23:40: re-run everything affected, a new scoring SHA, every touched hand row re-run into its own file |
| 23:20–23:45 | | heavy slot 2 | G5 rerun, then the G4 build |
| by 23:45 | T+100 | none | **G4**: full page on a local production build, MOCK banner, noindex meta and X-Robots-Tag checked |
| 23:55 | T+110 | none | **stop**: log the stop commit SHA. Nothing scored changes after it |
| by 00:00 | T+115 | none | **FREEZE.txt** posted on the drill PR |
| 00:05 | T+120 | answer key and scoring tool | scoring to 00:25 |
| 00:35 | T+150 | none | retro filed on the drill issue |

Heavy slots held by the other drills tonight (busy for this drill): 21:40–22:05, 22:45–23:10, 23:10–23:20, 23:50–00:10, 00:15–00:40 and 00:55–01:20. G2 has 20 minutes: run only the coded measures (`--measures`), and start the G4 build as soon as the G5 rerun SHA exists.

## Engine and data pair

The pair locked on the run branch: policyengine-uk 2.177.7, policyengine-core 3.34.10 (no policyengine.py), Microcosm build `uk-frs-calibration-attempt-20261112T133744Z-6f918b81`, SHA-256 `e268e3af7932784ad4471f008097a5acc6c3c5bc15c4c54fbb5a489b2a0ac9ae`, made on policyengine-uk 2.177.7 (`src/pip_review/data_build.py`). Every figure carries the label "build uk-frs-calibration-attempt-20261112T133744Z-6f918b81, policyengine-uk 2.177.7, not in a policyengine.py release; PIP-specific validation pending (#1, #4)".

policyengine.py 6.19.0 pins a different, certified pair (policyengine-uk 2.174.1 with build eeb6093e). Running eeb6093e under 2.177.7, or 6f918b81 under 2.174.1, is a mixed pair: its figures are invalid and are not scored. Figures from any pair not recorded at G0 are not scored.

## Gates

### G0: pair record, by hand (by 21:35)

This repository has no pair-check tool, so the check is done by hand and posted as a PR comment in the clock table:

```sh
git rev-parse HEAD; git status --porcelain                      # start SHA, clean tree
uv run --extra model python -c "import importlib.metadata as m; print('policyengine-uk', m.version('policyengine-uk'), 'core', m.version('policyengine-core'))"
uv run python -c "from pip_review.data_build import DATA_BUILD as b; print(b.id, b.sha256, b.engine, b.core)"
shasum -a 256 <the national file the run loads>                # must equal DATA_BUILD.sha256
```

Then read the build's recorded engine from its release manifests: the JSON files in the build's release folder, `releases/microcosm-uk-2024-25-national/<build id>/` in the dataset repository named by `data_build.HF_REPO` (JSON only; light; needs `HUGGING_FACE_TOKEN`). Record each policyengine-uk version they state: in `build_manifest.json`, `runtime["policyengine-uk"]`; in `release_manifest.json`, `built_with_model_package.version` and any `compatible_model_packages` specifier pinned with `==`. If the folder holds neither file, record the version from the data owner's release note and say so.

The G0 record has five items: installed engine version (policyengine-uk and core), build id, build SHA-256 (from `shasum`, not copied from the code), the build's recorded engine from its manifests, and the result: "pair holds" only if the installed engine, `DATA_BUILD.engine` and every manifest version are 2.177.7 and the SHA-256 matches.

### G1: coverage ledger (22:05–22:15)

One line per statement item in `drills/2026-11-15/ledger.csv`, each with a route, a cause class and the in-baseline flag. Items already in the baseline are flagged here and not coded. Coded measures go in `reforms.py` with ids that start `mock10_`, `placeholder=True`, and their values.

### G2: provisional numbers (by 22:35, inside heavy slot 1)

```sh
uv run pip-review generate --mode model --status mock --measures <mock10_ ids>   # takes the heavy-run lock itself
uv run pip-review household <preset> --reform <mock10_ id>                       # light
```

One hand-checked household per coded measure, saved as `drills/2026-11-15/g2_hand_checks.csv` with the commit SHA.

### G3: re-base and reconcile (22:45–23:15)

Re-base each official costing to our basis, put it in `data_inputs/official/costings_mock10.csv` (`measure_id,fiscal_year,value_m,basis,source`) and run:

```sh
uv run pip-review reconcile --out drills/2026-11-15/reconciliation.csv --reasons drills/2026-11-15/gap_reasons.csv
```

Every gap over 10% has a written reason and a **gap class**. The reconcile tool's `cause_class` column holds the gap class; the ledger keeps the separate **cause class**. Write the scored national file (`national.csv`, below) from this reconciliation. Update the ledger after G3, before the stop.

### G5: correction (23:20–23:40, inside heavy slot 2)

Re-run every affected measure, regenerate, re-reconcile, and record a new scoring SHA. Re-run **every G2 hand-check row the correction touches**, and save the re-runs as their own file, `drills/2026-11-15/g5_hand_checks.csv`, with the new SHA. Do not overwrite `g2_hand_checks.csv`.

### G4: publication path (by 23:45, inside heavy slot 2)

After the G5 rerun. The production build does not take the heavy-run lock itself: run it in a shell that has taken the lock and waited for memory with the lock lines in `docs/RUNBOOK.md` ("Commands"), and release the lock when done.

```sh
uv run python scripts/check_public_data.py data/results.json dashboard/public/data/results.json drills/2026-11-15/ledger.csv drills/2026-11-15/reconciliation.csv
cd dashboard && bun run data && bun run build && bun run smoke    # serves on port 3107, checks the robots meta and the MOCK banner, then stops the server

# the header: smoke has stopped its server, so serve again, check, stop
bun x next start -p 3107 >/tmp/pip-review-header.log 2>&1 & SERVER=$!
sleep 5; curl -sI http://localhost:3107/ | grep -i x-robots-tag    # must show noindex
kill $SERVER
```

`bun run smoke` checks the robots meta only, and the template sets no `X-Robots-Tag` header; a build without it fails this check. Nothing is deployed.

### Stop (23:55)

Log the stop commit SHA in the clock table. The scored files are their state at that commit.

## Freeze at stop

- The scored files are frozen at the stop commit. Within 5 minutes of the stop, and in any case before T+120 (00:05), the integrator posts `drills/2026-11-15/FREEZE.txt` on the drill PR: one line per scored file, `<sha256>  <path>`, from `shasum -a 256` run on the files at the stop commit.
- Scored files: the filled household scoring sheet, `ledger.csv`, `national.csv`, `g2_hand_checks.csv`, `g5_hand_checks.csv` and `data/results.json`.
- The scorer checks every FREEZE.txt hash against the blob at the stop commit (`git show <stop>:<path> | shasum -a 256`). A file whose hash matches a later commit, but not the stop commit, was changed after the stop: the stop-commit version is scored and the freeze points are lost.
- **Anything that arrives after the stop** (a message, a defect found, a better idea) is logged as a defect with its time, or saved as a new file, and is not applied to any frozen file. It is not scored. It goes in the retro.

## Scored file formats

The column names are fixed now; the allowed values for each column are given with the documents at T+40.

- Household sheet: a filled copy of the released blank sheet, same columns, the commit SHA of its scoring run on every row.
- `ledger.csv`: `line,route,cause,in_baseline_at_g1,coded,upstream_link,reason`.
- `national.csv`: `line,basis,gap_class,costing_recorded,reason`.

## Roles

| Role | Owns | Does not |
|---|---|---|
| Integrator | the run branch, the clock table, every commit, generation, re-basing, the G0 record, FREEZE.txt | read the packet before release; score households |
| Reconciler | the coverage ledger, the reconciliation and `national.csv`, defects as PR comments within 5 minutes, the hash check of each file on release | push code |
| Scorer (the reconciler after T+40) | the household sheet, one commit SHA per scoring run, the G5 hand-check file; the hash check of the key at 00:05 | edit reform code |
| Drill owner (not the integrator) | the sealed packet, releases at the set times, the answer key and scoring tool | take part in coding |

Who holds each role is recorded on the drill issue. Only the integrator pushes, and never to `main`.

## Routes

Every ledger line gets one route. The route says where the work lands:

| Route | Where the work lands | Meaning |
|---|---|---|
| `dashboard-param` | this repo | a parameter change in `reforms.py` |
| `dashboard-structural` | this repo | a hand-written modifier or mask, one module per modifier in `measures/` |
| `ledger` | this repo (ledger only) | not modelled (spending, administration, items already in the baseline); the official figure is recorded with its source |
| `not-computable` | data | the input the measure acts on is not in the data; published with the reason, never as £0 |
| `needs-pe-uk-first` | policyengine-uk | the engine needs a new formula or parameter; a draft upstream fix is filed the same day and the line links it |

A measure that acts through an input the engine stores rather than derives (#6) is routed `needs-pe-uk-first` with the upstream draft filed the same day, or shown through an in-repo modifier only as labelled illustrative, and only once a household test shows the modifier moves awards.

## Cause class and gap class

The ledger carries a **cause class** for each line: what the measure needs before PolicyEngine can show it. The national reconciliation carries a **gap class**: why our figure differs from the official one by more than 10%. They are separate columns; where they hold the same word, write the reason.

Cause classes:

- `parameter`: an existing parameter carries it.
- `formula`: engine or modifier logic must change.
- `coverage`: the input the measure acts on is not in the data or the model (every not-computable line).
- `baseline_mismatch`: the baseline already holds the measure, or holds a different value from the official baseline (every line already in the baseline).
- `timing_fiscal_calendar`: the start date, a part year or the fiscal year placement is the substance.
- `interaction`: the measure works through another benefit or measure.
- `data_calibration`: the data hold the input but its level is off.
- `basis`: a presentation choice only.

Gap classes:

- `basis`: static vs behavioural, accrued vs cash, geography, price base, gross vs net.
- `data_calibration`: the data's count or level of the affected group differs from the official one for the same year.
- `baseline_mismatch`: the official baseline holds different policy or forecast assumptions.
- `timing_fiscal_calendar`: start dates, part years, fiscal year placement.
- `coverage`: the model or data cannot reach part of the measure.
- `interaction`: the gap comes through another benefit or measure.

Declare the basis once, at G1, and repeat it next to every figure: static, cash, fiscal year, England and Wales, £ million, positive is a cost to the Exchequer. Official tables may use other conventions; re-base them at G3 and write down every conversion.

## Rubric (100)

| Area | Points | How it is scored |
|---|---|---|
| Example households | 20 | each scored cell within ±1p of the key, on the values in force after the correction |
| National figures | 30 | per statement line, basis (half) and gap class (half); for not-computable and ledger lines the basis column carries the costing's basis, and the gap point is for recording the costing and the reason no figure is shown |
| Ledger | 25 | per line, route and cause class at the frozen stop state; lines already in the baseline score only if flagged at G1 and left uncoded |
| Publication path | 10 | MOCK banner on every view, noindex meta and X-Robots-Tag on `next start`, not-computable lines shown with reasons and never as £0, the disclosure floor, every coded measure on the page |
| Process | 15 | G0 pair record by 21:35; gates on time; one commit SHA per scoring run; the correction logged and every touched hand row re-run into its own file; FREEZE.txt with the SHA-256 of every scored file posted before T+120, and nothing scored that changed after the stop |

The answer key states per-row weights and the rounding and part-year rules; the documents state the same rules at T+40. The households, national and ledger parts are scored by a tool released with the key, which refuses any file whose SHA-256 does not match FREEZE.txt.

## What to time and log

The integrator keeps a clock table in the drill PR, one row per step:

| Step | Start | End | Machine time | People time | Commit SHA | Note |
|---|---|---|---|---|---|---|

- Split machine time (generation, builds, tests) from people time (reading, coding, review).
- Log the time each release arrived and the result of its hash check, from one clock (the time the hash was checked).
- Log every defect as a PR comment within 5 minutes, with the time found and the time read.
- Log every rerun with its SHA; one SHA per scoring run.
- Log the correction: time received, what changed, which rows were re-run and into which file.
- Log every heavy run: lock taken and released, start, end, peak memory; any lock wait.
- Log every upstream draft filed (repository, link, time).
- Log the stop commit, the time FREEZE.txt was posted and its own SHA-256.

## MOCK and noindex rules

- Generate with `--status mock`. Every page built from the run branch shows a banner that contains **MOCK**; the template's placeholder banner is not enough.
- The served HTML carries a robots meta with `noindex` and `nofollow`, and responses carry `X-Robots-Tag: noindex`. Check both on the local production build, not only in the source.
- No deploy to any URL. The drill page is a local build only; stop the server after the check.
- The drill PR is a draft labelled `not for merge`, and is never merged or stacked on another unmerged PR.
- Public files on the run branch pass `scripts/check_public_data.py`: no ids or weights, the 10-household disclosure floor, no area codes.

## Packet hygiene

- The packet is written and held outside this repository. Only the hashes are committed, below.
- Files are released at the set times, not before. The reconciler checks each file's SHA-256 when it arrives (`shasum -a 256 <file>`) against the table below and logs the result; the scorer does the same for the key at 00:05.
- The integrator does not open any packet file before its release time.
- Nothing from the packet goes into a public file, issue, PR or comment until scoring ends.
- Figures in the packet are mock. Never call them DWP, OBR or other official figures in a note, reason or write-up.

## Packet hashes (SHA-256)

| File | Release | SHA-256 |
|---|---|---|
| `00-owner-notes.md` | drill owner only | `3ab716281781817c84b482716f8a27aef17d852845338c11b2704b3f18e8d61f` |
| `01-statement.md` | 22:05 | `b9531ff3feedb42688dbba326eb63cb7ccd53121d267b6a9292135b44602c444` |
| `02-documents.md` | 22:45 | `2a7c1a63cd5caec9ccea18708886ec90c2df622ba7fc972c569ae178ceb229aa` |
| `02-costings.csv` | 22:45 | `3271fc2d7f0b8bfc9aaba25234ebee0645b4cd509463a112c9c80eeb9d0985cf` |
| `02-households.csv` | 22:45 | `5b9061c271ec5ffc12dd33cf794e90bf8124f606c162ed363edda2ce3a8d5068` |
| `02-scoring-sheet.csv` | 22:45 | `5dad6abb0eae587cb5278042eb7730b363a6f238c5301220285e898556075487` |
| `03-inject.md` | 23:20 | `232963bbe9cea9384b2a843b6fce253bea1665ff085f84bb13a4300d8cf06a84` |
| `03b-notice.md` | drill owner only | `c39aa70c745747a4391e250f4ee73527885a487d47fb73b7b7525c7b0653609a` |
| `04-answer-key.md` | 00:05 | `45807491432ef5900d9683dc3300661d2ca599fa368faccf9a4cee551644007b` |
| `04-answer-key-households.csv` | 00:05 | `a0d87724f84363061acdce16c501bf0436a5c61ed4ae6c10e1b0a18b5141c6c6` |
| `04-answer-key-ledger.csv` | 00:05 | `f2bd6e16c3c12391e86bb319e7b18eaef6f05ad05234556ffeb4a304cb667e25` |
| `generate_household_key.py` | 00:05 | `011beb51067773afb53956d848edcfb9181644365eb58c0f1901c35cba85fdeb` |
| `04-score.py` | 00:05 | `d201561da7441371023efd1a2387ae33c7b18ecba2e536e80aab3470993ae870` |

## Retro

By 00:35, on the drill issue: score by rubric row, what was lost and why, defects by cause class, machine and people time per step, lock waits, and fixes to file before the real report.
