"""Guard for public files: run in CI and before any publish.

The figures come from licensed survey microdata, so every public data file
must pass, whatever ``sign_off.REQUIRED`` says:
- no record identifiers or weights;
- no record counts (the disclosure floor is applied before writing);
- no run of area codes (constituency or local authority) unless the file is
  listed in ``REFERENCE_GEOGRAPHY``;
- the results file passes ``publication.validate_public``.

Usage: ``uv run python scripts/check_public_data.py [paths...]``. With no
paths it checks ``data/`` and ``dashboard/public/data/``.
"""

import json
import re
import sys
from pathlib import Path

from pip_review.publication import FORBIDDEN_KEYS, validate_public

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = [ROOT / "data", ROOT / "dashboard" / "public" / "data"]
AREA_CODE = re.compile(r"\b[EWSN](0[0-9]|1[0-4])[0-9]{6}\b")
MAX_AREA_CODES = 5
REFERENCE_GEOGRAPHY: set[str] = set()


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text()
    codes = set(AREA_CODE.findall(text))
    if (
        len(AREA_CODE.findall(text)) > MAX_AREA_CODES
        and path.name not in REFERENCE_GEOGRAPHY
    ):
        errors.append(f"{path}: carries area codes ({len(codes)} distinct prefixes)")
    if path.suffix == ".csv":
        header = text.splitlines()[0].lower().split(",") if text else []
        for column in header:
            if column.strip() in FORBIDDEN_KEYS or column.strip() == "n_households":
                errors.append(f"{path}: column {column.strip()!r} is not publishable")
    if path.suffix == ".json":
        data = json.loads(text)
        if path.name == "results.json":
            errors.extend(f"{path}: {e}" for e in validate_public(data))
        else:
            for key in re.findall(r'"([A-Za-z_]+)"\s*:', text):
                if key.lower() in FORBIDDEN_KEYS:
                    errors.append(f"{path}: key {key!r} is not publishable")
    return errors


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv] or [
        p
        for d in DEFAULT_DIRS
        if d.exists()
        for p in sorted(d.rglob("*"))
        if p.is_file()
    ]
    errors = [e for p in paths if p.suffix in {".json", ".csv"} for e in check_file(p)]
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Checked {len(paths)} public files: {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
