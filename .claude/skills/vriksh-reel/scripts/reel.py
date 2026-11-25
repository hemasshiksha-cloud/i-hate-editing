"""Vriksh reel engine: turns a shot plan (JSON) into a finished 9:16 reel.

Usage:
  python3 reel.py all  plan.json      # render shots -> score -> assemble -> verify sheet
  python3 reel.py render plan.json [i ...]   # (re)render some shots only
  python3 reel.py assemble plan.json  # rebuild timeline, score and final mp4 from rendered shots
"""
import os, sys, json, math, subprocess
import multiprocessing as mp
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import brand as ms
from brand import (W, H, FPS, F, text_sprite, paste, reveal_word, prog, ease_out, ease_inout,
                   back_out, clamp, gradient, logo_sprite, Drift, GREEN, CREAM, GOLD, SAGE)

T = 0.3  # transition length (half a beat at 100 BPM)
PLAN, SHOTS, TRANS, UP, WORK, CL = {}, [], [], "", "", ""

def load_plan(path):
    global PLAN, SHOTS, TRANS, UP, WORK, CL
    PLAN = json.load(open(path))
    base = os.path.dirname(os.path.abspath(path))
    UP = os.path.join(base, PLAN.get("media_dir", ".")) + os.sep
    WORK = os.path.join(base, PLAN.get("work_dir", "work")); CL = os.path.join(WORK, "clips")
    os.makedirs(CL, exist_ok=True)
    SHOTS = PLAN["shots"]
    for sh in SHOTS:
        if "z" in sh: sh["z"] = tuple(sh["z"])
    default = ["fade", "smoothleft", "slideup", "circleopen", "zoomin", "slideleft", "smoothup", "radial"]
    TRANS = PLAN.get("transitions") or [default[i % len(default)] for i in range(len(SHOTS) - 1)]
    assert len(TRANS) == len(SHOTS) - 1, "need exactly one transition between each pair of shots"

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
        bg = gradient((20, 78, 68), (9, 46, 40), radial=True); drift = Drift(12, [SAGE, (214, 232, 120), (240, 180, 190)], 9, (50, 120))
        # official logo, edges feathered into a circle so it melts into the background
        lg = Image.open(os.path.join(SKILL, "assets", "vriksh_logo.jpg")).convert("RGB").resize((800, 795), Image.LANCZOS)
        yy, xx = np.mgrid[0:lg.height, 0:lg.width].astype(np.float32)
        r = np.sqrt((xx - lg.width / 2) ** 2 + (yy - lg.height / 2) ** 2)
        m = np.clip((405 - r) / 25, 0, 1) * 255
        logo = lg.convert("RGBA"); logo.putalpha(Image.fromarray(m.astype(np.uint8)))
        end = PLAN.get("end", {})
        sub = text_sprite(end.get("sub", "HERBAL SANITARY NAPKINS  ·  UAE & INDIA"), F("pp500", 32), SAGE, spacing=5)
        bw, bh = 820, 116
        btn = Image.new("RGBA", (bw + 4, bh + 4), (0, 0, 0, 0)); ImageDraw.Draw(btn).rounded_rectangle([2, 2, bw, bh], bh // 2, fill=GOLD)
        bt = text_sprite(end.get("handle", "@vrikshherbalsanitarynapkins"), F("pp600", 40), GREEN)
        btn.alpha_composite(bt, (bw // 2 - bt.width // 2 + 2, bh // 2 - bt.height // 2 + 4))
        fol = text_sprite(end.get("cta", "Follow our journey"), F("pf400i", 56), CREAM)
        def draw(t):
            fr = ms.kenburns(bg, t, s["d"], 1.0, 1.08); drift.draw(fr, t)
            lp = back_out(prog(t, .05, .75), 1.1)
            if lp > 0:
                breathe = 1 + .012 * math.sin(max(0, t - .9) * 2.4)
                paste(fr, logo, W / 2, 640, alpha=clamp(lp), scale=(.55 + .45 * lp) * breathe, rot=(1 - clamp(lp)) * -12)
            reveal_word(fr, sub, W / 2, 1110, t, .8, .5, 25)
            reveal_word(fr, fol, W / 2, 1210, t, 1.05, .5, 30)
            p = back_out(prog(t, 1.3, .55))
            if p > 0:
                pulse = 1 + .03 * math.sin(max(0, t - 1.9) * 6)
                paste(fr, btn, W / 2, 1335, alpha=clamp(p), scale=(.6 + .4 * p) * pulse)
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
        hk = PLAN.get("hook", {})
        hook_txt = [text_sprite(hk.get("label", "VRIKSH  ·  MADE FOR HER"), F("pp600", 32), GOLD, spacing=7, shadow=((0, 0, 0), 180)),
                    text_sprite(hk.get("l1", "Your period"), F("pf600", 86 if len(hk.get("l1", "")) < 22 else 74), CREAM, shadow=((0, 0, 0), 190)),
                    text_sprite(hk.get("l2", "deserves better."), F("pf400i", 96 if len(hk.get("l2", "")) < 20 else 80), GOLD, shadow=((0, 0, 0), 190))]

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
    out = os.path.join(WORK, PLAN.get("output", "Vriksh_Reel_9x16.mp4"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-i", os.path.join(WORK, "score.wav"),
                    "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "19", "-maxrate", "14M", "-bufsize", "28M", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-movflags", "+faststart", "-shortest", out], check=True)
    print("wrote", out, total)

def write_timeline():
    offs, total = timeline()
    music = PLAN.get("music", {})
    json.dump(dict(cuts=[o + T / 2 for o in offs], total=total, music=music, n=len(SHOTS)),
              open(os.path.join(WORK, "timeline.json"), "w"))
    return offs, total

def render_all(idx):
    with mp.get_context("fork").Pool(min(4, os.cpu_count() or 2)) as p:
        for i in p.imap_unordered(render_shot, idx): print("shot", i, "done", flush=True)

def verify():
    out = os.path.join(WORK, PLAN.get("output", "Vriksh_Reel_9x16.mp4")); vd = os.path.join(WORK, "verify"); os.makedirs(vd, exist_ok=True)
    offs, total = timeline(); starts = [0.0] + [o + T for o in offs]
    pts = [min(st + SHOTS[i]["d"] * .75, total - .1) for i, st in enumerate(starts)]
    for i, x in enumerate(pts):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{x:.2f}", "-i", out, "-frames:v", "1", "-vf", "scale=216:-1", f"{vd}/f{i:02d}.png"], check=True)
    ins = []; [ins.extend(["-i", f"{vd}/f{i:02d}.png"]) for i in range(len(pts))]
    cols = min(10, len(pts))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *ins, "-filter_complex", f"xstack=inputs={len(pts)}:grid={cols}x{math.ceil(len(pts)/cols)}:fill=black" if len(pts) > 1 else "null", f"{vd}/sheet.png"], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = [l.strip() for l in r.splitlines() if l.strip().startswith(("I:", "Peak:"))]
    print("contact sheet:", f"{vd}/sheet.png"); print("loudness:", lufs[-2:]); print("output:", out, f"{total}s")

if __name__ == "__main__":
    cmd, plan = sys.argv[1], sys.argv[2]
    load_plan(plan)
    if cmd in ("render", "all"):
        idx = [int(x) for x in sys.argv[3:]] or list(range(len(SHOTS)))
        render_all(idx)
    if cmd in ("assemble", "all"):
        write_timeline()
        subprocess.run([sys.executable, os.path.join(HERE, "score.py"), WORK], check=True)
        assemble(); verify()
