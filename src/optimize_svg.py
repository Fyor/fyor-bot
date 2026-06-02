#!/usr/bin/env python3
"""
Optimizes the Lundby AutoCAD PDF-exported SVG for web use.

Strategy:
- Add class="building" to yellow paths, class="infra" to gray label-outline paths
- For the 97k standard-transform paths: BAKE the transform into the path
  coordinates (eliminates ~97k repeated transform attr strings → -5 MB)
- Non-standard transform paths and <use> elements are left untouched
- Round all floating-point numbers to 2 decimal places
Output: public/lundby_map.svg
"""

import re
import os

INPUT  = "/tmp/lundby_map.svg"
OUTPUT = os.path.join(os.path.dirname(__file__), "../public/lundby_map.svg")

YELLOW_FILL = 'fill="rgb(100%, 87.449646%, 49.803162%)"'
GRAY_FILL   = 'fill="rgb(59.606934%, 59.606934%, 59.606934%)"'
STD_XFORM   = ' transform="matrix(0.12, 0, 0, -0.12, 0, 1191)"'

# Standard transform: x' = 0.12*x,  y' = -0.12*y + 1191
# Only M/L commands (all absolute) appear in AutoCAD-generated paths.
PATH_D_RE = re.compile(r'd="([^"]+)"')
COORD_RE  = re.compile(r'([ML])\s+([-\d.]+)\s+([-\d.]+)')

def bake_transform(d: str) -> str:
    """Apply matrix(0.12, 0, 0, -0.12, 0, 1191) to M/L coordinates in path d attr."""
    def transform_cmd(m):
        cmd = m.group(1)
        x = float(m.group(2)) * 0.12
        y = float(m.group(3)) * -0.12 + 1191
        return f"{cmd} {x:.2f} {y:.2f}"
    return COORD_RE.sub(transform_cmd, d)


def process_path_line(line: str) -> str:
    """Add class, bake transform for standard-transform paths."""
    has_std = STD_XFORM in line
    is_yellow = YELLOW_FILL in line
    is_gray   = GRAY_FILL in line

    if not has_std:
        return line

    # Add semantic class
    if is_yellow:
        line = line.replace("<path ", '<path class="building" ', 1)
    elif is_gray and 'fill-rule="nonzero"' in line:
        line = line.replace("<path ", '<path class="infra" ', 1)

    # Bake transform into coordinates
    m = PATH_D_RE.search(line)
    if m:
        new_d = bake_transform(m.group(1))
        line = line[:m.start(1)] + new_d + line[m.end(1):]

    # Remove the transform attribute
    line = line.replace(STD_XFORM, '')

    return line


def round_number(m: re.Match) -> str:
    return f"{float(m.group(0)):.2f}"


def main():
    print(f"Reading {INPUT} …")
    with open(INPUT, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Processing {len(lines):,} lines …")
    out = []
    for line in lines:
        out.append(process_path_line(line))

    content = "".join(out)

    # Round all remaining floating-point numbers (glyph defs, non-std paths, etc.)
    print("Rounding remaining floats …")
    content = re.sub(r"-?\d+\.\d{3,}", round_number, content)

    print(f"Writing {OUTPUT} …")
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT)), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(content)

    orig = os.path.getsize(INPUT)
    out_sz = os.path.getsize(OUTPUT)
    print(f"Original : {orig/1e6:.1f} MB")
    print(f"Optimized: {out_sz/1e6:.1f} MB  ({(1-out_sz/orig)*100:.0f}% reduction)")
    print("Done.")


if __name__ == "__main__":
    main()
