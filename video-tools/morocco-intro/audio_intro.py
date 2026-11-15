import sys, wave, numpy as np
from scipy.signal import lfilter
exec(open(sys.argv[1]).read())
SR = 44100; DUR = 5.0; N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(7); lp = lambda x, a: lfilter([a], [1, -(1 - a)], x)
mix = np.zeros(N)
def add(s, at):
    i = int(at * SR); mix[i:i + len(s)] += s[:N - i]
# rising drone
f = 55 * (1 + 0.5 * np.clip(t / 2.85, 0, 1))
ph = 2 * np.pi * np.cumsum(f) / SR
mix += (np.sin(ph) * 0.4 + np.sin(ph * 1.5) * 0.2 + np.sin(ph * 2.01) * 0.12) * np.clip(t / 2.85, 0, 1) ** 1.5 * (t < 2.85)
# riser noise
r = lp(rng.normal(0, 1, N), 0.2) * np.clip(t / 2.85, 0, 1) ** 3 * (t < 2.85) * 0.5
mix += r
# cut hits
tt0 = 0.0
for sh in SHOTS[:-1]:
    tt0 += sh["d"]
    n = int(0.25 * SR); tt = np.arange(n) / SR
    hit = (np.sin(2 * np.pi * (90 * tt - 80 * tt ** 2)) * np.exp(-tt * 18) * 0.9 + lfilter([1, -0.9], [1], rng.normal(0, 1, n)) * np.exp(-tt * 45) * 0.35)
    add(hit, tt0)
add(lfilter([1, -0.9], [1], rng.normal(0, 1, int(0.2 * SR))) * np.exp(-np.arange(int(0.2 * SR)) / SR * 40) * 0.4, 0.02)
# title boom
T = sum(sh["d"] for sh in SHOTS[:-1])
n = int(2.2 * SR); tt = np.arange(n) / SR
boom = np.sin(2 * np.pi * (45 * tt - 6 * tt ** 2)) * np.exp(-tt * 1.6) * 1.4 + lp(rng.normal(0, 1, n), 0.04) * np.exp(-tt * 4) * 3
add(boom, T)
# title text clicks
for ts in (0.45, 0.65, 0.9):
    n = int(0.1 * SR); tt = np.arange(n) / SR
    add(lp(rng.normal(0, 1, n), 0.35) * np.exp(-tt * 50) * 0.6, T + ts)
mix *= np.minimum(1, np.minimum(t / 0.05, (DUR - t) / 0.4))
mix = np.tanh(mix / np.abs(mix).max() * 1.5) * 0.9
st = np.stack([mix, np.roll(mix, 200)], 1)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
