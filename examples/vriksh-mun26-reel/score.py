"""Original score for the MUN reel, synced to timeline.json cuts. 100 BPM, F major, warm and uplifting."""
import json, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(HERE, "timeline.json")))
SR = 48000; DUR = tl["total"]; cuts = tl["cuts"]
N = int(SR * DUR); t = np.arange(N) / SR; rng = np.random.default_rng(3)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def onepole(x, a):
    y = np.empty_like(x); acc = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y

BPM = 100; beat = 60 / BPM; bar = 4 * beat
BREAK = (cuts[13], cuts[15])           # "And then..." -> tension, drums out
AWARD = cuts[15]; END = cuts[17]
FULL = cuts[7]                          # kick enters at the bag montage
chords = [[53, 57, 60, 64], [48, 55, 60, 64], [50, 57, 60, 65], [46, 53, 58, 62]]  # F  C  Dm  Bb
mix = np.zeros(N); drums = np.zeros(N)

# warm pad
for b in range(int(DUR / bar) + 2):
    s = int(b * bar * SR)
    if s >= N: break
    e = min(N, int(((b + 1) * bar + .5) * SR)); ch = chords[b % 4]; tt = np.arange(e - s) / SR
    env = np.minimum(1, tt / .6) * np.clip(((e - s) / SR - tt) / .5, 0, 1)
    for m in ch:
        for det in (-.08, .08):
            f = hz(m) * 2 ** (det / 12); mix[s:e] += .03 * env * (np.sin(2*np.pi*f*tt) + .3*np.sin(4*np.pi*f*tt))
    mix[s:e] += .06 * env * np.sin(2 * np.pi * hz(ch[0] - 12) * tt)

# pluck arp (sixteenth feel on eighths), from the first cut, out during the break
step = beat / 2; pat = [0, 2, 3, 1, 2, 3, 1, 2]
for k in range(int(DUR / step)):
    st = k * step
    if st < cuts[0] or (BREAK[0] < st < BREAK[1]) or st > DUR - 1.2: continue
    ch = chords[int(st / bar) % 4]; m = ch[pat[k % 8]] + 12
    s = int(st * SR); L = min(N - s, int(.7 * SR)); tt = np.arange(L) / SR
    g = .055 if st < AWARD else .07
    mix[s:s + L] += g * np.exp(-tt * 7) * (np.sin(2*np.pi*hz(m)*tt) + .25*np.sin(2*np.pi*hz(m)*3*tt))

# drums: shaker from first cut, kick + clap from FULL, out in the break, back bigger at the award
for k in range(int(DUR / beat) + 1):
    st = k * beat
    if st < cuts[0] or (BREAK[0] < st < BREAK[1]) or st > DUR - 1.0: continue
    s = int((st + beat / 2) * SR); L = min(N - s, int(.07 * SR))
    if L > 0:
        nz = rng.standard_normal(L); nz -= onepole(nz, .25); drums[s:s + L] += .045 * nz * np.exp(-np.arange(L) / SR * 55)
    if st >= FULL:
        s = int(st * SR); L = min(N - s, int(.4 * SR)); tt = np.arange(L) / SR
        f = 48 + 80 * np.exp(-tt * 28); drums[s:s + L] += .42 * np.exp(-tt * 8) * np.sin(2*np.pi*np.cumsum(f)/SR)
        if k % 2 == 1:
            L2 = min(N - s, int(.18 * SR)); nz = rng.standard_normal(L2); nz -= onepole(nz, .4)
            drums[s:s + L2] += .11 * nz * np.exp(-np.arange(L2) / SR * 22)

# whoosh on every cut (softer on the gentle fades)
for i, c in enumerate(cuts):
    L = int(.7 * SR); s = int((c - .45) * SR)
    if s < 0: continue
    L = min(L, N - s); tt = np.arange(L) / SR; env = np.sin(np.pi * tt / .7) ** 2
    y = onepole(rng.standard_normal(L), .03 + .3 * env)
    mix[s:s + L] += (.55 if i in (0, 8, 15, 17) else .3) * y * env ** 1.5

# riser through the break into the award, then a chime + sub hit
s0, s1 = int(BREAK[0] * SR), int(AWARD * SR); L = s1 - s0; tt = np.arange(L) / SR
ramp = (tt / tt[-1]) ** 2
mix[s0:s1] += .25 * onepole(rng.standard_normal(L), .02 + .4 * ramp) * ramp
mix[s0:s1] += .05 * ramp * np.sin(2 * np.pi * np.cumsum(220 + 660 * ramp) / SR)
for c, base in [(AWARD, 89), (END + .4, 84)]:
    s = int(c * SR); L = min(N - s, int(2.8 * SR)); tt = np.arange(L) / SR
    for m, g in [(base, 1), (base + 7, .55), (base + 12, .4), (base + 16, .25)]:
        mix[s:s + L] += .06 * g * np.exp(-tt * 1.8) * np.sin(2 * np.pi * hz(m) * tt)
s = int(AWARD * SR); L = int(1.2 * SR); tt = np.arange(L) / SR
drums[s:s + L] += .5 * np.exp(-tt * 3) * np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-tt * 10)) / SR)

out = mix + drums
out *= np.minimum(1, t / .3) * np.minimum(1, (DUR - t) / 1.8)
out = np.tanh(out * 1.3) / 1.3
st = np.stack([out, np.roll(out, 300) * .96], 1)
pcm = (st / np.max(np.abs(st)) * .85 * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, "score.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("score", DUR, "award at", round(AWARD, 2))
