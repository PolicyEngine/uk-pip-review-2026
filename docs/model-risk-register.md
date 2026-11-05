# Model risk register

| Risk | Effect on the day | Mitigation | Issue |
|---|---|---|---|
| Scotland and Northern Ireland inside PIP | Costs about 11% too high, wrong households in results | England and Wales mask; country test upstream | #1 |
| Carer's Allowance ignores PIP | Carers affected reported as zero | Ledger line with official figure; reform-time link | #2 |
| No points in the data | Points and descriptor measures not computable | Impute points per category from DWP tables | #3 |
| Caseload 9-10% high, flat after 2024-25 | Baseline level and growth wrong; costs scale with it | Recalibrate; year-specific targets | #4 |
| No condition or hospital data | Fast track and hospital rule not computable | Impute condition group, or fiscal lines | #5 |
| UC health element proxy | Gateway reform not computable; interaction missing | Reform parameter upstream; settle the proxy ruling | #6 |
| Stored disability flags, phasing bypasses knock-ons | Distribution and poverty understated | Recompute flags; phase at category level | #7 |
| Few survey records per constituency | Map not publishable | Disclosure gate; DWP admin counts | #8 |
| Static basis against DWP behavioural costings | Gaps that read as errors | Declare basis once; cause class `basis` | |
