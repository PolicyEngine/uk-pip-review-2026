# results.json schema (version 2)

One file, written by `pip-review generate` to `data/results.json` and copied to `dashboard/public/data/results.json`.

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | 2 |
| `status` | `placeholder`, `mock`, `provisional` or `final` | Defined once in `publication.STATUSES` |
| `banner` | string | Required for every status except `final`; a `mock` banner contains `MOCK`; empty on `final` |
| `engine` | object | `policyengine`, `policyengine_uk`, `policyengine_core` (from `uv.lock`, or the install in model mode), `dataset`, `dataset_sha256`, `certified_pair`, `pip_validation` |
| `provenance` | object | Model mode only: `commit`, `clean_tree`, `bundle`, `machine_seconds` |
| `basis` | object | `cost`, `distribution`, `behaviour` text; shown once, on Methodology |
| `base_year`, `years`, `distribution_year` | int, int[], int | Fiscal start years |
| `measures[]` | object | Registry summary (`in_report`, `route`, `withdrawn_reason`, ...) plus `status`, `receipt` and the tables below |
| `package` | object or null | Model mode with two or more measures: `measure_ids` plus the same tables for all of them together |
| `spending_path[]` | object | `year`, `fiscal_year`, `dwp_m`, `dwp_caseload_k`, `reformed_m` |
| `households[]` | object | `id`, `label`, `baseline` and `reform[measure id]`, each `{pip, net_income}`; `net_income` is null in placeholder mode |
| `data_limits[]`, `model_limits[]` | object | `key`, public `reason`, `issue` |

Tables per measure (null when the measure has no figures; the model-only ones are null in placeholder mode):

| Table | Rows |
|---|---|
| `budgetary_impact` | `year`, `fiscal_year`, `value_m` |
| `decile` | `decile`, `avg_change_gbp`, `pct_change`, `suppressed` |
| `winners_losers` | `decile`, five shares, `suppressed`; `winners_losers_all` is the same for everyone (model only) |
| `people_affected` | `gain_k`, `lose_k`, `suppressed` |
| `by_region`, `by_age` | `region` or `age_band`, average change, `suppressed` (model only) |
| `poverty` | `bhc`, `ahc`: `baseline_pct`, `change_pp` (model only) |
| `knock_ons` | `carers_allowance_m` (model only) |

Rules (checked by `publication.validate_public`, `scripts/check_public_data.py` and `dashboard/scripts/validate-results.mjs`):

- A measure that is not computable, or is withdrawn, has `null` figures, never zeros, and a reason.
- Placeholder measures appear only under `placeholder` or `mock`; outside them a modelled measure must carry figures.
- Every survey row says whether it is `suppressed`; cells below 10 survey households are blanked before writing.
- The preset households cover exactly the measures with figures.
- No record identifiers, weights or record counts.
- On `provisional` and `final`, every public data file has a sign-off row with its current SHA-256.
