"""The machine-wide heavy-run lock. Every test points the lock at a scratch
path; the real /tmp/pe-heavy.lock is never touched."""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from pip_review import heavy


@pytest.fixture(autouse=True)
def scratch_lock(tmp_path, monkeypatch):
    lock = tmp_path / "pe-heavy.lock"
    monkeypatch.setattr(heavy, "LOCK", lock)
    monkeypatch.setattr(heavy, "free_gb", lambda: 100.0)
    monkeypatch.delenv("PIP_REVIEW_NO_LOCK", raising=False)
    assert lock != Path("/tmp/pe-heavy.lock")
    return lock


def test_lock_is_a_file_with_pid_and_label(scratch_lock):
    with heavy.heavy_lock(poll=0):
        assert scratch_lock.is_file()
        assert scratch_lock.read_text().split() == [str(os.getpid()), "pip-review"]
    assert not scratch_lock.exists()


def test_lock_is_released_when_the_run_fails(scratch_lock):
    with pytest.raises(RuntimeError), heavy.heavy_lock(poll=0):
        raise RuntimeError("boom")
    assert not scratch_lock.exists()


def test_another_owners_lock_is_never_removed(scratch_lock):
    with heavy.heavy_lock(poll=0):
        scratch_lock.write_text("4242 someone-else\n")
    assert scratch_lock.read_text() == "4242 someone-else\n"


@pytest.mark.parametrize("held_as", ["file", "directory"])
def test_waits_while_another_lock_is_held(scratch_lock, held_as):
    if held_as == "file":
        scratch_lock.write_text("99999 other\n")
    else:
        scratch_lock.mkdir()
    taken = threading.Event()

    def run():
        with heavy.heavy_lock(poll=0.05):
            taken.set()

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(0.3)
    assert not taken.is_set()
    if held_as == "file":
        scratch_lock.unlink()
    else:
        scratch_lock.rmdir()
    thread.join(5)
    assert taken.is_set()
    assert not scratch_lock.exists()


def test_memory_gate_is_22_gb_and_waits_with_the_lock_held(scratch_lock, monkeypatch):
    readings = iter([10.0, 21.9, 22.0])
    held = []

    def free():
        held.append(scratch_lock.exists())
        return next(readings)

    monkeypatch.setattr(heavy, "free_gb", free)
    assert heavy.MIN_FREE_GB == 22.0
    with heavy.heavy_lock(poll=0):
        pass
    assert held == [True, True, True]


def test_no_lock_switch_skips_the_lock(scratch_lock, monkeypatch):
    monkeypatch.setenv("PIP_REVIEW_NO_LOCK", "1")
    with heavy.heavy_lock(poll=0):
        assert not scratch_lock.exists()


def test_sigterm_releases_the_lock(tmp_path):
    lock = tmp_path / "term.lock"
    code = (
        "import time\n"
        "from pip_review import heavy\n"
        "heavy.free_gb = lambda: 100.0\n"
        f"with heavy.heavy_lock(path={str(lock)!r}, poll=0):\n"
        "    print('held', flush=True)\n"
        "    time.sleep(30)\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "PIP_REVIEW_NO_LOCK"}
    proc = subprocess.Popen(
        [sys.executable, "-c", code], stdout=subprocess.PIPE, text=True, env=env
    )
    assert proc.stdout.readline().strip() == "held"
    assert lock.exists()
    proc.terminate()
    proc.wait(10)
    assert not lock.exists()
