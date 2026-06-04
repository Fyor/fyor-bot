#!/usr/bin/env python3
"""
Watch a folder (e.g. your OneDrive scans folder) and print/log the RITM
number(s) of every new photo that lands in it.  100% local, no cloud.

    python watch_folder.py "C:\\Users\\me\\OneDrive\\RITM-scans"
    python watch_folder.py ./incoming --interval 3 --move --clipboard

What it does each time a new (or changed) image appears:
  * waits until the file size is stable (so half-synced OneDrive files are
    not read too early),
  * scans it with ritm_scanner,
  * prints the result and appends a row to a CSV log,
  * optionally copies the RITM(s) to the clipboard (--clipboard),
  * optionally moves the photo into a 'processed/' subfolder (--move).

State is kept in '.ritm_seen.json' inside the watched folder, so restarting
the watcher does not reprocess everything.
"""

from __future__ import annotations

import os
import csv
import sys
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime

import ritm_scanner

IMAGE_EXTS = ritm_scanner._IMAGE_EXTS
STATE_NAME = ".ritm_seen.json"


def _load_state(folder: str) -> dict:
    try:
        with open(os.path.join(folder, STATE_NAME), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_state(folder: str, state: dict) -> None:
    try:
        with open(os.path.join(folder, STATE_NAME), "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
    except Exception as exc:
        print(f"  (could not save state: {exc})", file=sys.stderr)


def _stable_size(path: str, wait: float = 0.6) -> bool:
    """True if the file size is the same before and after a short wait."""
    try:
        a = os.path.getsize(path)
        time.sleep(wait)
        return a == os.path.getsize(path) and a > 0
    except OSError:
        return False


def _to_clipboard(text: str) -> None:
    """Best-effort clipboard copy (Windows 'clip', macOS 'pbcopy', or pyperclip)."""
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(text)
        return
    except Exception:
        pass
    cmd = None
    if os.name == "nt":
        cmd = ["clip"]
    elif sys.platform == "darwin":
        cmd = ["pbcopy"]
    elif shutil.which("xclip"):
        cmd = ["xclip", "-selection", "clipboard"]
    if cmd:
        try:
            subprocess.run(cmd, input=text.encode(), check=False)
        except Exception:
            pass


def _append_csv(log_path: str, row: dict) -> None:
    new = not os.path.exists(log_path)
    with open(log_path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["timestamp", "file", "ritm_1", "ritm_2",
                        "secondary_id", "needs_review", "orientation", "all_found"])
        ritms = row["ritms"]
        sec = row["secondary"]
        w.writerow([
            row["timestamp"], row["file"],
            ritms[0] if len(ritms) > 0 else "",
            ritms[1] if len(ritms) > 1 else "",
            " / ".join(sec),
            "yes" if not ritms and not sec else "",
            row["orientation"],
            " ".join(f"{k}({v})" for k, v in row["votes"].items()),
        ])


def process(path: str, args) -> dict:
    result = ritm_scanner.scan_image(path, min_votes=args.min_votes)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ritms = result["ritms"]
    sec = result.get("secondary", [])

    if ritms or sec:
        pretty = ", ".join(ritms) if ritms else "(no RITM)"
        if sec:
            pretty += f"   id: {' / '.join(sec)}"
    else:
        pretty = "(nothing read — CHECK THIS PHOTO BY HAND)"
    print(f"[{ts}] {result['file']}\n          -> {pretty}")

    row = {"timestamp": ts, "file": result["file"], "ritms": ritms, "secondary": sec,
           "orientation": result["orientation"], "votes": result["votes"]}
    _append_csv(args.log, row)

    # Clipboard / sidecar get whatever identifiers we have (RITM preferred).
    ids = ritms + sec
    if ids and args.clipboard:
        _to_clipboard(" ".join(ritms) if ritms else " ".join(sec))

    if args.sidecar and ids:
        with open(os.path.splitext(path)[0] + ".ritm.txt", "w", encoding="utf-8") as fh:
            fh.write("\n".join(ritms + [f"id: {s}" for s in sec]) + "\n")

    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Watch a folder and extract RITM numbers from new photos.")
    ap.add_argument("folder", help="folder to watch (e.g. your OneDrive scans folder)")
    ap.add_argument("--interval", type=float, default=3.0, help="seconds between scans (default 3)")
    ap.add_argument("--log", default=None, help="CSV log path (default: <folder>/ritm_results.csv)")
    ap.add_argument("--min-votes", type=int, default=2, help="agreement needed to keep a RITM (default 2)")
    ap.add_argument("--move", action="store_true", help="move processed photos into <folder>/processed/")
    ap.add_argument("--clipboard", action="store_true", help="copy the latest RITM(s) to the clipboard")
    ap.add_argument("--sidecar", action="store_true", help="write a <name>.ritm.txt next to each photo")
    ap.add_argument("--once", action="store_true", help="scan existing files once and exit (no watching)")
    args = ap.parse_args(argv)

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"not a folder: {folder}", file=sys.stderr)
        return 2
    if args.log is None:
        args.log = os.path.join(folder, "ritm_results.csv")

    processed_dir = os.path.join(folder, "processed")
    if args.move:
        os.makedirs(processed_dir, exist_ok=True)

    state = _load_state(folder)

    def is_image(name: str) -> bool:
        return os.path.splitext(name)[1].lower() in IMAGE_EXTS

    print(f"Watching: {folder}")
    print(f"Log:      {args.log}")
    print("Drop label photos in; press Ctrl+C to stop.\n" if not args.once else "")

    try:
        while True:
            for name in sorted(os.listdir(folder)):
                path = os.path.join(folder, name)
                if not is_image(name) or not os.path.isfile(path):
                    continue
                try:
                    mtime = os.path.getmtime(path)
                except OSError:
                    continue
                if state.get(name) == mtime:        # already handled this version
                    continue
                if not _stable_size(path):          # still being written/synced
                    continue

                try:
                    process(path, args)
                except Exception as exc:
                    print(f"  ERROR scanning {name}: {exc}", file=sys.stderr)

                state[name] = mtime
                _save_state(folder, state)

                if args.move:
                    dest = os.path.join(processed_dir, name)
                    try:
                        shutil.move(path, dest)
                        state.pop(name, None)
                        _save_state(folder, state)
                    except Exception as exc:
                        print(f"  (could not move {name}: {exc})", file=sys.stderr)

            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
