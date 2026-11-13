# Event-day checklist

One page; the detail is in [RUNBOOK.md](RUNBOOK.md).

- [ ] G0: start SHA, engine versions, dataset build id and SHA-256, label "build uk-frs-calibration-attempt-20261110T204756Z-9e18f010, policyengine-uk 2.177.7, not in a policyengine.py release; PIP-specific validation pending (#1, #4)"
- [ ] Freeze rule announced: calculation-path changes only through the integrator
- [ ] Autumn DWP tables swapped in, if published
- [ ] G1: ledger, every recommendation routed with a cause class; `in_report` set
- [ ] G2: `generate --mode model --status provisional`; one hand-checked household per measure
- [ ] G3: official costings in `data_inputs/official/costings_*.csv`; `reconcile` passes
- [ ] G4: sign-off rows; local build and `bun run smoke`; preview behind the login once Vercel exists
- [ ] Clock table row for every build, with SHA, results digest and deployment ID
- [ ] G5 ready: withdraw, fix, regenerate, re-reconcile, redeploy; rollback target recorded
