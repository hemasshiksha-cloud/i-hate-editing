"""Vriksh brand reel: renders 6 animated 1080x1920 scenes to ProRes-free mp4 clips."""
import math, os, subprocess, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(ROOT), "fonts")
OUT = os.path.join(ROOT, "clips")
os.makedirs(OUT, exist_ok=True)

def F(name, size): return ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)

# palette
GREEN = (31, 59, 45); GREEN2 = (48, 86, 64); SAGE = (168, 195, 160)
BLUSH = (246, 221, 216); CREAM = (251, 246, 238); GOLD = (201, 166, 107)
ROSE = (205, 120, 125); INK = (38, 44, 40)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_inout(x): x = clamp(x); return 4*x*x*x if x < .5 else 1 - (-2*x + 2) ** 3 / 2
def back_out(x, s=1.6): x = clamp(x); return 1 + (s+1)*(x-1)**3 + s*(x-1)**2
def prog(t, start, dur): return clamp((t - start) / dur)

# ---------- backgrounds ----------
def gradient(c1, c2, radial=False):
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    if radial:
        d = np.sqrt((x - .5) ** 2 * 1.0 + (y - .42) ** 2 * .55); k = clamp_arr(d / .75)
    else:
        k = np.broadcast_to(y, (H, W)) * 0.85 + np.broadcast_to(x, (H, W)) * 0.15
    a = np.array(c1)[None, None, :]; b = np.array(c2)[None, None, :]
    img = a * (1 - k[..., None]) + b * k[..., None]
    return Image.fromarray(img.astype(np.uint8), "RGB").convert("RGBA")
def clamp_arr(a): return np.clip(a, 0, 1)

# ---------- sprites ----------
def leaf_points(w, h, n=60):
    left, right = [], []
    for i in range(n + 1):
        s = i / n
        hw = w / 2 * (math.sin(math.pi * s) ** 0.85) * (1 - 0.25 * s)
        y = s * h
        bend = math.sin(s * math.pi) * w * 0.08
        left.append((w / 2 - hw + bend, y)); right.append((w / 2 + hw + bend, y))
    return left + right[::-1]

def leaf_sprite(w, h, color, rib=None, ss=4):
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(x * ss, y * ss) for x, y in leaf_points(w, h)], fill=color)
    if rib:
        pts = [((w / 2 + math.sin(s * math.pi) * w * .08) * ss, s * h * ss) for s in np.linspace(0.04, .96, 30)]
        d.line(pts, fill=rib, width=max(2, int(w * .025 * ss)))
        for s in np.linspace(.18, .8, 5):
            x0 = (w / 2 + math.sin(s * math.pi) * w * .08) * ss; y0 = s * h * ss
            for sgn in (-1, 1):
                d.line([(x0, y0), (x0 + sgn * w * .28 * ss, y0 - h * .08 * ss)], fill=rib, width=max(1, int(w * .015 * ss)))
    return im.resize((w, h), Image.LANCZOS)

def circle_sprite(r, color, ss=4):
    im = Image.new("RGBA", (2 * r * ss, 2 * r * ss), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, 2 * r * ss - 1, 2 * r * ss - 1], fill=color)
    return im.resize((2 * r, 2 * r), Image.LANCZOS)

