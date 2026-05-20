import os
import subprocess
import time
from pathlib import Path

import psutil

PROCESS_NAME = "Antigravity.exe"
INSTALL_PATHS = [
    Path(os.environ["LOCALAPPDATA"]) / "Programs" / "antigravity" / PROCESS_NAME,
    Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Google Antigravity" / PROCESS_NAME,
    Path("C:/Program Files/Google Antigravity") / PROCESS_NAME,
]


def find_executable() -> Path | None:
    for p in INSTALL_PATHS:
        if p.exists():
            return p
    # Fallback: find from running process
    for proc in psutil.process_iter(["name", "exe"]):
        if proc.info["name"] and proc.info["name"].lower() == PROCESS_NAME.lower():
            return Path(proc.info["exe"])
    return None


def is_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] and proc.info["name"].lower() == PROCESS_NAME.lower():
            return True
    return False


def close(timeout: float = 5.0) -> bool:
    """Gracefully terminate Antigravity, force kill after timeout. Returns True if it was running."""
    procs = [
        p for p in psutil.process_iter(["name"])
        if p.info["name"] and p.info["name"].lower() == PROCESS_NAME.lower()
    ]
    if not procs:
        return False

    for p in procs:
        p.terminate()

    _, alive = psutil.wait_procs(procs, timeout=timeout)
    for p in alive:
        p.kill()

    return True


def launch() -> bool:
    """Launch Antigravity. Returns True on success."""
    exe = find_executable()
    if exe is None:
        return False
    subprocess.Popen([str(exe)], creationflags=subprocess.DETACHED_PROCESS)
    return True
