"""Original, royalty-free soundtrack: warm pad + pluck arp + soft beat, with whooshes and a chime."""
import numpy as np, wave, os
SR = 48000; DUR = 21.5
ROOT = os.path.dirname(os.path.abspath(__file__))
N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(7)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a):  # one-pole lowpass, a in (0,1)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y

BPM = 84; beat = 60 / BPM; bar = 4 * beat
chords = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 57, 60, 64, 65], [46, 53, 57, 62]]  # Fmaj7 Am7 Dm9 Bbmaj7
mix = np.zeros(N); drums = np.zeros(N)

# pad
for b in range(int(DUR / bar) + 1):
    ch = chords[b % 4]; s = int(b * bar * SR); e = min(N, int((b + 1) * bar * SR + .4 * SR))
    if s >= N: break
    tt = np.arange(e - s) / SR; env = np.minimum(1, tt / .9) * np.minimum(1, (e - s) / SR - tt + .05) / 1
    for m in ch:
        for det in (-0.07, 0.07):
            f = hz(m) * 2 ** (det / 12)
            mix[s:e] += 0.035 * env * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt))
    mix[s:e] += 0.05 * env * np.sin(2 * np.pi * hz(ch[0] - 12) * tt)

# pluck arpeggio (eighths), enters at 2.9s
step = beat / 2
for k in range(int(DUR / step)):
    st = k * step
    if st < 2.9: continue
    ch = chords[int(st / bar) % 4]; m = ch[[0, 2, 1, 3, 2, 1, 3, 2][k % 8] % len(ch)] + 12
    s = int(st * SR); L = min(N - s, int(.9 * SR)); tt = np.arange(L) / SR
    mix[s:s + L] += 0.06 * np.exp(-tt * 6) * np.sin(2 * np.pi * hz(m) * tt) * (1 + 0.3 * np.sin(2 * np.pi * hz(m) * 2 * tt))

# soft kick + shaker from reveal (6.2s) until 20.5s
for k in range(int(DUR / beat)):
    st = k * beat
    if st < 6.2 or st > 20.3: continue
    if k % 2 == 0:
        s = int(st * SR); L = min(N - s, int(.35 * SR)); tt = np.arange(L) / SR
        f = 45 + 70 * np.exp(-tt * 30); drums[s:s + L] += 0.35 * np.exp(-tt * 9) * np.sin(2 * np.pi * np.cumsum(f) / SR)
    s = int((st + beat / 2) * SR); L = min(N - s, int(.08 * SR))
    if L > 0:
        nz = rng.standard_normal(L); nz = nz - lp(nz, .3)
        drums[s:s + L] += 0.05 * nz * np.exp(-np.arange(L) / SR * 50)

# whooshes centred on each transition
for c in [3.15, 6.45, 10.15, 13.85, 17.15]:
    L = int(.8 * SR); s = int((c - .5) * SR); tt = np.arange(L) / SR
    nz = rng.standard_normal(L); a = 0.02 + 0.25 * np.sin(np.pi * tt / .8) ** 2
    y = np.empty(L); acc = 0.0
    for i in range(L): acc += a[i] * (nz[i] - acc); y[i] = acc
    mix[s:s + L] += 0.5 * y * np.sin(np.pi * tt / .8) ** 3

# chime on logo reveal (~7.55s) and CTA button (~18.1s)
for c, base in [(7.85, 84), (18.1, 88)]:
    s = int(c * SR); L = min(N - s, int(2.5 * SR)); tt = np.arange(L) / SR
    for m, g in [(base, 1), (base + 7, .5), (base + 12, .35)]:
        mix[s:s + L] += 0.05 * g * np.exp(-tt * 2.2) * np.sin(2 * np.pi * hz(m) * tt)

out = mix + drums
fade = np.minimum(1, t / .4) * np.minimum(1, (DUR - t) / 1.6)
out *= fade
out = np.tanh(out * 1.4) / 1.4
st = np.stack([out, np.roll(out, 240) * .97], 1)  # light stereo width
pcm = (st / np.max(np.abs(st)) * 0.85 * 32767).astype(np.int16)
with wave.open(os.path.join(ROOT, "music.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("music.wav", DUR)
