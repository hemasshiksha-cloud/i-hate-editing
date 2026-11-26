"""Vriksh online orders (Amazon.ae + Flipkart): HANDMADE style, acoustic score."""
import os, sys, json, math, subprocess
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw
SK = "/home/user/i-hate-editing/.claude/skills/handmade-edit/scripts"
sys.path.insert(0, SK)
from handmade import *

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/edd7c674-b2d9-5a5c-bf23-e040c7fcf3b2/"
LOGO = "/home/user/i-hate-editing/.claude/skills/vriksh-reel/assets/vriksh_logo.jpg"
WORK = os.path.join(HERE, "work"); CL = os.path.join(WORK, "clips"); os.makedirs(CL, exist_ok=True)
P = PALETTES["vriksh"]; INK = P["ink"] + (255,); ACC = P["accent"] + (255,); RED = (196, 44, 56); GRN = (40, 130, 70)
YELLOW = (255, 226, 120); WHITE = (255, 255, 255, 255)

def load(src, blur=()):
    im = ImageOps.exif_transpose(Image.open(UP + src)).convert("RGB")
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
    return img.resize((W, H), Image.LANCZOS, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA"), (cx - cw / 2, cy - ch / 2, cw, ch)

def frames(src, ss, d, sp, size, fit="cover", fy=.5):
    """decode a clip at speed sp -> list of RGB frames (natural grade: tiny contrast, light sharpen)."""
    w, h = size; n = int(round(d * FPS))
    if fit == "cover": sc = f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h}:(iw-{w})/2:(ih-{h})*{fy}"
    else: sc = f"scale={w}:-2:flags=lanczos"
    vf = f"setpts=PTS/{sp},fps={FPS},{sc},unsharp=5:5:0.6,eq=contrast=1.03:saturation=1.04"
    p = subprocess.run(["ffmpeg", "-loglevel", "quiet", "-ss", str(ss), "-t", str(d * sp + .4), "-i", UP + src, "-vf", vf, "-an",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    raw = p.stdout
    if fit == "cover": fh = h
    else:
        probe = subprocess.run(["ffmpeg", "-loglevel", "quiet", "-ss", str(ss), "-i", UP + src, "-frames:v", "1", "-vf", sc, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        fh = len(probe) // (w * 3)
    fs = len(raw) // (w * fh * 3); out = []
    for k in range(n):
        j = min(k, fs - 1); out.append(Image.frombytes("RGB", (w, fh), raw[j * w * fh * 3:(j + 1) * w * fh * 3]))
    return out

def strokes(fr, items, t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for pts, t0, d, col, wd, head in items: draw_stroke(lay, pts, prog(t, t0, d), col, wd, head)
    fr.alpha_composite(lay)

def drop(fr, spr, cx, cy, t, t0, seed, rot=0, amp=2.0):
    sc = stamp_scale(t, t0, .24)
    if sc is None: return
    place_boil(fr, spr, cx, cy, t, seed, sc, rot + (sc - 1) * 25, amp)

def torn_shot(img, w, seed, rough=8):
    h = int(w * img.height / img.width); p = img.resize((w, h), Image.LANCZOS).convert("RGBA"); p.putalpha(torn_mask(w, h, seed, rough))
    return drop_shadow(p, 16, (6, 14), 120)

def strip_text(txt, f, seed, pad=(46, 24), col=None):
    t = text(txt, f, P["ink"]); s = torn_paper(t.width + pad[0] * 2, t.height + pad[1] * 2, col or P["paper"], seed, rough=7, shadow=False)
    s.alpha_composite(t, (pad[0], pad[1])); return drop_shadow(s, 10, (4, 8), 100)

# ---------------- scenes ----------------
def s_hook():
    d = 4.4; bg = paper(W, H, P["kraft"], 201)
    first = torn_shot(Image.open(os.path.join(HERE, "first_order.png")).convert("RGB"), 860, 2)
    oct29 = torn_shot(Image.open(os.path.join(HERE, "oct29.png")).convert("RGB"), 880, 5)
    nov1 = torn_shot(Image.open(os.path.join(HERE, "nov1.png")).convert("RGB"), 880, 6)
    amz = torn_shot(load("8d03a5c8-image.png").crop((0, int(.37 * 2796), 1290, int(.539 * 2796))), 900, 3)
    fk = torn_shot(load("2edffb05-image.jpg", [(.17, .55, .88, .70)]), 900, 4)
    ago = text("a month ago:", font("caveat700", 92), P["ink"]); now = text("now:", font("caveat700", 110), P["ink"])
    b1 = text("so let's", font("caveat700", 92), P["ink"]); b2 = text("pack them.", font("dmserif_i", 136), P["ink"])
    star = starburst(112, YELLOW, "2 STORES", seed=4)
    fh = first.height; circ = scribble_circle(W / 2 + 125, 470 - fh / 2 + 30 + .37 * (fh - 60), 250, 50, 3)
    stack = [(oct29, 1010, -4, 1.75), (nov1, 1120, 3, 1.95), (amz, 1240, -2, 2.15), (fk, 1400, 2, 2.4)]
    def draw(t):
        fr = bg.copy()
        drop(fr, ago, W / 2 - 230, 200, t, .05, 1, -4)
        drop(fr, first, W / 2, 470, t, .3, 2, -3)
        strokes(fr, [(circ, .85, .45, ACC, 9, False)], t)
        drop(fr, now, 170, 800, t, 1.45, 3, -6)
        for k, (spr, y, r, t0) in enumerate(stack): drop(fr, spr, W / 2 + (25 if k % 2 else -15), y, t, t0, 10 + k, r)
        drop(fr, star, 905, 790, t, 2.7, 4, 12)
        drop(fr, b1, W / 2 - 230, 1690, t, 3.0, 5, -3); drop(fr, b2, W / 2 + 60, 1810, t, 3.25, 6, -2)
        return fr
    return d, draw, dict(drops=[.05, .3, 1.45, 1.75, 1.95, 2.15, 2.4, 2.7, 3.0, 3.25], scrib=[(.85, .45)], ching=[.3, 2.15])

def clip_scene(src, ss, d, sp, fy, lab_txt=None, note_txt=None, lab_y=300, note_y=1600, extra=None):
    def make():
        fs = frames(src, ss, d, sp, (W, H), fy=fy)
        lab = label(lab_txt, P["paper"], P["ink"], len(lab_txt or "x") * 7, 46) if lab_txt else None
        note = strip_text(note_txt, font("caveat700", 78), len(note_txt or "y") * 5) if note_txt else None
        def draw(t):
            fr = fs[min(int(t * FPS), len(fs) - 1)].convert("RGBA")
            if lab: drop(fr, lab, W / 2, lab_y, t, .12, 1, -2)
            if note: drop(fr, note, W / 2 + 20, note_y, t, .5, 2, -3)
            return fr
        ev = dict(drops=([.12] if lab else []) + ([.5] if note else [])); ev.update(extra or {})
        return d, draw, ev
    return make

s_lights = clip_scene("619c1064-IMG_0749.mov", 0.25, 1.3, 1.0, .5, "the routine starts", None, extra=dict(click=[.55]))
s_laptop = clip_scene("e93b2d24-IMG_0822.mov", 2.6, 1.7, 1.4, .5, "step 1 · open the seller hub", None)
s_cupboard = clip_scene("0b654c6e-IMG_0750.mov", 0.35, 1.2, 1.0, .5, None, "grab from stock", note_y=1620)
s_mailer = clip_scene("207b7a9a-IMG_0751.mov", 0.0, 1.4, 0.85, .55, "into the mailer", None)

def s_shelf():
    d = 2.1; img = load("ad80ce39-image.jpg")
    lab = label("the stock room", P["paper"], P["ink"], 5, 54)
    note = strip_text("(yes, it's a shelf)", font("caveat700", 70), 6)
    def draw(t):
        fr, _ = cover(img, .5, .55, 1.0 + .07 * t / d)
        drop(fr, lab, W / 2 - 120, 330, t, .25, 1, -3); drop(fr, note, W / 2 + 140, 450, t, .7, 2, 2)
        return fr
    return d, draw, dict(drops=[.25, .7])

def s_pickup():
    d = 2.5; img = load("70e2dbe9-image.jpg")
    lab = label("step 2 · schedule the pickup", P["paper"], P["ink"], 7, 46)
    def draw(t):
        z = 1.05 + .1 * ease_inout(t / d)
        fr, (x, y, cw, ch) = cover(img, .52, .55, z)
        mp_ = lambda u, v: ((u * img.width - x) / cw * W, (v * img.height - y) / ch * H)
        (a0, b0), (a1, b1) = mp_(.39, .507), mp_(.65, .593)
        circ = scribble_circle((a0 + a1) / 2, (b0 + b1) / 2, (a1 - a0) / 2 + 40, (b1 - b0) / 2 + 30, 5)
        strokes(fr, [(circ, .7, .5, ACC, 10, False)], t)
        drop(fr, lab, W / 2, 330, t, .15, 1, -2)
        return fr
    return d, draw, dict(drops=[.15], scrib=[(.7, .5)], click=[1.3])

def s_print():
    d = 3.0; bg = paper(W, H, P["paper"], 301)
    fs = frames("4fc574c7-b1e98f07-5234-422c-8590-e10d90806365.mov", 0.0, d, 1.0, (760, 0), fit="w")
    lab = label("step 3 · print the label", P["paper"], P["ink"], 8, 48)
    note = text("little printer, big day", font("caveat700", 80), P["ink"])
    tp = tape(240, 70, (250, 246, 236), 9, 150)
    def draw(t):
        fr = bg.copy(); k = min(int(t * FPS), len(fs) - 1)
        pol = polaroid(fs[k], 820, 11, caption=None)
        sc = stamp_scale(t, 0, .24) or 1
        place_boil(fr, pol, W / 2, 930, t, 2, sc, -2 + (sc - 1) * 20, 1.2)
        place_boil(fr, tp, W / 2, 930 - pol.height / 2 + 30, t, 3, rot=-3)
        drop(fr, lab, W / 2, 260, t, .2, 1, -2)
        drop(fr, note, W / 2 - 30, 1700, t, 1.4, 4, -3)
        return fr
    return d, draw, dict(drops=[0, .2, 1.4], whirr=[(.35, 2.1)])

def s_peel():
    d = 1.7; fs = frames("3541e773-IMG_1371.mov", 2.9, d, 1.0, (W, H))
    lab = label("step 4 · barcode on every pack", P["paper"], P["ink"], 10, 44)
    def draw(t):
        fr = fs[min(int(t * FPS), len(fs) - 1)].convert("RGBA"); drop(fr, lab, W / 2, 300, t, .1, 1, -2); return fr
    return d, draw, dict(drops=[.1], peel=[.5])

def s_stick():
    d = 1.9; fs = frames("1ef17619-IMG_1372.mov", 0.3, d, 1.0, (W, H), fy=.45)
    note = strip_text("peel. stick. smooth.", font("caveat700", 78), 12)
    def draw(t):
        fr = fs[min(int(t * FPS), len(fs) - 1)].convert("RGBA"); drop(fr, note, W / 2, 1600, t, .5, 2, -3); return fr
    return d, draw, dict(drops=[.5], peel=[.15])

def s_pack():
    d = 2.4; fs = frames("e9d18149-IMG_1370.mov", 7.2, d, 1.6, (W, H), fy=.5)
    note = strip_text("packing the order", font("caveat700", 80), 13)
    def draw(t):
        fr = fs[min(int(t * FPS), len(fs) - 1)].convert("RGBA"); drop(fr, note, W / 2 + 30, 1620, t, .35, 2, 2); return fr
    return d, draw, dict(drops=[.35])

def s_hiccup():
    d = 3.2; bg = paper(W, H, P["kraft"], 401)
    em = load("f04a7591-image.png", [(0, .200, .72, .238), (.08, .452, .55, .498)]).crop((0, int(.10 * 2796), 1290, int(.70 * 2796)))
    S = torn_shot(em, 840, 7); sh = S.height; pad = (S.width - 840) // 2
    top = text("not every day is smooth...", font("caveat700", 84), P["ink"])
    b1 = text("fixed.", font("marker", 120), P["accent"]); b2 = text("back in stock.", font("caveat700", 92), P["ink"])
    ytop = 960 - sh / 2 + pad; hgt = sh - 2 * pad
    ul = scribble_underline(W / 2 - 420 + .11 * 840, W / 2 - 420 + .72 * 840, ytop + (.637 - .10) / .60 * hgt + 22, 6)
    def draw(t):
        fr = bg.copy()
        drop(fr, top, W / 2, 240, t, .05, 1, -2)
        drop(fr, S, W / 2, 960, t, .3, 2, -1.5)
        strokes(fr, [(ul, 1.0, .45, (40, 140, 80, 255), 9, False)], t)
        drop(fr, b1, W / 2 - 230, 1690, t, 1.7, 3, -5); drop(fr, b2, W / 2 + 160, 1700, t, 2.0, 4, -2)
        return fr
    return d, draw, dict(drops=[.05, .3, 1.7, 2.0], scrib=[(1.0, .45)])

def s_door():
    d = 2.6; fs = frames("500b663a-IMG_1375.mov", 3.7, d, .55, (W, H), fy=.6)
    lab = label("step 5 · ready for pickup", P["paper"], P["ink"], 14, 46)
    st = rubber_stamp("SHIPPED", RED, 5, 130, -12)
    def draw(t):
        fr = fs[min(int(t * FPS), len(fs) - 1)].convert("RGBA")
        drop(fr, lab, W / 2, 300, t, .15, 1, -2)
        sc = stamp_scale(t, 1.0, .14)
        if sc is not None: place(fr, st, W / 2 + 60, 1450, sc)
        return fr
    return d, draw, dict(drops=[.15], thud=[1.0])

def s_map():
    d = 3.2; bg = paper(W, H, P["kraft"], 501)
    t1 = strip_text("AMAZON.AE", font("marker", 76), 21, col=P["paper"]); t1b = text("UAE", font("typewriter", 52), P["ink"])
    t2 = strip_text("FLIPKART", font("marker", 76), 22, col=P["accent2"]); t2b = text("INDIA", font("typewriter", 52), P["ink"])
    mid1 = text("one little shelf.", font("caveat700", 96), P["ink"]); mid2 = text("two countries.", font("dmserif_i", 130), P["ink"])
    arc = scribble_arrow((300, 560), (760, 1220), .45, 8, n=90)
    dashes = [arc[i:i + 7] for i in range(0, len(arc) - 7, 12)]
    def draw(t):
        fr = bg.copy()
        drop(fr, t1, 300, 420, t, .1, 1, -4); drop(fr, t1b, 300, 530, t, .3, 2, -3)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); p = prog(t, .55, .7)
        for k, dsh in enumerate(dashes):
            if k / len(dashes) < p: draw_stroke(lay, dsh, 1, INK, 8)
        if p >= 1: draw_stroke(lay, arc[-14:], 1, INK, 8, head=True)
        fr.alpha_composite(lay)
        drop(fr, t2, 760, 1330, t, 1.25, 3, 3); drop(fr, t2b, 760, 1440, t, 1.45, 4, 2)
        drop(fr, mid1, W / 2 + 120, 760, t, 1.8, 5, -3); drop(fr, mid2, W / 2 + 60, 900, t, 2.1, 6, -2)
        return fr
    return d, draw, dict(drops=[.1, .3, 1.25, 1.45, 1.8, 2.1], scrib=[(.55, .7)])

def s_cta():
    d = 3.3; base = paper(W, H, P["kraft"], 601)
    sheet = torn_paper(W + 60, H + 60, P["paper"], 602, lined=True, holes=True, shadow=False); base.alpha_composite(sheet, (-30, -30))
    l1 = text("find Vriksh on", font("caveat700", 110), P["ink"])
    l2 = text("Amazon.ae & Flipkart", font("dmserif_i", 112), P["ink"])
    hl = highlighter(1000, 118, P["hi"], 5)
    lab = label('search "Vriksh Made For Her"', P["accent2"], P["ink"], 9, 46)
    st = starburst(120, YELLOW, "SHOP NOW", seed=7)
    arr = scribble_arrow((250, 1190), (330, 1050), .5, 6)
    def draw(t):
        fr = base.copy()
        drop(fr, l1, W / 2 - 130, 640, t, .1, 1, -3)
        p = ease_out(prog(t, .45, .3))
        if p > 0: place(fr, hl.crop((0, 0, max(1, int(hl.width * p)), hl.height)), W / 2 - 500 + hl.width * p / 2, 815, rot=-1)
        drop(fr, l2, W / 2, 800, t, .35, 2, -1); drop(fr, lab, W / 2 + 40, 1240, t, 1.0, 3, -2); drop(fr, st, 840, 470, t, 1.5, 4, 10)
        strokes(fr, [(arr, 1.25, .3, ACC, 8, True)], t)
        return fr
    return d, draw, dict(drops=[.1, .35, 1.0, 1.5], scrib=[(1.25, .3)], ching=[1.5])

def s_end():
    d = 3.0; bg = paper(W, H, (18, 74, 64), 701, strength=1.6)
    lg = Image.open(LOGO).convert("RGB").resize((760, 755), Image.LANCZOS)
    yy, xx = np.mgrid[0:lg.height, 0:lg.width].astype(np.float32); r = np.sqrt((xx - lg.width / 2) ** 2 + (yy - lg.height / 2) ** 2)
    logo = lg.convert("RGBA"); logo.putalpha(Image.fromarray((np.clip((385 - r) / 25, 0, 1) * 255).astype(np.uint8)))
    lab = label("herbal sanitary napkins · UAE & India", P["paper"], P["ink"], 3, 36)
    hd = text("@vrikshherbalsanitarynapkins", font("caveat700", 74), (246, 241, 230))
    def draw(t):
        fr = bg.copy(); drop(fr, logo, W / 2, 700, t, .05, 1, -2, 1.2); drop(fr, lab, W / 2, 1160, t, .7, 2, -2); drop(fr, hd, W / 2, 1290, t, 1.0, 3, -1)
        return fr
    return d, draw, dict(drops=[.05, .7, 1.0])

SCENES = [s_hook, s_lights, s_laptop, s_cupboard, s_shelf, s_pickup, s_print, s_peel, s_stick, s_mailer, s_hiccup, s_door, s_map, s_cta, s_end]
# transitions: paper wipes on story beats, hard cuts inside the fast dispatch run (4->5->6)
WIPES = [(P["paper"], 1, "up"), None, None, None, (P["accent2"], 2, "side"), (P["paper"], 3, "up"), (P["kraft"], 4, "side"), None, None,
         (P["paper"], 5, "up"), (P["accent2"], 6, "side"), (P["paper"], 7, "up"), (P["kraft"], 8, "side"), (P["paper"], 9, "up")]

def render(i):
    d, draw, ev = SCENES[i](); n = int(round(d * FPS)); path = os.path.join(CL, f"{i:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for j in range(n):
        t = j / FPS; fr = draw(t)
        if i > 0 and WIPES[i - 1]: c, s, dr = WIPES[i - 1]; wipe(fr, t, d, c, s, dr, "in")
        if i < len(SCENES) - 1 and WIPES[i]: c, s, dr = WIPES[i]; wipe(fr, t, d, c, s, dr, "out")
        fr.alpha_composite(grain(int(t * 12) + i * 100, 8))
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); return i, d, ev

def main(idx):
    with mp.get_context("fork").Pool(4) as p:
        for i, d, ev in p.imap_unordered(render, idx):
            json.dump([d, ev], open(os.path.join(WORK, f"ev{i:02d}.json"), "w")); print("scene", i, flush=True)

def assemble():
    evs = [json.load(open(os.path.join(WORK, f"ev{i:02d}.json"))) for i in range(len(SCENES))]
    durs = [e[0] for e in evs]; starts = np.cumsum([0] + durs[:-1]).tolist(); total = sum(durs)
    tl = dict(total=total, cuts=starts[1:], pops=[], thuds=[], scribbles=[], chings=[], whirrs=[], peels=[], clicks=[],
              rustles=[starts[k + 1] - .2 for k in range(len(WIPES)) if WIPES[k]], hits=[starts[k + 1] for k in range(len(WIPES)) if not WIPES[k]])
    for i, (d, ev) in enumerate(evs):
        s0 = starts[i]
        for k, dst in [("drops", "pops"), ("thud", "thuds"), ("ching", "chings"), ("peel", "peels"), ("click", "clicks")]:
            tl[dst] += [s0 + x for x in ev.get(k, [])]
        tl["scribbles"] += [[s0 + a, b] for a, b in ev.get("scrib", [])]; tl["whirrs"] += [[s0 + a, b] for a, b in ev.get("whirr", [])]
    json.dump(tl, open(os.path.join(WORK, "timeline.json"), "w"))
    subprocess.run([sys.executable, os.path.join(SK, "acoustic_score.py"), WORK], check=True)
    lst = os.path.join(WORK, "list.txt"); open(lst, "w").write("".join(f"file 'clips/{i:02d}.mp4'\n" for i in range(len(SCENES))))
    raw = os.path.join(WORK, "raw.mp4"); out = os.path.join(WORK, "Vriksh_Online_Orders_9x16.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(WORK, "score.wav"),
                    "-filter_complex", "[0:v]format=yuv420p[v];[1]volume=1.25,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", raw], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-c:v", "copy", "-af", "acompressor=threshold=0.12:ratio=3:attack=3:release=80:makeup=1.6,loudnorm=I=-14:TP=-2:LRA=8,aresample=48000",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
    print("wrote", out, round(total, 2))

if __name__ == "__main__":
    if sys.argv[1] == "render": main([int(x) for x in sys.argv[2:]] or list(range(len(SCENES))))
    else: assemble()
