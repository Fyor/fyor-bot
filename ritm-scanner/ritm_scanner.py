#!/usr/bin/env python3
"""
RITM label scanner — 100% local, no cloud / no AI API calls.

Reads a photo of a shipping/asset label in ANY orientation and extracts the
1 or 2 ``RITM`` numbers printed on it (format: ``RITM`` + 9 digits).

How it works
------------
1. Load the image (honouring the camera's EXIF rotation).
2. Try the 4 right-angle orientations (0/90/180/270).  Tesseract's OSD is
   used as a hint so the most likely orientation is tried first.
3. For each orientation, run Tesseract a few times with different
   binarisations / page-segmentation modes.
4. Pull out every ``RITM######### `` token with a tolerant regex, fixing the
   classic OCR digit/letter confusions (I->1, O->0, S->5, B->8 ...).
5. "Vote": a real RITM line gets read by several of the attempts, random
   noise does not — so we keep the tokens that showed up at least twice.

The only heavy dependency is the Tesseract engine itself.  Everything here
runs offline on a normal (even locked-down) Windows/Linux machine.

CLI
---
    python ritm_scanner.py path/to/image.jpg
    python ritm_scanner.py path/to/folder --json

If Tesseract is not on your PATH (e.g. a portable install on a work laptop),
point this at it with the TESSERACT_CMD environment variable, e.g.
    set TESSERACT_CMD=C:\\Tools\\Tesseract-OCR\\tesseract.exe
"""

from __future__ import annotations

import os
import re
import sys
import json
import argparse

import numpy as np
import cv2
import pytesseract
from PIL import Image, ImageOps

# --------------------------------------------------------------------------- #
# Tesseract location (supports a portable install via env var)
# --------------------------------------------------------------------------- #
_TCMD = os.environ.get("TESSERACT_CMD")
if _TCMD:
    pytesseract.pytesseract.tesseract_cmd = _TCMD

# --------------------------------------------------------------------------- #
# RITM extraction
# --------------------------------------------------------------------------- #

# A RITM number is the letters "RITM" followed by exactly 9 digits.
RITM_DIGITS = 9

# Letters Tesseract commonly confuses with digits.  We only apply these to the
# token that follows "RITM" (which is supposed to be all digits), so mapping a
# stray 'T' -> '7' there is safe.
_LETTER_TO_DIGIT = {
    "O": "0", "Q": "0", "D": "0", "U": "0",
    "I": "1", "L": "1", "|": "1", "!": "1", "/": "1", "\\": "1",
    "Z": "2",
    "E": "3",
    "A": "4",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
    "R": "8",
}

# "RITM" but tolerant of the usual misreads:
#   R, then I (or 1/l/|/!), then T (or 7), then M (or N/H), then a small gap
#   (Tesseract often splits the prefix onto its own line, so we allow a few
#   whitespace/punct chars incl. a newline), then the digit block (which may
#   contain look-alike letters and spaces that we clean up afterwards).
_RITM_RE = re.compile(
    r"R[I1L|!\]]\s?[T7]\s?[MNH][\s:#.\-]{0,6}([A-Za-z0-9|!/\\.\- ]{6,20})",
    re.IGNORECASE,
)


def _normalize_token(token: str) -> str:
    """Turn the raw text after 'RITM' into a digit string.

    Digits pass through, known look-alike letters are mapped to digits,
    separators (space/dot/dash) are skipped, and anything else stops the
    scan (it's usually the next word, e.g. a name, bleeding in).
    """
    out = []
    for ch in token.upper():
        if ch.isdigit():
            out.append(ch)
        elif ch in _LETTER_TO_DIGIT:
            out.append(_LETTER_TO_DIGIT[ch])
        elif ch in " .-_#":
            continue
        else:
            break
    return "".join(out)


def find_ritms(text: str) -> set[str]:
    """Return the set of normalised ``RITM#########`` strings found in *text*."""
    found = set()
    for m in _RITM_RE.finditer(text):
        digits = _normalize_token(m.group(1))
        if len(digits) >= RITM_DIGITS:
            found.add("RITM" + digits[:RITM_DIGITS])
    return found


# --------------------------------------------------------------------------- #
# Image loading / preprocessing
# --------------------------------------------------------------------------- #

def load_bgr(path: str) -> np.ndarray:
    """Load an image as an OpenCV BGR array, honouring EXIF orientation."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)          # respect phone rotation tag
    img = img.convert("RGB")
    return np.array(img)[:, :, ::-1].copy()      # RGB -> BGR


def _resize_for_ocr(gray: np.ndarray, lo: int = 1100, hi: int = 2400) -> np.ndarray:
    """Scale so the text is a comfortable size for Tesseract (and fast)."""
    h, w = gray.shape[:2]
    smaller = min(h, w)
    larger = max(h, w)
    scale = 1.0
    if smaller < lo:
        scale = lo / smaller
    elif larger > hi:
        scale = hi / larger
    if abs(scale - 1.0) > 1e-3:
        interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=interp)
    return gray


def preprocess(bgr: np.ndarray, variant: str) -> np.ndarray:
    """Produce a grayscale/binary image for OCR.

    variant: 'otsu' (global threshold), 'adaptive' (local threshold) or
    'gray' (contrast-stretched grayscale, no threshold).
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = _resize_for_ocr(gray)

    if variant == "gray":
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)

    if variant == "otsu":
        g = cv2.GaussianBlur(gray, (3, 3), 0)
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return th

    if variant == "adaptive":
        g = cv2.medianBlur(gray, 3)
        return cv2.adaptiveThreshold(
            g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 15
        )

    raise ValueError(f"unknown variant {variant!r}")


