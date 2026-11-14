#!/usr/bin/env python3
"""Generate entry.png: 1024x1024 news infographic for Friday, 13 November 2026."""
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

HEADLINES = [
    ("IRAN", "Iran claims radar strike in Bahrain; US intercepts 2 drones (Guardian/CENTCOM)"),
    ("USA", "FAA nationwide ground stop lifted after comms outage; SpaceX debris halted west coast flights (Guardian)"),
    ("TECH", "Nvidia CEO Jensen Huang resigns (AP/NPR)"),
    ("UKRAINE", "Russia-Ukraine peace talks in Abu Dhabi end without breakthrough — first talks in 9 months (AP/NPR)"),
    ("TECH", "Microsoft 365 global outage hit email and the workday (The Hindu/AP)"),
    ("INDIA", "Delhi world's most polluted city, AQI 334 (IQAir via The Hindu)"),
]

ACCENTS = ["#e5484d", "#f5a524", "#8e4ec6", "#30a46c", "#0091ff", "#ff6b35"]


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(FONT_DIR + name, size)


def wrap(draw, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


img = Image.new("RGB", (W, H), "#101418")
d = ImageDraw.Draw(img)

# Top band
d.rectangle([0, 0, W, 170], fill="#1a2028")
d.text((48, 40), "THE WORLD IN ONE DAY", font=font(52, True), fill="#ffffff")
d.text((48, 110), "Friday, 13 November 2026", font=font(26), fill="#9fb0c3")
d.line([(48, 170), (W - 48, 170)], fill="#2a3441", width=2)

y = 210
for i, (tag, text) in enumerate(HEADLINES):
    color = ACCENTS[i]
    # tag chip
    tf = font(20, True)
    tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([48, y, 48 + tw + 28, y + 36], 8, fill=color)
    d.text((62, y + 6), tag, font=tf, fill="#101418")
    # headline text
    bf = font(26, True)
    lines = wrap(d, text, bf, W - 48 - 130)
    ty = y + 4
    for ln in lines:
        d.text((48 + tw + 50, ty), ln, font=bf, fill="#e8edf2")
        ty += 36
    y = max(ty + 8, y + 44) + 22
    if i < len(HEADLINES) - 1:
        d.line([(48, y - 14), (W - 48, y - 14)], fill="#232b36", width=1)

# Footer
d.rectangle([0, H - 80, W, H], fill="#1a2028")
d.text((48, H - 58), "Six stories that shaped the day", font=font(24), fill="#9fb0c3")
d.text((W - 300, H - 54), "make.fun · news-image-01", font=font(20), fill="#5c6a7d")

img.save("entry.png", "PNG", optimize=True)
print("saved entry.png")
