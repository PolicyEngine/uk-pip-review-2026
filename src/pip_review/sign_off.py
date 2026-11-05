"""Whether publishing needs people's sign-off: one switch, on.

On (``REQUIRED = True``) until the event's figures are reconciled: every file
under ``dashboard/public/data/`` needs the reconciler's sign-off row in
``data_inputs/public_data_review.csv``, and a hand-written modifier is held
for a two-person check of its exact code. Every automated check
(``scripts/check_public_data.py``) blocks whatever the switch says.

Copied in shape from the AB2026 dashboard, where the switch was turned off on
the day once the review rows were in place.
"""

REQUIRED = True
