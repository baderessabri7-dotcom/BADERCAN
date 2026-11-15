"""Netflix-style documentary edit: archive images, red marker circles, headline boxes. 16:9."""
import math, sys, subprocess, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageEnhance, ImageChops

D = sys.argv[1]            # jr dir
FD = sys.argv[2]           # fonts dir
OUT = sys.argv[3]
PREVIEW = sys.argv[4:]     # list of times
W, H, FPS = 1920, 1080, 30
exec(open(D + "/scenes.py").read())   # defines SCENES, DUR
NF = int(DUR * FPS)
rng = np.random.default_rng(5)

def ss(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eo(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3

def font(name, size, wght=None):
    f = ImageFont.truetype(FD + "/" + name, size, layout_engine=ImageFont.Layout.RAQM)
    if wght:
        try: f.set_variation_by_axes([wght] if "Cairo" not in name else [wght, 0])
        except Exception:
            try: f.set_variation_by_axes([wght])
            except Exception: pass
    return f
F_EN = font("Anton.ttf", 96)
F_AR = font("Cairo.ttf", 84, 900)
F_AR_S = font("Cairo.ttf", 46, 800)
F_NOTE_AR = font("Marhey.ttf", 64, 700)
F_NOTE_EN = font("PermanentMarker.ttf", 54)
F_TYPE = font("SpecialElite.ttf", 34)
RED = (226, 32, 36)

def is_ar(s): return any("؀" <= c <= "ۿ" for c in s)
def tkw(s): return {"direction": "rtl", "language": "ar"} if is_ar(s) else {}

# ---------- image prep ----------
def prep(path, kind):
    im = Image.open(D + "/img/" + path).convert("RGB")
    if kind == "photo":
        g = ImageOps.grayscale(im)
        g = ImageOps.autocontrast(g, cutoff=1)
        g = ImageEnhance.Contrast(g).enhance(1.25)
        im = Image.merge("RGB", [g.point(lambda v: min(255, int(v * 1.02))), g, g.point(lambda v: int(v * 0.96))])
    elif kind == "letter":
        im = ImageEnhance.Color(im).enhance(0.55)
        im = ImageEnhance.Contrast(im).enhance(1.15)
    # upscale small images for clean zooms
    if im.width < 1800:
        f = 1800 / im.width
        im = im.resize((int(im.width * f), int(im.height * f)), Image.LANCZOS)
    return im

for sc in SCENES:
    if sc.get("card"):
        sc["im"] = None; sc["k"] = 1.0; continue
    sc["im"] = prep(sc["img"], sc.get("kind", "photo"))
    k = sc["im"].width / Image.open(D + "/img/" + sc["img"]).width
    sc["k"] = k  # coordinates in config are in original pixels
    bg = ImageOps.fit(sc["im"], (W // 4, H // 4)).filter(ImageFilter.GaussianBlur(6))
    sc["bg"] = ImageEnhance.Brightness(bg.resize((W, H), Image.BILINEAR)).enhance(0.45)

# ---------- text pieces ----------
def text_img(txt, f, fill=(255, 255, 255), box=None, pad=(28, 10), shadow=False):
    dd = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = dd.textbbox((0, 0), txt, font=f, **tkw(txt))
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2 + 14
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if box: d.rectangle([0, 0, w, h], fill=box)
    if shadow:
        sm = Image.new("L", (w, h), 0)
        ImageDraw.Draw(sm).text((pad[0] - bb[0], pad[1] - bb[1] + 7), txt, font=f, fill=200, **tkw(txt))
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 255)); sh.putalpha(sm.filter(ImageFilter.GaussianBlur(5)))
        im.alpha_composite(sh, (3, 4))
    d.text((pad[0] - bb[0], pad[1] - bb[1] + 7), txt, font=f, fill=fill, **tkw(txt))
    return im

def wipe(im, p, rtl=False):
    """reveal image horizontally by fraction p"""
    if p >= 1: return im
    w = int(im.width * eo(p))
    if w <= 0: return None
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    box = (im.width - w, 0, im.width, im.height) if rtl else (0, 0, w, im.height)
    out.paste(im.crop(box), box[:2])
    return out

# ---------- marker shapes ----------
def circle_pts(cx, cy, rx, ry, seed, p):
    r = np.random.default_rng(seed)
    a0 = -math.pi * 0.62 + r.uniform(-0.2, 0.2)
    span = 2 * math.pi + 0.55
    n = 140
    ph = r.uniform(0, 6, 3)
    pts = []
    for i in range(int(n * eo(p)) + 1):
        u = i / n
        a = a0 + span * u
        wob = 1 + 0.035 * math.sin(3 * a + ph[0]) + 0.02 * math.sin(5 * a + ph[1]) + 0.06 * u  # spiral out a bit
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a) + 4 * math.sin(2 * a + ph[2])))
    return pts

