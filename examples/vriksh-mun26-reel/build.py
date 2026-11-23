"""Vriksh x JSSPS MUN-26: kitchen table to stage. 9:16 reel builder."""
import os, sys, json, math, subprocess
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "reel"))
import make_scenes as ms
from make_scenes import (W, H, FPS, F, text_sprite, paste, reveal_word, prog, ease_out, ease_inout,
                         back_out, clamp, gradient, logo_sprite, Drift, GREEN, CREAM, GOLD, SAGE)

UP = "/root/.claude/uploads/edd7c674-b2d9-5a5c-bf23-e040c7fcf3b2/"
CL = os.path.join(HERE, "clips"); os.makedirs(CL, exist_ok=True)
T = 0.3  # transition length (half a beat at 100 BPM)

# kind, source, dur, opts
SHOTS = [
 dict(k="photo", src="fd570ad6-image.jpg", d=2.7, fx=.43, fy=.5, z=(1.18, 1.04), hook=True),
 dict(k="photo", src="f75d0160-image.jpg", d=2.4, fx=.4, fy=.55, z=(1.0, 1.1), lab="WHERE IT STARTS", l1="Herbal. Plant-based.", l2="Made for her."),
 dict(k="photo", src="de459e91-image.jpg", d=2.1, fx=.45, fy=.45, z=(1.12, 1.0), lab="STEP 1", l1="Design the cards", top=True),
 dict(k="video", src="9f6fb117-IMG_0238.mov", d=3.0, ss=0.0, sp=1.4, fy=.5, l1="Print. Check.", l2="Repeat."),
 dict(k="photo", src="5b2d9664-image.jpg", d=1.5, fx=.5, fy=.45, z=(1.0, 1.08), lab="STEP 2", l1="Cut by hand"),
 dict(k="photo", src="72696e42-image.jpg", d=1.5, fx=.45, fy=.4, z=(1.08, 1.0), l1="Family-powered", l2="always."),
 dict(k="video", src="192be916-IMG_0283.mov", d=3.0, ss=0.3, sp=1.5, fy=.55, lab="STEP 3", l1="Pack with love", top=True),
 dict(k="photo", src="bc4e4d87-image.jpg", d=1.8, fx=.4, fy=.5, z=(1.0, 1.1)),
 dict(k="video", src="f0a7ef72-IMG_0293.mov", d=3.6, ss=4.0, sp=2.2, fy=.5, l1="Bag after bag", l2="after bag."),
 dict(k="photo", src="dba8678b-image.jpg", d=2.4, fx=.5, fy=.5, z=(1.12, 1.0), lab="READY", l1="Sealed with our logo"),
 dict(k="video", src="212b9f78-IMG_0410.mov", d=2.4, ss=0.0, sp=0.78, fy=.5, lab="THE BIG DAY", l1="Off to JSSPS MUN-26"),
 dict(k="video", src="44e2627b-IMG_0411.mov", d=2.1, ss=0.3, sp=1.0, fy=.12, l1="We've arrived."),
 dict(k="fit", src="4bf0c0ad-image.jpg", d=2.1, scale=1.45, cx=.5, z=(1.0, 1.06), lab="JSSPS MUN 2026", l1="Closing Ceremony"),
 dict(k="fit", src="5b2275d4-image.jpg", d=3.0, scale=1.0, cx=.5, z=(1.0, 1.05), l1="Our goodie bags,", l2="in the best hands."),
 dict(k="photo", src="47a782b8-image.jpg", d=1.8, fx=.43, fy=.5, z=(1.0, 1.1), l1="And then..."),
 dict(k="photo", src="e7272406-image.jpg", d=2.1, fx=.39, fy=.5, z=(1.0, 1.12)),
 dict(k="photo", src="fd570ad6-image.jpg", d=3.2, fx=.43, fy=.5, z=(1.0, 1.1), spot=True, lab="JSSPS MUN-26", l1="Honoured on stage.", l2="Grateful beyond words."),
 dict(k="photo", src="dd620b66-image.jpg", d=2.4, fx=.5, fy=.45, z=(1.1, 1.0), l1="Thank you,", l2="JSS Private School."),
 dict(k="end", d=4.2),
]
TRANS = ["hblur", "smoothleft", "slideup", "fade", "fade", "circleopen", "smoothleft", "zoomin", "slideleft",
         "fadeblack", "smoothup", "fade", "circleopen", "fade", "fade", "fadewhite", "radial", "circleopen"]

# ---------- shared overlays ----------
def scrim(top=False):
    a = np.zeros((H, W), np.float32); y = np.arange(H)[:, None]
    if top: a[:] = np.clip((780 - y) / 600, 0, 1) ** 1.4 * 165
    else: a[:] = np.clip((y - 950) / 700, 0, 1) ** 1.2 * 175
    im = Image.new("RGBA", (W, H), (12, 22, 17, 0)); im.putalpha(Image.fromarray(a.astype(np.uint8))); return im

def band(y0, y1):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([-100, y0, W + 100, y1], fill=(10, 18, 14, 125))
    return im.filter(ImageFilter.GaussianBlur(45))

