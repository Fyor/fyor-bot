#!/usr/bin/env python3
"""
Generate synthetic stand-ins for the 5 real label photos.

These are NOT the real photos (those live only as pixels in the chat / on your
phone).  They recreate the same text, layout and fonts, then add rotation,
glare, perspective, noise and JPEG artefacts so the scanner's orientation
handling and RITM extraction get a real workout in the cloud.

They are deliberately a proxy: the true accuracy test is running
``ritm_scanner.py`` on your actual photos (see README).
"""

from __future__ import annotations

import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "test_images")

np.random.seed(7)  # deterministic output


def find_font(candidates):
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("no usable font found from: %s" % candidates)


SANS = find_font([
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
])
SERIF_IT = find_font([
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
    "C:/Windows/Fonts/timesi.ttf",
])


# --------------------------------------------------------------------------- #
# rendering + degradation helpers
# --------------------------------------------------------------------------- #

def render_label(lines, font_path, font_size=54, pad=48, line_gap=16):
    font = ImageFont.truetype(font_path, font_size)
    dummy = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    sizes = [dummy.textbbox((0, 0), ln, font=font) for ln in lines]
    text_w = max(b[2] - b[0] for b in sizes)
    line_h = max(b[3] - b[1] for b in sizes)
    W = text_w + 2 * pad
    H = 2 * pad + len(lines) * line_h + (len(lines) - 1) * line_gap
    card = Image.new("RGB", (W, H), (252, 252, 250))
    d = ImageDraw.Draw(card)
    y = pad
    for ln, b in zip(lines, sizes):
        w = b[2] - b[0]
        d.text(((W - w) // 2 - b[0], y - b[1]), ln, font=font, fill=(18, 18, 22))
        y += line_h + line_gap
    return np.array(card)[:, :, ::-1].copy()  # -> BGR


def add_noise(img, sigma=8):
    n = np.random.normal(0, sigma, img.shape)
    return np.clip(img.astype(np.float32) + n, 0, 255).astype(np.uint8)


def glare(img, center=None, strength=85, radius=None):
    h, w = img.shape[:2]
    center = center or (int(w * 0.65), int(h * 0.35))
    radius = radius or int(min(h, w) * 0.7)
    Y, X = np.ogrid[:h, :w]
    d = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
    mask = np.clip(1 - d / radius, 0, 1) ** 2
    return np.clip(img.astype(np.float32) + mask[..., None] * strength, 0, 255).astype(np.uint8)


def on_background(card, color, margin=90):
    h, w = card.shape[:2]
    bg = np.full((h + 2 * margin, w + 2 * margin, 3), color, np.uint8)
    bg = add_noise(bg, 5)
    bg[margin:margin + h, margin:margin + w] = card
    return bg


def rotate_bound(img, angle, border=(232, 232, 230)):
    h, w = img.shape[:2]
    cx, cy = w / 2, h / 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nW, nH = int(h * sin + w * cos), int(h * cos + w * sin)
    M[0, 2] += nW / 2 - cx
    M[1, 2] += nH / 2 - cy
    return cv2.warpAffine(img, M, (nW, nH), flags=cv2.INTER_CUBIC, borderValue=border)


def perspective(img, dx=0.07, dy=0.05, border=(232, 232, 230)):
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([
        [w * dx, h * dy],
        [w * (1 - dx * 0.4), h * dy * 0.5],
        [w * (1 - dx), h * (1 - dy)],
        [w * dx * 0.5, h * (1 - dy * 0.4)],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=border)


def jpeg(img, q=75):
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.imdecode(enc, cv2.IMREAD_COLOR)


# --------------------------------------------------------------------------- #
# the 5 samples (mirroring the real photos)
# --------------------------------------------------------------------------- #

def build():
    os.makedirs(OUT, exist_ok=True)
    samples = []

    # 1 & 2: white label on a plastic bag, clean sans-serif, TWO RITMs
    bag_lines = ["RITM001414834", "RITM103492101", "Nivaldo Junio", "A525252", "Arendal"]

    c = render_label(bag_lines, SANS)
    c = glare(c, strength=70)
    c = on_background(c, (236, 236, 238))
    c = rotate_bound(c, -4)
    samples.append(("01_arendal_bag.png", jpeg(add_noise(c, 6), 82)))

    c = render_label(bag_lines, SANS)
    h0, w0 = c.shape[:2]
    c = glare(c, center=(int(w0 * 0.35), int(h0 * 0.15)),  # soft sheen over the top margin
              strength=48, radius=int(max(h0, w0) * 1.1))
    c = on_background(c, (228, 231, 236))
    c = rotate_bound(c, 7)               # rotation + glare + compression (perspective is
    samples.append(("02_arendal_bag_rot.png", jpeg(add_noise(c, 5), 85)))  # covered by 4 & 5)

    # 3: white label on a dark box, ITALIC SERIF, rotated ~90 deg, ONE RITM
    c = render_label(["RITM103624341", "A223331", "Mikael Viinikanoja", "Lundby"], SERIF_IT)
    c = on_background(c, (46, 46, 50), margin=120)
    c = perspective(c, dx=0.06, dy=0.05)
    c = rotate_bound(c, 92, border=(46, 46, 50))
    samples.append(("03_lundby_box_italic.png", jpeg(add_noise(c, 7), 78)))

    # 4: white label on a red box, sans-serif, rotated ~ -90 deg, ONE RITM
    c = render_label(["RITM103642016", "Adi Karahasanovic", "A422377", "Lundby"], SANS)
    c = on_background(c, (52, 28, 138), margin=110)  # BGR -> a deep red
    c = perspective(c, dx=0.05, dy=0.06)
    c = rotate_bound(c, -92, border=(52, 28, 138))
    samples.append(("04_cirafon_red.png", jpeg(add_noise(c, 7), 80)))

    # 5: white label on a box, ITALIC SERIF, rotated ~90 + skew + blur, ONE RITM
    c = render_label(["RITM103618187", "T0490084", "Lars Nyhlen", "Lundby"], SERIF_IT)
    c = on_background(c, (150, 180, 205), margin=120)
    c = perspective(c, dx=0.09, dy=0.06)
    c = rotate_bound(c, 88, border=(150, 180, 205))
    c = cv2.GaussianBlur(c, (3, 3), 0)
    samples.append(("05_dell_mouse_italic.png", jpeg(add_noise(c, 8), 68)))

    for name, img in samples:
        cv2.imwrite(os.path.join(OUT, name), img)
        print(f"wrote {os.path.join('test_images', name)}  ({img.shape[1]}x{img.shape[0]})")


if __name__ == "__main__":
    build()
