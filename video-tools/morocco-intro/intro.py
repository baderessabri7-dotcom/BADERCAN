"""5-second documentary-style intro: fast archive montage of Morocco, ending on a title. 16:9."""
import math, sys, subprocess, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance

D, FD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
PREVIEW = sys.argv[4:]
W, H, FPS, DUR = 1920, 1080, 30, 5.0
NF = int(DUR * FPS)
RED = (226, 32, 36)

def ss(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eo(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def font(name, size, axes=None):
    f = ImageFont.truetype(FD + "/" + name, size, layout_engine=ImageFont.Layout.RAQM)
    if axes:
        try: f.set_variation_by_axes(axes)
        except Exception: pass
    return f
F_EN = font("Anton.ttf", 150)
F_AR = font("Cairo.ttf", 120, [900, 0])
F_TAG = font("Cairo.ttf", 44, [800, 0])
F_TYPE = font("SpecialElite.ttf", 50)
def is_ar(s): return any("؀" <= c <= "ۿ" for c in s)
def kw(s): return {"direction": "rtl", "language": "ar"} if is_ar(s) else {}
def text_box(txt, f, fill, box, pad):
    dd = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = dd.textbbox((0, 0), txt, font=f, **kw(txt))
    w, h = bb[2] - bb[0] + pad[0] * 2, bb[3] - bb[1] + pad[1] * 2 + 12
    im = Image.new("RGBA", (w, h), box)
    ImageDraw.Draw(im).text((pad[0] - bb[0], pad[1] - bb[1] + 6), txt, font=f, fill=fill, **kw(txt))
    return im
def wipe(im, p, rtl=False):
    if p >= 1: return im
    w = int(im.width * eo(p))
    if w <= 0: return None
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    box = (im.width - w, 0, im.width, im.height) if rtl else (0, 0, w, im.height)
    out.paste(im.crop(box), box[:2]); return out

# ---------- shots ----------
exec(open(D + "/shots.py").read())   # SHOTS = [(file, tag, focus(x,y frac), zoom_dir)], FINAL
def prep(path):
    im = Image.open(D + "/img/" + path).convert("RGB")
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.3)
    im = Image.merge("RGB", [g.point(lambda v: min(255, int(v * 1.03))), g, g.point(lambda v: int(v * 0.95))])
    # cover-fit at 1.15x of frame so we can zoom/pan
    s = max(W * 1.18 / im.width, H * 1.18 / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
imgs = {}
for sh in SHOTS:
    if sh["img"] not in imgs: imgs[sh["img"]] = prep(sh["img"])
# timeline: accelerating cuts
t = 0.0
for sh in SHOTS:
    sh["t0"] = t; t += sh["d"]; sh["t1"] = t
FINAL_T0 = SHOTS[-1]["t0"]
TAGS = {}

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.8 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2), 0.2, 1)[..., None]
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 14, (H // 2, W // 2)).astype(np.float32) for _ in range(8)]
def scratches(fi):
    r = np.random.default_rng(fi + 99)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for _ in range(r.integers(0, 3)):
        x = r.uniform(0, W); d.line([(x, 0), (x + r.uniform(-20, 20), H)], fill=int(r.uniform(60, 140)), width=1)
    for _ in range(r.integers(2, 10)):
        x, y, s_ = r.uniform(0, W), r.uniform(0, H), r.uniform(1, 4)
        d.ellipse([x, y, x + s_, y + s_ * r.uniform(1, 3)], fill=int(r.uniform(80, 200)))
    return np.asarray(im, np.float32)[..., None]

def circle_pts(cx, cy, rx, ry, p, seed=4):
    r = np.random.default_rng(seed); a0 = -math.pi * 0.6; span = 2 * math.pi + 0.5; n = 120; ph = r.uniform(0, 6, 2)
    out = []
    for i in range(int(n * eo(p)) + 1):
        u = i / n; a = a0 + span * u
        wob = 1 + 0.035 * math.sin(3 * a + ph[0]) + 0.05 * u
        out.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a) + 4 * math.sin(2 * a + ph[1])))
    return out

