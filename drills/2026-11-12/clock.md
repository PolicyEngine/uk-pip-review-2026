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
| G2 generate (model, status mock) | 14:08 | | | | (this commit) | |