def ring_sprite(r, color, width, ss=4):
    im = Image.new("RGBA", (2 * r * ss, 2 * r * ss), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([0, 0, 2 * r * ss - 1, 2 * r * ss - 1], outline=color, width=width * ss)
    return im.resize((2 * r, 2 * r), Image.LANCZOS)

def text_sprite(txt, font, color, spacing=0, shadow=None):
    if spacing:
        widths = [font.getbbox(c)[2] - font.getbbox(c)[0] if c != " " else font.size * .3 for c in txt]
        tw = int(sum(widths) + spacing * (len(txt) - 1)) + 20
    else:
        b = font.getbbox(txt); tw = b[2] - b[0] + 20
    asc, desc = font.getmetrics(); th = asc + desc + 20
    im = Image.new("RGBA", (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if spacing:
        x = 10
        for c, cw in zip(txt, widths):
            d.text((x - (font.getbbox(c)[0] if c != " " else 0), 10), c, font=font, fill=color); x += cw + spacing
    else:
        d.text((10 - font.getbbox(txt)[0], 10), txt, font=font, fill=color)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").point(lambda a: a * shadow[1] // 255))
        sh = Image.composite(Image.new("RGBA", im.size, shadow[0] + (255,)), sh, sh).filter(ImageFilter.GaussianBlur(8))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0)); base.alpha_composite(sh, (0, 6)); base.alpha_composite(im); im = base
    return im

def paste(frame, spr, cx, cy, alpha=1.0, scale=1.0, rot=0.0):
    if alpha <= 0.001: return
    s = spr
    if scale != 1.0:
        s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC)
    if rot: s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = s.getchannel("A").point(lambda v: int(v * alpha)); s = s.copy(); s.putalpha(a)
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    # clip-safe alpha composite
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + s.width), min(H, y + s.height)
    if x1 <= x0 or y1 <= y0: return
    frame.alpha_composite(s.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def reveal_word(frame, spr, cx, cy, t, start, dur=0.55, rise=70):
    """Kinetic text: rises from a mask line with a fade, like a premium title."""
    p = ease_out(prog(t, start, dur))
    if p <= 0: return
    paste(frame, spr, cx, cy + (1 - p) * rise, alpha=p)

# ---------- floating leaves ----------
class Drift:
    def __init__(self, n, colors, seed, size=(70, 190)):
        rnd = random.Random(seed); self.items = []
        for _ in range(n):
            w = rnd.randint(*size); h = int(w * rnd.uniform(1.6, 2.1))
            c = rnd.choice(colors)
            spr = leaf_sprite(w, h, c + (rnd.randint(60, 140),))
            self.items.append(dict(spr=spr, x=rnd.uniform(-50, W + 50), y=rnd.uniform(-100, H + 100),
                                   vx=rnd.uniform(-18, 18), vy=rnd.uniform(-45, -15), r0=rnd.uniform(0, 360),
                                   vr=rnd.uniform(-20, 20), ph=rnd.uniform(0, 6.28)))
    def draw(self, frame, t):
        for it in self.items:
            x = it["x"] + it["vx"] * t + math.sin(t * 1.3 + it["ph"]) * 22
            y = it["y"] + it["vy"] * t
            paste(frame, it["spr"], x, y, rot=it["r0"] + it["vr"] * t)

# ---------- render helper ----------
def render(name, dur, draw):
    path = os.path.join(OUT, name + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "14", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for i in range(n):
        fr = draw(i / FPS)
        p.stdin.write(fr.convert("RGB").tobytes())
    p.stdin.close(); p.wait(); print("rendered", name, n, "frames")

def kenburns(bg, t, dur, z0=1.0, z1=1.08):
    z = z0 + (z1 - z0) * ease_inout(t / dur)
    w, h = int(W * z), int(H * z)
    b = bg.resize((w, h), Image.BILINEAR)
    return b.crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))

