"""Vriksh first corporate order: HANDMADE cut (paper, tape, polaroids, stamps, scribbles)."""
import os, sys, json, math, subprocess
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw
sys.path.insert(0, "/home/user/i-hate-editing/.claude/skills/handmade-edit/scripts")
from handmade import *

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/edd7c674-b2d9-5a5c-bf23-e040c7fcf3b2/"
CUT = os.path.join(os.path.dirname(HERE), "solidpro", "cutouts")
LOGO = "/home/user/i-hate-editing/.claude/skills/vriksh-reel/assets/vriksh_logo.jpg"
WORK = os.path.join(HERE, "work"); CL = os.path.join(WORK, "clips"); os.makedirs(CL, exist_ok=True)
P = PALETTES["vriksh"]; INK = P["ink"] + (255,); RED = (196, 44, 56); ACC = P["accent"] + (255,)
YELLOW = (255, 226, 120)

def load(src, blur=()):
    im = ImageOps.exif_transpose(Image.open(src if src.startswith("/") else UP + src)).convert("RGB")
    for (x0, y0, x1, y1) in blur:
        b = (int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height))
        reg = im.crop(b); w, h = reg.size
        px = reg.resize((max(1, w // 18), max(1, h // 18)), Image.BILINEAR).resize((w, h), Image.BILINEAR)
        im.paste(px.filter(ImageFilter.GaussianBlur(max(6, min(w, h) // 10))), b)
    return im

def cover(img, fx, fy, z):
    iw, ih = img.size; ch = ih / z if iw / ih >= W / H else (iw * H / W) / z; cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    return img.resize((W, H), Image.LANCZOS, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")

def strokes(fr, items, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for pts, t0, d, col, wd, head in items: draw_stroke(lay, pts, prog(t, t0, d), col, wd, head)
    fr.alpha_composite(lay)

def drop(fr, spr, cx, cy, t, t0, seed, rot=0, amp=2.0):
    sc = stamp_scale(t, t0, .24)
    if sc is None: return
    place_boil(fr, spr, cx, cy, t, seed, sc, rot + (sc - 1) * 25, amp)

def words(fr, items, t):
    """items: (sprite, cx, cy, t0, rot, seed) -> each stamped in by hand."""
    for spr, cx, cy, t0, rot, seed in items: drop(fr, spr, cx, cy, t, t0, seed, rot, 1.6)

# ---------------- scenes ----------------
def s_hook():
    d = 3.2; bg = paper(W, H, P["kraft"], 11)
    pol = polaroid(load("0a5478b7-image.jpg"), 860, 3, caption="solidpro, chennai")
    note = torn_paper(960, 470, P["paper"], 4, lined=True, holes=True)
    hl = highlighter(800, 118, P["hi"], 2)
    w1 = text("our very first", font("caveat700", 104), P["ink"])
    w2 = text("corporate order", font("dmserif_i", 124), P["ink"])
    star = starburst(125, YELLOW, "200 PADS", seed=2)
    tp1, tp2 = tape(250, 72, (250, 246, 236), 5, 150), tape(230, 66, (250, 246, 236), 8, 150)
    circ = scribble_circle(W / 2 + 10, 520, 440, 92, 4)
    arr = scribble_arrow((205, 1090), (330, 985), .45, 2)
    def draw(t):
        fr = bg.copy()
        drop(fr, pol, W / 2 + 20, 1230, t, 0.0, 1, 4)
        if t > .12: place_boil(fr, tp2, W / 2 - 250, 830, t, 9, rot=-32)
        drop(fr, note, W / 2, 470, t, .35, 2, -2)
        if t > .5: place_boil(fr, tp1, W / 2 + 10, 245, t, 7, rot=3)
        if t > .55:
            p = ease_out(prog(t, .95, .3)); place(fr, hl.crop((0, 0, max(1, int(hl.width * p)), hl.height)), W / 2 - 400 + hl.width * p / 2 + 10, 535, rot=-1)
        words(fr, [(w1, W / 2 - 130, 380, .6, -4, 3), (w2, W / 2, 520, .85, -1, 4)], t)
        strokes(fr, [(circ, 1.35, .55, ACC, 9, False), (arr, 1.95, .3, INK, 8, True)], t)
        drop(fr, star, 175, 960, t, 1.75, 5, -10)
        return fr
    return d, draw, dict(drops=[0, .35, .6, .85, 1.75], scrib=[(1.35, .55), (1.95, .3)])

def s_email():
    d = 3.0; bg = paper(W, H, P["paper"], 21)
    em = load("c4a1bc82-image.png", [(0, .165, 1, .238), (.08, .44, .8, .505), (0, .70, 1, .885)])
    em = em.crop((0, int(.085 * em.height), em.width, int(.60 * em.height)))
    pw = 900; ph = int(pw * em.height / em.width)
    piece = em.resize((pw, ph), Image.LANCZOS).convert("RGBA"); piece.putalpha(torn_mask(pw, ph, 6, 8))
    piece = drop_shadow(piece, 16, (6, 14), 120)
    pad = (piece.width - pw) // 2
    # circle target: "Napkin (L Size) - 200 Nos" at x .05-.60, y .372-.425 of full shot -> in crop
    y0 = (.372 - .085) / .515 * ph; y1 = (.425 - .085) / .515 * ph
    tp = tape(260, 74, (250, 246, 236), 3, 150)
    h1 = text("it started with", font("caveat700", 96), P["ink"])
    h2 = text("one email.", font("dmserif_i", 130), P["ink"])
    lab = label("nov 2 · napkin order request", P["paper"], P["ink"], 4, 38)
    def draw(t):
        fr = bg.copy(); z = 1 + .04 * t
        words(fr, [(h1, W / 2 - 150, 250, .1, -3, 1), (h2, W / 2 + 40, 370, .35, -1, 2)], t)
        top = 520; cx = W / 2
        if t > .5:
            sc = stamp_scale(t, .5, .25) or 1
            place_boil(fr, piece, cx, top + piece.height / 2, t, 3, sc * z, -1.5, 1.5)
            place_boil(fr, tp, cx + 10, top + 30, t, 4, rot=-3)
            ox, oy = cx - pw / 2, top + pad - 10
            circ = scribble_circle(ox + (.05 + .60) / 2 * pw, oy + (y0 + y1) / 2, .30 * pw, (y1 - y0) * .85, 9)
            strokes(fr, [(circ, 1.15, .55, ACC, 9, False)], t)
        drop(fr, lab, W / 2 - 60, 1740, t, 1.6, 5, -2)
        return fr
    return d, draw, dict(drops=[.1, .35, .5, 1.6], scrib=[(1.15, .55)])

def s_products():
    d = 3.0
    img = load("5443a15f-image.jpg", [(0, .585, .215, .665), (.255, .515, .43, .575), (.565, .525, .755, .59), (.755, .645, .965, .725), (.315, .83, .515, .9), (.09, .19, .245, .27)])
    pads = load("2216771e-image.jpg", [(.085, .385, .205, .432), (.375, .368, .525, .412), (.485, .418, .585, .462), (.245, .478, .375, .528), (.085, .16, .195, .205)])
    pol = polaroid(pads.crop((int(.25 * pads.width), int(.45 * pads.height), pads.width, pads.height)), 520, 6, caption="200 pads")
    strip = torn_paper(900, 190, P["paper"], 7, rough=10)
    tx = text("packed by hand, with love", font("caveat700", 80), P["ink"])
    star = starburst(110, P["accent2"], "2 OFFICES", seed=3)
    def draw(t):
        fr = cover(img, .45, .55, 1.0 + .08 * t / d)
        drop(fr, pol, 800, 1260, t, .5, 2, 6)
        drop(fr, strip, W / 2 - 40, 1650, t, .9, 3, -2)
        if stamp_scale(t, .9) is not None: place_boil(fr, tx, W / 2 - 40, 1645, t, 3, rot=-2)
        drop(fr, star, 230, 420, t, 1.4, 4, -8)
        return fr
    return d, draw, dict(drops=[.5, .9, 1.4])

def s_cable():
    d = 2.0; img = load("2d04058e-image.jpg")
    lab = label("even the cable glows", P["paper"], P["ink"], 6, 50)
    arr = scribble_arrow((300, 520), (560, 760), -.35, 3)
    def draw(t):
        fr = cover(img, .6, .45, 1.15 - .1 * t / d)
        drop(fr, lab, W / 2, 360, t, .2, 1, -3)
        strokes(fr, [(arr, .6, .35, (255, 255, 255, 255), 9, True)], t)
        return fr
    return d, draw, dict(drops=[.2], scrib=[(.6, .35)])

def collage(lab_txt, pics, d, seed):
    bg = paper(W, H, P["kraft"], seed)
    lab = label(lab_txt, P["paper"], P["ink"], seed, 54)
    pols = [polaroid(im, w, seed + k, caption=c) for k, (im, w, c, x, y, r) in enumerate(pics)]
    tps = [tape(200, 60, (250, 246, 236), seed + 10 + k, 150) for k in range(len(pics))]
    def draw(t):
        fr = bg.copy()
        drop(fr, lab, W / 2, 230, t, .1, seed, -2)
        for k, ((im, w, c, x, y, r), pol, tp) in enumerate(zip(pics, pols, tps)):
            t0 = .4 + k * .5
            drop(fr, pol, x, y, t, t0, seed + k, r)
            if t > t0 + .25: place_boil(fr, tp, x, y - pol.height / 2 + 40, t, seed + k + 30, rot=r * 2 + (8 if k % 2 else -8))
        return fr
    return d, draw, dict(drops=[.1] + [.4 + k * .5 for k in range(len(pics))])

def s_stop1():
    return collage("stop 1 · guindy", [
        (load("7dc870d8-image.jpg"), 560, "the building", 330, 720, -6),
        (load("ec8a9819-image.jpg", [(.03, .285, .33, .365)]), 560, "4th floor", 760, 1030, 5),
        (load("83dfb7ec-image.jpg"), 600, "welcome!", 380, 1450, -3)], 3.2, 31)

def delivered(src, cap, note_txt, seed, crop=None):
    d = 2.8; bg = paper(W, H, P["paper"], seed)
    im = load(src)
    if crop: im = im.crop(crop(im))
    pol = polaroid(im, 900, seed, caption=cap)
    st = rubber_stamp("DELIVERED", RED, seed, 120, -14)
    nt = text(note_txt, font("marker", 84), P["ink"])
    ck = check_mark(870, 1690, 40, seed)
    tp = tape(240, 70, (250, 246, 236), seed, 150)
    def draw(t):
        fr = bg.copy()
        drop(fr, pol, W / 2, 900, t, 0, seed, -3)
        if t > .2: place_boil(fr, tp, W / 2, 900 - pol.height / 2 + 30, t, seed + 1, rot=-4)
        sc = stamp_scale(t, .85, .14)
        if sc is not None: place(fr, st, W / 2 + 150, 1300, sc, 0)
        drop(fr, nt, W / 2 - 80, 1690, t, 1.3, seed + 2, -3)
        strokes(fr, [(ck, 1.55, .25, (40, 140, 80, 255), 12, False)], t)
        return fr
    return d, draw, dict(drops=[0, 1.3], thud=[.85], scrib=[(1.55, .25)])

def s_del1(): return delivered("81dda3e6-image.jpg", "handed over in person", "100 pads", 41)

def s_stop2():
    return collage("stop 2 · vandalur", [
        (load("185a4fd3-image.jpg"), 480, "AIC Crescent", 330, 650, -5),
        (load("75fc7e52-image.jpg"), 500, "in we go", 780, 1010, 6),
        (load(os.path.join(HERE, "selfie.jpg")), 460, "almost there", 360, 1500, -4)], 3.2, 51)

def s_del2(): return delivered("2eafdb42-image.jpg", "every woman, every day", "100 more", 61, crop=lambda im: (0, int(.08 * im.height), im.width, int(.88 * im.height)))

def s_deal():
    d = 2.8; bg = paper(W, H, P["kraft"], 71)
    doc = load("1b74c03c-image.jpg", [(0, .108, 1, .247), (.02, .262, 1, .318), (.02, .334, 1, .39), (.02, .405, 1, .452), (.02, .47, 1, .512), (.02, .53, 1, .685), (.02, .70, 1, .775), (0, .78, 1, 1.0)])
    pw = 820; page = doc.resize((pw, int(pw * doc.height / doc.width)), Image.LANCZOS).convert("RGBA"); page = drop_shadow(page, 18, (8, 16), 120)
    note = sticky_note(560, 520, YELLOW, 3)
    n1 = text("next up:", font("caveat700", 92), P["ink"]); n2 = text("1-year", font("marker", 110), P["ink"]); n3 = text("supply deal", font("caveat700", 96), P["ink"])
    ul = scribble_underline(590, 900, 1478, 4)
    def draw(t):
        fr = bg.copy()
        drop(fr, page, W / 2 - 60, 820, t, 0, 1, -4)
        drop(fr, note, 730, 1330, t, .55, 2, 5)
        if stamp_scale(t, .55) is not None:
            words(fr, [(n1, 700, 1180, .75, 5, 3), (n2, 730, 1300, .95, 5, 4), (n3, 740, 1420, 1.15, 5, 5)], t)
        strokes(fr, [(ul, 1.5, .3, ACC, 8, False)], t)
        return fr
    return d, draw, dict(drops=[0, .55, .75, .95, 1.15], scrib=[(1.5, .3)])

def s_founder():
    d = 3.0; bg = paper(W, H, P["kraft"], 81)
    c = Image.open(os.path.join(CUT, "6f69f974_cut.png")); a = np.array(c.getchannel("A")); a[int(.88 * c.height):, :int(.3 * c.width)] = 0; c.putalpha(Image.fromarray(a))
    c = c.crop(c.getbbox()); c = c.resize((int(c.width * 1150 / c.height), 1150), Image.LANCZOS)
    stk = sticker_cut(c, 16)
    note = torn_paper(900, 430, P["paper"], 82, lined=True)
    l1 = text("if a small brand", font("caveat700", 92), P["ink"]); l2 = text("can do it...", font("caveat700", 92), P["ink"])
    l3 = text("so can you.", font("marker", 120), P["accent"])
    def draw(t):
        fr = bg.copy()
        drop(fr, stk, W / 2 + 150, H - stk.height / 2 + 60, t, 0, 1, 3)
        drop(fr, note, W / 2 - 20, 430, t, .35, 2, -3)
        if stamp_scale(t, .35) is not None:
            words(fr, [(l1, W / 2 - 40, 330, .55, -3, 3), (l2, W / 2 - 80, 440, .85, -3, 4), (l3, W / 2 + 10, 570, 1.3, -4, 5)], t)
        return fr
    return d, draw, dict(drops=[0, .35, .55, .85, 1.3])

def s_cta():
    d = 3.2; bg = torn_paper(W + 60, H + 60, P["paper"], 91, lined=True, holes=True, shadow=False)
    base = paper(W, H, P["kraft"], 92); base.alpha_composite(bg, (-30, -30))
    l1 = text("become a", font("caveat700", 110), P["ink"])
    l2 = text("Vriksh reseller", font("dmserif_i", 132), P["ink"])
    hl = highlighter(860, 128, P["hi"], 5)
    lab = label('DM "RESELLER" to start', P["accent2"], P["ink"], 9, 50)
    st = starburst(120, YELLOW, "START TODAY", seed=7)
    arr = scribble_arrow((260, 1180), (330, 1030), .5, 6)
    def draw(t):
        fr = base.copy()
        words(fr, [(l1, W / 2 - 170, 640, .1, -3, 1)], t)
        p = ease_out(prog(t, .45, .3))
        if p > 0: place(fr, hl.crop((0, 0, max(1, int(hl.width * p)), hl.height)), W / 2 - 430 + hl.width * p / 2, 815, rot=-1)
        words(fr, [(l2, W / 2, 800, .35, -1, 2), (lab, W / 2 + 40, 1240, 1.0, -2, 3), (st, 820, 520, 1.5, 10, 4)], t)
        strokes(fr, [(arr, 1.25, .3, ACC, 8, True)], t)
        return fr
    return d, draw, dict(drops=[.1, .35, 1.0, 1.5], scrib=[(1.25, .3)])

def s_end():
    d = 3.4; bg = paper(W, H, (18, 74, 64), 101, strength=1.6)
    lg = Image.open(LOGO).convert("RGB").resize((760, 755), Image.LANCZOS)
    yy, xx = np.mgrid[0:lg.height, 0:lg.width].astype(np.float32); r = np.sqrt((xx - lg.width / 2) ** 2 + (yy - lg.height / 2) ** 2)
    logo = lg.convert("RGBA"); logo.putalpha(Image.fromarray((np.clip((385 - r) / 25, 0, 1) * 255).astype(np.uint8)))
    lab = label("herbal sanitary napkins · UAE & India", P["paper"], P["ink"], 3, 36)
    hd = text("@vrikshherbalsanitarynapkins", font("caveat700", 74), (246, 241, 230))
    def draw(t):
        fr = bg.copy()
        drop(fr, logo, W / 2, 700, t, .05, 1, -2, 1.2)
        drop(fr, lab, W / 2, 1160, t, .7, 2, -2)
        drop(fr, hd, W / 2, 1290, t, 1.0, 3, -1)
        return fr
    return d, draw, dict(drops=[.05, .7, 1.0])

SCENES = [s_hook, s_email, s_products, s_cable, s_stop1, s_del1, s_stop2, s_del2, s_deal, s_founder, s_cta, s_end]
WIPES = [(P["paper"], 1, "up"), (P["accent2"], 2, "side"), (P["paper"], 3, "up"), (P["kraft"], 4, "side"), (P["paper"], 5, "up"),
         (P["accent2"], 6, "side"), (P["paper"], 7, "up"), (P["kraft"], 8, "side"), (P["accent2"], 9, "up"), (P["paper"], 10, "side"), (P["paper"], 11, "up")]

def render(i):
    d, draw, ev = SCENES[i](); n = int(round(d * FPS))
    path = os.path.join(CL, f"{i:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for j in range(n):
        t = j / FPS; fr = draw(t)
        if i > 0: c, s, dr = WIPES[i - 1]; wipe(fr, t, d, c, s, dr, "in")
        if i < len(SCENES) - 1: c, s, dr = WIPES[i]; wipe(fr, t, d, c, s, dr, "out")
        fr.alpha_composite(grain(int(t * 12) + i * 100, 9))
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()
    return i, d, ev

def main(idx):
    with mp.get_context("fork").Pool(4) as p:
        res = {i: (d, ev) for i, d, ev in p.imap_unordered(render, idx)}
    for i in sorted(res): print("scene", i, flush=True)
    json.dump({str(i): res[i] for i in res}, open(os.path.join(WORK, f"ev_{'_'.join(map(str, idx))}.json"), "w"))

def assemble():
    evs = {}
    for f in os.listdir(WORK):
        if f.startswith("ev_"): evs.update(json.load(open(os.path.join(WORK, f))))
    durs = [evs[str(i)][0] for i in range(len(SCENES))]; starts = np.cumsum([0] + durs[:-1]).tolist(); total = sum(durs)
    tl = dict(total=total, n=len(SCENES), cuts=starts[1:], pops=[], thuds=[], scribbles=[], rustles=[s - .2 for s in starts[1:]])
    for i in range(len(SCENES)):
        ev = evs[str(i)][1]; s0 = starts[i]
        tl["pops"] += [s0 + x for x in ev.get("drops", [])]; tl["thuds"] += [s0 + x for x in ev.get("thud", [])]
        tl["scribbles"] += [[s0 + a, b] for a, b in ev.get("scrib", [])]
    json.dump(tl, open(os.path.join(WORK, "timeline.json"), "w"))
    subprocess.run([sys.executable, "/home/user/i-hate-editing/.claude/skills/handmade-edit/scripts/lofi_score.py", WORK], check=True)
    lst = os.path.join(WORK, "list.txt"); open(lst, "w").write("".join(f"file 'clips/{i:02d}.mp4'\n" for i in range(len(SCENES))))
    out = os.path.join(WORK, "Vriksh_Corporate_Order_Handmade_9x16.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(WORK, "score.wav"),
                    "-filter_complex", "[0:v]eq=contrast=1.03:saturation=1.05,format=yuv420p[v];[1]volume=1.25,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    fin = out.replace(".mp4", "_final.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-c:v", "copy", "-af", "volume=1.3dB,alimiter=limit=0.79:level=false",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", fin], check=True); os.replace(fin, out)
    print("wrote", out, total)

if __name__ == "__main__":
    if sys.argv[1] == "render": main([int(x) for x in sys.argv[2:]] or list(range(len(SCENES))))
    else: assemble()
