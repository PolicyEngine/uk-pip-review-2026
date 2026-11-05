# Method

## Basis (declared once)

- Static microsimulation: no behavioural response, no change in claim rates.
- Cash, fiscal year (year Y is Y-(Y+1)), £ million, nominal.
- England and Wales only. PIP applies there; Scotland has Adult Disability Payment. Until the model has a country test (#1), every reform is masked to England and Wales.
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

## What the data hold

PIP awards by component (none, standard or enhanced), not assessment points (#3). No health condition or hospital stays (#5). Carer's Allowance does not follow the cared-for person's award (#2). The UC health element follows a stored disability flag, not PIP (#6, #7). Caseload is 9-10% above DWP for England and Wales (#4).

## Not modelled

Non-cash support and services, the assessment process itself (forms, advocacy, digital services), award review timing and flows, Blue Badge and Motability.
