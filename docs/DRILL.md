# Drills

Each drill has one plan, in `drills/<date>/DRILL.md` on its drill PR: clock, roles, ledger lines, rubric, commands and packet hashes. Nothing about a drill is repeated here, so the plan has one home.

Generic rules for any drill branch:

- Generate with `--status mock`; the banner must contain MOCK, and every drill measure id starts with a `mock<n>_` prefix so none can survive into the real registry.
- The page is noindex; check the banner and noindex on a local production build (`bun run build && bun run smoke`).
- Expect trap rows: items already in the baseline.
