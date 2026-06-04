# RITM label scanner (offline, no AI)

Reads a photo of a label **in any orientation** and pulls out **two
identifiers**:

* the 1–2 `RITM` numbers (`RITM` + 9 digits), and
* the secondary id underneath (`A525252`, `T0490084`, `V028937`, `YF71889`, …).

Two ids means redundancy: if the RITM is misread but the secondary is right
(or vice-versa), you can still find the request. Everything runs locally with
**Tesseract OCR** — no cloud, no AI API, nothing leaves the machine. Light
enough for a locked-down work laptop.

```
RITM001414834      ->  RITM001414834, RITM103492101   id: A525252
RITM103492101          (works upside-down, sideways, italic, on a bag/box)
Nivaldo Junio
A525252
Arendal
```

---

## Results on the 13 real sample photos

Measured against ground truth read by eye (`eval_real.py`):

| Metric                                   | Score   |
|------------------------------------------|---------|
| RITM read exactly                        | 10 / 13 |
| Secondary id read correctly              | 10 / 13 |
| **Usable (≥1 of the two ids correct)**   | **11 / 13** |
| Speed                                    | ~5 s/photo |

The 2 it can't read (`100202`, `100923`) are labels that are **curved on the
box / under glare** — Tesseract returns garbage even from a clean, leveled
crop, so the watcher flags them `needs_review` for a quick manual glance. A
local neural OCR reads exactly those (see *Harder photos* below).

---

## Install

**1. Python packages**
```bash
pip install -r requirements.txt
```

**2. The Tesseract engine** (separate from pip):

- **Windows:** install the [UB Mannheim build](https://github.com/UB-Mannheim/tesseract/wiki)
  (`tesseract-ocr-w64-setup-….exe`). If you can't add it to PATH (work laptop),
  point the scanner at it instead:
  ```cmd
  set TESSERACT_CMD=C:\Tools\Tesseract-OCR\tesseract.exe
  ```
  A *portable* install works too: unzip Tesseract into a folder and set
  `TESSERACT_CMD` to its `tesseract.exe` — no admin rights needed.
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt-get install tesseract-ocr`

Check it: `tesseract --version`.

---

## Use it

**Scan one photo or a whole folder:**
```bash
python ritm_scanner.py path\to\photo.jpg
python ritm_scanner.py path\to\folder --json
```

**Watch your OneDrive scans folder** (the main workflow — drop a photo, get the
number a few seconds later):
```bash
python watch_folder.py "C:\Users\me\OneDrive\RITM-scans" --clipboard
```
Each new photo is scanned, printed, and appended to `ritm_results.csv` (columns:
`ritm_1, ritm_2, secondary_id, needs_review, …`). With `--clipboard` the RITM
(or the secondary id, if no RITM) is copied ready to paste. Add `--move` to
file processed photos into a `processed/` subfolder; `--once` scans what's
already there and exits. Photos it can't read are marked `needs_review` so you
know to eyeball just those.

---

## Test it

The real photos only exist as pixels in chat / on your phone, so the repo ships
**synthetic stand-ins** that recreate each label (same text, fonts, plus
rotation, glare, perspective, noise, JPEG) to exercise the pipeline:

```bash
python make_test_images.py      # creates test_images/
python test_ritm_scanner.py     # -> "5/5 labels correct"
```

⚠️ **These are proxies, not your real photos.** They prove the orientation
handling + extraction logic works; they can't prove real-world accuracy on
glare/plastic/odd lighting. The true test is running `ritm_scanner.py` on your
actual photos — drop them in [`samples/`](samples/) and they can be scanned for
real.

---

## How it works

1. Load the image, honour the camera's EXIF rotation.
2. **Level it:** find the bright label rectangle and warp it upright — this
   removes the background clutter *and* the skew in one step (so photos don't
   need to be at a clean 90°). The whole photo is kept as a fallback.
3. Try the 4 right-angle orientations of the leveled crop. A cheap 2-pass
   **probe** finds the correct one (Tesseract's OSD is unreliable on these
   sparse labels), then the full set of passes runs only there — fast (~5 s).
4. Each orientation is OCR'd a few ways (Otsu / adaptive / grayscale × page
   modes × a digit-only pass).
5. Tolerant regexes pull out `RITM` + 9 digits **and** the secondary id,
   fixing the classic OCR confusions (`I→1`, `O→0`, `S→5`, `B→8`, …) and
   tolerating the prefix and number landing on separate lines.
6. **Voting:** a real id gets read by several passes; noise doesn't. Tokens
   seen ≥ 2 times are kept (tune with `--min-votes`).

---

## Harder photos (optional neural OCR)

The 2–3 photos Tesseract can't read are a recognition-engine limit, not a
preprocessing one (leveling/sharpening don't help). A local **neural** OCR —
**EasyOCR** or **PaddleOCR**, still 100% offline, no cloud — reads exactly
those, and as a *fallback after* Tesseract it would push this to ~13/13.

It's left out by default because it's heavy (~1–2 GB incl. PyTorch) and slower
(~20 s/photo on CPU) — a lot for a limited work PC, and it is itself an AI
model (just a local one). If you want it wired in as an opt-in fallback (off
unless installed), say so and I'll add it.

## Tuning for your real photos

Run `python ritm_scanner.py samples --debug` to see the raw OCR per pass. Knobs:

- consistently misread digit → adjust `_LETTER_TO_DIGIT` (`ritm_scanner.py`),
- a number missed entirely → loosen `_RITM_RE` / `_SECONDARY_RE` or add a pass
  to `_FULL`,
- too slow → drop a variant/pass from `_FULL`,
- false second number → raise `--min-votes`.
