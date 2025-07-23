#!/usr/bin/env python3
"""Utility to manage .var files with version numbers."""
import os
import re
import json
import tkinter as tk
from tkinter import filedialog

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".var_cleaner_config.json")


def load_last_dir():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_dir")
        except Exception:
            return None
    return None


def save_last_dir(path: str) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"last_dir": path}, f)
    except Exception:
        pass


def pick_directory() -> str:
    """Return a directory chosen by the user.

    Uses a Tkinter directory picker when possible. If the GUI cannot be
    started (e.g. in a headless environment), falls back to a text prompt.
    """
    initial = load_last_dir() or os.getcwd()
    try:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(initialdir=initial)
        root.destroy()
    except Exception:
        path = input(f"Enter directory path [{initial}]: ").strip() or initial

    if path and os.path.isdir(path):
        save_last_dir(path)
        return path
    return None


VERSION_RE = re.compile(r"^(?P<base>.+?)\.(?P<version>\d+)\.var$", re.IGNORECASE)


def scan_directory(dirpath: str):
    latest = {}
    for name in os.listdir(dirpath):
        if not name.lower().endswith(".var"):
            continue
        m = VERSION_RE.match(name)
        if not m:
            continue
        base = m.group("base")
        ver = int(m.group("version"))
        if ver > latest.get(base, -1):
            latest[base] = ver

    outdated = []
    total_size = 0
    for name in os.listdir(dirpath):
        if not name.lower().endswith(".var"):
            continue
        m = VERSION_RE.match(name)
        if not m:
            continue
        base = m.group("base")
        ver = int(m.group("version"))
        if ver < latest.get(base, ver):
            path = os.path.join(dirpath, name)
            outdated.append(path)
            try:
                total_size += os.path.getsize(path)
            except OSError:
                pass
    return outdated, total_size


def format_size(num: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB"]:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PB"


def main() -> None:
    dirpath = pick_directory()
    if not dirpath:
        print("No directory selected. Exiting.")
        return

    mode = input("Choose mode (VIEW/UPDATE): ").strip().lower()
    if mode not in ("view", "update"):
        print("Invalid mode. Exiting.")
        return

    outdated, size = scan_directory(dirpath)
    count = len(outdated)
    print(f"Outdated files: {count}")
    print(f"Disk space used: {format_size(size)}")

    if mode == "update" and count > 0:
        resp = input("OK to delete? [y/N]: ").strip().lower()
        if resp.startswith("y"):
            for path in outdated:
                try:
                    os.remove(path)
                except OSError as e:
                    print(f"Failed to delete {path}: {e}")
            print(f"Deleted {len(outdated)} files.")
        else:
            print("Deletion cancelled.")

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
