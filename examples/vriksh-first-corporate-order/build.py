"""Vriksh: first corporate order. High-retention 9:16 reel.
python3 build.py render [i ...] | assemble
"""
import os, sys, json, math, random, subprocess
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SK = "/home/user/i-hate-editing/.claude/skills/vriksh-reel"
sys.path.insert(0, SK + "/scripts")
import brand as ms
from brand import W, H, FPS, prog, ease_out, ease_inout, back_out, clamp, gradient, Drift, paste, GREEN, CREAM, GOLD, SAGE

UP = "/root/.claude/uploads/edd7c674-b2d9-5a5c-bf23-e040c7fcf3b2/"
F2 = os.path.join(os.path.dirname(HERE), "fonts2")
WORK = os.path.join(HERE, "work"); CL = os.path.join(WORK, "clips"); os.makedirs(CL, exist_ok=True)
T = 0.25
LIME = (215, 247, 91); DARK = (14, 40, 32); WHITE = (255, 255, 255)
BRAND_BG = ((20, 78, 68), (8, 40, 34))

def FT(name, size): return ImageFont.truetype(os.path.join(F2, name + ".ttf"), size)

# ---------------- shot plan ----------------
# cap: list of lines, words wrapped in * are highlighted
SHOTS = [
 dict(k="hook", d=2.9),
 dict(k="photo", src="c4a1bc82-image.png", d=2.8, fx=.4, fy=.40, z=(1.0, 1.55), sharp=0,
      blur=[(0, .165, 1, .238), (.08, .44, .8, .505), (0, .70, 1, .885)],
      ring=(.05, .372, .60, .425, .55), cap=["IT STARTED WITH", "*ONE EMAIL*"], top=True),
 dict(k="photo", src="2216771e-image.jpg", d=2.0, fx=.55, fy=.6, z=(1.12, 1.0),
      blur=[(.085, .385, .205, .432), (.375, .368, .525, .412), (.485, .418, .585, .462), (.245, .478, .375, .528), (.085, .16, .195, .205)],
      cap=["*200 PADS*", "2 OFFICES"]),
 dict(k="photo", src="5443a15f-image.jpg", d=1.6, fx=.45, fy=.55, z=(1.0, 1.1),
      blur=[(0, .585, .215, .665), (.255, .515, .43, .575), (.565, .525, .755, .59), (.755, .645, .965, .725), (.315, .83, .515, .9), (.09, .19, .245, .27)],
      cap=["BRANDED", "*PAD HOLDERS*"]),
 dict(k="photo", src="2d04058e-image.jpg", d=1.5, fx=.6, fy=.45, z=(1.15, 1.02), cap=["EVEN THE", "*CABLE* GLOWS"]),
 dict(k="photo", src="7dc870d8-image.jpg", d=1.6, fx=.4, fy=.45, z=(1.12, 1.0), cap=["STOP 1:", "*GUINDY*"], top=True),
 dict(k="photo", src="ec8a9819-image.jpg", d=1.3, fx=.55, fy=.35, z=(1.0, 1.1), blur=[(.03, .285, .33, .365)]),
 dict(k="photo", src="659d8dd3-image.jpg", d=1.0, fx=.72, fy=.27, z=(1.35, 1.5), blur=[(.36, .31, .87, .39)]),
 dict(k="photo", src="83dfb7ec-image.jpg", d=1.3, fx=.6, fy=.2, z=(1.05, 1.15)),
 dict(k="photo", src="f27af10c-image.jpg", d=1.2, fx=.62, fy=.5, z=(1.0, 1.1)),
 dict(k="card", src="81dda3e6-image.jpg", d=2.6, cap=["*DELIVERED.*", "100 PADS"]),
 dict(k="photo", src="185a4fd3-image.jpg", d=1.6, fx=.5, fy=.42, z=(1.0, 1.1), cap=["STOP 2:", "*VANDALUR*"], top=True),
 dict(k="photo", src="75fc7e52-image.jpg", d=1.1, fx=.5, fy=.5, z=(1.1, 1.0)),
 dict(k="video", src="bc58fdd7-c3a95c3a-ee2d-4d3e-a9f4-b124f2e4d659.mov", d=1.6, ss=27.0, sp=1.0, fy=.5, cap=["ALMOST", "*THERE*"]),
 dict(k="card", src="2eafdb42-image.jpg", d=2.6, cw=800, cap=["*DELIVERED.*", "100 MORE"]),
 dict(k="card", src="1b74c03c-image.jpg", d=2.6, quiet=True, cw=880,
      blur=[(0, .108, 1, .247), (.02, .262, 1, .318), (.02, .334, 1, .39), (.02, .405, 1, .452), (.02, .47, 1, .512), (.02, .53, 1, .685), (.02, .70, 1, .775), (0, .78, 1, 1.0)],
      cap=["NEXT:", "*1-YEAR SUPPLY DEAL*"]),
 dict(k="founder", d=2.7),
 dict(k="cta", d=3.8),
 dict(k="end", d=3.4),
]
TRANS = ["zoomin", "slideup", "smoothleft", "smoothleft", "fadeblack", "smoothup", "slideleft", "smoothleft",
         "slideup", "fadewhite", "fadeblack", "slideleft", "smoothleft", "fadewhite", "smoothup", "circleopen",
         "slideup", "circleopen"]
