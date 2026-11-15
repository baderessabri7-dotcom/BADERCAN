import sys, wave, math
import numpy as np
SR, DUR = 44100, 20.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(1)

def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):  # simple one-pole (vectorised below for speed)
        pass
    return y

def onepole(x, alpha):
    # y[n] = y[n-1] + alpha*(x[n]-y[n-1]) via lfilter-like cumulative trick in chunks
    from scipy.signal import lfilter
    return lfilter([alpha], [1, -(1 - alpha)], x)

# ocean waves
w = onepole(rng.normal(0, 1, N), 0.02)
w = onepole(w, 0.05)
env = 0.55 + 0.45 * np.sin(2 * np.pi * t / 5.5) ** 2
waves = w / np.abs(w).max() * env * 0.35

# drone (D + A) with slow swell
drone = (np.sin(2 * np.pi * 73.42 * t) * 0.5 + np.sin(2 * np.pi * 110 * t) * 0.35 + np.sin(2 * np.pi * 146.83 * t) * 0.18)
drone *= 0.18 * (0.7 + 0.3 * np.sin(2 * np.pi * t / 8))

# oud-like plucks (Karplus-Strong), D hijaz
def pluck(freq, dur=1.6, amp=0.5):
    n = int(SR * dur); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out * amp
D4 = 293.66
scale = [1, 16 / 15, 5 / 4, 4 / 3, 3 / 2, 8 / 5, 16 / 9, 2]  # hijaz-ish
melody = [0, 1, 2, 1, 0, -1, 3, 2, 1, 0, 2, 3, 4, 3, 2, 1, 0, 4, 5, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 7]
music = np.zeros(N)
beat = 0.5
for k, deg in enumerate(melody):
    st = 2.6 + k * beat if k < 24 else 2.6 + 24 * beat + (k - 24) * 0.33
    if st > DUR - 1.8: break
    f = D4 * (scale[deg] if deg >= 0 else 0.5 * scale[6])
    s = pluck(f, 1.6, 0.4)
    i = int(st * SR); music[i:i + len(s)] += s[:N - i]
    if k % 4 == 0:  # bass on downbeats
        b = pluck(D4 / 4, 2.0, 0.5); music[i:i + len(b)] += b[:N - i]

# frame drum hits
def drum(at, amp):
    n = int(0.35 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * (90 * tt - 60 * tt ** 2)) * np.exp(-tt * 14) * amp
    i = int(at * SR); music[i:i + n] += s[:N - i]
for k in range(32):
    at = 4.6 + k * 0.375
    if at > 16.4: break
    drum(at, 0.55 if k % 4 == 0 else 0.25)

# whooshes at transitions
def whoosh(at, d=1.4, amp=0.4):
    n = int(d * SR); x = rng.normal(0, 1, n)
    x = onepole(x, 0.08) * np.sin(np.linspace(0, np.pi, n)) ** 2
    i = int(at * SR); music[i:i + n] += (x / np.abs(x).max() * amp)[:N - i]
whoosh(3.0); whoosh(16.3)
mix = waves + drone + music
fade = np.minimum(1, np.minimum(t / 0.8, (DUR - t) / 1.2))
mix *= fade
mix = mix / np.abs(mix).max() * 0.85
st = np.stack([mix, np.roll(mix, 300)], 1)
with wave.open(sys.argv[1], "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((st * 32767).astype(np.int16).tobytes())
