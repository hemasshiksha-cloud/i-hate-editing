"""Vriksh brand kit: palette, fonts, easing, sprites (leaves, logo badge, text) and helpers."""
import math, os, subprocess, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(ROOT), "assets", "fonts")

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
def render(name, dur, draw, out_dir="."):
    path = os.path.join(out_dir, name + ".mp4")
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

def logo_sprite(scale=1.0, col=CREAM, accent=GOLD):
    r = int(150 * scale)
    im = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0))
    paste_im = ring_sprite(r, accent + (255,), max(3, int(5 * scale)))
    im.alpha_composite(paste_im, (10, 10))
    lf = leaf_sprite(int(r * .78), int(r * 1.35), col + (255,), rib=GREEN + (255,))
    lf = lf.rotate(-18, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lf, (10 + r - lf.width // 2, 10 + r - lf.height // 2))
    return im

