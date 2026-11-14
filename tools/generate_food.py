#!/usr/bin/env python3
"""Generate entry.png: a top-down ramen bowl, drawn with PIL."""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
CX = CY = 512


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def main():
    random.seed(7)
    img = Image.new("RGB", (W, H), (28, 18, 14))
    d = ImageDraw.Draw(img)

    # ---------- wooden table background ----------
    for y in range(H):
        t = y / H
        base = lerp((52, 30, 20), (30, 17, 12), t)
        d.line([(0, y), (W, y)], fill=base)
    rnd = random.Random(42)
    for _ in range(260):  # wood grain streaks
        y = rnd.randint(0, H - 1)
        x = rnd.randint(0, W - 1)
        ln = rnd.randint(60, 380)
        shade = rnd.randint(-14, 14)
        c = (52 + shade, 30 + shade // 2, 20 + shade // 3)
        d.line([(x, y), (x + ln, y + rnd.randint(-3, 3))], fill=c, width=rnd.choice([1, 1, 2]))

    # ---------- bowl ----------
    bowl_r = 452          # outer ceramic rim
    rim_w = 46            # ceramic thickness
    inner_r = bowl_r - rim_w

    # shadow under bowl
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).ellipse([CX - bowl_r - 26, CY - bowl_r - 14, CX + bowl_r + 26, CY + bowl_r + 26], fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    img.paste(Image.new("RGB", (W, H), (8, 4, 3)), (0, 0), sh)

    # ceramic outer ring
    d.ellipse([CX - bowl_r, CY - bowl_r, CX + bowl_r, CY + bowl_r], fill=(232, 226, 214))
    d.ellipse([CX - bowl_r + 6, CY - bowl_r + 6, CX + bowl_r - 6, CY + bowl_r - 6], fill=(214, 205, 190))
    # subtle rim shading (bottom-right darker)
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.ellipse([CX - bowl_r, CY - bowl_r, CX + bowl_r, CY + bowl_r], fill=(0, 0, 0, 0))
    rd.arc([CX - bowl_r + 3, CY - bowl_r + 3, CX + bowl_r - 3, CY + bowl_r - 3], 20, 160, fill=(120, 108, 92, 200), width=10)
    rd.arc([CX - bowl_r + 8, CY - bowl_r + 8, CX + bowl_r - 8, CY + bowl_r - 8], 300, 80, fill=(255, 255, 248, 180), width=8)
    img.paste(rim, (0, 0), rim)

    # inner bowl wall (dark ring inside ceramic)
    d.ellipse([CX - inner_r, CY - inner_r, CX + inner_r, CY + inner_r], fill=(60, 44, 36))

    # ---------- broth: radial gradient amber ----------
    bro = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(bro)
    center = (198, 122, 44)
    edge = (138, 78, 28)
    for i in range(inner_r, 0, -1):
        t = i / inner_r
        c = lerp(center, edge, t ** 1.4)
        bd.ellipse([CX - i, CY - i, CX + i, CY + i], fill=c)
    # mask to inner circle
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([CX - inner_r, CY - inner_r, CX + inner_r, CY + inner_r], fill=255)
    img.paste(bro, (0, 0), mask)

    # glossy broth highlight (top-left specular)
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gl)
    gd.ellipse([CX - inner_r + 60, CY - inner_r + 70, CX + 40, CY + 130], fill=(255, 236, 190, 60))
    gd.ellipse([CX - 260, CY - 320, CX + 60, CY - 40], fill=(255, 244, 210, 70))
    gl = gl.filter(ImageFilter.GaussianBlur(30))
    img.paste(gl, (0, 0), gl)

    # ---------- noodles: clean nested arcs in a swirl ----------
    nood = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(nood)
    rnd_n = random.Random(11)
    for ring in range(7):
        rr0 = 60 + ring * 47
        for s in range(7):
            ph = rnd_n.uniform(0, math.tau)
            amp = rnd_n.uniform(10, 20)
            pts = []
            for k in range(0, 361, 5):
                th = math.radians(k)
                rr = rr0 + amp * math.sin(2.3 * th + ph)
                x = CX + rr * math.cos(th + ph)
                y = CY + rr * math.sin(th + ph) * 0.96
                pts.append((x, y))
            shade = rnd_n.randint(-16, 14)
            col = (238 + shade, 186 + shade, 80 + shade // 2)
            nd.line(pts, fill=col, width=14)
            nd.line(pts, fill=(252, 218, 140, 150), width=5)
    nood = nood.filter(ImageFilter.GaussianBlur(0.8))
    img.paste(nood, (0, 0), nood)

    # ---------- egg halves ----------
    def egg(cx, cy, rx, ry, ang):
        e = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(e)
        ed.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(246, 244, 236))     # white
        ed.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=(214, 206, 190), width=3)
        yx, yy = cx + rx * 0.12 * math.cos(ang), cy - ry * 0.15 * math.sin(ang)
        ed.ellipse([yx - rx * 0.62, yy - ry * 0.62, yx + rx * 0.62, yy + ry * 0.62], fill=(238, 150, 34))   # yolk
        ed.ellipse([yx - rx * 0.40, yy - ry * 0.40, yx + rx * 0.40, yy + ry * 0.40], fill=(247, 176, 56))
        ed.ellipse([yx - rx * 0.26, yy - ry * 0.30, yx - rx * 0.02, yy - ry * 0.08], fill=(255, 224, 150))  # shine
        ed.ellipse([yx - rx * 0.30, yy + ry * 0.16, yx + rx * 0.28, yy + ry * 0.42], fill=(196, 108, 20))   # cured edge
        img.paste(e, (0, 0), e)

    egg(352, 560, 92, 108, 0.4)
    egg(648, 470, 88, 104, 0.2)

    # ---------- chashu (braised pork) slice ----------
    def chashu(cx, cy, r, ang):
        chs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd2 = ImageDraw.Draw(chs)
        cd2.ellipse([cx - r, cy - r * 0.9, cx + r, cy + r * 0.9], fill=(150, 84, 54))
        cd2.ellipse([cx - r + 8, cy - r * 0.9 + 7, cx + r - 8, cy + r * 0.9 - 7], fill=(178, 110, 72))
        cd2.ellipse([cx - r * 0.5, cy - r * 0.42, cx + r * 0.5, cy + r * 0.42], fill=(214, 158, 118))  # marbled fat
        for i in range(4):  # fat swirls
            cd2.arc([cx - r + 20 + i * 14, cy - r * 0.7 + i * 16, cx + r - 20 - i * 14, cy + r * 0.7 - i * 16],
                    30 + i * 20, 220 + i * 15, fill=(206, 150, 108), width=5)
        chs = chs.rotate(math.degrees(ang), resample=Image.BICUBIC)
        img.paste(chs, (0, 0), chs)

    chashu(548, 690, 78, 0.3)

    # ---------- scallion rings (fresh sprinkle, last before nori) ----------
    rnds2 = random.Random(5)
    for _ in range(52):
        ang = rnds2.uniform(0, math.tau)
        rr = rnds2.uniform(0.2, 0.95) * (inner_r - 45)
        x = CX + rr * math.cos(ang)
        y = CY + rr * math.sin(ang) * 0.97
        if (x - 352) ** 2 + (y - 560) ** 2 < 150 ** 2:
            continue
        if (x - 648) ** 2 + (y - 470) ** 2 < 145 ** 2:
            continue
        r = rnds2.randint(8, 15)
        g = rnds2.randint(120, 170)
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=(58, g, 60))
        d.ellipse([x - r + 4, y - r * 0.8 + 3, x + r - 4, y + r * 0.8 - 3], fill=(128, 198, 128))
        d.ellipse([x - r + 7, y - r * 0.8 + 5, x + r - 7, y + r * 0.8 - 5], fill=(66, 138, 82))

    # ---------- chili oil droplets ----------
    for _ in range(46):
        ang = random.uniform(0, math.tau)
        rr = random.uniform(0.2, 0.9) * (inner_r - 50)
        x = CX + rr * math.cos(ang)
        y = CY + rr * math.sin(ang)
        if (x - 352) ** 2 + (y - 560) ** 2 < 165 ** 2:
            continue
        if (x - 648) ** 2 + (y - 470) ** 2 < 160 ** 2:
            continue
        r = random.randint(4, 12)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 68, 22))
        d.ellipse([x - r + 2, y - r + 2, x + r - 2, y + r - 2], fill=(224, 96, 34))

    # ---------- nori sheets (drawn last so they sit on top, tucked at rim) ----------
    nor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nod = ImageDraw.Draw(nor)

    def nori(cx, cy, w, h, ang):
        n = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
        nnd = ImageDraw.Draw(n)
        nnd.rectangle([10, 10, w + 10, h + 10], fill=(26, 58, 42))
        nnd.rectangle([10, 10, w + 10, h + 10], outline=(12, 30, 20), width=4)
        rndt = random.Random(int(cx))
        for i in range(7):  # texture flecks
            yy = 18 + i * (h / 7)
            nnd.line([(14, yy), (w + 6, yy + rndt.randint(-4, 4))], fill=(40, 82, 58), width=2)
        for _ in range(18):
            fx = rndt.randint(14, w + 6)
            fy = rndt.randint(14, h + 6)
            nnd.point((fx, fy), fill=(52, 100, 70))
        n = n.rotate(ang, expand=True, resample=Image.BICUBIC)
        nor.paste(n, (int(cx - n.width / 2), int(cy - n.height / 2)), n)

    nori(748, 668, 170, 200, 24)
    nori(272, 340, 160, 190, -18)
    img.paste(nor, (0, 0), nor)

    # ---------- chili oil droplets ----------
    for _ in range(46):
        ang = random.uniform(0, math.tau)
        rr = random.uniform(0.2, 0.9) * (inner_r - 50)
        x = CX + rr * math.cos(ang)
        y = CY + rr * math.sin(ang)
        r = random.randint(4, 12)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 68, 22))
        d.ellipse([x - r + 2, y - r + 2, x + r - 2, y + r - 2], fill=(224, 96, 34))

    # ---------- chopsticks resting across the rim ----------
    ch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(ch)
    cd.line([(150, 170), (880, 60)], fill=(140, 84, 40, 255), width=16)
    cd.line([(158, 196), (888, 86)], fill=(122, 70, 32, 255), width=15)
    ch = ch.filter(ImageFilter.GaussianBlur(1))
    img.paste(ch, (0, 0), ch)

    # ---------- steam wisps ----------
    st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    rnds = random.Random(99)
    for _ in range(9):
        x0 = rnds.randint(CX - 260, CX + 260)
        y0 = rnds.randint(CY - 200, CY + 60)
        for k in range(10):
            rr = 22 + k * 7
            a = max(0, 26 - k * 3)
            xx = x0 + math.sin(k * 0.9) * 40
            yy = y0 - k * 34
            sd.ellipse([xx - rr, yy - rr * 0.8, xx + rr, yy + rr * 0.8], fill=(255, 250, 240, a))
    st = st.filter(ImageFilter.GaussianBlur(16))
    img.paste(st, (0, 0), st)

    # ---------- vignette ----------
    vg = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vg)
    vd.rectangle([0, 0, W, H], fill=120)
    vd.ellipse([-160, -160, W + 160, H + 160], fill=0)
    vg = vg.filter(ImageFilter.GaussianBlur(120))
    img.paste(Image.new("RGB", (W, H), (10, 5, 3)), (0, 0), vg)

    img.save("/tmp/mfwork/food-picture-01/entry.png", optimize=True)
    print("saved", img.size)


if __name__ == "__main__":
    main()
