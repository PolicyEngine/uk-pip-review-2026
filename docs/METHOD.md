# Method

## Basis (declared once)

- Static microsimulation: no behavioural response, no change in claim rates.
- Cash, fiscal year (year Y is Y-(Y+1)), £ million, nominal.
- England and Wales only. PIP applies there; Scotland has Adult Disability Payment. The model has no country test (#1), so every table keeps England and Wales households only; in a static run this gives the same figures a country test would.
- Positive is a cost to the Exchequer.
- Distribution: change in household net income by equivalised household income decile.

DWP costings include behavioural effects and phasing at award review. Our static figures will differ from them for that reason alone; the reconciliation records it as cause class `basis`.

## Routes

Each recommendation gets one route before anything is coded:

| Route | Meaning |
|---|---|
| `dashboard-param` | Modelled by a parameter change |
| `dashboard-structural` | Modelled by a modifier in `src/pip_review/measures/` |
| `ledger` | Not modelled; any official figure recorded as a fiscal line |
| `not-computable` | A data limit; shown with the reason, never as £0 |
| `needs-pe-uk-first` | Needs a model change upstream before it can be costed |

Rate measures are written as changes to each year's current-law rate (`reforms.CURRENT_LAW_RATES`), so CPI uprating never turns an illustrative rise into a cut.

## What the data hold

PIP awards by component (none, standard or enhanced), not assessment points (#3). No health condition or hospital stays (#5). Carer's Allowance does not follow the cared-for person's award (#2). The UC health element follows a stored disability flag, not PIP (#6, #7); the gateway measure wraps that flag. The modelled caseload is close to DWP's in 2025-26 but flat afterwards, so it falls below DWP's growing forecast in later years (#4). The gap comes from the projection, not the base year: weights grow with ONS population and PIP status is fixed (policyengine-uk#2889 item 6). Any figure scaled by the ratio of DWP's caseload to the modelled caseload assumes the missing claimants look like the modelled ones, with the same award mix, ages and incomes.

These statements describe the certified build `eeb6093e`. On `6f918b81` four of them change: PIP points are stored, LCW and LCWRA come from the FRS UC admin record, carers carry `cares_for_severely_disabled_person`, and `is_severely_disabled_for_benefits` is no longer stored (#18).

## Not modelled

Non-cash support and services, the assessment process itself (forms, advocacy, digital services), award review timing and flows, Blue Badge and Motability.
