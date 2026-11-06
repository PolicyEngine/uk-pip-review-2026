"""Hand-written simulation modifiers, one module per modifier.

Rules, copied from the AB2026 dashboard's ``budget_measures``:
- one modifier per module, with literal defaults and no runtime state, so a
  receipt can bind the module's exact source;
- a modifier built only from ``pip_review.measure_templates`` needs no
  two-person attestation; any other modifier does while ``sign_off.REQUIRED``
  is on;
- day-of measures are written here, in this repository, not upstream: an
  upstream merge, release and adoption takes days.

No modifier is needed yet: the template's computable measures are parameter
changes. The first likely modifiers are an England and Wales mask (issue #1)
and a category-level phasing scenario (issue #7).
"""
