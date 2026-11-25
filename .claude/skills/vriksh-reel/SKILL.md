---
name: vriksh-reel
description: Turn Hema's photos and phone clips into a finished, on-brand 9:16 Vriksh reel (Instagram Reels + YouTube Shorts) with kinetic text, beat-synced transitions, spotlight cutouts, an original royalty-free score and the official Vriksh logo end card. Use when Hema shares media for Vriksh and asks for a reel, edit, video, story or "make it viral".
---

# Vriksh Reel

Brand: **Vriksh, Made For Her**, herbal and plant-based sanitary napkins, UAE & India.
Instagram: `@vrikshherbalsanitarynapkins`. Owner: Hema (founder).

The engine lives in `scripts/` and is driven by one JSON shot plan. You make the
creative decisions (story, order, text, timing); the engine does the craft.

## Workflow

1. **Inventory every file.** `ffprobe` each video (duration, fps, rotation; phone
   clips report landscape with a -90 rotation, ffmpeg autorotates them, that is fine).
   Make a 4-6 frame contact sheet per video and look at it. Note dead frames
   (dashboard, floor, blur) so you can trim them.
2. **Find the story.** Default arc that works for Vriksh:
   hook (best/most emotional frame first) -> where it starts (product) ->
   process (making, packing) -> payoff (rows of finished work) -> journey ->
   the moment (spotlight) -> gratitude -> logo end card.
   Hook text must make a promise in under 8 words ("From my kitchen table / to the MUN stage.").
3. **Write `plan.json`** in a project folder (e.g. `reels/<name>/plan.json`). Copy
   `examples/mun26_plan.json` and edit. Schema below.
4. **Render:** `python3 .claude/skills/vriksh-reel/scripts/reel.py all reels/<name>/plan.json`
   (about 1 to 2 min for 40 s). Re-render single shots with `render plan.json 3 7`
   then `assemble plan.json`.
5. **Verify (gate, never skip).** Read `work/verify/sheet.png` (one frame per shot).
   Check: right photo in each slot, text readable, nobody's face covered by text,
   no dark/dead frames, logo end card clean. Loudness must print about -14 LUFS.
   Look at the hook frame at full size; it is the thumbnail that stops the scroll.
6. **Deliver:** send the mp4 plus a cover jpg (hook frame at ~1.9 s), then run
   `/vriksh-caption` for the caption, 5 hashtags and keywords.
   `*.mp4` is gitignored in this repo: use `git add -f` if a reel must be committed.

## Plan schema

```json
{
  "media_dir": "/path/to/uploads",          // absolute, or relative to plan.json
  "work_dir": "work", "output": "Vriksh_<Name>_9x16.mp4",
  "hook": {"label": "VRIKSH  ·  BEHIND THE SCENES", "l1": "From my kitchen table", "l2": "to the MUN stage."},
  "end":  {"sub": "HERBAL SANITARY NAPKINS  ·  UAE & INDIA", "cta": "Follow our journey", "handle": "@vrikshherbalsanitarynapkins"},
  "music": {"beat_from": 8, "brk": [14, 16], "hit": 16},
  "shots": [ ... ], "transitions": [ ... one fewer than shots ... ]
}
```

Shot kinds (`d` = seconds on screen, 1.5 to 3.6; transitions overlap 0.3 s):

| kind | use for | keys |
|---|---|---|
| `photo` | portrait photos, close crops of landscape | `src, d, fx, fy` (focus 0-1), `z: [start, end]` zoom (1.0 to 1.18) |
| `fit` | wide group/stage shots where nobody may be cropped | `src, d, scale` (1.0 = full width), `cx, z` (blurred fill behind) |
| `video` | phone clips | `src, d, ss` (start s), `sp` (speed; 2.2 = fast montage, 0.8 = slow), `fy` (vertical crop focus) |
| `end` | logo end card, always last | `d` (about 4.2) |

Optional per shot: `hook: true` (first shot only), `lab` (small gold caps label),
`l1` (white serif line), `l2` (gold italic line), `top: true` (text at top when
the bottom of the frame is busy or holds a face), `spot: true` (spotlight cutout
for the big moment).

Transitions (ffmpeg xfade): `hblur` out of the hook, `fade`, `smoothleft`,
`slideup`, `slideleft`, `smoothup`, `circleopen`, `zoomin`, `radial`,
`fadeblack` (time jump), `fadewhite` (into the big moment).

Music keys are shot indexes: `beat_from` = kick drum enters, `brk` = drums drop
out (tension, e.g. on "And then..."), `hit` = chime + bass hit on the big moment.
The score is synthesised, so it is always original and never gets muted.

## House style (learned from Hema's approvals, follow it)

- Palette: forest green, sage, blush, cream, gold. Fonts: Playfair Display + Poppins (bundled).
- End card is always the **official logo** (`assets/vriksh_logo.jpg`) on its own green; never a drawn substitute. Hema asked for this explicitly.
- Text sits on a soft dark band, inside the Reels safe zone (y 250 to 1500, never the bottom 400 px).
- Short lines: label in caps, one white line, one gold italic line. No emojis in rendered text (fonts lack them); emojis go in captions.
- Never show another store's logo or shopping bag; skip off-story shots (outfit selfies, random rooms).
- Children: never put a child's name on screen. Use "Family-powered, always." unless Hema names them.
- Claims: say "Herbal. Plant-based. Made for her.", "soft on skin", "breathable". Never "rash-free", "cures", or medical promises (Meta ads rejects them).
- Never write em dashes in any text Hema will publish.
- Length: 20 to 45 s. Hook in the first 2.5 s. Loudness -14 LUFS.

## Files

- `scripts/reel.py`: engine (render, assemble, verify).
- `scripts/brand.py`: palette, fonts, easing, sprites, kinetic text helpers.
- `scripts/score.py`: original 100 BPM score synced to the cuts.
- `assets/`: official logo, fonts (SIL OFL).
- `examples/mun26_plan.json`: the approved MUN-26 reel, a full working example.
