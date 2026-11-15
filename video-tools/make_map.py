"""Build a large vintage parchment map of Morocco (static layer)."""
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

D = sys.argv[1]
S = 280.0
LON0, LON1, LAT0, LAT1 = -19.5, 1.0, 20.0, 37.6
K = math.cos(math.radians(30))
W = int((LON1 - LON0) * S * K)
H = int((LAT1 - LAT0) * S)

def P(lon, lat):
    return ((lon - LON0) * S * K, (LAT1 - lat) * S)

FONT = D + "/fonts/IMFellI.ttf"
FONTR = D + "/fonts/IMFell.ttf"
rng = np.random.default_rng(7)

# ---------- parchment ----------
def noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, np.float32) / 255.0

n = 0.45 * noise(H, W, 400, 1) + 0.3 * noise(H, W, 90, 2) + 0.25 * noise(H, W, 12, 3)
base = np.array([238, 226, 196], np.float32)
dark = np.array([196, 168, 120], np.float32)
t = np.clip((n - 0.35) * 1.4, 0, 1)[..., None]
paper = base * (1 - t * 0.55) + dark * (t * 0.55)
# stains
st = np.zeros((H, W), np.float32)
for _ in range(40):
    cx, cy, r = rng.random() * W, rng.random() * H, rng.uniform(60, 380)
    yy, xx = np.ogrid[:H, :W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ring = np.exp(-((d - r) / (r * 0.06)) ** 2) * 0.5 + np.exp(-(d / r) ** 2) * 0.25
    st += ring * rng.uniform(0.2, 0.6)
paper -= st[..., None] * np.array([30, 40, 55], np.float32)

# ---------- geography ----------
geo = json.load(open(D + "/geo/countries.geojson"))
def polys(name):
    for f in geo["features"]:
        if f["properties"]["NAME"] == name:
            g = f["geometry"]
            cs = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in cs:
                yield [P(x, y) for x, y in poly[0]]

land_names = ["Spain", "Portugal", "Algeria", "Mauritania", "Mali", "Tunisia", "France", "Gibraltar"]
moro = ["Morocco", "W. Sahara"]

landmask = Image.new("L", (W, H), 0)
moromask = Image.new("L", (W, H), 0)
dl, dm = ImageDraw.Draw(landmask), ImageDraw.Draw(moromask)
for nm in land_names + moro:
    for p in polys(nm):
        dl.polygon(p, fill=255)
for nm in moro:
    for p in polys(nm):
        dm.polygon(p, fill=255)
landmask = landmask.filter(ImageFilter.GaussianBlur(1.2))
moromask = moromask.filter(ImageFilter.GaussianBlur(1.2))
L = np.asarray(landmask, np.float32)[..., None] / 255
M = np.asarray(moromask, np.float32)[..., None] / 255

sea = paper * np.array([0.93, 0.95, 0.97], np.float32)
img = sea * (1 - L) + paper * L
# Morocco: golden olive wash with texture
gold = np.array([206, 176, 102], np.float32)
tex = (0.85 + 0.3 * noise(H, W, 30, 9))[..., None]
img = img * (1 - M * 0.62) + gold * tex * (M * 0.62)

# coastal water lines (old map ripple lines) via distance transform
from scipy.ndimage import distance_transform_edt
lm = np.asarray(landmask.resize((W//2, H//2), Image.BILINEAR)) > 128
dist = distance_transform_edt(~lm) * 2.0
ripple = np.zeros_like(dist, dtype=np.float32)
for i in range(1, 8):
    r0 = i * 26.0
    ripple += np.exp(-((dist - r0) / 3.2) ** 2).astype(np.float32) * (1.0 - i * 0.12)
ripple = np.asarray(Image.fromarray((np.clip(ripple,0,1)*255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)/255
ink = np.array([92, 78, 58], np.float32)
img = img * (1 - ripple[..., None] * 0.5) + ink * ripple[..., None] * 0.5

# graticule
g = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(g)
for lon in range(-19, 2, 2):
    x, _ = P(lon, 0)
    gd.line([(x, 0), (x, H)], fill=110, width=3)
for lat in range(20, 38, 2):
    _, y = P(0, lat)
    gd.line([(0, y), (W, y)], fill=110, width=3)
G = np.asarray(g, np.float32)[..., None] / 255
img = img * (1 - G * 0.35) + ink * G * 0.35

out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(out)

# coastlines and borders
for nm in land_names:
    for p in polys(nm):
        d.line(p + [p[0]], fill=(70, 55, 38), width=6, joint="curve")
# outer Morocco outline from merged mask
mm = np.asarray(moromask) > 128
from scipy.ndimage import binary_dilation, binary_erosion
edge = binary_dilation(mm, iterations=5) & ~binary_erosion(mm, iterations=4)
E = Image.fromarray((edge*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
red = Image.new("RGB", (W, H), (125, 38, 28))
out.paste(red, (0, 0), E)
d = ImageDraw.Draw(out)

# mountains (Atlas, Rif) as hachure peaks
ranges = [
    [(-9.3, 30.7), (-8.0, 31.1), (-6.8, 31.5), (-5.6, 32.0), (-4.5, 32.4), (-3.4, 32.7), (-2.3, 33.0)],  # High Atlas
    [(-6.2, 33.0), (-5.2, 33.4), (-4.3, 33.8), (-3.5, 34.1)],  # Middle Atlas
    [(-8.8, 29.9), (-7.6, 30.2), (-6.4, 30.5), (-5.2, 30.8)],  # Anti Atlas
    [(-5.4, 35.0), (-4.6, 35.0), (-3.8, 34.9)],  # Rif
]
for rg in ranges:
    for (a, b) in zip(rg, rg[1:]):
        for k in range(6):
            u = k / 6
            lon = a[0] + (b[0] - a[0]) * u + rng.uniform(-0.15, 0.15)
            lat = a[1] + (b[1] - a[1]) * u + rng.uniform(-0.2, 0.2)
            x, y = P(lon, lat)
            s = rng.uniform(16, 26)
            d.polygon([(x - s, y + s * 0.6), (x, y - s * 0.8), (x + s, y + s * 0.6)], fill=(170, 140, 90))
            d.line([(x - s, y + s * 0.6), (x, y - s * 0.8), (x + s, y + s * 0.6)], fill=(70, 50, 30), width=4)
            d.line([(x, y - s * 0.8), (x + s * 0.4, y + s * 0.6)], fill=(90, 65, 40), width=3)

def label(lon, lat, text, size, fnt=FONT, fill=(60, 42, 28), anchor="mm", spacing=0):
    f = ImageFont.truetype(fnt, size)
    x, y = P(lon, lat)
    if spacing:
        text = (" " * spacing).join(text)
    d.text((x, y), text, font=f, fill=fill, anchor=anchor)

label(-14.5, 33.0, "OCEANUS", 150, FONTR, (80, 70, 60), spacing=1)
label(-14.5, 32.3, "ATLANTICUS", 150, FONTR, (80, 70, 60), spacing=1)
label(-2.2, 36.6, "MARE  MEDITERRANEUM", 95, FONTR, (80, 70, 60))
label(-5.4, 30.05, "REGNUM  MAROCCANUM", 84, FONTR, (110, 35, 25))
label(-4.5, 37.05, "HISPANIA", 90, FONTR, (90, 80, 70))
label(-0.8, 30.5, "ALGERIA", 100, FONTR, (90, 80, 70))
label(-12.0, 21.0, "MAURITANIA", 100, FONTR, (90, 80, 70))
label(-12.3, 25.0, "SAHARA", 120, FONTR, (110, 35, 25), spacing=2)

cities = {
    "Tanger": (-5.80, 35.77), "Rabat": (-6.84, 34.02), "Casablanca": (-7.59, 33.57),
    "Essaouira": (-9.77, 31.51), "Agadir": (-9.60, 30.42), "Laâyoune": (-13.20, 27.15),
    "Dakhla": (-15.94, 23.70), "Fès": (-5.00, 34.03), "Marrakech": (-7.99, 31.63),
    "Meknès": (-5.55, 33.89), "Oujda": (-1.91, 34.68), "Ouarzazate": (-6.91, 30.92),
    "Tétouan": (-5.37, 35.57), "El Jadida": (-8.50, 33.25), "Safi": (-9.24, 32.30),
    "Errachidia": (-4.42, 31.93), "Guelmim": (-10.06, 28.99), "Nador": (-2.93, 35.17),
}
for nm, (lon, lat) in cities.items():
    x, y = P(lon, lat)
    d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(240, 228, 200), outline=(60, 40, 25), width=5)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(60, 40, 25))
    f = ImageFont.truetype(FONT, 64)
    d.text((x + 24, y - 6), nm, font=f, fill=(55, 38, 24), anchor="lm")

# compass rose
cx, cy = P(-16.8, 35.6)
R = 260
for ang in range(0, 360, 45):
    a = math.radians(ang)
    long_ = R if ang % 90 == 0 else R * 0.6
    tip = (cx + math.sin(a) * long_, cy - math.cos(a) * long_)
    l = (cx + math.sin(a - 0.35) * 55, cy - math.cos(a - 0.35) * 55)
    r = (cx + math.sin(a + 0.35) * 55, cy - math.cos(a + 0.35) * 55)
    d.polygon([tip, l, (cx, cy)], fill=(120, 40, 30))
    d.polygon([tip, r, (cx, cy)], fill=(230, 215, 180))
    d.line([tip, l, (cx, cy), r, tip], fill=(60, 40, 25), width=4)
d.ellipse([cx - R * 0.75, cy - R * 0.75, cx + R * 0.75, cy + R * 0.75], outline=(60, 40, 25), width=4)
d.text((cx, cy - R - 50), "N", font=ImageFont.truetype(FONTR, 110), fill=(60, 40, 25), anchor="mm")

# decorative frame
for i, (wd, col) in enumerate([(26, (60, 40, 25)), (8, (150, 110, 60))]):
    m = 30 + i * 44
    d.rectangle([m, m, W - m, H - m], outline=col, width=wd)

out = out.filter(ImageFilter.GaussianBlur(0.6))
out.save(D + "/map.png")
print(W, H)
json.dump({"S": S, "LON0": LON0, "LAT1": LAT1, "K": K, "W": W, "H": H}, open(D + "/map.json", "w"))
