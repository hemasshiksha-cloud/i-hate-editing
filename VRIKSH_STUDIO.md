# Vriksh Studio: Master Guide

Everything Hema and Claude have built, in one place. Open this file whenever you
forget something. Claude reads it automatically at the start of every session
in this project (via `CLAUDE.md`).

---

## 1. How to start a new video

1. Open a Claude Code session on this project (`hemasshiksha-cloud/i-hate-editing`).
2. Send your photos and clips, and say what the video is about.
3. Claude checks the **Video log** (section 5) and picks a **new style and a new sound** (section 3 and 4).
4. You get the reel, a cover image and a numbered frame for each scene.
   Reply with notes in plain words ("scene 3: bigger stamp") and only those scenes are redone.
5. Say **"caption"** for the caption, 5 hashtags and keywords.

---

## 2. Your skills

| Skill | Say this | What it does |
|---|---|---|
| `/vriksh-reel` | "Vriksh reel" + your media | Builds a 9:16 reel from photos and clips: transitions, text, spotlight, music, official logo end card |
| `/handmade-edit` | "handmade edit" / "uncommon edit" | The signature handmade style: paper, tape, polaroids, stamps, scribbles, paper wipes, lo-fi music with paper sounds |
| `/vriksh-caption` | "caption" | Hooky caption, exactly 5 hashtags, keywords in one comma line, alt text, YouTube Shorts title and tags |
| `/vriksh-dm` | "someone commented..." / "reply to this DM" | Comment replies, DM-to-order flow, follow-ups, blocked-DM fixes, ManyChat and WhatsApp automation |
| `i-hate-editing` (built into this project) | "edit this talking video" | Edits videos of you speaking to camera: cuts pauses, adds captions, sound and colour |

### Instagram pack (11 skills)

| Skill | Say this | What it does |
|---|---|---|
| `/ig-post` | "write a post for this photo" | Hook (3 options), caption, CTA, 5 hashtags, keyword line, alt text, first comment to pin |
| `/ig-reel` | "reel idea: ..." | Before filming: scored hooks, beat sheet, script, shot list, which studio style + sound |
| `/ig-carousel` | "make a carousel on ..." | 7 to 10 slides: swipe-worthy cover, slide copy, design notes; can render slides |
| `/ig-story` | "stories for today" | Frame-by-frame Stories with poll, quiz, question and link stickers |
| `/ig-plan` | "plan my week" | Weekly or monthly calendar: format, hook, style + sound rotation, posting times |
| `/ig-viral` | "why did this reel go viral?" | Breaks down viral reels you share, builds a swipe file and Vriksh versions |
| `/ig-hashtag` | "hashtags / keywords" | 5-hashtag sets, keyword lines, alt text and name-field keywords |
| `/ig-profile` | "fix my profile" | Scores your profile out of 100, rewrites bio, highlights, pinned posts |
| `/ig-comment` | "comments for these posts" | Genuine comments for OTHER accounts' posts to grow reach and network |
| `/ig-reply` | "reply to these comments" | Replies to comments on YOUR posts, buyers first, turns them into DMs |
| `/ig-stats` | (share Insights screenshots) | Explains your numbers in plain words + 3 actions for next week |

Note: Claude cannot log in to Instagram, so for stats, viral research and comments,
share screenshots or paste the text.

Skill files live in `.claude/skills/<name>/SKILL.md`.

---

## 3. Style library (never repeat the last video's style)

| # | Style | Look | Fonts | Used in |
|---|---|---|---|---|
| 1 | **Elegant Botanical** | Forest green, gold, cream, floating leaves, soft text reveals | Playfair Display + Poppins | Vriksh brand reel, JSSPS MUN-26 reel |
| 2 | **Bold Viral** | Lime highlight boxes, words popping one by one, sticker cutouts, confetti, screen shake, light rays | Montserrat Black + Anton | Solidpro first corporate order |
| 3 | **Handmade** | Kraft paper, torn notebook notes, tape, polaroids, DELIVERED stamps, self-drawing marker scribbles, paper wipes | Caveat, Permanent Marker, Special Elite, DM Serif | Online orders reel (Amazon.ae + Flipkart) |