# =================== SCENES ===================
def logo_sprite(scale=1.0, col=CREAM, accent=GOLD):
    r = int(150 * scale)
    im = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0))
    paste_im = ring_sprite(r, accent + (255,), max(3, int(5 * scale)))
    im.alpha_composite(paste_im, (10, 10))
    lf = leaf_sprite(int(r * .78), int(r * 1.35), col + (255,), rib=GREEN + (255,))
    lf = lf.rotate(-18, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lf, (10 + r - lf.width // 2, 10 + r - lf.height // 2))
    return im

def scene1():  # HOOK
    dur = 3.4
    bg = gradient((44, 82, 60), (18, 36, 28), radial=True)
    drift = Drift(14, [SAGE, (120, 160, 120), GOLD], 1)
    f1, f2 = F("pf600", 118), F("pf400i", 124)
    l1 = text_sprite("Your period", f1, CREAM, shadow=((0, 0, 0), 120))
    l2 = text_sprite("deserves", f2, GOLD, shadow=((0, 0, 0), 120))
    l3 = text_sprite("better.", f2, GOLD, shadow=((0, 0, 0), 120))
    tag = text_sprite("A NOTE FOR EVERY WOMAN", F("pp500", 34), SAGE, spacing=8)
    def draw(t):
        fr = kenburns(bg, t, dur, 1.12, 1.0); drift.draw(fr, t)
        reveal_word(fr, tag, W / 2, 640, t, 0.05, .5, 30)
        reveal_word(fr, l1, W / 2, 800, t, 0.25)
        reveal_word(fr, l2, W / 2, 950, t, 0.65)
        reveal_word(fr, l3, W / 2, 1090, t, 0.95)
        # gold underline drawing in
        p = ease_inout(prog(t, 1.3, .7))
        if p > 0:
            d = ImageDraw.Draw(fr); x0 = W / 2 - 230; d.line([(x0, 1185), (x0 + 460 * p, 1185)], fill=GOLD, width=5)
        return fr
    render("s1", dur, draw)

def scene2():  # PROBLEM
    dur = 3.8
    bg = gradient(BLUSH, (238, 200, 196))
    drift = Drift(8, [(255, 255, 255), ROSE], 2, (60, 120))
    fh = F("pp600", 44); fb = F("pf600", 96)
    head = text_sprite("SOUND FAMILIAR?", fh, ROSE, spacing=10)
    lines = ["Plastic layers.", "Harsh chemicals.", "Itchy, sweaty days."]
    spr = [text_sprite(s, fb, INK) for s in lines]
    ys = [820, 980, 1140]
    def draw(t):
        fr = kenburns(bg, t, dur, 1.0, 1.06); drift.draw(fr, t)
        reveal_word(fr, head, W / 2, 620, t, 0.1, .45, 30)
        d = ImageDraw.Draw(fr)
        for i, (s, y) in enumerate(zip(spr, ys)):
            st = 0.35 + i * 0.45
            p = back_out(prog(t, st, .45))
            if p > 0: paste(fr, s, W / 2, y, alpha=clamp(p), scale=0.6 + 0.4 * p)
            q = ease_inout(prog(t, st + 0.55, .35))
            if q > 0:
                half = s.width / 2 - 10
                d.line([(W / 2 - half, y + 6), (W / 2 - half + 2 * half * q, y - 4)], fill=ROSE, width=9)
        return fr
    render("s2", dur, draw)

def scene3():  # REVEAL with leaf cutout mask
    dur = 4.2
    cream = gradient(CREAM, (243, 233, 218))
    green = gradient((52, 92, 68), (22, 44, 33), radial=True)
    drift = Drift(10, [SAGE, GOLD], 3, (50, 120))
    mask_leaf = leaf_sprite(600, 1000, (255, 255, 255, 255))
    logo = logo_sprite(1.0)
    name_f = F("pf600", 150); tag_f = F("pf400i", 70); small = F("pp300", 38)
    intro = text_sprite("Introducing", F("pf400i", 64), GREEN)
    def draw(t):
        p = ease_inout(prog(t, 0.95, 1.0))
        fr = cream.copy()
        reveal_word(fr, intro, W / 2, 960, t, 0.1, .4, 40)
        if p > 0:
            sc = 0.02 + p * 4.8
            m = mask_leaf.resize((max(1, int(600 * sc)), max(1, int(1000 * sc))), Image.BILINEAR).rotate(-20 + 20 * p, expand=True)
            mk = Image.new("L", (W, H), 0)
            mk.paste(m.getchannel("A"), (int(W / 2 - m.width / 2), int(H / 2 - m.height / 2)))
            g = green.copy(); drift.draw(g, t)
            fr = Image.composite(g, fr, mk)
        # logo + letter-spaced wordmark
        lp = back_out(prog(t, 1.65, .6), 1.2)
        if lp > 0: paste(fr, logo, W / 2, 700, alpha=clamp(lp), scale=0.5 + 0.5 * lp, rot=(1 - clamp(lp)) * 40)
        sp = ease_out(prog(t, 1.95, 1.0))
        if sp > 0:
            nm = text_sprite("VRIKSH", name_f, CREAM, spacing=int(70 - 46 * sp))
            paste(fr, nm, W / 2, 1010, alpha=sp)
        reveal_word(fr, text_sprite("Made For Her", tag_f, GOLD), W / 2, 1160, t, 2.4)
        reveal_word(fr, text_sprite("herbal  ·  organic  ·  sanitary napkins", small, SAGE), W / 2, 1265, t, 2.7, .5, 30)
        return fr
    render("s3", dur, draw)

def icon(kind, r=95):
    im = circle_sprite(r, CREAM + (255,)); d = ImageDraw.Draw(im)
    if kind == "leaf":
        lf = leaf_sprite(int(r * .8), int(r * 1.3), GREEN2 + (255,), rib=CREAM + (255,)).rotate(-25, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(lf, (r - lf.width // 2, r - lf.height // 2))
    elif kind == "cotton":
        for dx, dy in [(-28, -10), (28, -10), (0, -36), (-14, 18), (14, 18)]:
            c = circle_sprite(30, (232, 226, 214, 255)); im.alpha_composite(c, (r + dx - 30, r + dy - 30))
            c2 = ring_sprite(30, GREEN2 + (255,), 3); im.alpha_composite(c2, (r + dx - 30, r + dy - 30))
        d.line([(r, r + 40), (r, r + 70)], fill=GREEN2, width=6)
    else:  # air waves
        for k, yy in enumerate([-30, 0, 30]):
            pts = [(r - 55 + x, r + yy + math.sin(x / 14 + k) * 9) for x in range(0, 111, 4)]
            d.line(pts, fill=GREEN2, width=7)
    ring = ring_sprite(r, GOLD + (255,), 4); im.alpha_composite(ring)
    return im

def card(kind, title, sub):
    cw, ch = 860, 250
    im = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([20, 28, cw + 20, ch + 28], 60, fill=(20, 40, 30, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(im).rounded_rectangle([20, 20, cw + 20, ch + 20], 60, fill=(255, 255, 255, 235))
    ic = icon(kind); im.alpha_composite(ic, (55, 20 + ch // 2 - ic.height // 2))
    d = ImageDraw.Draw(im)
    d.text((290, 75), title, font=F("pf600", 64), fill=GREEN)
    d.text((292, 165), sub, font=F("pp300", 34), fill=(90, 105, 95))
    return im

def scene4():  # INGREDIENTS cards
    dur = 4.2
    bg = gradient((196, 216, 188), (150, 182, 145))
    drift = Drift(9, [(255, 255, 255), GREEN2], 4, (50, 110))
    head = text_sprite("What's inside", F("pf400i", 92), GREEN)
    hsub = text_sprite("THOUGHTFULLY CHOSEN", F("pp500", 34), (70, 100, 80), spacing=8)
    cards = [card("leaf", "Herbal care", "Infused with plant goodness"),
             card("cotton", "Organic touch", "Soft, gentle top layer"),
             card("air", "Breathable", "Stay fresh, all day long")]
    ys = [860, 1140, 1420]
    def draw(t):
        fr = kenburns(bg, t, dur, 1.0, 1.05); drift.draw(fr, t)
        reveal_word(fr, hsub, W / 2, 560, t, 0.05, .45, 30)
        reveal_word(fr, head, W / 2, 660, t, 0.2)
        for i, (c, y) in enumerate(zip(cards, ys)):
            p = ease_out(prog(t, 0.55 + i * 0.4, .6))
            if p > 0: paste(fr, c, W / 2 + (1 - p) * 900, y, alpha=clamp(p * 1.4))
        return fr
    render("s4", dur, draw)

def scene5():  # BENEFITS, highlight wipes
    dur = 3.8
    bg = gradient(CREAM, (244, 228, 222))
    drift = Drift(7, [SAGE, ROSE], 5, (50, 110))
    fb = F("pf600", 104)
    rows = [("Soft on skin.", SAGE), ("Kind to Earth.", (233, 207, 160)), ("Made for every her.", (240, 190, 190))]
    sprs = [text_sprite(s, F("pf600", 104 if len(s) < 16 else 86), GREEN) for s, _ in rows]
    ys = [800, 990, 1180]
    def draw(t):
        fr = kenburns(bg, t, dur, 1.0, 1.05); drift.draw(fr, t)
        d = ImageDraw.Draw(fr)
        for i, ((_, col), s, y) in enumerate(zip(rows, sprs, ys)):
            st = 0.2 + i * 0.5
            q = ease_inout(prog(t, st, .45))
            if q > 0:
                x0 = W / 2 - s.width / 2 - 10; x1 = x0 + (s.width + 20) * q
                d.rounded_rectangle([x0, y - 20, x1, y + 62], 18, fill=col)
            reveal_word(fr, s, W / 2, y, t, st + 0.15, .5, 40)
        return fr
    render("s5", dur, draw)

def scene6():  # CTA
    dur = 4.6
    bg = gradient((44, 82, 60), (16, 32, 25), radial=True)
    drift = Drift(14, [SAGE, GOLD, (120, 160, 120)], 6)
    logo = logo_sprite(0.8)
    h1 = text_sprite("Make the", F("pf600", 112), CREAM)
    h2 = text_sprite("switch.", F("pf400i", 130), GOLD)
    # pill button
    bw, bh = 640, 130
    btn = Image.new("RGBA", (bw + 4, bh + 4), (0, 0, 0, 0))
    ImageDraw.Draw(btn).rounded_rectangle([2, 2, bw, bh], bh // 2, fill=GOLD)
    bt = text_sprite("Shop now  ·  Link in bio", F("pp600", 44), GREEN)
    btn.alpha_composite(bt, (bw // 2 - bt.width // 2 + 2, bh // 2 - bt.height // 2 + 4))
    region = text_sprite("NOW SHIPPING  ·  UAE  &  INDIA", F("pp500", 34), SAGE, spacing=6)
    handle = text_sprite("Vriksh  ·  Made For Her", F("pf400i", 50), CREAM)
    def draw(t):
        fr = kenburns(bg, t, dur, 1.0, 1.1); drift.draw(fr, t)
        lp = back_out(prog(t, 0.1, .6), 1.2)
        if lp > 0: paste(fr, logo, W / 2, 520, alpha=clamp(lp), scale=.4 + .6 * lp)
        reveal_word(fr, h1, W / 2, 790, t, 0.4)
        reveal_word(fr, h2, W / 2, 935, t, 0.7)
        p = back_out(prog(t, 1.2, .55))
        if p > 0:
            pulse = 1 + 0.035 * math.sin(max(0, t - 1.8) * 6.0)
            glow = 0.5 + 0.5 * math.sin(max(0, t - 1.8) * 6.0)
            g = ring_sprite(int(bh / 2 + 20), GOLD + (int(120 * glow),), 3)
            paste(fr, btn, W / 2, 1140, alpha=clamp(p), scale=(0.6 + 0.4 * p) * pulse)
        reveal_word(fr, region, W / 2, 1290, t, 1.6, .5, 30)
        reveal_word(fr, handle, W / 2, 1390, t, 1.9, .5, 30)
        return fr
    render("s6", dur, draw)

if __name__ == "__main__":
    which = sys.argv[1:] or ["1", "2", "3", "4", "5", "6"]
    for k in which: globals()["scene" + k]()
