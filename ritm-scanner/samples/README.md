# 📥 Upload your real label photos here

Drop the actual phone photos of the labels into **this folder** on the
`claude/zen-allen-1PoEc` branch and commit them. Any orientation is fine —
the scanner rotates them itself.

### How to upload from GitHub (web)

1. Make sure the branch selector (top-left of the file list) says
   **`claude/zen-allen-1PoEc`**.
2. Open this `ritm-scanner/samples/` folder.
3. Click **Add file → Upload files**.
4. Drag in your photos (`.jpg`, `.jpeg`, `.png`, `.heic`, …).
5. Under "Commit changes", keep **"Commit directly to the
   `claude/zen-allen-1PoEc` branch"** selected, then **Commit changes**.

That's it — once they're here I can pull them and run the real OCR, compare
against the baseline I read by eye, and tune the pipeline to match.

Supported extensions: `.jpg .jpeg .png .bmp .tif .tiff .webp .heic`

(If a `.heic` won't load, the `pillow-heif` package adds HEIC support, or just
share JPEGs — most phones can export those.)