def texts(s):
    out = {}
    if s.get("lab"): out["lab"] = text_sprite(s["lab"], F("pp600", 34), GOLD, spacing=8, shadow=((0, 0, 0), 160))
    if s.get("l1"): out["l1"] = text_sprite(s["l1"], F("pf600", 92 if len(s["l1"]) < 18 else 80), CREAM, shadow=((0, 0, 0), 170))
    if s.get("l2"): out["l2"] = text_sprite(s["l2"], F("pf400i", 84 if len(s["l2"]) < 18 else 70), GOLD, shadow=((0, 0, 0), 170))
    return out

def draw_texts(fr, tx, t, top=False):
    base = 330 if top else 1190
    y = base
    if "lab" in tx: reveal_word(fr, tx["lab"], W / 2, y, t, 0.12, .4, 25); y += 82
    if "l1" in tx: reveal_word(fr, tx["l1"], W / 2, y, t, 0.22); y += 108
    if "l2" in tx: reveal_word(fr, tx["l2"], W / 2, y, t, 0.45)

# ---------- sources ----------
def load(src): return ImageOps.exif_transpose(Image.open(UP + src)).convert("RGB")

def cover_frame(img, fx, fy, z):
    """crop a 9:16 window zoomed by z around focus (fx, fy)."""
    iw, ih = img.size
    ch = ih / z if iw / ih >= W / H else (iw * H / W) / z
    cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")

def video_frames(s):
    src = UP + s["src"]; n = int(round(s["d"] * FPS))
    vf = (f"setpts=PTS/{s['sp']},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{s['fy']}")
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", str(s["ss"]), "-t", str(s["d"] * s["sp"] + 0.5), "-i", src,
                          "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    last = None
    for _ in range(n):
        b = p.stdout.read(W * H * 3)
        if len(b) == W * H * 3: last = Image.frombytes("RGB", (W, H), b)
        yield last.convert("RGBA")
    p.stdout.close(); p.wait()

