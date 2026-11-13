# Model risk register

| Risk | Effect on the day | Mitigation | Issue |
|---|---|---|---|
| Scotland and Northern Ireland inside PIP | Costs about 11% too high, wrong households in results | Tables keep England and Wales households only (`aggregate`); country test upstream | #1 |
| Carer's Allowance ignores PIP | Carers affected reported as zero | Ledger line with official figure; reform-time link | #2 |
| Points held only for PIP recipients (6f918b81); the other component drawn below 8 | Threshold cuts not computable; threshold raises rest on the drawn points | Cuts not computable; raises costed with the assumption stated; impute points for people turned down from DWP tables | #3 |
| Caseload flat after 2024-25 against DWP's growing forecast | Baseline and proportional costs too low in later years | DWP path plus modelled change on the spending chart; ledger ratio per year; year-specific targets | #4 |
| No condition or hospital data | Fast track and hospital rule not computable | Impute condition group, or fiscal lines | #5 |
| UC health element proxy | Interaction missing for other PIP measures | Gateway measure wraps the flag; reform parameter upstream; settle the proxy ruling | #6 |
| Stored disability flags, phasing bypasses knock-ons | Distribution and poverty understated | Recompute flags; phase at category level | #7 |
| Few survey records per constituency | Map not publishable | Disclosure gate; DWP admin counts | #8 |
| Static basis against DWP behavioural costings | Gaps that read as errors | Declare basis once; cause class `basis` | |