def arrow_pts(x0, y0, x1, y1, bend, p):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    L = math.hypot(nx, ny) or 1
    cx, cy = mx + nx / L * bend, my + ny / L * bend
    pts = []
    n = 60
    for i in range(int(n * eo(p)) + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u * u * y1))
    return pts

def draw_stroke(d, pts, w):
    if len(pts) < 2: return
    d.line(pts, fill=RED + (255,), width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=RED + (255,))

# ---------- grading assets ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.75 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2), 0.25, 1)[..., None]
GRAIN = [rng.normal(0, 13, (H // 2, W // 2)).astype(np.float32) for _ in range(8)]
def scratches(fi):
    r = np.random.default_rng(fi)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for _ in range(r.integers(0, 3)):
        x = r.uniform(0, W); d.line([(x, 0), (x + r.uniform(-20, 20), H)], fill=int(r.uniform(60, 140)), width=1)
    for _ in range(r.integers(2, 9)):
        x, y, s = r.uniform(0, W), r.uniform(0, H), r.uniform(1, 4)
        d.ellipse([x, y, x + s, y + s * r.uniform(1, 3)], fill=int(r.uniform(80, 200)))
    return np.asarray(im, np.float32)[..., None]

# ---------- render ----------
def scene_at(t):
    for i, sc in enumerate(SCENES):
        if sc["t0"] <= t < sc["t1"]: return i, sc
    return len(SCENES) - 1, SCENES[-1]

def fractal(h, w, seed):
    r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for sc_ in (240, 120, 60, 30):
        sm = r.random((h // sc_ + 2, w // sc_ + 2)).astype(np.float32)
        acc += amp * np.asarray(Image.fromarray((sm * 255).astype(np.uint8)).resize((w + 2 * sc_, h + 2 * sc_), Image.BICUBIC), np.float32)[:h, :w] / 255
        tot += amp; amp *= 0.55
    return acc / tot
SM1 = fractal(H * 2, W, 1); SM2 = fractal(H * 2, W, 2)
SMASK = (np.clip(1 - np.abs(xx - W / 2) / (W * 0.45), 0, 1) ** 1.5 * np.clip((yy + 200) / H, 0, 1) ** 1.2)
def smoke(t, strength=1.0):
    o1 = int(t * 70) % H; o2 = int(t * 40 + 300) % H
    a = SM1[H - o1:2 * H - o1]; b = SM2[H - o2:2 * H - o2]
    v = np.clip((a * 0.6 + b * 0.6 - 0.55) * 2.6, 0, 1) * SMASK * strength
    arr = np.stack([v * 200 + 8, v * 196 + 7, v * 190 + 7], -1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
F_SUB = font("Cairo.ttf", 44, 700)
F_BIG = font("Anton.ttf", 230)
SUB_CACHE = {}
def subtitle(frame, t):
    for (a, b, txt) in SUBS:
        if a <= t < b:
            al = ss((t - a) / 0.15) * (1 - ss((t - b + 0.15) / 0.15))
            if txt not in SUB_CACHE:
                SUB_CACHE[txt] = text_img(txt, F_SUB, fill=(255, 255, 255), box=(0, 0, 0, 170), pad=(26, 0))
            im = SUB_CACHE[txt]
            if al < 1:
                im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * al)))
            frame.alpha_composite(im, ((W - im.width) // 2, H - 95 - im.height))

def render(fi):
    t = fi / FPS
    si, sc = scene_at(t)
    lt = t - sc["t0"]
    dur = sc["t1"] - sc["t0"]
    u = lt / dur
    im = sc["im"]; k = sc["k"]
    if sc.get("card"):
        return render_card(fi, t, si, sc, lt)
    # camera: base scale
    if sc.get("fit") == "height":
        base = H * sc.get("fill", 1.1) / im.height
    elif sc.get("fit") == "width":
        base = W * sc.get("fill", 0.95) / im.width
    else:
        base = max(W / im.width, H / im.height)
    z0, z1 = sc.get("zoom", (1.0, 1.12))
    s = base * (z0 + (z1 - z0) * ss(u * 0.85 + 0.15 * u))
    fx0, fy0 = [v * k for v in sc["focus"][0]]
    fx1, fy1 = [v * k for v in sc["focus"][1]]
    e = ss(u)
    fx, fy = fx0 + (fx1 - fx0) * e, fy0 + (fy1 - fy0) * e
    # shake on scene start
    sh = max(0, 1 - lt / 0.35)
    jx = math.sin(fi * 2.7) * 14 * sh + math.sin(fi * 0.37) * 1.5
    jy = math.cos(fi * 3.1) * 10 * sh + math.cos(fi * 0.29) * 1.5
    ox, oy = W / 2 + jx, H / 2 + jy
    # clamp so cover images don't show edges
    if sc.get("fit") not in ("height", "width"):
        fx = min(max(fx, (W / 2) / s), im.width - (W / 2) / s)
        fy = min(max(fy, (H / 2) / s), im.height - (H / 2) / s)
    def S(px, py):  # original-pixel coords -> screen
        return ((px * k - fx) * s + ox, (py * k - fy) * s + oy)
    inv = (1 / s, 0, fx - ox / s, 0, 1 / s, fy - oy / s)
    frame = sc["bg"].copy().convert("RGBA")
    fg = im.convert("RGBA").transform((W, H), Image.AFFINE, inv, Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    if sc.get("fit") in ("height", "width"):
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        a = fg.getchannel("A").filter(ImageFilter.GaussianBlur(25)).point(lambda v: int(v * 0.8))
        shadow.putalpha(a)
        frame.alpha_composite(shadow, (10, 16))
    frame.alpha_composite(fg)

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    # focus isolation (blur outside first circle)
    iso_cs = []
    for c in sc.get("circles", []):
        a_ = ss((lt - c["t"]) / 0.5) * sc.get("iso", 1.0)
        if a_ > 0.01: iso_cs.append((c, a_))
    if iso_cs:
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        for c, a_ in iso_cs:
            cx, cy = S(c["c"][0], c["c"][1])
            rx, ry = c["r"][0] * k * s * 1.05, c["r"][1] * k * s * 1.05
            md.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(25))
        iso = max(a_ for _, a_ in iso_cs)
        rgb = frame.convert("RGB")
        bl = rgb.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
        bl = ImageEnhance.Brightness(bl).enhance(0.55)
        mixed = Image.composite(rgb, bl, m)
        frame = Image.blend(rgb, mixed, iso).convert("RGBA")
    for j, c in enumerate(sc.get("circles", [])):
        p = (lt - c["t"]) / 0.55
        if p > 0:
            cx, cy = S(*c["c"])
            draw_stroke(od, circle_pts(cx, cy, c["r"][0] * k * s, c["r"][1] * k * s, 11 + j + si * 7, p), 9)
    for j, a in enumerate(sc.get("arrows", [])):
        p = (lt - a["t"]) / 0.45
        if lt > a.get("t_end", 99): continue
        if p > 0:
            x1, y1 = S(*a["to"]) if a.get("to_img", True) else a["to"]
            x0, y0 = a["from"]
            pts = arrow_pts(x0, y0, x1, y1, a.get("bend", 120), p)
            draw_stroke(od, pts, 8)
            if p >= 1 and len(pts) > 3:
                (ax, ay), (bx, by) = pts[-4], pts[-1]
                ang = math.atan2(by - ay, bx - ax)
                for da in (2.55, -2.55):
                    draw_stroke(od, [(bx, by), (bx + 38 * math.cos(ang + da), by + 38 * math.sin(ang + da))], 8)
    frame.alpha_composite(ov)

    # notes (red handwriting)
    for n_ in sc.get("notes", []):
        a = (lt - n_["t"]) / 0.35
        if lt > n_.get("t_end", 99): continue
        if a > 0:
            f = F_NOTE_AR if is_ar(n_["text"]) else F_NOTE_EN
            ti = n_.get("_im")
            if ti is None:
                ti = text_img(n_["text"], f, fill=RED, pad=(20, 10), shadow=True)
                ti = ti.rotate(n_.get("rot", 0), resample=Image.BICUBIC, expand=True)
                n_["_im"] = ti
            wi = wipe(ti, a, rtl=is_ar(n_["text"]))
            if wi is not None:
                frame.alpha_composite(wi, (int(n_["pos"][0] - ti.width / 2), int(n_["pos"][1] - ti.height / 2)))
    # headline boxes
    hl = sc.get("headline")
    if hl:
        for j, (txt, kind) in enumerate(hl):
            key = "_hl%d" % j
            if key not in sc:
                if kind == "en":
                    sc[key] = text_img(txt, F_EN, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 6))
                elif kind == "ar":
                    sc[key] = text_img(txt, F_AR, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 0))
                else:
                    sc[key] = text_img(txt, F_AR_S if is_ar(txt) else F_TYPE, fill=(255, 255, 255), box=RED + (240,), pad=(22, 2))
        hy = sc.get("hl_y", 70)
        if hy == "bottom":
            tot = 0
            for j, (txt, kind) in enumerate(hl):
                if "_hl%d" % j in sc: tot += sc["_hl%d" % j].height + 10
            hy = H - 70 - tot if tot else H
        y = hy
        for j, (txt, kind) in enumerate(hl):
            a = (lt - 0.15 - j * 0.18) / 0.3
            key = "_hl%d" % j
            if key not in sc:
                if kind == "en":
                    sc[key] = text_img(txt, F_EN, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 6))
                elif kind == "ar":
                    sc[key] = text_img(txt, F_AR, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 0))
                elif kind == "red":
                    sc[key] = text_img(txt, F_AR_S if is_ar(txt) else F_TYPE, fill=(255, 255, 255), box=RED + (240,), pad=(22, 2))
                else:
                    sc[key] = text_img(txt, F_TYPE, fill=(235, 235, 235), box=(0, 0, 0, 200), pad=(20, 4))
            ti = sc[key]
            if a > 0:
                wi = wipe(ti, a, rtl=is_ar(txt))
                if wi is not None:
                    pos = sc.get("hl_pos", "center")
                    x = (W - ti.width) // 2 if pos == "center" else (W - 90 - ti.width if pos == "right" else 90)
                    frame.alpha_composite(wi, (x, y))
            y += ti.height + 10

    subtitle(frame, t)
    return finish(frame, fi, t, si, sc)

def finish(frame, fi, t, si, sc):
    lt = t - sc["t0"]
    arr = np.asarray(frame.convert("RGB"), np.float32)
    flick = 1 + 0.03 * math.sin(fi * 1.9) + 0.02 * rng.standard_normal()
    arr = arr * VIG * flick
    g = GRAIN[fi % 8]; arr += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    arr += scratches(fi) * 0.5
    # cut transition: flash + rgb split for first frames of a scene (except first)
    if si > 0 and lt < 0.2:
        q = 1 - lt / 0.2
        sh_ = int(28 * q)
        arr[..., 0] = np.roll(arr[..., 0], sh_, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -sh_, axis=1)
        arr = arr + 160 * q ** 2
    # pre-cut darkening flash
    if si < len(SCENES) - 1 and sc["t1"] - t < 0.07:
        arr = arr * 0.4 + 120
    fade = min(ss(t / 0.5), 1 - ss((t - (DUR - 0.8)) / 0.8))
    arr *= fade
    # letterbox bars
    arr[:40] *= 0; arr[-40:] *= 0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def render_card(fi, t, si, sc, lt):
    c = sc["card"]
    frame = smoke(t, c.get("smoke", 1.7))
    if c.get("counter"):
        val, ts, td = c["counter"][:3]
        plain = len(c["counter"]) > 3
        p = eo((lt - ts) / td)
        if lt >= ts:
            n = int(val * p)
            txt = str(n) if plain else "{:,}".format(n) + ("+" if p >= 1 else "")
            ti = text_img(txt, F_BIG, fill=(255, 255, 255), pad=(30, 0), shadow=True)
            sc_ = 1 + 0.06 * max(0, 1 - (lt - ts - td) / 0.25) if p >= 1 else 1
            if sc_ != 1: ti = ti.resize((int(ti.width * sc_), int(ti.height * sc_)), Image.LANCZOS)
            frame.alpha_composite(ti, ((W - ti.width) // 2, 330 - (ti.height - 300) // 2))
    for j, (txt, kind, y, ts) in enumerate(c.get("texts", [])):
        a = (lt - ts) / 0.3
        if a <= 0: continue
        key = "_ct%d" % j
        if key not in sc:
            if kind == "en": sc[key] = text_img(txt, F_EN, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 6))
            elif kind == "ar": sc[key] = text_img(txt, F_AR, fill=(255, 255, 255), box=(0, 0, 0, 235), pad=(34, 0))
            else: sc[key] = text_img(txt, F_AR_S if is_ar(txt) else F_TYPE, fill=(255, 255, 255), box=RED + (240,), pad=(22, 2))
        wi = wipe(sc[key], a, rtl=is_ar(txt))
        if wi is not None: frame.alpha_composite(wi, ((W - sc[key].width) // 2, y))
    subtitle(frame, t)
    return finish(frame, fi, t, si, sc)

if PREVIEW:
    for tt in PREVIEW:
        render(int(float(tt) * FPS)).save(f"{OUT}_{float(tt):04.1f}.jpg", quality=85)
    sys.exit()
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                       "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for fi in range(NF):
    ff.stdin.write(render(fi).tobytes())
    if fi % 60 == 0: print("frame", fi, flush=True)
ff.stdin.close(); ff.wait()
