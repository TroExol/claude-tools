#!/usr/bin/env python
"""
Ensure Chrome with remote-debug port запущен. Если нет — стартует в background.

Usage:
    python bin/ensure_chrome.py [port] [user_data_dir]

Возвращает CDP URL на stdout (e.g. http://localhost:9222) если успех, exit 0.
Exit 1 если не удалось запустить.
"""
from __future__ import annotations
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def cdp_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def find_chrome() -> str | None:
    for p in CHROME_PATHS:
        if Path(p).exists():
            return p
    return None


def launch_chrome(port: int, user_data_dir: str) -> None:
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome not found")
    Path(user_data_dir).mkdir(parents=True, exist_ok=True)
    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
    ]
    # Detached background process (Windows: DETACHED_PROCESS=0x00000008)
    creationflags = 0x00000008 if sys.platform == "win32" else 0
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=creationflags, close_fds=True)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9222
    user_data_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "chrome-debug-profile")
    if cdp_alive(port):
        print(f"http://localhost:{port}", flush=True)
        return
    launch_chrome(port, user_data_dir)
    for _ in range(30):
        time.sleep(1)
        if cdp_alive(port):
            print(f"http://localhost:{port}", flush=True)
            return
    sys.exit(f"Chrome failed to start on port {port} within 30s")


if __name__ == "__main__":
    main()
