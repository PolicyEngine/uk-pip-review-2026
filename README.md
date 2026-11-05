# PIP review dashboard

PolicyEngine UK dashboard for the independent review of Personal Independence Payment (PIP). The review's final report is expected in November 2026; no publication date has been announced. This repository holds the analysis pipeline and the dashboard we will use to estimate what its proposals would cost and who they would affect.

**Status: pre-release template.** Nothing here is a PolicyEngine estimate yet. The template runs on placeholder figures until the report is published and its recommendations are coded and checked.

## What the dashboard will show

- **Cost.** Static cost of each modelled recommendation and of the package, £m a year for 2026-27 to 2030-31, England and Wales, set against the DWP and OBR spending path for PIP.
- **Who is affected.** Average change in household net income by income decile, the share of households that gain or lose, and changes by age group, family type and region (England and Wales).
- **People affected.** Number of people whose daily living or mobility award would change, and knock-on effects on Carer's Allowance and the Universal Credit health element where the model supports them.
- **Poverty.** Change in relative and absolute poverty, before and after housing costs.
- **Households.** Example households under current law and under each scenario.
- **Method and limits.** What we can and cannot model, measure by measure, with the reason.

The review reports to the Secretary of State and is expected to set out recommendations and principles rather than costed parameters. The dashboard will therefore show illustrative parameter scenarios mapped to each recommendation, labelled as such.

## Method in brief

- PolicyEngine UK static microsimulation on the Microcosm UK dataset. No behavioural response is modelled.
- England and Wales only for PIP. In Scotland, Adult Disability Payment has replaced PIP.
- Each recommendation is routed before anything is published: modelled by a parameter change, modelled by a structural change, recorded as a fiscal line from official figures, or not computable with the current data (with the reason). A measure we cannot compute is never shown as £0.
- The data hold PIP awards (none, standard or enhanced, for each component), not assessment points. Reforms to points or descriptors need imputed points before they can be modelled.

## Data and model

| Item | Version |
|---|---|
| policyengine | 6.11.1 (`policyengine[uk]`) |
| policyengine-uk | 2.151.0 |
| Dataset | Microcosm UK 2024-25 national build `20261025T091414Z-a6299504` |

Versions will be frozen and recorded before the event. Microdata are licensed and are not stored in this repository; only aggregate outputs that pass a disclosure check are published.

## Licence

AGPL-3.0, as for other PolicyEngine repositories. See [LICENSE](LICENSE).
