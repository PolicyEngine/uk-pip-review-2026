# results.json schema (version 1)

One file, written by `pip-review generate` to `data/results.json` and copied to `dashboard/public/data/results.json`. Every field is required; there are no defaults.

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | 1 |
| `status` | `"placeholder"` or `"final"` | `"placeholder"` while any measure is a placeholder |
| `banner` | string | Shown on every view while `status` is `"placeholder"` |
| `engine` | object | `policyengine`, `policyengine_uk`, `dataset`, `validated_pair` |
| `basis` | object | `cost`, `distribution`, `behaviour` text |
| `base_year`, `years` | int, int[] | Fiscal start years |
| `measures[]` | object | Registry summary plus `status`, `receipt`, `budgetary_impact`, `decile`, `winners_losers`, `people_affected_k` |
| `spending_path[]` | object | `year`, `fiscal_year`, `dwp_m`, `reformed_m` |
| `households[]` | object | `id`, `label`, `baseline_pip`, `reform_pip` by measure id |
| `data_limits[]`, `model_limits[]` | object | `key`, `reason`, `issue` |

Rules (checked by `publication.validate_public`, `scripts/check_public_data.py` and `dashboard/scripts/validate-results.mjs`):

- A measure that is not computable has `null` figures, never zeros, and a `route_reason`.
- No record identifiers, weights or record counts.
- Cells below 10 survey households are blanked (`suppressed: true`) before writing.
