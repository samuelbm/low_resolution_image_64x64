"""Make sure only one program drives the panel: a new one stops the old one.

Two programs on the same GPIO pins mix their pictures on the panel, and their
two real-time refresh threads starve the Zero (lost SSH, shutdown button
ignored; happened 2026-10-28, D-019).
"""

import fcntl
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import TextIO

# /run is in RAM: emptied at every boot, so no stale lock after a power cut.
LOCK_PATH = Path("/run/rgbmatrix-panel.lock")
SERVICE = "rgbmatrix-display.service"
# loop.py loads all files before it creates the matrix, so stopping can take
# a moment while the old program finishes its current step.
STOP_TIMEOUT_S = 10.0

# Kept open for the life of the program: the kernel holds the lock exactly as
# long as this file is open, and frees it even after a crash or kill -9.
_lock_file: TextIO | None = None


def _is_from_service(pid: int) -> bool:
    try:
        return SERVICE in Path(f"/proc/{pid}/cgroup").read_text()
    except OSError:
        return False


def _stop(pid: int) -> None:
    if _is_from_service(pid):
        # A plain signal is not enough: Restart=always would start the service
        # again after 5 s and take the panel back. Stopped, it stays stopped
        # until "systemctl start" or the next boot.
        print(
            f"stopping {SERVICE} (start it again with: "
            f"sudo systemctl start {SERVICE.removesuffix('.service')})"
        )
        subprocess.run(["systemctl", "stop", SERVICE], check=False)
        return
    print(f"stopping the program already using the panel (pid {pid})")
    try:
        # Same as Ctrl+C: our scripts then clear the panel before exiting.
        os.kill(pid, signal.SIGINT)
    except ProcessLookupError:
        pass


def _wait_for_lock(lock: TextIO, pid: int) -> None:
    deadline = time.monotonic() + STOP_TIMEOUT_S
    killed = False
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            pass
        if time.monotonic() > deadline:
            if killed or pid <= 0:
                raise SystemExit("the panel is still in use, giving up")
            print(f"pid {pid} did not stop, killing it")
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            killed = True
            deadline = time.monotonic() + STOP_TIMEOUT_S
        time.sleep(0.1)


def take_panel() -> None:
    """Stop whichever of our programs drives the panel, then claim it."""
    global _lock_file
    try:
        # No "with": the file must stay open as long as the program runs.
        lock = open(LOCK_PATH, "a+")  # noqa: SIM115
    except PermissionError:
        raise SystemExit("run with sudo: the panel needs root") from None
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        # The holder wrote its pid while holding the lock, so the pid is one
        # of our programs, not an unrelated process that reused the number.
        lock.seek(0)
        text = lock.read().strip()
        pid = int(text) if text.isdigit() else 0
        if pid > 0:
            _stop(pid)
        _wait_for_lock(lock, pid)
    lock.seek(0)
    lock.truncate()
    lock.write(f"{os.getpid()}\n")
    lock.flush()
    _lock_file = lock
