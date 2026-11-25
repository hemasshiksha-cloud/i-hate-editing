"""Handmade texture kit: paper, torn edges, tape, polaroids, stamps, sticky notes,
hand-drawn scribbles, stop-motion boil, grain, paper-wipe transitions.

Everything is generated procedurally (no stock assets) so it is original and
license-free. Canva exports (transparent PNG) drop in via `canva_asset()`.
"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H, FPS = 1080, 1920, 30
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(KIT, "assets", "fonts")

# ---------- palettes (pick one per brand; override freely) ----------
PALETTES = {
    "petal":  dict(paper=(247, 240, 228), kraft=(196, 160, 118), ink=(38, 30, 28), accent=(226, 96, 79),
                   accent2=(245, 196, 205), hi=(255, 233, 120), tape=(240, 226, 190), green=(52, 92, 68)),
    "vriksh": dict(paper=(246, 241, 230), kraft=(201, 168, 126), ink=(24, 48, 40), accent=(214, 98, 120),
                   accent2=(246, 205, 214), hi=(226, 240, 140), tape=(236, 228, 196), green=(20, 78, 68)),
    "night":  dict(paper=(30, 30, 34), kraft=(60, 52, 48), ink=(245, 240, 230), accent=(255, 120, 90),
                   accent2=(140, 120, 255), hi=(255, 230, 90), tape=(220, 210, 180), green=(80, 160, 120)),
}

def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)

# ---------- easing ----------
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def prog(t, s, d): return clamp((t - s) / d)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def ease_inout(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def back_out(x, s=1.7): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2

def boil(t, seed, amp=3.0, rot=0.8, fps=12):
    """stop-motion jitter: new random offset 12x per second, like hand-placed paper."""
    r = random.Random(seed * 1000 + int(t * fps))
    return r.uniform(-amp, amp), r.uniform(-amp, amp), r.uniform(-rot, rot)

def stamp_scale(t, start, d=.22):
    """placed-by-hand: drops from 1.35x with a little overshoot. None = not yet visible."""
    p = prog(t, start, d)
    if p <= 0: return None
    return 1 + .35 * (1 - back_out(p, 2.2))

# ---------- textures ----------
def _noise(w, h, scale, seed):
    r = np.random.default_rng(seed)
    small = r.standard_normal((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return np.array(Image.fromarray(small).resize((w, h), Image.BICUBIC))

_paper_cache = {}
def paper(w, h, color, seed=1, fibers=True, strength=1.0):
    key = (w, h, color, seed, fibers, strength)
    if key in _paper_cache: return _paper_cache[key].copy()
    n = (_noise(w, h, 3, seed) * 3 + _noise(w, h, 24, seed + 1) * 5 + _noise(w, h, 160, seed + 2) * 7) * strength
    arr = np.clip(np.array(color, np.float32)[None, None, :] + n[..., None], 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    if fibers:
        lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
        for _ in range(int(w * h / 9000)):
            x, y = r.uniform(0, w), r.uniform(0, h); a = r.uniform(0, math.pi); L = r.uniform(8, 40)
            tone = r.choice([(255, 255, 255, 40), (0, 0, 0, 22)])
            d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=tone, width=1)
        im.alpha_composite(lay)
    _paper_cache[key] = im; return im.copy()

def grain(seed, amount=10):
    """full-frame film/paper grain overlay; call with seed=int(t*12) for 12fps boil."""
    r = np.random.default_rng(seed)
    g = r.integers(0, amount * 2 + 1, (H // 2, W // 2), dtype=np.int16) - amount
    a = np.abs(g).astype(np.uint8) * 2
    col = np.where(g[..., None] > 0, 255, 0).astype(np.uint8).repeat(3, 2)
    im = Image.fromarray(np.dstack([col, a]), "RGBA").resize((W, H), Image.NEAREST)
    return im

def torn_mask(w, h, seed, rough=10, edges="tblr"):
    """polygon with hand-torn edges. edges = which sides are torn."""
    r = random.Random(seed); pts = []
    def side(p0, p1, torn, n):
        out = []
        for i in range(n):
            t = i / n; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
            if torn:
                nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0]); L = math.hypot(nx, ny) or 1
                j = r.uniform(-rough, rough) * (1 + .6 * math.sin(i * .7))
                x += nx / L * j; y += ny / L * j
            out.append((x, y))
        return out
    m = rough + 2
    corners = [(m, m), (w - m, m), (w - m, h - m), (m, h - m)]
    pts += side(corners[0], corners[1], "t" in edges, max(4, w // 14))
    pts += side(corners[1], corners[2], "r" in edges, max(4, h // 14))
    pts += side(corners[2], corners[3], "b" in edges, max(4, w // 14))
    pts += side(corners[3], corners[0], "l" in edges, max(4, h // 14))
    mk = Image.new("L", (w, h), 0); ImageDraw.Draw(mk).polygon(pts, fill=255)
    return mk.filter(ImageFilter.GaussianBlur(.6))

def drop_shadow(im, blur=16, off=(0, 12), alpha=110):
    a = im.getchannel("A")
    pad = blur * 2 + max(abs(off[0]), abs(off[1]))
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(a.point(lambda v: v * alpha // 255))
    sh = Image.composite(Image.new("RGBA", im.size, (20, 12, 8, 255)), sh, sh)
    big = Image.new("RGBA", out.size, (0, 0, 0, 0)); big.alpha_composite(sh, (pad + off[0], pad + off[1]))
    out.alpha_composite(big.filter(ImageFilter.GaussianBlur(blur))); out.alpha_composite(im, (pad, pad))
    return out

def torn_paper(w, h, color, seed=1, lined=False, holes=False, rough=9, edges="tblr", shadow=True):
    im = paper(w, h, color, seed)
    if lined:
        d = ImageDraw.Draw(im)
        for y in range(70, h, 46): d.line([(0, y), (w, y)], fill=(120, 160, 210, 120), width=2)
        d.line([(80, 0), (80, h)], fill=(230, 120, 120, 150), width=2)
    if holes:
        d = ImageDraw.Draw(im)
        for y in range(90, h - 40, 140): d.ellipse([22, y, 46, y + 24], fill=(0, 0, 0, 0))
    m = torn_mask(w, h, seed, rough, edges)
    if holes:
        a = np.array(im.getchannel("A")); m = Image.fromarray(np.minimum(np.array(m), a))
    im.putalpha(m)
    return drop_shadow(im) if shadow else im

def tape(w, h, color, seed=1, alpha=175):
    im = paper(w, h, color, seed + 50, fibers=False, strength=.6)
    d = ImageDraw.Draw(im)
    for x in range(0, w, 9): d.line([(x, 0), (x, h)], fill=(255, 255, 255, 18), width=3)
    m = torn_mask(w, h, seed, rough=5, edges="lr").point(lambda v: v * alpha // 255)
    im.putalpha(m); return im

def sticky_note(w, h, color, seed=1):
    im = paper(w, h, color, seed, fibers=False, strength=.7)
    a = np.zeros((h, w), np.uint8) + 255
    # slight curl: darker bottom-right corner
    yy, xx = np.mgrid[0:h, 0:w]; curl = np.clip(((xx / w) + (yy / h) - 1.55) * 3, 0, 1)
    arr = np.array(im.convert("RGB")).astype(np.float32) * (1 - .18 * curl[..., None])
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"); im.putalpha(Image.fromarray(a))
    return drop_shadow(im, 14, (6, 14), 120)

def polaroid(photo, w, seed=1, caption=None, cap_font=None, ink=(40, 32, 30), paper_col=(250, 248, 242)):
    """photo -> polaroid with paper-textured frame and handwritten caption."""
    pw = w - 56; ph = int(pw * photo.height / photo.width)
    ph = min(ph, int(pw * 1.25))
    pic = photo.convert("RGB")
    # center-crop to pw:ph
    sc = max(pw / pic.width, ph / pic.height); pic = pic.resize((int(pic.width * sc) + 1, int(pic.height * sc) + 1), Image.LANCZOS)
    pic = pic.crop(((pic.width - pw) // 2, (pic.height - ph) // 2, (pic.width - pw) // 2 + pw, (pic.height - ph) // 2 + ph))
    bottom = 150 if caption else 90
    fr = paper(w, ph + 28 + bottom, paper_col, seed, strength=.5)
    fr.paste(pic.filter(ImageFilter.UnsharpMask(1.2, 50, 2)), (28, 28))
    if caption:
        f = cap_font or font("caveat700", 64); d = ImageDraw.Draw(fr)
        b = f.getbbox(caption); d.text(((w - (b[2] - b[0])) // 2 - b[0], ph + 28 + (bottom - (b[3] - b[1])) // 2 - b[1] - 6), caption, font=f, fill=ink)
    return drop_shadow(fr, 18, (8, 16), 120)

def text(txt, f, fill, stroke=0, stroke_fill=None):
    b = f.getbbox(txt, stroke_width=stroke); w, h = b[2] - b[0], b[3] - b[1]
    im = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((12 - b[0], 12 - b[1]), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def label(txt, color_paper, ink, seed=1, size=44):
    """typewriter text on a torn paper strip (the 'label maker' look)."""
    t = text(txt, font("typewriter", size), ink)
    strip = torn_paper(t.width + 50, t.height + 26, color_paper, seed, rough=5, edges="lr", shadow=False)
    strip.alpha_composite(t, ((strip.width - t.width) // 2, (strip.height - t.height) // 2))
    return drop_shadow(strip, 8, (3, 6), 90)

def highlighter(w, h, color, seed=1, alpha=200):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); r = random.Random(seed); d = ImageDraw.Draw(im)
    pts = [(r.uniform(0, 12), r.uniform(4, 14))]
    pts += [(w * k / 6 + r.uniform(-6, 6), r.uniform(0, 10)) for k in range(1, 6)]
    pts += [(w - r.uniform(0, 12), r.uniform(4, 14)), (w - r.uniform(0, 14), h - r.uniform(4, 14))]
    pts += [(w * k / 6 + r.uniform(-6, 6), h - r.uniform(0, 10)) for k in range(5, 0, -1)]
    pts += [(r.uniform(0, 14), h - r.uniform(4, 14))]
    d.polygon(pts, fill=color + (alpha,)); return im.filter(ImageFilter.GaussianBlur(1))

def rubber_stamp(txt, color, seed=1, size=110, angle=-12):
    """distressed ink stamp (DELIVERED, APPROVED, SOLD OUT...)."""
    t = text(txt, font("anton", size), color)
    w, h = t.width + 70, t.height + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 8, w - 8, h - 8], 18, outline=color + (255,), width=10)
    im.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2))
    r = np.random.default_rng(seed); a = np.array(im.getchannel("A")).astype(np.float32)
    speck = (r.random(a.shape) > .78) * r.uniform(.3, 1, a.shape)
    blot = np.array(Image.fromarray((r.random((h // 12 + 1, w // 12 + 1)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255
    a = a * (1 - .85 * speck) * (.55 + .45 * blot)
    im.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)

def starburst(r, color, txt=None, f=None, ink=(30, 24, 20), points=14, seed=1):
    s = 2 * r + 20; im = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rr = random.Random(seed)
    pts = []
    for k in range(points * 2):
        a = math.pi * k / points - math.pi / 2; rad = (r if k % 2 == 0 else r * .72) * 2 * rr.uniform(.94, 1.04)
        pts.append((s + rad * math.cos(a), s + rad * math.sin(a)))
    d.polygon(pts, fill=color); im = im.resize((s, s), Image.LANCZOS)
    if txt:
        t = text(txt, f or font("marker", int(r * .55)), ink)
        if t.width > s * .8: t = t.resize((int(s * .8), int(t.height * s * .8 / t.width)), Image.LANCZOS)
        im.alpha_composite(t, ((s - t.width) // 2, (s - t.height) // 2))
    return drop_shadow(im, 8, (3, 6), 90)

# ---------- hand-drawn strokes (animate with progress p in 0..1) ----------
def _wobble(pts, seed, amp):
    r = random.Random(seed); out = []
    ph1, ph2 = r.uniform(0, 6), r.uniform(0, 6)
    for i, (x, y) in enumerate(pts):
        out.append((x + amp * math.sin(i * .21 + ph1), y + amp * math.cos(i * .17 + ph2)))
    return out

def scribble_circle(cx, cy, rx, ry, seed=1, turns=1.18, n=140):
    r = random.Random(seed); a0 = r.uniform(-2.6, -1.8); pts = []
    for i in range(n):
        t = i / (n - 1); a = a0 + t * 2 * math.pi * turns; grow = 1 + .07 * t
        pts.append((cx + rx * grow * math.cos(a), cy + ry * grow * math.sin(a) * (1 + .05 * math.sin(a * 3))))
    return _wobble(pts, seed, 3)

def scribble_underline(x0, x1, y, seed=1, n=60):
    r = random.Random(seed)
    return _wobble([(x0 + (x1 - x0) * i / (n - 1), y + 8 * math.sin(i / (n - 1) * math.pi) * r.uniform(.6, 1)) for i in range(n)], seed, 2)

def scribble_arrow(p0, p1, bend=.3, seed=1, n=60):
    (x0, y0), (x1, y1) = p0, p1; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0) * bend, (x1 - x0) * bend
    pts = []
    for i in range(n):
        t = i / (n - 1); a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t * t
        pts.append((a * x0 + b * (mx + nx) + c * x1, a * y0 + b * (my + ny) + c * y1))
    return _wobble(pts, seed, 2)

def check_mark(cx, cy, s, seed=1):
    return _wobble([(cx - s, cy), (cx - s * .3, cy + s * .7), (cx + s * 1.1, cy - s * .9)], seed, 1)

def draw_stroke(img, pts, p, color, width=10, head=False):
    """draw first p (0..1) of a stroke onto img (RGBA), marker-style round caps."""
    if p <= 0: return
    k = max(2, int(len(pts) * clamp(p)))
    if len(pts) <= 4:  # polyline with few points -> densify
        dense = []
        for (a, b) in zip(pts[:-1], pts[1:]):
            for i in range(20): t = i / 20; dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        dense.append(pts[-1]); pts = dense; k = max(2, int(len(pts) * clamp(p)))
    seg = pts[:k]; d = ImageDraw.Draw(img)
    d.line(seg, fill=color, width=width, joint="curve")
    for (x, y) in (seg[0], seg[-1]): d.ellipse([x - width / 2, y - width / 2, x + width / 2, y + width / 2], fill=color)
    if head and p >= 1:
        (xa, ya), (xb, yb) = pts[-6], pts[-1]; ang = math.atan2(yb - ya, xb - xa)
        for s in (2.5, -2.5):
            hx, hy = xb - 38 * math.cos(ang + s / 6), yb - 38 * math.sin(ang + s / 6)
            d.line([(xb, yb), (hx, hy)], fill=color, width=width)

# ---------- compositing ----------
def place(frame, spr, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if spr is None or alpha <= 0: return
    s = spr
    if abs(scale - 1) > 1e-3: s = s.resize((max(1, int(s.width * scale)), max(1, int(s.height * scale))), Image.BICUBIC)
    if abs(rot) > 1e-3: s = s.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1: s = s.copy(); s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - s.width / 2), int(cy - s.height / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(frame.width, x + s.width), min(frame.height, y + s.height)
    if x1 > x0 and y1 > y0: frame.alpha_composite(s.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def place_boil(frame, spr, cx, cy, t, seed, scale=1.0, rot=0.0, amp=2.5, ramp=.8, alpha=1.0):
    dx, dy, dr = boil(t, seed, amp, ramp); place(frame, spr, cx + dx, cy + dy, scale, rot + dr, alpha)

def sticker_cut(rgba, border=14, color=(255, 255, 255)):
    a = rgba.getchannel("A"); big = a.filter(ImageFilter.MaxFilter(2 * border + 1)).filter(ImageFilter.GaussianBlur(1.5))
    pad = border + 4; out = Image.new("RGBA", (rgba.width + 2 * pad, rgba.height + 2 * pad), (0, 0, 0, 0))
    white = Image.new("RGBA", rgba.size, color + (0,)); white.putalpha(big)
    out.alpha_composite(white, (pad, pad)); out.alpha_composite(rgba, (pad, pad))
    return drop_shadow(out.crop(out.getbbox()), 14, (6, 12), 110)

def canva_asset(path, width=None):
    """load a PNG exported from Canva (transparent background) as a sprite."""
    im = Image.open(path).convert("RGBA")
    if width: im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return im

# ---------- paper-wipe transitions (rendered inside shots, cut joins them) ----------
_wipe_cache = {}
def wipe_sheet(color, seed):
    key = (color, seed)
    if key not in _wipe_cache:
        _wipe_cache[key] = torn_paper(W + 300, H + 300, color, seed, rough=26, edges="tb", shadow=True)
    return _wipe_cache[key]

def wipe(frame, t, d, color, seed, direction="up", mode="out", dur=.32):
    """mode='out': sheet slides IN over the last `dur` s; mode='in': slides OUT over first `dur` s."""
    if mode == "out": p = ease_in(prog(t, d - dur, dur)); off = 1 - p
    else: p = ease_out(prog(t, 0, dur)); off = p
    if mode == "out" and p <= 0: return
    if mode == "in" and p >= 1: return
    sheet = wipe_sheet(color, seed)
    if direction == "up": cx, cy = W / 2, H / 2 + off * (H + 400) * (1 if mode == "out" else -1)
    else: cx, cy = W / 2 + off * (W + 400) * (1 if mode == "out" else -1), H / 2
    place(frame, sheet, cx, cy, rot=-2 if direction == "up" else 1.5)