def _rotate(bgr: np.ndarray, deg: int) -> np.ndarray:
    deg %= 360
    if deg == 0:
        return bgr
    if deg == 90:
        return cv2.rotate(bgr, cv2.ROTATE_90_CLOCKWISE)
    if deg == 180:
        return cv2.rotate(bgr, cv2.ROTATE_180)
    if deg == 270:
        return cv2.rotate(bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError("deg must be a multiple of 90")


def _osd_orientation(bgr: np.ndarray) -> int | None:
    """Ask Tesseract which way is up. Returns 0/90/180/270 or None."""
    try:
        osd = pytesseract.image_to_osd(bgr)
        m = re.search(r"Rotate:\s*(\d+)", osd)
        if m:
            return int(m.group(1)) % 360
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------- #
# OCR + scan orchestration
# --------------------------------------------------------------------------- #

# OCR passes, each is (binarisation variant, page-seg-mode, char whitelist).
#   psm 6  = assume a uniform block of text
#   psm 11 = sparse text (good when the prefix and number land on separate lines)
# A cheap PROBE set locates the correct orientation; the FULL set is then run
# only at that orientation to gather votes.
_PROBE = [
    ("otsu", 6, None),
    ("gray", 11, None),
]
_FULL = [
    ("otsu", 6, None),
    ("gray", 11, None),
    ("otsu", 11, None),
    ("adaptive", 6, None),
    ("adaptive", 11, None),
    ("gray", 6, None),
    ("otsu", 6, "RITM0123456789"),
    ("adaptive", 6, "RITM0123456789"),
]


def _ocr(img: np.ndarray, psm: int, whitelist: str | None) -> str:
    # --dpi 300 silences Tesseract's "invalid resolution" guess and improves
    # both orientation handling and digit accuracy on phone photos.
    config = f"--oem 3 --psm {psm} --dpi 300"
    if whitelist:
        config += f" -c tessedit_char_whitelist={whitelist}"
    try:
        return pytesseract.image_to_string(img, lang="eng", config=config)
    except Exception:
        return ""


def _orientation_order(bgr: np.ndarray) -> list[int]:
    """0/90/180/270 with Tesseract's OSD guess (if any) tried first."""
    order: list[int] = []
    osd = _osd_orientation(bgr)
    if osd in (0, 90, 180, 270):
        order.append(osd)
    for d in (0, 90, 180, 270):
        if d not in order:
            order.append(d)
    return order


def scan_image(path: str, min_votes: int = 2, debug: bool = False) -> dict:
    """Scan one image and return the detected RITM number(s).

    A cheap probe locates the correct right-angle orientation, then the full
    set of OCR passes runs only at that orientation and the results are voted
    on.  Falls back to a thorough sweep if the probe finds nothing.

    Returns a dict: {file, path, orientation, ritms: [...], votes: {ritm: n}}.
    """
    bgr = load_bgr(path)
    order = _orientation_order(bgr)

    proc_cache: dict = {}

    def proc(deg: int, variant: str) -> np.ndarray:
        key = (deg, variant)
        if key not in proc_cache:
            proc_cache[key] = preprocess(_rotate(bgr, deg), variant)
        return proc_cache[key]

    def run(deg: int, combos, votes: dict) -> dict:
        for variant, psm, wl in combos:
            text = _ocr(proc(deg, variant), psm, wl)
            for ritm in find_ritms(text):
                votes[ritm] = votes.get(ritm, 0) + 1
            if debug and text.strip():
                tag = f"deg={deg} {variant} psm={psm}{'/wl' if wl else ''}"
                print(f"    [{tag}] {text.strip()!r}", file=sys.stderr)
        return votes

    votes: dict[str, int] = {}
    chosen = None

    # Phase 1 — cheap probe to find the orientation.
    for deg in order:
        v = run(deg, _PROBE, {})
        if v:
            chosen, votes = deg, v
            break

    if chosen is not None:
        # Phase 2 — gather more votes at the winning orientation.
        rest = [c for c in _FULL if c not in _PROBE]
        run(chosen, rest, votes)
    else:
        # Fallback — nothing in the probes; sweep every orientation fully.
        for deg in order:
            v = run(deg, _FULL, {})
            if v:
                chosen, votes = deg, v
                break

    # Keep tokens seen by at least `min_votes` passes; fall back to anything.
    strong = {r: n for r, n in votes.items() if n >= min_votes}
    keep = strong or votes
    ritms = sorted(keep, key=lambda r: (-keep[r], r))

    return {
        "file": os.path.basename(path),
        "path": path,
        "orientation": chosen,
        "ritms": ritms,
        "votes": dict(sorted(votes.items(), key=lambda kv: -kv[1])),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".heic"}


def _iter_images(target: str):
    if os.path.isdir(target):
        for name in sorted(os.listdir(target)):
            if os.path.splitext(name)[1].lower() in _IMAGE_EXTS:
                yield os.path.join(target, name)
    else:
        yield target


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Extract RITM numbers from label photos (offline).")
    ap.add_argument("target", help="image file or a folder of images")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    ap.add_argument("--min-votes", type=int, default=2, help="agreement needed to keep a RITM (default 2)")
    ap.add_argument("--debug", action="store_true", help="print raw OCR text to stderr")
    args = ap.parse_args(argv)

    results = [scan_image(p, min_votes=args.min_votes, debug=args.debug) for p in _iter_images(args.target)]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            ritms = ", ".join(r["ritms"]) if r["ritms"] else "(none found)"
            orient = f"orient={r['orientation']}" if r["orientation"] is not None else "orient=?"
            print(f"{r['file']:<34} {ritms:<32} [{orient}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
