"""The shared heavy-run lock: one data-loading job at a time on a laptop.

``heavy_lock()`` takes ``/tmp/pe-heavy.lock`` (a directory, so ``mkdir`` is
the atomic test), waits until free plus inactive memory reaches
``MIN_FREE_GB``, and releases the lock on exit. The same lock is used by the
shell one-liner in ``docs/RUNBOOK.md``, so the generator and hand-run builds
queue behind each other.

Set ``PIP_REVIEW_NO_LOCK=1`` only for runs on a small synthetic file (tests).
"""

import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

LOCK = Path("/tmp/pe-heavy.lock")
MIN_FREE_GB = 14.0
POLL_SECONDS = 15


def free_gb() -> float | None:
    """Free plus inactive memory in GB (macOS ``vm_stat``), or None elsewhere."""
    try:
        text = subprocess.run(
            ["vm_stat"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    page = int(re.search(r"page size of (\d+)", text).group(1))
    pages = 0
    for label in ("Pages free", "Pages inactive"):
        match = re.search(rf"{label}:\s+(\d+)", text)
        pages += int(match.group(1)) if match else 0
    return pages * page / 1e9


@contextmanager
def heavy_lock(min_free_gb: float = MIN_FREE_GB):
    if os.environ.get("PIP_REVIEW_NO_LOCK") == "1":
        yield
        return
    while True:
        try:
            LOCK.mkdir()
            break
        except FileExistsError:
            print(f"Waiting for {LOCK}", file=sys.stderr)
            time.sleep(POLL_SECONDS)
    try:
        while (free := free_gb()) is not None and free < min_free_gb:
            print(f"Waiting for memory: {free:.1f} GB free", file=sys.stderr)
            time.sleep(POLL_SECONDS)
        yield
    finally:
        LOCK.rmdir()