**Ideas for future styles** (each new video gets one of these, or a fresh idea):
- **Editorial Magazine**: big serif cover headlines, column layouts, page-turn transitions
- **Film Diary**: warm film grain, light leaks, date stamps, frame borders, slow and nostalgic
- **Retro Poster**: bold Indian vintage-poster colours, halftone dots, starbursts
- **Minimal Luxury**: lots of white space, thin serif, slow zooms, a single accent colour
- **Glass Modern**: frosted-glass cards, soft gradients, clean product focus
- **Comic Pop**: panels, speech bubbles, action words for fun or educational posts

---

## 4. Sound library (never repeat the last video's sound)

All music is composed in code, so it is original, royalty-free and never gets muted.

| # | Sound | Feel | Used in |
|---|---|---|---|
| A | Warm pad + gentle plucks, 84 to 100 BPM, F major, whooshes and chimes | Calm, emotional | Brand reel, MUN-26 |
| B | 120 BPM beat, a pop on every word, camera shutter, bass booms | Energetic, viral | Solidpro corporate order |
| C | Lo-fi piano, vinyl crackle, paper taps, stamp thuds, marker scratches, paper swooshes | Cosy, handmade | Handmade demo (unused for posting) |
| D | Acoustic guitar strums + picked melody, claps, shaker; printer whirr, sticker peel, mouse clicks, cash-register cha-ching | Bright, feel-good | Online orders reel |

**Ideas for future sounds:** acoustic guitar folk, tabla and flute fusion (Indian), soft
house groove, music box and bells, cinematic strings swell, synthwave, playful ukulele,
claps-and-snaps percussion. Sound effects change with the style (page turns, film
projector, typewriter keys, glass clinks, cash register, and so on).

---

## 5. Video log

| Date | Video | Style | Sound | Status |
|---|---|---|---|---|
| Nov 2026 | Vriksh brand reel (no footage) | 1 Elegant Botanical | A | Done |
| Nov 2026 | JSSPS MUN-26: kitchen table to stage | 1 Elegant Botanical | A | Done |
| Nov 2026 | Solidpro: OUR FIRST CORPORATE ORDER (Guindy + Vandalur) | 2 Bold Viral | B | **In Instagram drafts, posting tomorrow. Do not change.** |
| Nov 2026 | Online orders: Amazon.ae + Flipkart dispatch | 3 Handmade | D Acoustic | Delivered, awaiting Hema's notes |
| Next | (next video) | Not 3 (pick a new style, e.g. Editorial Magazine or Film Diary) | Not D | Waiting for footage |

Add a row for every new video.

Saved files: `examples/` (each reel with its build script and cover).

---

## 6. Hema's rules (always follow)

**Writing**
- No em dashes, ever.
- Captions: hook first line, short story, CTA, **exactly 5 hashtags**, SEO keywords as **one comma-separated line**.
- Phone numbers go in **captions only**, never on the video.
- No medical claims: no "rash-free" or "cures". Use "soft on skin", "breathable", "plant-based".

**Editing**
- Every video gets a **new style and new sound effects**.
- **HD only**: no blurry or shaky clips, and no zooming into tiny low-resolution crops.
- **Privacy**: blur GST numbers, addresses, phone numbers, emails, prices, signatures and other companies' names.
- Avoid using Claude's usual default fonts and layouts. Always choose fonts that fit the story.
- End card always uses the **official Vriksh logo**.
- Never put a child's name on screen. Ask about consent for anyone else shown.
- Strong hook in the first 2 seconds. Low skip rate is the goal.
- Loudness -14 LUFS (Instagram/YouTube standard).

---

## 7. Brand facts

- **Brand:** Vriksh, Made For Her. Herbal, plant-based sanitary napkins and the anion disposable period panty. UAE and India.
- **Instagram:** @vrikshherbalsanitarynapkins
- **Reseller WhatsApp (Rajalakshmi):** +91 97907 82105 (captions only)
  Click-to-chat: `https://wa.me/919790782105?text=Hi%20Vriksh,%20I%20want%20to%20become%20a%20reseller`
- **CTA keywords:** VRIKSH (order), RESELLER (become a reseller), OFFICE (workplace pad stations). Set these up in ManyChat.
- **Milestones:** first corporate order (Solidpro, 200 pads, Guindy + Vandalur, 1-year supply deal in discussion), honoured on stage at JSSPS MUN-26.

---

## 8. Agency (future business)

The handmade and bold styles are the portfolio. Package ideas: Starter (3 reels a month),
Brand (8 reels plus a custom Canva sticker kit), Launch (event or launch recap).
Canva + Claude: clients' stickers, frames and logos are designed in Canva, exported as
transparent PNGs and placed into reels by the `/handmade-edit` kit.
