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

On build 6f918b81 the data hold each person's daily living and mobility assessment points for 2024, from which the model derives the award in each year; there is no score per activity (#3). On build 6f918b81 the points are drawn only for people with a PIP award; everyone else holds -1 (not assessed). A recipient of one component has the other drawn below 8: daily living mostly over 4 to 7, mobility at 0 or 4 (the file's 359 mobility-only recipient rows hold daily living points of 4 to 7 in 295 cases and 0 to 3 in 64; 152 are at 6 or 7). So a cut to a standard threshold is not computable, alone or bundled with any other change: people turned down at those points are not in the data, and only existing recipients of the other component could move (a daily living threshold of 6 would move the mobility-only recipients drawn at 6 or 7, about 77k people from 88 distinct survey households; a mobility threshold of 5 to 7 moves no one, and 4 or lower moves only daily-living-only recipients drawn at 4). The model validator and the publication gate refuse any computable measure that holds such a cut (`data_limits.refusing_limits`). A threshold raise, and an enhanced threshold lowered but kept at 8 or more (12 to 10, say, which moves only standard-rate recipients of the same component, all in the data), are computable on the stated assumption that the drawn points place recipients correctly within their award; an enhanced threshold below 8 counts as a standard cut (`data_limits.LIMITS_BY_BUILD`; facts from María, data owner, 13 November 2026). No health condition or hospital stays (#5). Carer's Allowance does not follow the cared-for person's award in the model; the link measure makes it follow for carers in the same household, and carers of someone in another household are not reached (#2). The UC health element follows a stored disability flag, not PIP (#6, #7); the gateway measure wraps that flag. The modelled caseload is close to DWP's in 2025-26 but flat afterwards, so it falls below DWP's growing forecast in later years (#4).

## Not modelled

Non-cash support and services, the assessment process itself (forms, advocacy, digital services), award review timing and flows, Blue Badge and Motability.
