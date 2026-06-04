#!/usr/bin/env python3
"""
Evaluate the scanner against the REAL uploaded photos in samples/.

Ground truth (RITM + secondary id) was read by eye at full resolution.
The key metric is "usable": at least one of the two identifiers is correct,
which is enough to find the request.

    python eval_real.py
"""

from __future__ import annotations

import os
import time

import ritm_scanner

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")

# (expected RITM set, expected secondary id)
GROUND_TRUTH = {
    "20260410_114646.jpg": ({"RITM001414834", "RITM103492101"}, "A525252"),
    "20260520_095547.jpg": ({"RITM103624341"}, "A223331"),
    "20260520_100126.jpg": ({"RITM103642016"}, "A422377"),
    "20260520_100134.jpg": ({"RITM103618187"}, "T0490084"),
    "20260520_100145.jpg": ({"RITM103654085"}, "A444784"),
    "20260520_100158.jpg": ({"RITM103657055"}, "A529917"),
    "20260520_100202.jpg": ({"RITM103656785"}, "V028937"),
    "20260520_100845.jpg": ({"RITM103621703"}, "YF71889"),
    "20260520_100847.jpg": ({"RITM103618713"}, "T029709"),
    "20260520_100915.jpg": ({"RITM103641411"}, "T080949"),
    "20260520_100921.jpg": ({"RITM103653984"}, "A241329"),
    "20260520_100923.jpg": ({"RITM103652557"}, "T071750"),
    "20260520_100925.jpg": ({"RITM103651812"}, "A390860"),
}


def main() -> int:
    ritm_ok = sec_ok = usable = 0
    total = len(GROUND_TRUTH)
    t0 = time.time()

    for name, (exp_ritms, exp_sec) in GROUND_TRUTH.items():
        path = os.path.join(SAMPLES, name)
        if not os.path.exists(path):
            print(f"missing {name}")
            continue
        s = time.time()
        res = ritm_scanner.scan_image(path)
        dt = time.time() - s

        got_ritms = set(res["ritms"])
        got_sec = set(res.get("secondary", []))

        r_hit = exp_ritms <= got_ritms          # all expected RITMs present
        r_clean = got_ritms == exp_ritms
        s_hit = exp_sec in got_sec
        use = r_hit or s_hit

        ritm_ok += r_clean
        sec_ok += s_hit
        usable += use

        mark = "OK " if use else "XX "
        ritm_str = ",".join(sorted(got_ritms)) or "-"
        sec_str = ",".join(sorted(got_sec)) or "-"
        rflag = "ok" if r_clean else ("partial" if r_hit else "MISS")
        sflag = "ok" if s_hit else "MISS"
        print(f"[{mark}] {name:<22} {dt:4.1f}s  RITM[{rflag:7}]={ritm_str:<28} "
              f"id[{sflag:4}]={sec_str:<10} exp_id={exp_sec}")

    print(f"\nRITM exact:                 {ritm_ok}/{total}")
    print(f"secondary id correct:       {sec_ok}/{total}")
    print(f"USABLE (>=1 id correct):    {usable}/{total}")
    print(f"avg {(time.time() - t0)/total:.1f}s/photo")
    return 0 if usable == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