assert len(TRANS) == len(SHOTS) - 1
CAP_T0, CAP_STAG = 0.12, 0.09

# ---------------- helpers ----------------
_cache = {}
def load(src, blur=()):
    key = (src, tuple(blur))
    if key in _cache: return _cache[key]
    im = ImageOps.exif_transpose(Image.open(UP + src)).convert("RGB")
    for (x0, y0, x1, y1) in blur:
        b = (int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height))
        reg = im.crop(b); w, h = reg.size
        px = reg.resize((max(1, w // 18), max(1, h // 18)), Image.BILINEAR).resize((w, h), Image.BILINEAR)
        im.paste(px.filter(ImageFilter.GaussianBlur(max(6, min(w, h) // 10))), b)
    _cache[key] = im; return im

def crop_box(iw, ih, fx, fy, z):
    ch = ih / z if iw / ih >= W / H else (iw * H / W) / z
    cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    return cx - cw / 2, cy - ch / 2, cw, ch

def cover(img, fx, fy, z, sharpen=True):
    x, y, cw, ch = crop_box(img.width, img.height, fx, fy, z)
    fr = img.resize((W, H), Image.LANCZOS, box=(x, y, x + cw, y + ch))
    if sharpen and cw < W * .95: fr = fr.filter(ImageFilter.UnsharpMask(1.4, 70, 2))
    return fr.convert("RGBA"), (x, y, cw, ch)

def text_img(txt, font, fill, stroke=0, sc=DARK):
    b = font.getbbox(txt, stroke_width=stroke); w, h = b[2] - b[0], b[3] - b[1]
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((15 - b[0], 15 - b[1]), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=sc)
    return im

def word_sprite(word, hi, size=84):
    f = FT("mont900", size)
    if hi:
        t = text_img(word, f, DARK)
        pad = 18; im = Image.new("RGBA", (t.width + 2 * pad - 20, t.height + pad - 6), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([0, 0, im.width - 1, im.height - 1], 18, fill=LIME)
        im.alpha_composite(t, (pad - 10, pad // 2 - 10)); return im
    t = text_img(word, f, WHITE, stroke=7)
    sh = Image.new("RGBA", t.size, (0, 0, 0, 0)); sh.putalpha(t.getchannel("A").point(lambda a: a * 150 // 255))
    out = Image.new("RGBA", (t.width + 10, t.height + 14), (0, 0, 0, 0))
    out.alpha_composite(Image.composite(Image.new("RGBA", t.size, (0, 0, 0, 255)), sh, sh).filter(ImageFilter.GaussianBlur(6)), (4, 10))
    out.alpha_composite(t, (0, 0)); return out

def caption_layout(lines, size=84):
    """-> list of (sprite, cx, cy_offset, order)"""
    items, order, y = [], 0, 0
    for line in lines:
        toks = []; hi = False; cur = []
        for w in line.split(" "):
            st = w.startswith("*"); en = w.endswith("*")
            ww = w.strip("*")
            if st: hi = True
            toks.append((ww, hi))
            if en: hi = False
        # merge consecutive highlighted words into one box
        groups = []
        for ww, h in toks:
            if groups and h and groups[-1][1]: groups[-1] = (groups[-1][0] + " " + ww, True)
            else: groups.append((ww, h))
        sprs = [word_sprite(g, h, size) for g, h in groups]
        gap = 14; tw = sum(s.width for s in sprs) + gap * (len(sprs) - 1); x = -tw / 2
        lh = max(s.height for s in sprs)
        for s in sprs:
            items.append((s, x + s.width / 2, y + lh / 2, order)); x += s.width + gap; order += 1
        y += lh + 6
    return items, y

def draw_caption(fr, items, total_h, t, top=False, t0=CAP_T0):
    base = 300 if top else 1230 - total_h / 2
    for s, cx, cy, k in items:
        p = prog(t, t0 + k * CAP_STAG, .22)
        if p <= 0: continue
        sc = .55 + .45 * back_out(p, 2.4)
        paste(fr, s, W / 2 + cx, base + cy, alpha=clamp(p * 2), scale=sc)

def sticker(cut, border=12):
    a = cut.getchannel("A")
    big = a.filter(ImageFilter.MaxFilter(2 * border + 1)).filter(ImageFilter.GaussianBlur(1.5))
    out = Image.new("RGBA", cut.size, (255, 255, 255, 0)); out.putalpha(big)
    sh = Image.new("RGBA", cut.size, (0, 0, 0, 0)); sh.putalpha(big.point(lambda v: v * 110 // 255))
    sh = Image.composite(Image.new("RGBA", cut.size, (0, 0, 0, 255)), sh, sh).filter(ImageFilter.GaussianBlur(14))
    res = Image.new("RGBA", (cut.width + 40, cut.height + 40), (0, 0, 0, 0))
    res.alpha_composite(sh, (20, 34)); res.alpha_composite(out, (20, 20)); res.alpha_composite(cut, (20, 20))
    bb = res.getbbox(); return res.crop(bb)

def brand_bg(t, d, rays=True):
    bg = gradient(*BRAND_BG, radial=True)
    fr = ms.kenburns(bg, t, d, 1.0, 1.06)
    if rays:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay); cx, cy = W / 2, H * .55
        for k in range(14):
            a0 = math.radians(k * 360 / 14 + t * 14); a1 = a0 + math.radians(9)
            dr.polygon([(cx, cy), (cx + 2400 * math.cos(a0), cy + 2400 * math.sin(a0)), (cx + 2400 * math.cos(a1), cy + 2400 * math.sin(a1))], fill=(255, 255, 255, 16))
        fr.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))
    return fr

class Confetti:
    def __init__(self, n=90, seed=5, t0=0.0):
        r = random.Random(seed); self.t0 = t0
        cols = [LIME, (255, 214, 102), (246, 160, 180), WHITE, (120, 220, 170)]
        self.p = [dict(x=W / 2 + r.uniform(-120, 120), y=H * .42, vx=r.uniform(-900, 900), vy=r.uniform(-1700, -500),
                       w=r.randint(12, 22), h=r.randint(22, 38), c=r.choice(cols), rot=r.uniform(0, 360), vr=r.uniform(-500, 500)) for _ in range(n)]
    def draw(self, fr, t):
        tt = t - self.t0
        if tt <= 0: return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for q in self.p:
            x = q["x"] + q["vx"] * tt * .9; y = q["y"] + q["vy"] * tt + 1500 * tt * tt
            if y > H + 50: continue
            ang = math.radians(q["rot"] + q["vr"] * tt); sq = abs(math.cos(ang * 1.7))
            hw, hh = q["w"] / 2, q["h"] / 2 * (.3 + .7 * sq); ca, sa = math.cos(ang), math.sin(ang)
            pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca) for dx, dy in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]]
            d.polygon(pts, fill=q["c"] + (int(255 * clamp(1.6 - tt * .7)),))
        fr.alpha_composite(lay)

def shake(fr, t, t_hit, amp=18):
    dt = t - t_hit
    if not 0 <= dt < .25: return fr
    a = amp * (1 - dt / .25); dx = int(a * math.sin(dt * 90)); dy = int(a * math.cos(dt * 70))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255)); out.alpha_composite(fr.resize((W + 40, H + 70)).crop((20 + dx, 35 + dy, 20 + dx + W, 35 + dy + H))); return out

def flash(fr, t, t_hit, dur=.22):
    dt = t - t_hit
    if 0 <= dt < dur:
        fr.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(235 * (1 - dt / dur) ** 2))))

def handover_cut():
    c = Image.open(os.path.join(HERE, "cutouts", "0a5478b7_cut.png"))
    a = np.array(c.getchannel("A")).astype(np.float32)
    # add the parcel back (object, not a person)
    pm = Image.new("L", c.size, 0); ImageDraw.Draw(pm).rounded_rectangle([int(.462 * c.width), int(.255 * c.height), int(.64 * c.width), int(.69 * c.height)], 18, fill=255)
    a = np.maximum(a, np.array(pm.filter(ImageFilter.GaussianBlur(2))).astype(np.float32))
    c.putalpha(Image.fromarray(a.astype(np.uint8))); return c.crop(c.getbbox())

def founder_cut():
    c = Image.open(os.path.join(HERE, "cutouts", "6f69f974_cut.png"))
    a = np.array(c.getchannel("A")); a[int(.88 * c.height):, :int(.3 * c.width)] = 0; c.putalpha(Image.fromarray(a))
    return c.crop(c.getbbox())

# ---------------- render ----------------
def frames_for(i):
    s = SHOTS[i]; n = int(round(s["d"] * FPS)); k = s["k"]
    caps = caption_layout(s["cap"]) if s.get("cap") else None
    top = s.get("top", False)
    scrim = None
    if caps:
        a = np.zeros((H, W), np.float32); y = np.arange(H)[:, None]
        a[:] = (np.clip((700 - y) / 500, 0, 1) if top else np.clip((y - 850) / 600, 0, 1)) ** 1.3 * 150
        scrim = Image.new("RGBA", (W, H), (5, 15, 12, 0)); scrim.putalpha(Image.fromarray(a.astype(np.uint8)))

    if k == "hook":
        cut = sticker(handover_cut(), 12); sc = 1180 / cut.height; cut = cut.resize((int(cut.width * sc), int(cut.height * sc)), Image.LANCZOS)
        l1 = text_img("OUR FIRST", FT("mont900", 86), WHITE, 6)
        l2 = Image.new("RGBA", (1, 1)); t2 = text_img("CORPORATE", FT("anton", 196), DARK)
        l2 = Image.new("RGBA", (t2.width + 30, t2.height - 10), (0, 0, 0, 0)); ImageDraw.Draw(l2).rounded_rectangle([0, 0, l2.width - 1, l2.height - 1], 26, fill=LIME); l2.alpha_composite(t2, (15, -12))
        l3 = text_img("ORDER", FT("anton", 230), WHITE, 9)
        conf = Confetti(110, 3, 1.0)
        def gen():
            for j in range(n):
                t = j / FPS; fr = brand_bg(t, s["d"])
                p = back_out(prog(t, 0, .45), 1.4)
                paste(fr, cut, W / 2, H - cut.height / 2 + 40 + (1 - clamp(p)) * 500, alpha=clamp(p * 2))
                for spr, y, th in [(l1, 300, .1), (l2, 470, .4), (l3, 690, .72)]:
                    q = prog(t, th, .18)
                    if q > 0: paste(fr, spr, W / 2, y, alpha=clamp(q * 2), scale=1 + 1.2 * (1 - ease_out(q)))
                conf.draw(fr, t)
                fr = shake(fr, t, .58, 16); fr = shake(fr, t, .9, 22)
                yield fr
        return gen(), n, caps, top, scrim
    if k == "card":
        img = load(s["src"], s.get("blur", ())); bgi = cover(img, .5, .5, 1.0, False)[0].filter(ImageFilter.GaussianBlur(28))
        bgi = Image.blend(bgi.convert("RGB"), Image.new("RGB", (W, H), (10, 30, 24)), .45).convert("RGBA")
        cw = s.get("cw", 1000); chh = int(cw * img.height / img.width)
        card = Image.new("RGBA", (cw + 36, chh + 36), WHITE + (255,)); card.paste(img.resize((cw, chh), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2)), (18, 18))
        sh = Image.new("RGBA", (card.width + 80, card.height + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([40, 55, card.width + 40, card.height + 55], fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(22)); sh.alpha_composite(card, (40, 40)); card = sh
        conf = Confetti(120, 8 + i, .45)
        def gen():
            for j in range(n):
                t = j / FPS; fr = ms.kenburns(bgi, t, s["d"], 1.05, 1.12)
                p = ease_out(prog(t, 0, .4)); z = 1 + .03 * t
                paste(fr, card, W / 2, 1010, alpha=clamp(p * 2), scale=(1.35 - .35 * p) * z, rot=-4 * p)
                if not s.get("quiet"): flash(fr, t, .4); conf.draw(fr, t)
                yield fr
        return gen(), n, caps, True, None
    if k == "founder":
        cut = sticker(founder_cut(), 12); sc = 1250 / cut.height; cut = cut.resize((int(cut.width * sc), int(cut.height * sc)), Image.LANCZOS)
        drift = Drift(10, [SAGE, (214, 232, 120)], 4, (50, 110))
        l1 = text_img("IF A SMALL BRAND", FT("mont900", 74), WHITE, 6)
        l2 = text_img("CAN DO IT...", FT("anton", 170), LIME, 0)
        def gen():
            for j in range(n):
                t = j / FPS; fr = brand_bg(t, s["d"], rays=False); drift.draw(fr, t)
                p = ease_out(prog(t, 0, .5))
                paste(fr, cut, W / 2 + 120 + (1 - p) * 600, H - cut.height / 2 + 30)
                for spr, y, th in [(l1, 330, .2), (l2, 500, .5)]:
                    q = prog(t, th, .2)
                    if q > 0: paste(fr, spr, W / 2, y, alpha=clamp(q * 2), scale=1 + .9 * (1 - ease_out(q)))
                yield fr
        return gen(), n, None, False, None
    if k == "cta":
        drift = Drift(14, [SAGE, GOLD, (214, 232, 120)], 7, (50, 120))
        l1 = text_img("SO CAN YOU.", FT("anton", 190), WHITE, 8)
        l2 = text_img("BECOME A VRIKSH", FT("mont900", 70), WHITE, 5)
        t3 = text_img("RESELLER", FT("anton", 170), DARK)
        l3 = Image.new("RGBA", (t3.width + 30, t3.height - 10), (0, 0, 0, 0)); ImageDraw.Draw(l3).rounded_rectangle([0, 0, l3.width - 1, l3.height - 1], 26, fill=LIME); l3.alpha_composite(t3, (15, -12))
        WA = (37, 211, 102)
        bw, bh = 900, 150
        btn = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(btn).rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=WA)
        ic = Image.new("RGBA", (96, 96), (0, 0, 0, 0)); di = ImageDraw.Draw(ic)
        di.ellipse([6, 6, 90, 90], outline=WHITE, width=8); di.polygon([(14, 92), (22, 66), (38, 80)], fill=WHITE)
        di.rounded_rectangle([34, 30, 46, 52], 5, fill=WHITE); di.rounded_rectangle([50, 46, 66, 58], 5, fill=WHITE); di.line([(40, 50), (56, 52)], fill=WHITE, width=9)
        bt = text_img("+91 97907 82105", FT("mont900", 58), WHITE)
        gx = (bw - (ic.width + 20 + bt.width)) // 2
        btn.alpha_composite(ic, (gx, bh // 2 - ic.height // 2)); btn.alpha_composite(bt, (gx + ic.width + 20, bh // 2 - bt.height // 2))
        wl = text_img("WHATSAPP TO START TODAY", FT("mont900", 46), WHITE, 4)
        def gen():
            for j in range(n):
                t = j / FPS; fr = brand_bg(t, s["d"]); drift.draw(fr, t)
                for spr, y, th in [(l1, 560, .05), (l2, 780, .45), (l3, 930, .65)]:
                    q = prog(t, th, .2)
                    if q > 0: paste(fr, spr, W / 2, y, alpha=clamp(q * 2), scale=1 + 1.0 * (1 - ease_out(q)))
                q = prog(t, .95, .2)
                if q > 0: paste(fr, wl, W / 2, 1110, alpha=clamp(q * 2), scale=1 + .6 * (1 - ease_out(q)))
                p = back_out(prog(t, 1.15, .45))
                if p > 0: paste(fr, btn, W / 2, 1250, alpha=clamp(p), scale=(.6 + .4 * p) * (1 + .03 * math.sin(max(0, t - 1.6) * 7)))
                fr = shake(fr, t, .2, 14)
                yield fr
        return gen(), n, None, False, None
    if k == "end":
        bg = gradient((20, 78, 68), (9, 46, 40), radial=True); drift = Drift(12, [SAGE, (214, 232, 120), (240, 180, 190)], 9, (50, 120))
        lg = Image.open(SK + "/assets/vriksh_logo.jpg").convert("RGB").resize((760, 755), Image.LANCZOS)
        yy, xx = np.mgrid[0:lg.height, 0:lg.width].astype(np.float32); r = np.sqrt((xx - lg.width / 2) ** 2 + (yy - lg.height / 2) ** 2)
        logo = lg.convert("RGBA"); logo.putalpha(Image.fromarray((np.clip((385 - r) / 25, 0, 1) * 255).astype(np.uint8)))
        sub = text_img("HERBAL SANITARY NAPKINS  ·  UAE & INDIA", FT("mont700", 32), SAGE)
        hd = text_img("@vrikshherbalsanitarynapkins", FT("mont800", 44), WHITE)
        def gen():
            for j in range(n):
                t = j / FPS; fr = ms.kenburns(bg, t, s["d"], 1.0, 1.08); drift.draw(fr, t)
                lp = back_out(prog(t, .05, .7), 1.1)
                if lp > 0: paste(fr, logo, W / 2, 660, alpha=clamp(lp), scale=(.55 + .45 * lp) * (1 + .012 * math.sin(max(0, t - .9) * 2.4)))
                ms.reveal_word(fr, sub, W / 2, 1110, t, .7, .45, 25); ms.reveal_word(fr, hd, W / 2, 1200, t, .95, .45, 25)
                yield fr
        return gen(), n, None, False, None
    if k == "video":
        vf = (f"setpts=PTS/{s['sp']},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{s['fy']},unsharp=5:5:0.9,eq=contrast=1.05:saturation=1.08")
        def gen():
            p = subprocess.Popen(["ffmpeg", "-loglevel", "quiet", "-ss", str(s["ss"]), "-t", str(s["d"] * s["sp"] + .5), "-i", UP + s["src"],
                                  "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
            last = None
            for _ in range(n):
                b = p.stdout.read(W * H * 3)
                if len(b) == W * H * 3: last = Image.frombytes("RGB", (W, H), b)
                yield last.convert("RGBA")
            p.kill()
        return gen(), n, caps, top, scrim
    # photo
    img = load(s["src"], s.get("blur", ()))
    def gen():
        for j in range(n):
            t = j / FPS; z = s["z"][0] + (s["z"][1] - s["z"][0]) * ease_inout(t / s["d"])
            fr, (x, y, cw, ch) = cover(img, s["fx"], s["fy"], z)
            if s.get("ring"):
                x0, y0, x1, y1, ts = s["ring"]; q = ease_inout(prog(t, ts, .5))
                if q > 0:
                    mpx = lambda u, v: ((u * img.width - x) / cw * W, (v * img.height - y) / ch * H)
                    (a0, b0), (a1, b1) = mpx(x0, y0), mpx(x1, y1)
                    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
                    d.arc([a0 - 30, b0 - 26, a1 + 30, b1 + 26], -90, -90 + 360 * q, fill=LIME, width=10)
                    fr.alpha_composite(lay)
            yield fr
    return gen(), n, caps, top, scrim

def render_shot(i):
    gen, n, caps, top, scrim = frames_for(i)
    path = os.path.join(CL, f"{i:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    items = caption_layout(SHOTS[i]["cap"]) if caps else None
    for j, fr in enumerate(gen):
        t = j / FPS
        if scrim is not None: fr.alpha_composite(scrim)
        if items: draw_caption(fr, items[0], items[1], t, top)
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); return i

def timeline():
    offs, acc = [], 0.0
    for i, s in enumerate(SHOTS[:-1]):
        acc += s["d"]; offs.append(round(acc - (i + 1) * T, 3))
    return offs, round(sum(s["d"] for s in SHOTS) - T * (len(SHOTS) - 1), 3)

def write_timeline():
    offs, total = timeline(); start = lambda i: 0.0 if i == 0 else offs[i - 1]
    pops = []
    for i, s in enumerate(SHOTS):
        if s.get("cap"):
            nwords = len(caption_layout(s["cap"])[0]); pops += [start(i) + CAP_T0 + k * CAP_STAG for k in range(nwords)]
    hook_hits = [.1, .4, .72]; pops += hook_hits
    idx = {}
    for i, s in enumerate(SHOTS): idx.setdefault(s["k"], i)
    pops += [start(idx["founder"]) + .2, start(idx["founder"]) + .5, start(idx["cta"]) + .05, start(idx["cta"]) + .45, start(idx["cta"]) + .65]
    tl = dict(cuts=[o + T / 2 for o in offs], total=total, n=len(SHOTS), pops=sorted(pops),
              shutter=[start(i) + .38 for i, s in enumerate(SHOTS) if s["k"] == "card" and not s.get("quiet")],
              booms=[.58, .9, start(idx["cta"]) + .2] + [start(i) for i, s in enumerate(SHOTS) if s.get("cap") and s["cap"][0].startswith("STOP")],
              music=dict(bpm=120, beat_from=1, brk=[idx["card"] - 2, idx["card"]], hit=idx["card"]))
    json.dump(tl, open(os.path.join(WORK, "timeline.json"), "w")); return offs, total

def assemble():
    offs, total = write_timeline()
    subprocess.run([sys.executable, os.path.join(HERE, "score2.py"), WORK], check=True)
    ins = []; [ins.extend(["-i", os.path.join(CL, f"{i:02d}.mp4")]) for i in range(len(SHOTS))]
    fc, prev = [], "[0]"
    for i, (o, tr) in enumerate(zip(offs, TRANS)):
        fc.append(f"{prev}[{i+1}]xfade=transition={tr}:duration={T}:offset={o}[x{i}]"); prev = f"[x{i}]"
    fc.append(f"{prev}eq=contrast=1.05:saturation=1.1,vignette=PI/9,format=yuv420p[v]")
    fc.append(f"[{len(SHOTS)}]loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    out = os.path.join(WORK, "Vriksh_First_Corporate_Order_9x16.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", os.path.join(WORK, "score.wav"), "-filter_complex", ";".join(fc),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
                    "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    print("wrote", out, total)

if __name__ == "__main__":
    if sys.argv[1] == "render":
        idx = [int(x) for x in sys.argv[2:]] or list(range(len(SHOTS)))
        with mp.get_context("fork").Pool(4) as p:
            for i in p.imap_unordered(render_shot, idx): print("shot", i, flush=True)
    elif sys.argv[1] == "assemble":
        assemble()
