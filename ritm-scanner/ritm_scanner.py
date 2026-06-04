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


# A secondary identifier under the RITM: a 1-2 letter prefix + 5-8 digits, e.g.
# A525252, T0490084, V028937, YF71889.  Useful as a cross-check / fallback: if
# the RITM is misread but this is right (or vice-versa), the request can still
# be found.  The digit part tolerates the usual look-alike letters.
_SECONDARY_RE = re.compile(r"\b([A-Z]{1,2})[ .]?([0-9OQDILZSGB|!]{5,8})\b", re.IGNORECASE)
_SECONDARY_SKIP = {"RI", "IT", "TM", "RITM", "ID", "NR", "NO"}


def find_secondary_ids(text: str) -> set[str]:
    """Return secondary identifiers (e.g. ``A525252``) found in *text*."""
    cleaned = _RITM_RE.sub("  ", text)          # remove RITM tokens first
    found = set()
    for m in _SECONDARY_RE.finditer(cleaned):
        prefix = m.group(1).upper()
        if prefix in _SECONDARY_SKIP:
            continue
        digits = _normalize_token(m.group(2))
        if 5 <= len(digits) <= 8:
            found.add(prefix + digits)
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


def _cap_size(bgr: np.ndarray, max_dim: int = 2200) -> np.ndarray:
    """Shrink huge phone photos up front — label text stays plenty legible and
    everything downstream (detection, warp, OSD, OCR) gets much faster."""
    h, w = bgr.shape[:2]
    m = max(h, w)
    if m > max_dim:
        s = max_dim / m
        bgr = cv2.resize(bgr, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return bgr


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
        osd = pytesseract.image_to_osd(_cap_size(bgr, 1200))
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


# --------------------------------------------------------------------------- #
# Label localisation + deskew
# --------------------------------------------------------------------------- #
# Photos are rarely at a clean 0/90/180/270 angle, and the label sits among
# clutter (other boxes, printed packaging).  Finding the bright label rectangle
# and warping it upright removes the clutter and the skew in one step, which
# both fixes tilted photos and speeds OCR up.

def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]          # top-left
    rect[2] = pts[np.argmax(s)]          # bottom-right
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]          # top-right
    rect[3] = pts[np.argmax(d)]          # bottom-left
    return rect


def _warp_rect(bgr: np.ndarray, rect) -> "np.ndarray | None":
    src = _order_points(cv2.boxPoints(rect).astype("float32"))
    tl, tr, br, bl = src
    w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if w < 10 or h < 10:
        return None
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
    m = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(bgr, m, (w, h))


def find_label_crops(bgr: np.ndarray, max_crops: int = 2) -> list:
    """Return up to `max_crops` deskewed crops of the white label rectangle(s).

    The label is white (low saturation, high brightness); the boxes/bags around
    it are coloured or dark.  We threshold on that, keep only contours that fill
    a rotated rectangle well (i.e. are actually rectangular), and warp them
    upright — which removes both the background clutter and any skew.
    """
    h, w = bgr.shape[:2]
    area = h * w
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    white = ((hsv[:, :, 1] < 70) & (hsv[:, :, 2] > 130)).astype(np.uint8) * 255
    white = cv2.morphologyEx(white, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)), iterations=2)
    cnts, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cand = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 0.03 * area or a > 0.92 * area:
            continue
        rect = cv2.minAreaRect(c)
        rw, rh = rect[1]
        if min(rw, rh) < 60:
            continue
        if max(rw, rh) / max(1.0, min(rw, rh)) > 4.5:     # too elongated for a label
            continue
        if a / (rw * rh + 1e-6) < 0.5:                    # contour not rectangular enough
            continue
        cand.append((a, rect))

    crops = []
    for _, rect in sorted(cand, key=lambda t: -t[0])[:max_crops]:
        crop = _warp_rect(bgr, rect)
        if crop is not None:
            crop = cv2.copyMakeBorder(crop, 16, 16, 16, 16, cv2.BORDER_CONSTANT,
                                      value=(255, 255, 255))
            crops.append(crop)
    return crops


# --------------------------------------------------------------------------- #
# Result selection
# --------------------------------------------------------------------------- #

