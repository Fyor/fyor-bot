# RITM label scanner (offline, no AI)

Reads a photo of a label **in any orientation** and pulls out the 1–2
`RITM` numbers on it (format: `RITM` + 9 digits). Everything runs locally with
**Tesseract OCR** — no cloud, no AI API, nothing leaves the machine. Designed
to be light enough for a locked-down work laptop.

```
RITM001414834          ->  detected: RITM001414834, RITM103492101
RITM103492101              (works upside-down, sideways, italic, on a bag/box)
Nivaldo Junio
A525252
Arendal
```

---

## The baseline (read by eye from the 5 example photos)

| Photo                        | Expected RITM number(s)            |
|------------------------------|------------------------------------|
| Arendal / Nivaldo (bag)      | `RITM001414834`, `RITM103492101`   |
| Arendal / Nivaldo (bag, 2nd) | `RITM001414834`, `RITM103492101`   |
| Lundby / Mikael (italic box) | `RITM103624341`                    |
| Lundby / Adi (red Cirafon)   | `RITM103642016`                    |
| Lundby / Lars (Dell, italic) | `RITM103618187`                    |

These are the ground truth the test harness checks against.

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
Each new photo is scanned, printed, appended to `ritm_results.csv`, and (with
`--clipboard`) the RITM is copied ready to paste. Add `--move` to file
processed photos into a `processed/` subfolder. `--once` scans what's already
there and exits.

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
2. Try the 4 right-angle orientations. A cheap 2-pass **probe** finds the
   correct one (Tesseract's OSD is unreliable on these sparse labels), then the
   full set of passes runs only there — keeps it fast (~3–5 s/photo).
3. Each orientation is OCR'd a few ways (Otsu / adaptive / grayscale × page
   modes × a digit-only pass).
4. A tolerant regex finds `RITM` + 9 digits, fixing the classic OCR confusions
   (`I→1`, `O→0`, `S→5`, `B→8`, …) and tolerating the prefix and number landing
   on separate lines.
5. **Voting:** a real RITM gets read by several passes; noise doesn't. Tokens
   seen ≥ 2 times are kept (tune with `--min-votes`).

---

## Tuning for your real photos

Once real samples are in `samples/`, run `python ritm_scanner.py samples --debug`
to see the raw OCR text per pass. Common knobs:

- consistently misread digit → add/adjust a mapping in `_LETTER_TO_DIGIT`
  (`ritm_scanner.py`),
- a number missed entirely → loosen `_RITM_RE` or add an OCR pass to `_FULL`,
- too slow → drop a variant/pass from `_FULL`,
- false second number → raise `--min-votes`.

If accuracy on the hardest photos (heavy italic/glare) isn't enough, a local
neural OCR like **EasyOCR** or **PaddleOCR** (still offline, no cloud) is a
drop-in upgrade for the OCR step — heavier to install, but much better on
rotated/italic text. Ask and I'll wire it in as an optional backend.
