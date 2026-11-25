"""Original lo-fi score + paper foley synced to timeline.json.

timeline.json keys: total, cuts[], pops[] (paper lands), thuds[] (rubber stamp),
scribbles[[start, dur]] (marker drawing), rustles[] (paper wipe), bpm (default 86)
Usage: python3 lofi_score.py <work_dir>  -> score.wav
"""
import json, os, sys, wave
import numpy as np

WD = sys.argv[1]; tl = json.load(open(os.path.join(WD, "timeline.json")))
SR = 48000; DUR = tl["total"]; N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(11)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a):
    y = np.empty_like(x); acc = 0.0; a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def bp(x, a_lo, a_hi): return lp(x, a_hi) - lp(x, a_lo)

BPM = tl.get("bpm", 86); beat = 60 / BPM; bar = 4 * beat
chords = [[50, 53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62], [45, 52, 55, 60, 64]]  # Dm9 G7 Em7 Am9 (lo-fi ii-V-iii-vi)
music = np.zeros(N); fx = np.zeros(N)

# warm electric-piano chords, slightly detuned + wow/flutter
wow = 1 + .0025 * np.sin(2 * np.pi * .6 * t)
for b in range(int(DUR / bar) + 2):
    s = int(b * bar * SR)
    if s >= N: break
    ch = chords[b % 4]
    for k, m in enumerate(ch):
        st = s + int(k * .018 * SR); e = min(N, st + int(bar * SR * 1.05))
        if st >= N: continue
        tt = np.arange(e - st) / SR; env = np.exp(-tt * 1.1) * np.minimum(1, tt / .01)
        f = hz(m) * wow[st:e]; ph = 2 * np.pi * np.cumsum(f) / SR
        music[st:e] += .045 * env * (np.sin(ph) + .35 * np.sin(2 * ph) * np.exp(-tt * 3))
    e = min(N, s + int(bar * SR)); tt = np.arange(e - s) / SR
    music[s:e] += .07 * np.exp(-tt * .9) * np.sin(2 * np.pi * hz(ch[0] - 12) * tt)

# dusty drums: kick 1 & 3 (+ "and" of 3), brush snare 2 & 4, soft hats
for k in range(int(DUR / beat) + 1):
    st = k * beat
    if st < tl.get("drums_from", 0.0) or st > DUR - .8: continue
    pos = k % 4
    if pos in (0, 2):
        s = int(st * SR); L = min(N - s, int(.35 * SR)); tt = np.arange(L) / SR
        music[s:s + L] += .32 * np.exp(-tt * 10) * np.sin(2 * np.pi * np.cumsum(50 + 70 * np.exp(-tt * 30)) / SR)
    if pos in (1, 3):
        s = int(st * SR); L = min(N - s, int(.22 * SR)); nz = bp(rng.standard_normal(L), .05, .5)
        music[s:s + L] += .13 * nz * np.exp(-np.arange(L) / SR * 16)
    for off in (0, .5):
        s = int((st + off * beat + .012 * rng.standard_normal()) * SR); L = min(N - s, int(.04 * SR))
        if L > 0: nz = rng.standard_normal(L); nz -= lp(nz, .5); music[s:s + L] += .025 * nz * np.exp(-np.arange(L) / SR * 70)

# vinyl crackle bed
cr = np.zeros(N); idx = rng.integers(0, N, int(DUR * 14)); cr[idx] = rng.uniform(-.25, .25, len(idx))
music += lp(cr, .35) * .5 + lp(rng.standard_normal(N), .02) * .006

music = lp(music, .55)  # tape-ish top roll-off

# ---- foley ----
for c in tl.get("pops", []):          # paper placed on paper
    s = int(c * SR); L = min(N - s, int(.12 * SR))
    if L <= 0: continue
    nz = bp(rng.standard_normal(L), .02, .25); fx[s:s + L] += .35 * nz * np.exp(-np.arange(L) / SR * 38)
for c in tl.get("thuds", []):         # rubber stamp
    s = int(c * SR); L = min(N - s, int(.35 * SR)); tt = np.arange(L) / SR
    fx[s:s + L] += .55 * np.exp(-tt * 18) * np.sin(2 * np.pi * np.cumsum(70 + 90 * np.exp(-tt * 40)) / SR)
    nz = bp(rng.standard_normal(L), .03, .3); fx[s:s + L] += .35 * nz * np.exp(-tt * 30)
for c, d in tl.get("scribbles", []):  # marker on paper
    s = int(c * SR); L = min(N - s, int(d * SR))
    if L <= 0: continue
    tt = np.arange(L) / SR; nz = bp(rng.standard_normal(L), .08, .6)
    am = .55 + .45 * np.abs(np.sin(2 * np.pi * 7 * tt + rng.uniform(0, 3)))
    fx[s:s + L] += .16 * nz * am * np.minimum(1, tt / .03) * np.minimum(1, (d - tt) / .05)
for c in tl.get("rustles", []):       # paper sheet slide
    L = int(.5 * SR); s = int(c * SR)
    if s < 0: continue
    L = min(L, N - s); tt = np.arange(L) / SR; env = np.sin(np.pi * tt / .5) ** 2
    fx[s:s + L] += .3 * lp(rng.standard_normal(L), .05 + .35 * env) * env

out = music + fx
out *= np.minimum(1, t / .3) * np.minimum(1, (DUR - t) / 1.5)
out = np.tanh(out * 1.2) / 1.2
st = np.stack([out, np.roll(out, 260) * .97], 1)
pcm = (st / np.max(np.abs(st)) * .85 * 32767).astype(np.int16)
with wave.open(os.path.join(WD, "score.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("lofi score", round(DUR, 2), "s")
