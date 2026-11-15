"""Documentary-style map animation: ship sails Morocco's Atlantic coast."""
import json, math, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

D = sys.argv[1]
OUT = sys.argv[2]
PREVIEW = len(sys.argv) > 3  # render only some frames as stills
FPS, DUR = 30, 20.0
NF = int(FPS * DUR)
OW, OH = 1080, 1920

meta = json.load(open(D + "/map.json"))
def P(lon, lat):
    return np.array([(lon - meta["LON0"]) * meta["S"] * meta["K"], (meta["LAT1"] - lat) * meta["S"]])

base = Image.open(D + "/map.png").convert("RGBA")
mips = [base]
for _ in range(3):
    m = mips[-1]
    mips.append(m.resize((m.width // 2, m.height // 2), Image.LANCZOS))

_b = mips[3].crop((60, 60, mips[3].width * 0.62, mips[3].height - 60)).resize((OW, OH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))
BG = Image.eval(_b.convert("RGB"), lambda v: int(v * 0.55)).convert("RGBA")
FD = D + "/fonts/"
def cinzel(size, wght=800):
    f = ImageFont.truetype(FD + "Cinzel.ttf", size)
    try:
        f.set_variation_by_axes([wght])
    except Exception:
        pass
    return f
def amiri(size):
    return ImageFont.truetype(FD + "Amiri-Bold.ttf", size, layout_engine=ImageFont.Layout.RAQM)

# ---------------- path ----------------
wp = [(-5.45, 35.95), (-5.95, 35.92), (-6.25, 35.55), (-6.75, 34.55), (-7.05, 34.12), (-7.65, 33.72),
      (-8.6, 33.38), (-9.45, 32.5), (-9.95, 31.6), (-10.0, 30.95), (-9.85, 30.42), (-10.4, 29.5),
      (-11.6, 28.55), (-12.9, 27.95), (-13.55, 27.2), (-14.7, 26.2), (-15.6, 24.9), (-16.2, 23.75), (-16.25, 23.45)]
pts = np.array([P(*w) for w in wp])
def catmull(p, n=60):
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)
path = catmull(pts)
seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
arc = np.concatenate([[0], np.cumsum(seg)])
arc /= arc[-1]
def at(s):
    s = min(max(s, 0), 1)
    return np.array([np.interp(s, arc, path[:, 0]), np.interp(s, arc, path[:, 1])])

cities = [("طنجة", "TANGER", (-5.80, 35.77)), ("الرباط", "RABAT", (-6.84, 34.02)),
          ("الدار البيضاء", "CASABLANCA", (-7.59, 33.57)), ("الصويرة", "ESSAOUIRA", (-9.77, 31.51)),
          ("أكادير", "AGADIR", (-9.60, 30.42)), ("العيون", "LAÂYOUNE", (-13.20, 27.15)),
          ("الداخلة", "DAKHLA", (-15.94, 23.70))]
city_s = []
for ar, la, ll in cities:
    c = P(*ll)
    i = np.argmin(np.linalg.norm(path - c, axis=1))
    city_s.append(arc[i])
city_s[0] = 0.0

# ---------------- timeline ----------------
def ss(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)
def ease_io(x):
    x = min(max(x, 0), 1)
    return 0.5 - 0.5 * math.cos(math.pi * x)

T_A, T_B, T_C, T_D = 3.0, 4.6, 16.4, 20.0
def ship_s(t):
    if t < T_B: return 0.0
    if t > T_C: return 1.0
    u = (t - T_B) / (T_C - T_B)
    # ease in/out but keep moving steadily
    return 0.85 * u + 0.15 * ease_io(u) if u > 0 else 0

WIDE = (P(-8.6, 29.3), 4.3, 1.0)
def follow(t):
    s = ship_s(t)
    look = at(s + 0.035) * 0.6 + at(s) * 0.4
    z = 1.05 + 0.25 * math.sin(math.pi * min(max((s - 0.45) / 0.55, 0), 1))  # pull back on long desert leg
    return (look, z, 1.5)
def cam(t):
    if t < T_A:
        u = t / T_A
        c, z, ti = WIDE
        return (c, z * (1 - 0.08 * u), ti)
    if t < T_B:
        u = ease_io((t - T_A) / (T_B - T_A))
        a, b = (WIDE[0], WIDE[1] * 0.92, 1.0), follow(t)
    elif t <= T_C:
        return follow(t)
    else:
        u = ease_io((t - T_C) / 2.6)
        a, b = follow(T_C), (P(-9.0, 29.6), 4.0, 1.12)
    c = a[0] * (1 - u) + b[0] * u
    z = math.exp(math.log(a[1]) * (1 - u) + math.log(b[1]) * u)
    ti = a[2] * (1 - u) + b[2] * u
    return (c, z, ti)

# ---------------- projection ----------------
def homography(src, dst):
    A, B = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    h = np.linalg.solve(np.array(A, float), np.array(B, float))
    return np.append(h, 1).reshape(3, 3)
OUTC = [(0, 0), (OW, 0), (OW, OH), (0, OH)]
def quad(c, z, ti):
    hw, hh = OW / 2 * z, OH / 2 * z
    k = ti - 1
    top = c[1] - hh * (1 + 0.55 * k)
    bot = c[1] + hh * (1 - 0.35 * k)
    return [(c[0] - hw * ti * 1.05, top), (c[0] + hw * ti * 1.05, top), (c[0] + hw, bot), (c[0] - hw, bot)]

def project(Hf, p):
    v = Hf @ np.array([p[0], p[1], 1.0])
    return v[:2] / v[2]

# ---------------- sprites ----------------
def make_ship(scale=4):
    w, h = 300 * scale, 300 * scale
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    S = scale
    # hull
    hull = [(40, 200), (260, 200), (240, 240), (70, 245)]
    d.polygon([(x * S, y * S) for x, y in hull], fill=(110, 58, 30))
    d.polygon([(x * S, y * S) for x, y in [(40, 200), (260, 200), (256, 212), (44, 212)]], fill=(190, 140, 60))
    d.polygon([(x * S, y * S) for x, y in [(230, 185), (265, 185), (260, 200), (232, 200)]], fill=(130, 70, 35))
    for gx in range(80, 230, 28):
        d.rectangle([gx * S, 220 * S, (gx + 8) * S, 227 * S], fill=(50, 25, 12))
    # masts
    for mx, top in [(105, 60), (150, 35), (200, 70)]:
        d.rectangle([(mx - 2.5) * S, top * S, (mx + 2.5) * S, 200 * S], fill=(80, 45, 25))
    # sails
    def sail(cx, y0, y1, wdt):
        pts = []
        for i in range(21):
            u = i / 20
            pts.append(((cx - wdt / 2 + wdt * u) * S, (y0 + 4 * math.sin(math.pi * u)) * S))
        for i in range(21):
            u = 1 - i / 20
            pts.append(((cx - wdt / 2 + wdt * u) * S, (y1 + 9 * math.sin(math.pi * u)) * S))
        d.polygon(pts, fill=(246, 240, 225), outline=(150, 130, 100))
        d.line([((cx - wdt / 2 + 6) * S, (y1 + 4) * S), ((cx + wdt / 2 - 6) * S, (y1 + 4) * S)], fill=(215, 205, 185), width=3 * S)
    for mx, top in [(105, 60), (150, 35), (200, 70)]:
        sail(mx, top + 12, top + 62, 64 if mx != 150 else 76)
        sail(mx, top + 70, top + 118, 72 if mx != 150 else 86)
    # jib
    d.polygon([(x * S, y * S) for x, y in [(207, 80), (275, 185), (208, 185)]], fill=(240, 232, 214), outline=(150, 130, 100))
    # Moroccan flag
    fx, fy = 152, 12
    d.rectangle([(fx) * S, fy * S, (fx + 38) * S, (fy + 25) * S], fill=(193, 39, 45))
    cx, cy, r = fx + 19, fy + 12.5, 8
    star = [(cx + r * math.sin(math.radians(a * 144)), cy - r * math.cos(math.radians(a * 144))) for a in range(5)]
    d.line([(x * S, y * S) for x, y in star + [star[0]]], fill=(0, 98, 51), width=int(1.8 * S))
    d.rectangle([(fx - 2) * S, fy * S, (fx + 1) * S, 40 * S], fill=(80, 45, 25))
    im = im.resize((w // scale, h // scale), Image.LANCZOS)
    return im
SHIP = make_ship()
SHIP_SHADOW = Image.new("RGBA", SHIP.size, (0, 0, 0, 0))
ImageDraw.Draw(SHIP_SHADOW).ellipse([30, 225, 280, 262], fill=(40, 30, 20, 110))
SHIP_SHADOW = SHIP_SHADOW.filter(ImageFilter.GaussianBlur(8))

def make_pin(scale=4):
    S = scale
    im = Image.new("RGBA", (80 * S, 110 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([22 * S, 96 * S, 58 * S, 108 * S], fill=(30, 20, 10, 90))
    d.polygon([(16 * S, 48 * S), (64 * S, 48 * S), (40 * S, 102 * S)], fill=(160, 28, 34))
    d.ellipse([10 * S, 10 * S, 70 * S, 70 * S], fill=(193, 39, 45), outline=(110, 20, 25), width=3 * S)
    d.ellipse([27 * S, 27 * S, 53 * S, 53 * S], fill=(250, 240, 220))
    return im.resize((80, 110), Image.LANCZOS)
PIN = make_pin()

def gold_text(text, font, pad=40, shadow=True, arabic=False):
    dummy = ImageDraw.Draw(Image.new("L", (1, 1)))
    kw = {"direction": "rtl", "language": "ar"} if arabic else {}
    bb = dummy.textbbox((0, 0), text, font=font, **kw)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((pad - bb[0], pad - bb[1]), text, font=font, fill=255, **kw)
    # vertical gold gradient
    y = np.linspace(0, 1, h)[:, None]
    top = np.array([255, 232, 120]); mid = np.array([245, 190, 40]); bot = np.array([200, 120, 10])
    col = np.where(y[..., None] < 0.5, top + (mid - top) * (y[..., None] / 0.5), mid + (bot - mid) * ((y[..., None] - 0.5) / 0.5))
    col = np.broadcast_to(col, (h, w, 3)).astype(np.uint8)
    goldim = Image.fromarray(col, "RGB").convert("RGBA")
    goldim.putalpha(mask)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", (w, h), (20, 10, 0, 0))
        sm = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(6))
        sh.putalpha(sm.point(lambda v: min(255, int(v * 1.3))))
        out.alpha_composite(sh, (0, 6))
        outline = Image.new("RGBA", (w, h), (70, 35, 0, 255))
        outline.putalpha(mask.filter(ImageFilter.MaxFilter(5)))
        out.alpha_composite(outline)
    out.alpha_composite(goldim)
    return out

def cream_text(text, font, fill=(250, 240, 220), arabic=False):
    dummy = ImageDraw.Draw(Image.new("L", (1, 1)))
    kw = {"direction": "rtl", "language": "ar"} if arabic else {}
    bb = dummy.textbbox((0, 0), text, font=font, **kw)
    pad = 24
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), text, font=font, fill=255, **kw)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.9)))
    im.alpha_composite(sh, (0, 3))
    fg = Image.new("RGBA", (w, h), fill + (255,)); fg.putalpha(m)
    im.alpha_composite(fg)
    return im

