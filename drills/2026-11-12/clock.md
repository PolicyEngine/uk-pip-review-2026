# Drill 6 clock (12 November 2026)

Times, SHAs, hashes and pass/fail only. No packet content. Local run branch `drill6-run`, never pushed.
Mock edits stay uncommitted in the working tree; each SHA below is bound to the working-tree diff by the SHA-256s in the note column.

| Step | Start | End | Machine time | People time | Commit SHA | Note |
|---|---|---|---|---|---|---|
| G0 setup: uv sync, bun install, versions, dataset hash | 13:47 | 13:48 | 2 s | 1 min | 761c6219891f (start) | policyengine 6.17.2, pe-uk 2.174.1, pe-core 3.33.3; dataset SHA-256 0a9b77db...1f25 matches; G0 posted to #12 at 13:47 (planned 13:30) |
| Baseline caseload run (E&W modelled / DWP ratio, 2026-27 to 2030-31) | 13:48:28 | 13:50:38 | 129 s | 2 min | 761c6219891f | under /tmp/pe-heavy.lock; lock released 13:50:38 |
| tests/test_model_import.py (current-law rates vs installed engine) | 13:50:44 | 13:50:45 | 1 s | - | 761c6219891f | pass |
| statement.md received / hash checked | 14:00:13 | 14:00:13 | - | - | 761c6219891f | SHA-256 14a5aecc...427c: match |
| G1 coverage ledger (due 14:10) | 14:00 | 14:01 | - | 1 min | 761c6219891f | every line routed + cause class; guard pass; ledger held locally |
| Coding: registry replaced, one structural module | 14:01 | 14:07 | - | 6 min | - | household checks of each coded measure during coding |
| G2 generate (model, status mock) | 14:07:36 | 14:19:09 | 588 s (baseline 52, 4 measures ~106 each, package 110, households) | 4 min hand checks | e345b3a993ac | provenance clean_tree false by design (mock edits uncommitted); worktree patch SHA-256 19710942...be73, module 2e03e99d...36b8, reforms.py 68ff1291...02e4; results.json SHA-256 e3f7285c...21fb; lock released 14:19:09 |
| G2 hand checks: one household per coded measure + national arithmetic | 14:19 | 14:21 | - | 2 min | e345b3a993ac | 4/4 measures match to 1p (households) and to rounding (national); guard on results.json pass |
| Trial G4 build + smoke (G2 data) and screenshot test | 14:19:4x | 14:20:12 | ~15 s | - | e345b3a993ac | smoke pass (noindex, status mock); servers killed; ports 3107/3108 free; lock released 14:19:55 |
| documents.zip received / hash checked | 14:40:05 | 14:40:08 | - | - | e345b3a993ac | SHA-256 d2a6a6f0...6bd686: match |
| G3 re-base + reconcile (to 15:10) | 14:40 | 14:41 | <1 s | 1 min | e345b3a993ac | reconcile 0 problems; every gap over 10% has a reason + cause class |
| Scoring run 1 (pre-inject, specimen households) | 14:42:10 | 14:42:28 | 18 s | 2 min | 77881895d350 | 12 rows; worktree patch SHA-256 5d1d7bdd...fac3; module 2e03e99d...36b8 |
| R11 loser-count check (G3 reason) | 14:43:49 | 14:44:31 | 42 s | 3 min | 77881895d350 | under lock, released 14:44:31; reconciliation re-run, 0 problems |
| inject.md + inject_rows.csv received / hashes checked | 15:15:05 | 15:15:11 | - | - | 77881895d350 | inject.md 4e1e249f...72cb match; inject_rows.csv 8550cdb2...9fe match. Inject changes two coded measures' rate paths; all 12 specimen rows to be re-run |
| G5 rerun (model, status mock) after inject fix | 15:17 | | | | (this commit) | |
