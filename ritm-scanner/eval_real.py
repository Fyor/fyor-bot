#!/usr/bin/env python3
"""
Evaluate the scanner against the REAL uploaded photos in samples/.

Ground truth was read by eye (full resolution) from each photo. Run:

    python eval_real.py
"""

from __future__ import annotations

import os
import sys
import time

import ritm_scanner

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")

# Hand-read ground truth for the uploaded photos.
GROUND_TRUTH = {
    "20260410_114646.jpg": {"RITM001414834", "RITM103492101"},
    "20260520_095547.jpg": {"RITM103624341"},
    "20260520_100126.jpg": {"RITM103642016"},
    "20260520_100134.jpg": {"RITM103618187"},
    "20260520_100145.jpg": {"RITM103654085"},
    "20260520_100158.jpg": {"RITM103657055"},
    "20260520_100202.jpg": {"RITM103656785"},
    "20260520_100845.jpg": {"RITM103621703"},
    "20260520_100847.jpg": {"RITM103618713"},
    "20260520_100915.jpg": {"RITM103641411"},
    "20260520_100921.jpg": {"RITM103653984"},
    "20260520_100923.jpg": {"RITM103652557"},
    "20260520_100925.jpg": {"RITM103651812"},
}


def main() -> int:
    exact = found_all = clean = 0
    total = len(GROUND_TRUTH)
    t0 = time.time()

    for name, expected in GROUND_TRUTH.items():
        path = os.path.join(SAMPLES, name)
        if not os.path.exists(path):
            print(f"missing {name}")
            continue
        s = time.time()
        got = set(ritm_scanner.scan_image(path)["ritms"])
        dt = time.time() - s

        missing = expected - got
        extra = got - expected
        is_exact = not missing and not extra
        exact += is_exact
        found_all += not missing
        clean += not extra

        mark = "OK  " if is_exact else "    "
        line = f"[{mark}] {name:<24} {dt:4.1f}s  got={sorted(got)}"
        if missing:
            line += f"  MISSING={sorted(missing)}"
        if extra:
            line += f"  EXTRA={sorted(extra)}"
        print(line)

    print(f"\nexact match:      {exact}/{total}")
    print(f"all expected hit: {found_all}/{total}")
    print(f"no false extras:  {clean}/{total}")
    print(f"avg {(time.time() - t0)/total:.1f}s/photo")
    return 0 if exact == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
