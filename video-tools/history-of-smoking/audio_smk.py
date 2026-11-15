import sys, wave, numpy as np
from scipy.signal import lfilter
exec(open(sys.argv[1]).read())
SR = 44100; N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(2)
lp = lambda x, a: lfilter([a], [1, -(1 - a)], x)
mix = np.zeros(N)
# dark drone: D1/A1/Eb2 cluster with slow beating
for f, a in [(36.7, .5), (55.0, .35), (77.8, .18), (73.6, .2)]:
    mix += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.11 * t))
mix *= 0.22 * (0.6 + 0.4 * np.minimum(1, t / 4))
# wind/room tone
mix += lp(lp(rng.normal(0, 1, N), 0.01), 0.03) * 2.5
def add(sig, at):
    i = int(at * SR); mix[i:i + len(sig)] += sig[:N - i]
# clock ticks
for k in range(int(DUR / 0.5)):
    n = int(0.03 * SR); tt = np.arange(n) / SR
    tick = rng.normal(0, 1, n) * np.exp(-tt * 300) * (0.25 if k % 2 else 0.18)
    add(lfilter([1, -0.95], [1], tick), k * 0.5 + 0.02)
# impacts at cuts
def boom(at, amp=1.0):
    n = int(1.6 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (55 * tt - 18 * tt ** 2)) * np.exp(-tt * 3.2) * amp
    s += lp(rng.normal(0, 1, n), 0.05) * np.exp(-tt * 9) * amp * 2.2
    add(s, at)
def whoosh(at, d=0.6, amp=0.5):
    n = int(d * SR); x = lp(rng.normal(0, 1, n), 0.15) * np.linspace(0, 1, n) ** 3
    add(x / (np.abs(x).max() + 1e-9) * amp, at - d)
def scribble(at, d=0.55):
    n = int(d * SR); tt = np.arange(n) / SR
    x = lfilter([1, -0.97], [1], rng.normal(0, 1, n)) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * tt))) * np.sin(np.pi * tt / d)
    add(x / np.abs(x).max() * 0.16, at)
boom(0.05, 1.1)
for sc in SCENES[1:]:
    whoosh(sc["t0"]); boom(sc["t0"], 0.9)
for sc in SCENES:
    for c in sc.get("circles", []): scribble(sc["t0"] + c["t"])
    for j, _ in enumerate(sc.get("headline", [])):
        n = int(0.12 * SR); tt = np.arange(n) / SR
        add(lp(rng.normal(0, 1, n), 0.3) * np.exp(-tt * 40) * 0.5, sc["t0"] + 0.15 + j * 0.18)
# final low swell
add(np.sin(2 * np.pi * 36.7 * t[:int(3 * SR)]) * np.linspace(0, 0.6, int(3 * SR)), DUR - 3.4)
mix *= np.minimum(1, np.minimum(t / 0.3, (DUR - t) / 0.9))
mix = np.tanh(mix / np.abs(mix).max() * 1.6) * 0.85
st = np.stack([mix, np.roll(mix, 220)], 1)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
