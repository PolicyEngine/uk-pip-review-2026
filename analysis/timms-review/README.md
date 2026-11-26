# Timms Review of PIP: PIP daily living as the route to the UC health element

This folder holds the code and results behind PolicyEngine's post on the [Timms Review of PIP](https://www.gov.uk/government/publications/the-timms-review-final-report) (final report published 24 November 2026). The post models the government's plan, set out in the [Pathways to Work Green Paper](https://www.gov.uk/government/consultations/pathways-to-work-reforming-benefits-and-support-to-get-britain-working-green-paper), to make the PIP daily living component the single route to the Universal Credit (UC) health element. It does so for 2029-30 in three versions.

| Version | Rule |
|---|---|
| Every award (`full`) | A UC award includes the health element only if a claimant receives PIP daily living. Awards that keep it keep their current rate. |
| New claims only (`new_claims`) | Awards at the rate for claims from April 2026 need a claimant on PIP daily living; awards at the earlier, protected rate keep the element. |
| Existing awards protected (`protected`) | Every existing award keeps the element. |

In all three, awards with a claimant on PIP daily living but no element gain it at the new-claim rate (£217.26 a month in 2029-30). Each claimant's assessment of limited capability for work is unchanged, so the work allowance still applies. An award without the element loses the benefit cap exemption that rests on it.

Under [reg. 29(4) of the Universal Credit Regulations 2013](https://www.legislation.gov.uk/uksi/2013/376/regulation/29), a claimant in respect of whom the health element is included has only that element, not the carer element. PolicyEngine UK applies this to awards that keep or lose the element, so a claimant who loses it and cares for a severely disabled person receives the carer element instead. The script applies it to awards that gain the element too: the element is included in respect of a claimant on PIP daily living who isn't a carer if there is one, and otherwise the elder, and that claimant's carer element is removed. The carer element (£228.51 a month in 2029-30) is above the new-claim rate of the health element, so an award where that claimant cares ends up about £135 a year worse off.

## Results (2029-30)

| | Every award | New claims only | Existing awards protected |
|---|---:|---:|---:|
| Change in UC spending | −£3.2bn | +£0.1bn | +£0.5bn |
| Claimants losing the health element | 703,000 | 134,000 | none |
| Claimants gaining the health element whose UC rises | 188,000 | 188,000 | 188,000 |
| Awards gaining the health element whose UC falls, as the carer element goes | 39,000 | 39,000 | 39,000 |
| Change in absolute poverty before housing costs | +148,000 | −52,000 | −75,000 |

The full outputs are in [`results/timms_gateway.json`](results/timms_gateway.json): spending, the benefit cap, who loses and gains by age, PIP receipt, family type and nation, average changes, poverty before and after housing costs (including children), deciles, and a profile of PIP under current law. The overlap between the health element and PIP (daily living and any component) under current law, for the UK, Great Britain and England and Wales, is in [`results/timms_overlap.json`](results/timms_overlap.json). Each figure carries the number of survey households it rests on (`n` or `survey_households`). Any figure resting on fewer than three is null.

## Model and data

- `policyengine[uk]==6.20.3`, which pins policyengine-uk 2.179.2 and its certified dataset.
- Static: no change in behaviour, claims or take-up.
- UK-wide. In Scotland, the data record Adult Disability Payment as PIP.
- New-claim status (`uc_receives_new_claimant_health_element`) comes from the dataset's ordering of claims by the survey's UC start date, set against the expected share of awards on the new-claim rate (22% in 2029-30). The data have no claim dates.
- The data can't identify people who meet the severe conditions criteria.

## How to run

The scripts use the simulation builder and survey-household mapping from [PolicyEngine/uk-milburn-review-dashboard](https://github.com/PolicyEngine/uk-milburn-review-dashboard). Set that up first (see its README), then:

```bash
MILBURN_DASHBOARD=/path/to/uk-milburn-review-dashboard /path/to/uk-milburn-review-dashboard/.venv/bin/python timms_overlap.py
```

```bash
MILBURN_DASHBOARD=/path/to/uk-milburn-review-dashboard /path/to/uk-milburn-review-dashboard/.venv/bin/python timms_gateway.py
```

Each writes `results/*_raw.json`, which is ignored by git. The committed files are those outputs with the disclosure floor applied to every cell. A run takes about 10 minutes and needs around 20 GB of memory.
