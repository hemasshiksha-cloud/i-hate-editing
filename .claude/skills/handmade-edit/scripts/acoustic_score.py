"""Sound D: original acoustic-guitar score (plucked strings, claps, shaker) + dispatch foley.

timeline.json keys: total, cuts, pops, thuds, scribbles[[t,d]], chings, whirrs[[t,d]],
peels, clicks, rustles, hits (hard-cut accents), bpm (default 102)
Usage: python3 acoustic_score.py <work_dir> -> score.wav
"""
import json, os, sys, wave
import numpy as np

WD = sys.argv[1]; tl = json.load(open(os.path.join(WD, "timeline.json")))
SR = 48000; DUR = tl["total"]; N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(23)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, a):
    y = np.empty_like(x); acc = 0.0; a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y
def bp(x, lo, hi): return lp(x, hi) - lp(x, lo)

def pluck(f, dur, bright=.5, decay=.996):
    """Karplus-Strong plucked string, vectorised one period at a time."""
    P = max(2, int(SR / f)); L = int(dur * SR)
    buf = rng.uniform(-1, 1, P); buf = lp(buf, bright)
    out = np.zeros(L + P); out[:P] = buf
    for s in range(P, L + P, P):
        e = min(s + P, L + P); seg = out[s - P:e - P]; prev = np.concatenate([[out[s - P - 1] if s - P - 1 >= 0 else 0], seg[:-1]])
        out[s:e] = decay * .5 * (seg + prev)
    return out[:L]

BPM = tl.get("bpm", 102); beat = 60 / BPM; bar = 4 * beat
chords = [[43, 47, 50, 55, 59, 67], [38, 45, 50, 54, 57, 62], [40, 47, 52, 55, 59, 64], [36, 43, 48, 52, 55, 60]]  # G D Em C
music = np.zeros(N); fx = np.zeros(N)

def add(dst, sig, start, g):
    s = int(start * SR)
    if s >= N or s < 0: return
    L = min(len(sig), N - s); dst[s:s + L] += g * sig[:L]

# strummed guitar: down on 1, up-down pattern (D . D U . U D U)
pattern = [(0, 1, .9), (1, 1, .55), (1.5, -1, .4), (2.5, -1, .45), (3, 1, .55), (3.5, -1, .4)]
for b in range(int(DUR / bar) + 1):
    ch = chords[b % 4]
    for off, direction, g in pattern:
        st = b * bar + off * beat
        if st > DUR - .3: continue
        strings = ch if direction > 0 else ch[::-1][:4]
        for k, m in enumerate(strings):
            add(music, pluck(hz(m), 1.4, .45 if direction > 0 else .7), st + k * .011, .055 * g)
# lead picking melody from the 2nd bar (G major pentatonic)
mel = [74, 71, 69, 67, 69, 71, 74, 76, 74, 71, 69, 71]
for k in range(int((DUR - bar) / (beat * 1.5))):
    st = bar + k * beat * 1.5
    if st > DUR - 1: break
    add(music, pluck(hz(mel[k % len(mel)]), .9, .8, .997), st, .07)
# percussion: claps 2 & 4, shaker 16ths, soft kick on 1
for k in range(int(DUR / beat) + 1):
    st = k * beat
    if st > DUR - .6: continue
    if k % 4 in (1, 3):
        for o in (0, .008, .019):
            L = int(.15 * SR); nz = bp(rng.standard_normal(L), .08, .6) * np.exp(-np.arange(L) / SR * 30); add(music, nz, st + o, .09)
    if k % 4 == 0:
        L = int(.3 * SR); tt = np.arange(L) / SR; add(music, np.exp(-tt * 12) * np.sin(2 * np.pi * np.cumsum(55 + 60 * np.exp(-tt * 35)) / SR), st, .3)
    for q in range(4):
        L = int(.05 * SR); nz = rng.standard_normal(L); nz -= lp(nz, .55)
        add(music, nz * np.exp(-np.arange(L) / SR * 60), st + q * beat / 4, .03 if q % 2 else .045)

# ---- dispatch foley ----
for c in tl.get("pops", []):
    L = int(.1 * SR); add(fx, bp(rng.standard_normal(L), .02, .25) * np.exp(-np.arange(L) / SR * 40), c, .3)
for c in tl.get("thuds", []):
    L = int(.35 * SR); tt = np.arange(L) / SR
    add(fx, np.exp(-tt * 18) * np.sin(2 * np.pi * np.cumsum(70 + 90 * np.exp(-tt * 40)) / SR) + .5 * bp(rng.standard_normal(L), .03, .3) * np.exp(-tt * 30), c, .55)
for c, d in tl.get("scribbles", []):
    L = int(d * SR); tt = np.arange(L) / SR
    add(fx, bp(rng.standard_normal(L), .08, .6) * (.55 + .45 * np.abs(np.sin(2 * np.pi * 7 * tt))) * np.minimum(1, (d - tt) / .05), c, .15)
for c in tl.get("chings", []):  # cash register: bell + drawer
    L = int(1.2 * SR); tt = np.arange(L) / SR
    bell = sum(g * np.sin(2 * np.pi * f * tt) for f, g in [(2093, 1), (2637, .6), (3136, .4), (4186, .25)]) * np.exp(-tt * 4)
    add(fx, bell, c + .06, .09)
    Ld = int(.12 * SR); add(fx, bp(rng.standard_normal(Ld), .05, .4) * np.exp(-np.arange(Ld) / SR * 25), c, .35)
for c, d in tl.get("whirrs", []):  # thermal printer
    L = int(d * SR); tt = np.arange(L) / SR
    motor = np.sign(np.sin(2 * np.pi * 180 * tt)) * .3 + bp(rng.standard_normal(L), .1, .5)
    add(fx, lp(motor, .25) * (.6 + .4 * np.sin(2 * np.pi * 11 * tt) ** 2) * np.minimum(1, tt / .05) * np.minimum(1, (d - tt) / .08), c, .1)
for c in tl.get("peels", []):  # sticker peel: rising crackle
    L = int(.45 * SR); tt = np.arange(L) / SR; env = (tt / .45) ** .5 * np.minimum(1, (.45 - tt) / .05)
    cr = (rng.random(L) > .9) * rng.uniform(-1, 1, L); add(fx, bp(cr, .1, .7) * env, c, .55)
for c in tl.get("clicks", []):
    for o in (0, .09):
        L = int(.02 * SR); add(fx, bp(rng.standard_normal(L), .2, .8) * np.exp(-np.arange(L) / SR * 200), c + o, .4)
for c in tl.get("rustles", []):
    L = int(.5 * SR); tt = np.arange(L) / SR; env = np.sin(np.pi * tt / .5) ** 2
    add(fx, lp(rng.standard_normal(L), .05 + .35 * env) * env, c, .28)
for c in tl.get("hits", []):  # hard-cut accent: muted string slap
    add(fx, pluck(hz(43), .25, .9, .95), c, .3)

out = music + fx
out *= np.minimum(1, t / .2) * np.minimum(1, (DUR - t) / 1.4)
out = np.tanh(out * 1.2) / 1.2
st = np.stack([out, np.roll(out, 220) * .97], 1)
pcm = (st / np.max(np.abs(st)) * .85 * 32767).astype(np.int16)
with wave.open(os.path.join(WD, "score.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("acoustic score", round(DUR, 2), "s")
