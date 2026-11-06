# PIP review dashboard

PolicyEngine UK dashboard for the independent review of Personal Independence Payment (PIP). The review's final report is expected in November 2026; no publication date has been announced. This repository holds the analysis pipeline and the dashboard we will use to estimate what its proposals would cost and who they would affect.

**Status: pre-release template.** Nothing here is a PolicyEngine estimate yet. The template runs on placeholder figures until the report is published and its recommendations are coded and checked.

## What the dashboard will show

- **Cost.** Static cost of each modelled recommendation and of the package, £m a year for 2027-28 to 2030-31, England and Wales, set against the DWP and OBR spending path for PIP.
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
| Dataset | Microcosm UK 2024-25 national build `20261025T091414Z-a6299504`, SHA-256 `b96a8cd625b645a409c063b1de5158532708a2f0d3c3897a794a8fb0bbd5064e` |

This is the bundle's certified pair; PIP-specific validation is pending (#1, #4). policyengine 6.11.1 to 6.15.0 all pin the same UK pair, so the 6.11.1 pin stays until the drill on 12 November (its answer key was built on it); the version is frozen again at G0. Microdata are licensed and are not stored in this repository; only aggregate outputs that pass a disclosure check are published.

## Licence

AGPL-3.0, as for other PolicyEngine repositories. See [LICENSE](LICENSE).

## How to run (template)

```sh
uv sync --extra dev                 # analysis package and tests, no engine
uv run pytest -q                    # registry, templates, data limits, publication, households
uv run pip-review generate          # writes data/results.json and the dashboard copy (placeholder mode)
uv run python scripts/check_public_data.py

cd dashboard && bun install && bun run dev   # local page on http://localhost:3000
```

`uv sync --extra model` adds `policyengine[uk]==6.11.1` for model runs (`uv run pip-review generate --mode model`, which takes the heavy-run lock) and preset households (`uv run pip-review household <preset>`). `docs/RUNBOOK.md` has every command for the day.

## Layout

| Path | What it holds |
|---|---|
| `src/pip_review/reforms.py` | Measure registry: every candidate recommendation with its route; all placeholders |
| `src/pip_review/measures/` | Hand-written modifiers, one per module (UC health gateway, move to PIP at 18) |
| `src/pip_review/measure_templates.py` | Parameter builders (`rate_change`, `threshold_change`) |
| `src/pip_review/model_run.py`, `aggregate.py`, `heavy.py` | Model mode: one simulation per process, England and Wales tables, the heavy-run lock |
| `src/pip_review/reconcile.py` | G3 reconciliation against official costings |
| `src/pip_review/data_limits.py`, `model_limits.py` | What the data and the model cannot cost, with the reason |
| `src/pip_review/publication.py`, `sign_off.py` | Page status, manifest, receipts, disclosure floor, validation; sign-off rows enforced once a page is provisional or final |
| `src/pip_review/pipeline.py`, `cli.py`, `household.py` | Generation and the household calculator |
| `data_inputs/` | Official figures, expected effects, drill packet hashes |
| `docs/` | Method, schema, data contract, colours, runbook, drill, candidate reforms, risk register |
| `dashboard/` | Next 16, React 19, `@policyengine/ui-kit`, Recharts, bun |