TITLE_AR = gold_text("المغرب", amiri(230), arabic=True)
TITLE_EN = gold_text("MOROCCO", cinzel(150, 900))
SUB = cream_text("A JOURNEY ALONG THE ATLANTIC COAST", cinzel(38, 600))
OUT_AR = gold_text("من طنجة إلى الداخلة", amiri(120), arabic=True)
OUT_EN = cream_text("FROM TANGIER TO DAKHLA", cinzel(50, 700))
CAP = [(gold_text(ar, amiri(150 if len(ar) < 8 else 120), arabic=True), cream_text(la, cinzel(56, 700))) for ar, la, _ in cities]

def paste_center(dst, im, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------------- grading assets ----------------
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
vig = 1 - 0.55 * np.clip(((xx - OW / 2) / (OW * 0.62)) ** 2 + ((yy - OH / 2) / (OH * 0.58)) ** 2, 0, 1.4) ** 1.4
vig = np.clip(vig, 0, 1)[..., None]
dof_top = np.clip((820 - yy) / 520, 0, 1) ** 1.2
dof_bot = np.clip((yy - 1500) / 420, 0, 1) ** 1.2 * 0.7
DOF = np.clip(dof_top + dof_bot, 0, 1)[..., None]
topdark = np.clip((520 - yy) / 520, 0, 1)[..., None] ** 1.5 * 0.55
botdark = np.clip((yy - 1300) / 620, 0, 1)[..., None] ** 1.5 * 0.6
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 7, (OH // 2, OW // 2)).astype(np.float32) for _ in range(6)]

# ---------------- render ----------------
def render(fi):
    t = fi / FPS
    c, z, ti = cam(t)
    q = quad(c, z, ti)
    lvl = 0
    while lvl < 3 and z / (2 ** lvl) > 1.6:
        lvl += 1
    src = mips[lvl]
    sc = 2 ** lvl
    qs = [(x / sc, y / sc) for x, y in q]
    Hinv = homography(OUTC, qs)  # output -> source(level)
    coeffs = (Hinv / Hinv[2, 2]).flatten()[:8]
    frame = src.transform((OW, OH), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    bgf = BG.copy(); bgf.alpha_composite(frame); frame = bgf
    Hf = homography(q, OUTC)  # source(full) -> output

    ov = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    s = ship_s(t)
    # trail
    if s > 0.001:
        n = max(2, int(s * 900))
        ssamp = np.linspace(0, s, n)
        sp = np.array([project(Hf, at(v)) for v in ssamp])
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
        dash = 34
        for i in range(len(sp) - 1):
            if (L[i] // dash) % 2 == 0:
                yv = sp[i][1]
                wdt = int(np.clip(4 + 7 * (yv / OH), 3, 12))
                od.line([tuple(sp[i]), tuple(sp[i + 1])], fill=(150, 30, 30, 235), width=wdt)
    # pins
    for k, cs in enumerate(city_s):
        if t >= T_B - 0.3 and s >= cs - 0.002:
            # time since reached
            if k == 0:
                t0 = T_B - 0.3
            else:
                # find time when ship_s reached cs
                lo, hi = T_B, T_C
                for _ in range(30):
                    mid = (lo + hi) / 2
                    if ship_s(mid) < cs: lo = mid
                    else: hi = mid
                t0 = hi
            dt = t - t0
            bounce = 1 + 0.35 * math.exp(-dt * 5) * math.sin(dt * 18) if dt < 1.2 else 1
            drop = max(0, 1 - dt / 0.25)
            pp = project(Hf, P(*cities[k][2]))
            psc = np.clip(0.9 + 1.0 * (pp[1] / OH), 0.7, 1.8) / max(0.6, min(z, 2.0)) ** 0.5
            pin = PIN.resize((int(80 * psc * bounce), int(110 * psc * bounce)), Image.LANCZOS)
            ov.alpha_composite(pin, (int(pp[0] - pin.width / 2), int(pp[1] - pin.height * 0.95 - drop * 120)))
    # ship
    if t >= T_A - 0.5:
        p = project(Hf, at(s))
        p2 = project(Hf, at(s + 0.01))
        facing_left = p2[0] < p[0] - 0.5
        ssc = np.clip(0.55 + 0.9 * (p[1] / OH), 0.4, 1.6) / max(0.7, z) ** 0.8
        appear = ss((t - (T_A - 0.5)) / 0.8)
        bob = math.sin(t * 3.1) * 3
        sh = SHIP_SHADOW
        sp_ = SHIP
        if facing_left:
            sp_ = sp_.transpose(Image.FLIP_LEFT_RIGHT); sh = sh.transpose(Image.FLIP_LEFT_RIGHT)
        sp_ = sp_.rotate(bob, resample=Image.BICUBIC, center=(150, 240))
        size = int(300 * ssc * appear)
        if size > 4:
            sh2 = sh.resize((size, size), Image.LANCZOS)
            sp2 = sp_.resize((size, size), Image.LANCZOS)
            yb = math.sin(t * 2.3) * 4 * ssc
            ov.alpha_composite(sh2, (int(p[0] - size / 2), int(p[1] - size * 0.80)))
            ov.alpha_composite(sp2, (int(p[0] - size / 2), int(p[1] - size * 0.80 + yb)))

    frame = frame.convert("RGBA")
    frame.alpha_composite(ov)
    # depth of field (tilt-shift) scaled by tilt
    k = np.clip((ti - 1) / 0.5, 0, 1)
    arr = np.asarray(frame.convert("RGB"), np.float32)
    if k > 0.02:
        small = frame.convert("RGB").resize((OW // 3, OH // 3), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))
        bl = np.asarray(small.resize((OW, OH), Image.BILINEAR), np.float32)
        m = DOF * k
        arr = arr * (1 - m) + bl * m
    # grade: warm, contrast, vignette, darken top/bottom for text
    arr = (arr - 128) * 1.08 + 128
    arr *= np.array([1.04, 1.0, 0.92], np.float32)
    arr *= vig
    arr *= (1 - topdark) * (1 - botdark)
    intro = 1 - ss((t - T_A + 0.3) / 0.8)
    if intro > 0:
        band = np.clip(1 - np.abs(yy - 520) / 380, 0, 1)[..., None] * 0.6 * intro
        arr *= (1 - band)
    g = GRAIN[fi % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr += g
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    # ---- titles ----
    # intro big title
    a_in = ss((t - 0.3) / 0.8)
    if t < T_B + 0.2:
        a = a_in * (1 - ss((t - T_A + 0.2) / 0.8))
        paste_center(frame, TITLE_AR, OW / 2, 330 - 20 * (1 - a_in), 1.0, a)
        paste_center(frame, TITLE_EN, OW / 2, 560, 1.0, a)
        paste_center(frame, SUB, OW / 2, 690, 1.0, a * ss((t - 0.9) / 0.8))
    # persistent header during journey
    if T_A <= t < T_D:
        a = ss((t - T_A - 0.4) / 0.6) * (1 - ss((t - T_C - 0.2) / 0.5))
        paste_center(frame, TITLE_EN, OW / 2, 210, 0.62, a)
        paste_center(frame, TITLE_AR, OW / 2, 110, 0.42, a)
    # city captions
    for k, cs in enumerate(city_s):
        if k == 0:
            t0 = T_B - 0.1
        else:
            lo, hi = T_B, T_C
            for _ in range(30):
                mid = (lo + hi) / 2
                if ship_s(mid) < cs: lo = mid
                else: hi = mid
            t0 = hi
        dur = 1.5
        if k + 1 < len(city_s):
            lo, hi = T_B, T_C
            for _ in range(30):
                mid = (lo + hi) / 2
                if ship_s(mid) < city_s[k + 1]: lo = mid
                else: hi = mid
            dur = min(1.5, hi - t0 - 0.05)
        dt = t - t0
        if 0 <= dt <= dur:
            a = ss(dt / 0.25) * (1 - ss((dt - dur + 0.3) / 0.3))
            off = 40 * (1 - ss(dt / 0.3))
            ar, la = CAP[k]
            paste_center(frame, ar, OW / 2, 1590 + off, 1.0, a)
            paste_center(frame, la, OW / 2, 1730 + off, 1.0, a)
    # outro
    if t > T_C + 1.0:
        a = ss((t - T_C - 1.0) / 0.8)
        paste_center(frame, OUT_AR, OW / 2, 250 - 30 * (1 - a), 1.0, a)
        paste_center(frame, OUT_EN, OW / 2, 400, 1.0, a)
        paste_center(frame, TITLE_EN, OW / 2, 1700, 0.75, ss((t - T_C - 1.6) / 0.8))
    # fades
    fade = min(ss(t / 0.6), 1 - ss((t - (DUR - 0.5)) / 0.5))
    rgb = frame.convert("RGB")
    if fade < 1:
        rgb = Image.blend(Image.new("RGB", (OW, OH)), rgb, fade)
    return rgb

if PREVIEW:
    for t in [1.5, 4.7, 18.8]:
        render(int(t * FPS)).save(f"{OUT}_{t:04.1f}.jpg", quality=85)
    sys.exit()

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                       "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    ff.stdin.write(render(fi).tobytes())
    if fi % 60 == 0:
        print("frame", fi, flush=True)
ff.stdin.close(); ff.wait()
