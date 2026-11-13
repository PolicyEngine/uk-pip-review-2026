"""The shared heavy-run lock: one data-loading job at a time on a laptop.

The machine protocol, shared with every repository on the machine and the
shell lines in ``docs/RUNBOOK.md``:

- the lock is a FILE, ``/tmp/pe-heavy.lock``, holding ``"<pid> <label>"``;
- it is created with noclobber (``O_CREAT | O_EXCL``), so any held lock,
  file or legacy directory, makes the caller wait;
- it is removed only by its owner (the pid in its first field), also when
  the run fails or receives SIGTERM;
- once the lock is held, the run waits until free plus inactive memory
  reaches ``MIN_FREE_GB`` (22 GB).

Set ``PIP_REVIEW_NO_LOCK=1`` only for runs on a small synthetic file (tests).
"""

import os
import re
import signal
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

LOCK = Path("/tmp/pe-heavy.lock")
LABEL = "pip-review"
MIN_FREE_GB = 22.0
POLL_SECONDS = 15


def free_gb() -> float | None:
    """Free plus inactive memory in GB (macOS ``vm_stat``), or None elsewhere."""
    try:
        text = subprocess.run(
            ["vm_stat"], capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    match = re.search(r"page size of (\d+)", text)
    if match is None:
        return None
    page = int(match.group(1))
    pages = 0
    for label in ("Pages free", "Pages inactive"):
        found = re.search(rf"{label}:\s+(\d+)", text)
        pages += int(found.group(1)) if found else 0
    return pages * page / 1e9


def owner(path: Path) -> str | None:
    """The pid field of the lock file, or None if there is no such file."""
    try:
        fields = Path(path).read_text().split()
    except OSError:
        return None
    return fields[0] if fields else None


def _try_acquire(path: Path, label: str) -> bool:
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as handle:
        handle.write(f"{os.getpid()} {label}\n")
    return True


def _release(path: Path) -> None:
    """Remove the lock only if this process wrote it."""
    if owner(path) == str(os.getpid()):
        Path(path).unlink(missing_ok=True)


def _exit_on_term(signum, frame):
    raise SystemExit(128 + signum)


@contextmanager
def heavy_lock(
    min_free_gb: float | None = None,
    path: Path | None = None,
    label: str = LABEL,
    poll: float | None = None,
):
    """Hold the heavy-run lock, after waiting for memory; release on exit.

    ``path``, ``min_free_gb`` and ``poll`` default to the module's values,
    read at call time (tests point ``LOCK`` at a scratch file).
    """
    if os.environ.get("PIP_REVIEW_NO_LOCK") == "1":
        yield
        return
    path = Path(LOCK if path is None else path)
    min_free_gb = MIN_FREE_GB if min_free_gb is None else min_free_gb
    poll = POLL_SECONDS if poll is None else poll
    while not _try_acquire(path, label):
        print(f"Waiting for {path} (held by {owner(path) or '?'})", file=sys.stderr)
        time.sleep(poll)
    main = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGTERM, _exit_on_term) if main else None
    try:
        while (free := free_gb()) is not None and free < min_free_gb:
            print(f"Waiting for memory: {free:.1f} GB free", file=sys.stderr)
            time.sleep(poll)
        yield
    finally:
        if main:
            signal.signal(signal.SIGTERM, previous)
        _release(path)
