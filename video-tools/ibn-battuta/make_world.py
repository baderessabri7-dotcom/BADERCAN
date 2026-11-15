import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D, FD = sys.argv[1], sys.argv[2]
exec(open(D + "/geo.py").read())
W, H = int((LON1 - LON0) * SC), int((LAT1 - LAT0) * SC)
geo = json.load(open(sys.argv[3]))
sea = Image.new("RGB", (W, H), (14, 30, 44))
yy, xx = np.mgrid[0:H, 0:W]
arr = np.asarray(sea, np.float32) * (0.85 + 0.25 * (1 - yy / H))[..., None]
im = Image.fromarray(arr.astype(np.uint8))
land = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(land)
polys = []
for f in geo["features"]:
    g = f["geometry"]; cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in cs:
        pts = [P(x, y) for x, y in poly[0]]
        if max(p[0] for p in pts) < -50 or min(p[0] for p in pts) > W + 50: continue
        dl.polygon(pts, fill=255); polys.append(pts)
r = np.random.default_rng(1)
tex = Image.fromarray((r.random((H // 40 + 2, W // 40 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
landcol = np.asarray(Image.new("RGB", (W, H), (176, 150, 104)), np.float32) * (0.94 + 0.1 * np.asarray(tex, np.float32)[..., None] / 255)
L = np.asarray(land.filter(ImageFilter.GaussianBlur(1)), np.float32)[..., None] / 255
glow = np.asarray(land.filter(ImageFilter.GaussianBlur(14)), np.float32)[..., None] / 255
base = np.asarray(im, np.float32)
base = base + (glow - L).clip(0, 1) * np.array([60, 80, 90])
out = base * (1 - L) + landcol * L
im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
for lon in range(-20, 126, 15):
    x, _ = P(lon, 0); d.line([(x, 0), (x, H)], fill=(40, 60, 76), width=1)
for lat in range(-10, 57, 15):
    _, y = P(0, lat); d.line([(0, y), (W, y)], fill=(40, 60, 76), width=1)
for pts in polys: d.line(pts + [pts[0]], fill=(110, 90, 62), width=2)
f = ImageFont.truetype(FD + "/Cairo.ttf", 34, layout_engine=ImageFont.Layout.RAQM)
try: f.set_variation_by_axes([800, 0])
except Exception: pass
for name, (lon, lat) in CITIES.items():
    x, y = P(lon, lat)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255), outline=(20, 20, 20), width=2)
    d.text((x + 12, y - 4), name, font=f, fill=(255, 255, 255), anchor="lm", direction="rtl", language="ar", stroke_width=3, stroke_fill=(15, 15, 15))
im.save(D + "/img/world.jpg", quality=92); print(W, H)