# ---------- per-shot render ----------
def render_shot(i):
    s = SHOTS[i]; n = int(round(s["d"] * FPS)); path = os.path.join(CL, f"{i:02d}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "15",
                            "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    tx = texts(s); top = s.get("top", False); sc = scrim(top) if tx or s.get("hook") else None
    if sc is not None and s["k"] != "end":
        nl = 3 if s.get("hook") else len(tx)
        y0 = (250 if top else 1120); y1 = y0 + 90 + nl * 100
        sc.alpha_composite(band(y0, y1))

    if s["k"] == "end":
        bg = gradient((44, 82, 60), (16, 32, 25), radial=True); drift = Drift(14, [SAGE, GOLD, (120, 160, 120)], 9)
        logo = logo_sprite(0.85)
        nm = text_sprite("Vriksh", F("pf600", 140), CREAM); tg = text_sprite("Made For Her", F("pf400i", 74), GOLD)
        sub = text_sprite("HERBAL SANITARY NAPKINS  ·  UAE & INDIA", F("pp500", 30), SAGE, spacing=5)
        bw, bh = 820, 116
        btn = Image.new("RGBA", (bw + 4, bh + 4), (0, 0, 0, 0)); ImageDraw.Draw(btn).rounded_rectangle([2, 2, bw, bh], bh // 2, fill=GOLD)
        bt = text_sprite("@vrikshherbalsanitarynapkins", F("pp600", 40), GREEN)
        btn.alpha_composite(bt, (bw // 2 - bt.width // 2 + 2, bh // 2 - bt.height // 2 + 4))
        fol = text_sprite("Follow our journey", F("pf400i", 56), CREAM)
        def draw(t):
            fr = ms.kenburns(bg, t, s["d"], 1.0, 1.08); drift.draw(fr, t)
            lp = back_out(prog(t, .1, .6), 1.2)
            if lp > 0: paste(fr, logo, W / 2, 520, alpha=clamp(lp), scale=.4 + .6 * lp)
            reveal_word(fr, nm, W / 2, 790, t, .35); reveal_word(fr, tg, W / 2, 915, t, .6)
            reveal_word(fr, sub, W / 2, 1020, t, .85, .5, 25)
            reveal_word(fr, fol, W / 2, 1170, t, 1.15, .5, 30)
            p = back_out(prog(t, 1.4, .55))
            if p > 0:
                pulse = 1 + .03 * math.sin(max(0, t - 2.0) * 6)
                paste(fr, btn, W / 2, 1295, alpha=clamp(p), scale=(.6 + .4 * p) * pulse)
            return fr
        frames = (draw(j / FPS) for j in range(n))
    elif s["k"] == "video":
        frames = video_frames(s)
    else:
        img = load(s["src"])
        if s["k"] == "fit":
            bgi = img.resize((max(1, img.width // 8), max(1, img.height // 8))).filter(ImageFilter.GaussianBlur(6))
            bgi = ImageOps.fit(bgi, (W // 4, H // 4)).resize((W, H), Image.BILINEAR)
            bgi = Image.blend(bgi, Image.new("RGB", (W, H), (15, 25, 20)), .35)
            fw = int(W * s["scale"]); fh = int(fw * img.height / img.width)
            fg = img.resize((int(fw * 1.12), int(fh * 1.12)), Image.LANCZOS)
        def frames_photo():
            for j in range(n):
                t = j / FPS; z = s["z"][0] + (s["z"][1] - s["z"][0]) * ease_inout(t / s["d"])
                if s["k"] == "photo":
                    yield cover_frame(img, s["fx"], s["fy"], z)
                else:
                    fr = bgi.copy().convert("RGBA")
                    w2, h2 = int(fw * z), int(fh * z); f2 = fg.resize((w2, h2), Image.BILINEAR)
                    cy = int(H * .42)
                    sh = Image.new("RGBA", (w2 + 80, h2 + 80), (0, 0, 0, 0))
                    ImageDraw.Draw(sh).rectangle([40, 50, w2 + 40, h2 + 50], fill=(0, 0, 0, 120))
                    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)), (W // 2 - w2 // 2 - 40, cy - h2 // 2 - 40))
                    fr.paste(f2, (W // 2 - w2 // 2 + int((.5 - s["cx"]) * w2), cy - h2 // 2))
                    yield fr
        frames = frames_photo()

    # spotlight mask for the award moment
    spot = None
    if s.get("spot"):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        spot = np.sqrt(((xx - W * .5) / 520) ** 2 + ((yy - H * .40) / 820) ** 2)

    hook_txt = None
    if s.get("hook"):
        hook_txt = [text_sprite("VRIKSH  ·  BEHIND THE SCENES", F("pp600", 32), GOLD, spacing=7, shadow=((0, 0, 0), 180)),
                    text_sprite("From my kitchen table", F("pf600", 86), CREAM, shadow=((0, 0, 0), 190)),
                    text_sprite("to the MUN stage.", F("pf400i", 96), GOLD, shadow=((0, 0, 0), 190))]

    for j, fr in enumerate(frames):
        t = j / FPS
        if spot is not None:
            k = ease_inout(prog(t, .2, 1.4)); a = np.clip((spot - 0.75) / 0.6, 0, 1) * 0.62 * k
            arr = np.asarray(fr.convert("RGB")).astype(np.float32) * (1 - a[..., None])
            # warm glow inside the light
            arr[..., 0] += (1 - np.clip(spot, 0, 1)) * 14 * k; arr[..., 1] += (1 - np.clip(spot, 0, 1)) * 8 * k
            fr = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        if sc is not None: fr.alpha_composite(sc)
        if hook_txt:
            reveal_word(fr, hook_txt[0], W / 2, 1160, t, .05, .4, 25)
            reveal_word(fr, hook_txt[1], W / 2, 1255, t, .2)
            reveal_word(fr, hook_txt[2], W / 2, 1365, t, .75)
            # gold flash bar under the hook
            p = ease_inout(prog(t, 1.2, .5))
            if p > 0: ImageDraw.Draw(fr).line([(W / 2 - 200, 1440), (W / 2 - 200 + 400 * p, 1440)], fill=GOLD, width=5)
        else:
            draw_texts(fr, tx, t, top)
        enc.stdin.write(fr.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); return i

def timeline():
    offs, acc = [], 0.0
    for i, s in enumerate(SHOTS[:-1]):
        acc += s["d"]; offs.append(round(acc - (i + 1) * T, 3))
    total = sum(s["d"] for s in SHOTS) - T * (len(SHOTS) - 1)
    return offs, round(total, 3)

def assemble():
    offs, total = timeline()
    ins = []; [ins.extend(["-i", os.path.join(CL, f"{i:02d}.mp4")]) for i in range(len(SHOTS))]
    fc, prev = [], "[0]"
    for i, (o, tr) in enumerate(zip(offs, TRANS)):
        out = f"[x{i}]"; fc.append(f"{prev}[{i+1}]xfade=transition={tr}:duration={T}:offset={o}{out}"); prev = out
    fc.append(f"{prev}eq=contrast=1.04:saturation=1.08:gamma=1.01,colorbalance=rs=.02:bs=-.02:rh=.02,"
              f"vignette=PI/7,noise=alls=2:allf=t,format=yuv420p[v]")
    fc.append(f"[{len(SHOTS)}]loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    out = os.path.join(HERE, "out", "Vriksh_MUN26_Reel_9x16.mp4"); os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", os.path.join(HERE, "score.wav"),
                    "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "19", "-maxrate", "14M", "-bufsize", "28M", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    print("wrote", out, total)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "render":
        idx = [int(x) for x in sys.argv[2:]] or list(range(len(SHOTS)))
        with Pool(4) as p:
            for i in p.imap_unordered(render_shot, idx): print("shot", i, flush=True)
    elif cmd == "timeline":
        offs, total = timeline(); json.dump(dict(cuts=[o + T / 2 for o in offs], total=total), open(os.path.join(HERE, "timeline.json"), "w")); print(offs, total)
    elif cmd == "assemble":
        assemble()
