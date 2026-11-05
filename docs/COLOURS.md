# Colours

Roles copied from the AB2026 dashboard. Literals live only in `dashboard/src/utils/chartTheme.js` and the `:root` tokens of `dashboard/app/globals.css`; `src/colourGuard.test.js` fails on any other hex value.

| Role | JS name | Hex |
|---|---|---|
| Households gain (a cost to the Exchequer) | `CHART_COLOURS.gain` | `#319795` |
| Small gain | `.gainLight` | `#81E6D9` |
| Households lose (a saving) | `.loss` | `#D97706` |
| Small loss | `.lossLight` | `#FBBF24` |
| No change, baseline | `.noChange`, `.before` | `#9CA3AF` |
| Official figure (dashed) | `.official` | `#6B7280` |
| Net total, highlight | `.highlight` | `#285E61` |
| Measures, in catalogue order | `MEASURE_RAMP` | `#285E61`, `#319795`, `#4FD1C5`, `#81E6D9` |

Selected chips change fill and border only.
