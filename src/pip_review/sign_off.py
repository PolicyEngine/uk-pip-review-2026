"""Whether publishing needs people's sign-off: one switch, on.

On (``REQUIRED = True``) until the event's figures are reconciled: a measure
is held at ``held-sign-off`` and a hand-written modifier is held for a
two-person check of its exact code.

Sign-off rows are enforced, not only documented: once ``results.json`` has
status ``provisional`` or ``final``, every file under
``dashboard/public/data/`` needs a row in ``data_inputs/public_data_review.csv``
(``path,sha256,reviewer,reviewed_on``) matching its current SHA-256.
``scripts/check_public_data.py`` (CI) and
``dashboard/scripts/validate-results.mjs`` (every build) both refuse the file
without it. Placeholder and mock pages need no rows. Every other automated
check blocks whatever the switch says.

Copied in shape from the AB2026 dashboard, where the switch was turned off on
the day once the review rows were in place.
"""

REQUIRED = True