def _select(votes: dict, min_votes: int) -> list:
    """Pick the winning RITM(s): drop low-confidence reads and de-duplicate
    near-identical reads that differ only by a stray leading/trailing digit."""
    if not votes:
        return []
    top = max(votes.values())
    threshold = max(min_votes, (top + 1) // 2)
    strong = {r: n for r, n in votes.items() if n >= threshold} or dict(votes)

    kept: list[tuple[str, int]] = []
    for ritm, n in sorted(strong.items(), key=lambda kv: (-kv[1], kv[0])):
        d = ritm[4:]
        # a "shift" duplicate: same digits with one stray digit at an end
        dup = any(d == k[4:] or d[1:] == k[4:][:-1] or d[:-1] == k[4:][1:]
                  for k, _ in kept)
        if not dup:
            kept.append((ritm, n))
    return [r for r, _ in kept]


def _select_secondary(votes: dict, min_votes: int, top: int = 2) -> list:
    """Return the best-voted secondary identifier(s).

    We keep up to `top` candidates rather than de-duplicating aggressively: the
    point of the secondary id is to be a *fallback* the user can cross-check, so
    it's better to surface both close reads (e.g. ``A223331`` and a noisy
    ``A2223331``) than to risk hiding the correct one.
    """
    if not votes:
        return []
    top_votes = max(votes.values())
    threshold = max(min_votes, (top_votes + 1) // 2)
    keep = {k: v for k, v in votes.items() if v >= threshold} or dict(votes)
    return [k for k, _ in sorted(keep.items(), key=lambda kv: (-kv[1], kv[0]))[:top]]


def scan_image(path: str, min_votes: int = 2, debug: bool = False) -> dict:
    """Scan one image and return the detected RITM number(s).

    Pipeline: isolate + deskew the label (falling back to the whole photo),
    then for each candidate try the 4 right-angle orientations.  A cheap probe
    finds the correct orientation, the full set of OCR passes runs only there,
    and the reads are voted on.

    Returns a dict: {file, path, orientation, ritms: [...], votes: {ritm: n}}.
    """
    bgr = _cap_size(load_bgr(path))
    try:
        bases = find_label_crops(bgr)
    except Exception:
        bases = []
    bases.append(bgr)                    # whole photo as the final fallback

    rit_votes: dict[str, int] = {}
    sec_votes: dict[str, int] = {}
    chosen = None
    rest = [c for c in _FULL if c not in _PROBE]

    for bi, base in enumerate(bases):
        cache: dict = {}

        def proc(deg, variant, _base=base, _cache=cache):
            key = (deg, variant)
            if key not in _cache:
                _cache[key] = preprocess(_rotate(_base, deg), variant)
            return _cache[key]

        def run(deg, combos, racc, sacc):
            for variant, psm, wl in combos:
                text = _ocr(proc(deg, variant), psm, wl)
                for ritm in find_ritms(text):
                    racc[ritm] = racc.get(ritm, 0) + 1
                for sid in find_secondary_ids(text):
                    sacc[sid] = sacc.get(sid, 0) + 1
                if debug and text.strip():
                    tag = f"base{bi} deg={deg} {variant} psm={psm}{'/wl' if wl else ''}"
                    print(f"    [{tag}] {text.strip()!r}", file=sys.stderr)
            return racc

        # Phase 1 — find the orientation via a cheap RITM probe.
        found_deg = None
        racc: dict = {}
        sacc: dict = {}
        for deg in _orientation_order(base):
            r_try, s_try = {}, {}
            run(deg, _PROBE, r_try, s_try)
            if r_try:
                found_deg, racc, sacc = deg, r_try, s_try
                break
        if found_deg is not None:
            # Phase 2 — full passes at the winning orientation; gather both ids.
            run(found_deg, rest, racc, sacc)
            rit_votes, sec_votes, chosen = racc, sacc, found_deg
            break                        # first candidate that yields RITM(s) wins

    return {
        "file": os.path.basename(path),
        "path": path,
        "orientation": chosen,
        "ritms": _select(rit_votes, min_votes),
        "secondary": _select_secondary(sec_votes, min_votes),
        "votes": dict(sorted(rit_votes.items(), key=lambda kv: -kv[1])),
        "secondary_votes": dict(sorted(sec_votes.items(), key=lambda kv: -kv[1])),
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
            ritms = ", ".join(r["ritms"]) if r["ritms"] else ""
            sec = ", ".join(r.get("secondary", []))
            if ritms or sec:
                ident = ritms or "(no RITM)"
                if sec:
                    ident += f"   id: {sec}"
            else:
                ident = "(nothing read — check this photo by hand)"
            print(f"{r['file']:<30} {ident}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
