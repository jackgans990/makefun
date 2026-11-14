from PIL import Image, ImageDraw, ImageFilter
import math, random

W = H = 1024
random.seed(7)

img = Image.new("RGB", (W, H))
px = img.load()
# warm vertical gradient background: deep peach -> soft cream
top = (255, 170, 100)
bot = (255, 236, 200)
for y in range(H):
    t = y / H
    t = t * t * (3 - 2 * t)
    c = tuple(int(a + (b - a) * t) for a, b in zip(top, bot))
    for x in range(W):
        px[x, y] = c

# warm radial glow behind sun
glow = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(glow)
cx, cy = 512, 430
for r in range(420, 0, -6):
    a = int(90 * (1 - r / 420) ** 1.6)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a)
glow = glow.filter(ImageFilter.GaussianBlur(40))
yellow = Image.new("RGB", (W, H), (255, 215, 120))
img = Image.composite(yellow, img, glow)

draw = ImageDraw.Draw(img, "RGBA")


def soft_shadow(draw_fn, blur=18, alpha=70, offset=(0, 22)):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    draw_fn(ld, fill=(40, 30, 20, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGB", (W, H), (60, 40, 25)), (0, 0), layer)
    # note: shadow tint applied via mask; then redraw offset shape later


# --- ground / table ---
def table(ld, **kw):
    ld.rounded_rectangle([140, 700, 884, 780], 40, **kw)
soft_shadow(table)
draw.rounded_rectangle([140, 700, 884, 780], 40, fill=(255, 140, 105))
draw.rounded_rectangle([140, 700, 884, 726], 40, fill=(255, 165, 130))

# --- sun rays ---
ray_cols = [(255, 205, 90), (255, 190, 70)]
for i in range(12):
    ang = i * math.pi / 6
    r1, r2 = 190, 265
    x1, y1 = cx + r1 * math.cos(ang), cy + r1 * math.sin(ang)
    x2, y2 = cx + r2 * math.cos(ang), cy + r2 * math.sin(ang)
    wdt = 26
    dx, dy = -math.sin(ang) * wdt, math.cos(ang) * wdt
    draw.polygon([(x1 - dx, y1 - dy), (x1 + dx, y1 + dy), (x2 + dx, y2 + dy), (x2 - dx, y2 - dy)],
                 fill=ray_cols[i % 2] + (255,))

# --- sun body ---
draw.ellipse([cx - 160, cy - 160, cx + 160, cy + 160], fill=(255, 200, 70))
draw.ellipse([cx - 145, cy - 150, cx + 150, cy + 155], fill=(255, 214, 88))

# --- face ---
# eyes (happy closed arcs)
for ex in (-60, 60):
    draw.arc([cx + ex - 34, cy - 40, cx + ex + 34, cy + 30], 200, 340, fill=(120, 60, 10), width=14)
# blush
for ex in (-95, 95):
    draw.ellipse([cx + ex - 22, cy + 30, cx + ex + 22, cy + 52], fill=(255, 150, 120, 150))
# smile
draw.arc([cx - 55, cy - 10, cx + 55, cy + 75], 15, 165, fill=(120, 60, 10), width=13)

# --- arms ---
arm_col = (255, 190, 75)
draw.line([cx - 150, cy + 60, cx - 230, cy + 150], fill=arm_col, width=34)
draw.line([cx + 150, cy + 60, cx + 235, cy + 150], fill=arm_col, width=34)
for px_, py_ in ((cx - 230, cy + 150), (cx + 235, cy + 150)):
    draw.ellipse([px_ - 22, py_ - 22, px_ + 22, py_ + 22], fill=arm_col)

# --- coffee mug in right hand ---
mx, my = cx + 250, cy + 160
# shadow
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sh)
sd.ellipse([mx - 55, my + 88, mx + 75, my + 112], fill=(60, 40, 25, 80))
sh = sh.filter(ImageFilter.GaussianBlur(10))
img.paste(Image.new("RGB", (W, H), (120, 70, 40)), (0, 0), sh)
draw.rounded_rectangle([mx - 60, my - 60, mx + 60, my + 90], 26, fill=(255, 245, 240))
draw.rounded_rectangle([mx - 60, my - 60, mx + 60, my - 30], 26, fill=(255, 120, 110))
draw.ellipse([mx - 50, my - 62, mx + 50, my - 34], fill=(90, 60, 40))  # coffee top
draw.arc([mx + 55, my - 30, mx + 115, my + 40], 270, 90, fill=(255, 245, 240), width=18)
# steam
for sx, wob in ((mx - 25, 12), (mx + 5, -10), (mx + 30, 14)):
    pts = []
    for t in range(0, 61, 6):
        yy = my - 70 - t
        xx = sx + math.sin((t + sx) / 18) * wob
        pts.append((xx, yy))
    draw.line(pts, fill=(255, 255, 255, 170), width=9, joint="curve")

# --- confetti ---
conf_cols = [(255, 90, 90), (255, 170, 40), (90, 200, 120), (90, 160, 255),
             (200, 110, 230), (255, 220, 90), (60, 200, 200)]
spots = [(120, 130), (240, 70), (820, 110), (900, 260), (70, 330), (950, 480),
         (60, 560), (930, 640), (200, 250), (800, 350), (330, 60), (690, 70),
         (140, 470), (870, 470), (430, 940), (620, 950), (240, 910), (800, 900),
         (70, 800), (960, 810), (500, 60), (1000, 180), (20, 210)]
for i, (x, y) in enumerate(spots):
    c = conf_cols[i % len(conf_cols)]
    shape = i % 3
    ang = random.uniform(0, math.pi)
    if shape == 0:  # rectangle confetti
        dx, dy = 22 * math.cos(ang), 22 * math.sin(ang)
        draw.polygon([(x - dx, y - dy), (x + dx, y + dy), (x + dy, y - dx), (x - dy, y + dx)], fill=c)
    elif shape == 1:  # circle
        r = random.randint(9, 15)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c)
    else:  # triangle
        r = random.randint(12, 18)
        pts = [(x + r * math.cos(ang + k * 2.094), y + r * math.sin(ang + k * 2.094)) for k in range(3)]
        draw.polygon(pts, fill=c)

# --- sparkles (4-point stars) ---
for x, y, r in ((160, 620, 22), (880, 590, 26), (300, 880, 18), (740, 870, 20), (60, 90, 18)):
    draw.polygon([(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3),
                  (x, y + r), (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)],
                 fill=(255, 255, 235, 230))

# --- caption banner ---
draw.rounded_rectangle([262, 820, 762, 880], 40, fill=(255, 255, 255, 220))
draw.rounded_rectangle([262, 820, 762, 880], 40, outline=(255, 140, 105), width=5)
try:
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
except Exception:
    font = ImageFont.load_default()
tb = draw.textbbox((0, 0), "HAPPY DAY!", font=font)
draw.text((512 - (tb[2] - tb[0]) / 2 - tb[0], 850 - (tb[3] - tb[1]) / 2 - tb[1]),
          "HAPPY DAY!", font=font, fill=(255, 110, 90))

# soft vignette
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.ellipse([-150, -150, W + 150, H + 150], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(120))
img = Image.composite(img, Image.new("RGB", (W, H), (230, 130, 90)), vig)

img.save("/tmp/mfwork/ai-happy-01/entry.png", optimize=True)
import os
print("bytes:", os.path.getsize("/tmp/mfwork/ai-happy-01/entry.png"))
