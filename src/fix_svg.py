#!/usr/bin/env python3
"""
Post-processes public/lundby_map.svg to fix visual bugs:
1. Drop <defs> section (font glyphs for legend text, ~4k lines)
2. Drop <use> elements (legend text symbols)
3. Drop paths with transform= attr (non-standard transforms → diagonal lines)
4. Drop paths entirely below y=910 in screen space (bottom legend banner)
"""

import re
import os

SVG = os.path.join(os.path.dirname(__file__), "../public/lundby_map.svg")

MAP_Y_MAX = 910.0  # baked screen-space y threshold; paths entirely below this = legend

# Matches M/L coords in already-baked d attributes (e.g. "M 234.56 567.89")
COORD_RE = re.compile(r'[ML]\s+([-\d.]+)\s+([-\d.]+)')


def path_in_map_area(d: str) -> bool:
    """Return True if any coordinate has baked y <= MAP_Y_MAX (main map area)."""
    for m in COORD_RE.finditer(d):
        if float(m.group(2)) <= MAP_Y_MAX:
            return True
    return False


def main():
    print(f"Reading {SVG} …")
    with open(SVG, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"  {len(lines):,} lines, {os.path.getsize(SVG)/1e6:.1f} MB")

    out = []
    in_defs = False
    stats = {'defs': 0, 'use': 0, 'nonstd': 0, 'legend': 0, 'kept': 0}

    for line in lines:
        s = line.lstrip()

        # ── <defs> block ──────────────────────────────────────────
        if s.startswith('<defs'):
            in_defs = True
            stats['defs'] += 1
            continue
        if in_defs:
            stats['defs'] += 1
            if '</defs' in line:
                in_defs = False
            continue

        # ── <use> elements ────────────────────────────────────────
        if s.startswith('<use ') or s.startswith('<use>'):
            stats['use'] += 1
            continue

        # ── <path> elements ───────────────────────────────────────
        if s.startswith('<path '):
            # Drop paths that still have a transform= attribute;
            # these are non-standard-transform paths (small symbols, arrows, etc.)
            # that were not baked by the optimizer and cause diagonal rendering.
            if 'transform=' in line:
                stats['nonstd'] += 1
                continue

            # Drop paths entirely below the map area (legend banner at bottom)
            m = re.search(r'\bd="([^"]+)"', line)
            if m:
                d = m.group(1)
                if not path_in_map_area(d):
                    stats['legend'] += 1
                    continue

        stats['kept'] += 1
        out.append(line)

    content = "".join(out)

    print(f"Writing fixed SVG …")
    with open(SVG, "w", encoding="utf-8") as f:
        f.write(content)

    new_sz = os.path.getsize(SVG)
    print(f"  {len(out):,} lines, {new_sz/1e6:.1f} MB")
    print(f"\nDropped:")
    print(f"  {stats['defs']:,} defs lines")
    print(f"  {stats['use']:,} <use> elements")
    print(f"  {stats['nonstd']:,} non-standard transform paths")
    print(f"  {stats['legend']:,} legend-area paths")
    print(f"Kept: {stats['kept']:,} lines")


if __name__ == "__main__":
    main()
