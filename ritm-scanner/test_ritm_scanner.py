#!/usr/bin/env python3
"""
Run the scanner over the synthetic test images and check it against the
ground-truth RITM numbers (read by eye from the real photos).

    python make_test_images.py     # once, to create test_images/
    python test_ritm_scanner.py

Exit code is non-zero if any label fails, so it doubles as a CI check.
"""

from __future__ import annotations

import os
import sys

import ritm_scanner

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "test_images")

# Ground truth: what a human reads on each real label.
EXPECTED = {
    "01_arendal_bag.png":        {"RITM001414834", "RITM103492101"},
    "02_arendal_bag_rot.png":    {"RITM001414834", "RITM103492101"},
    "03_lundby_box_italic.png":  {"RITM103624341"},
    "04_cirafon_red.png":        {"RITM103642016"},
    "05_dell_mouse_italic.png":  {"RITM103618187"},
}


def main() -> int:
    if not os.path.isdir(IMG_DIR) or not os.listdir(IMG_DIR):
        print("test_images/ is empty — run:  python make_test_images.py", file=sys.stderr)
        return 2

    passed = 0
    for name, expected in EXPECTED.items():
        path = os.path.join(IMG_DIR, name)
        result = ritm_scanner.scan_image(path)
        got = set(result["ritms"])
        ok = got == expected
        passed += ok
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name:<28} got={sorted(got)}  expected={sorted(expected)}"
              f"  (orient={result['orientation']})")
        if not ok:
            print(f"        votes={result['votes']}")

    total = len(EXPECTED)
    print(f"\n{passed}/{total} labels correct")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