def render(fi):
    t = fi / FPS
    idx = max(i for i, sh in enumerate(SHOTS) if sh["t0"] <= t + 1e-6)
    sh = SHOTS[idx]; lt = t - sh["t0"]; u = lt / (sh["t1"] - sh["t0"])
    im = imgs[sh["img"]]
    final = idx == len(SHOTS) - 1
    z0, z1 = sh.get("zoom", (1.0, 1.08))
    z = z0 + (z1 - z0) * (ss(u) if final else u)
    fx, fy = sh.get("focus", (0.5, 0.5))
    dx, dy = sh.get("pan", (0, 0))
    cx = im.width * fx + dx * im.width * 0.04 * u
    cy = im.height * fy + dy * im.height * 0.04 * u
    shake = max(0, 1 - lt / 0.18)
    jx = math.sin(fi * 2.7) * 22 * shake; jy = math.cos(fi * 3.3) * 14 * shake
    s = z
    cw, ch = W / s, H / s
    cx = min(max(cx, cw / 2), im.width - cw / 2); cy = min(max(cy, ch / 2), im.height - ch / 2)
    box = (cx - cw / 2 - jx / s, cy - ch / 2 - jy / s, cx + cw / 2 - jx / s, cy + ch / 2 - jy / s)
    frame = im.transform((W, H), Image.EXTENT, box, Image.BICUBIC).convert("RGBA")

    if final:
        # darken + red circle + titles
        k = ss((lt - 0.15) / 0.4)
        arr = np.asarray(frame.convert("RGB"), np.float32) * (1 - 0.45 * k)
        frame = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        circ = sh.get("circle")
        if circ:
            p = (lt - 0.25) / 0.45
            if p > 0:
                # circle given in image fractions -> screen
                px = (circ[0] * im.width - box[0]) / (box[2] - box[0]) * W
                py = (circ[1] * im.height - box[1]) / (box[3] - box[1]) * H
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
                pts = circle_pts(px, py, circ[2] * z, circ[3] * z, p)
                if len(pts) > 1: od.line(pts, fill=RED + (255,), width=10, joint="curve")
                frame.alpha_composite(ov)
        y = 330
        for j, (txt, kind, ts) in enumerate(FINAL["titles"]):
            key = "f%d" % j
            if key not in TAGS:
                if kind == "en": TAGS[key] = text_box(txt, F_EN, (255, 255, 255), (0, 0, 0, 240), (48, 8))
                elif kind == "ar": TAGS[key] = text_box(txt, F_AR, (255, 255, 255), (0, 0, 0, 240), (48, 0))
                else: TAGS[key] = text_box(txt, F_TAG, (255, 255, 255), RED + (245,), (28, 0))
            ti = TAGS[key]
            a = (lt - ts) / 0.28
            if a > 0:
                wi = wipe(ti, a, rtl=is_ar(txt))
                if wi is not None: frame.alpha_composite(wi, ((W - ti.width) // 2, y))
            y += ti.height + 12
    else:
        tag = sh.get("tag")
        if tag:
            key = "t" + tag
            if key not in TAGS: TAGS[key] = text_box(tag, F_TAG, (255, 255, 255), RED + (240,), (26, 0))
            ti = TAGS[key]
            a = (lt - 0.03) / 0.12
            if a > 0:
                wi = wipe(ti, a, rtl=is_ar(tag))
                if wi is not None: frame.alpha_composite(wi, (W - 110 - ti.width, H - 150 - ti.height))
        yr = sh.get("year")
        if yr:
            key = "y" + yr
            if key not in TAGS: TAGS[key] = text_box(yr, F_TYPE, (240, 240, 240), (0, 0, 0, 210), (18, 4))
            frame.alpha_composite(TAGS[key], (110, 90))

    arr = np.asarray(frame.convert("RGB"), np.float32)
    flick = 1 + 0.04 * math.sin(fi * 2.1) + 0.025 * rng.standard_normal()
    arr = arr * VIG * flick
    g = GRAIN[fi % 8]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr += scratches(fi) * 0.5
    if idx > 0 and lt < 0.1:
        q = 1 - lt / 0.1
        sh_ = int(34 * q)
        arr[..., 0] = np.roll(arr[..., 0], sh_, axis=1); arr[..., 2] = np.roll(arr[..., 2], -sh_, axis=1)
        arr = arr + 200 * q ** 2
    fade = min(ss(t / 0.25), 1 - ss((t - (DUR - 0.35)) / 0.35))
    arr *= fade
    arr[:40] = 0; arr[-40:] = 0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

if PREVIEW:
    for tt in PREVIEW:
        render(int(float(tt) * FPS)).save(f"{OUT}_{float(tt):03.2f}.jpg", quality=85)
    sys.exit()
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    ff.stdin.write(render(fi).tobytes())
ff.stdin.close(); ff.wait()
