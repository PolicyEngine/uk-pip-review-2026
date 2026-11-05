import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_public_data", ROOT / "scripts" / "check_public_data.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def test_committed_public_files_pass():
    assert guard.main([]) == 0


def test_guard_flags_weights_and_area_codes(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("decile,household_weight\n1,2\n")
    assert guard.check_file(bad_csv)
    codes = tmp_path / "areas.json"
    codes.write_text(json.dumps({"rows": [f"E14{n:06d}" for n in range(1, 10)]}))
    assert guard.check_file(codes)


def test_guard_passes_clean_file(tmp_path):
    ok = tmp_path / "ok.json"
    ok.write_text(json.dumps({"rows": [{"decile": 1, "value": 2}]}))
    assert guard.check_file(ok) == []
