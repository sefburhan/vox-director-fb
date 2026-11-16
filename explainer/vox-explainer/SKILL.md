---
name: vox-explainer
description: Make a factual Vox-style explainer film (maps, timelines, stats, news clippings, paper-collage posters, hand-drawn arrows) fully on this Mac's local models, from a script or an explainer pack. Use when the user asks for a Vox-style video, a documentary explainer, a map-and-data explainer, a paper-collage explainer on a real topic (economics, geopolitics, history, mining, Pakistan), or to check, sample or re-render one. Complements vox-director (cloud, collage-only) with local rendering, real maps and sourced data.
---

# Vox-style explainer films (local)

Facts on Vox-style **maps and data**, story beats on **paper-collage posters**, all rendered locally with Pillow + ffmpeg. Built and proven on the Reko Diq film (`vox/projects/reko diq/`).

- **Skill home** `$K` = `/Volumes/Data/Claude.io/Video/video-gen/skills-src/vox-explainer/`
- **Engine** `$K/tools/engine.py`: copy into `<project>/build/` and import it. A working 20 s example: `$K/tools/example_map_sample.py`.
- **Projects** live under `/Volumes/Data/Claude.io/Video/video-gen/vox/projects/<slug>/` with `build/{posters,vo,music,sfx,geo,cut,logs}`.

Read before building:
- `references/style-sheet.md`: fixed values (palette and colour meaning, type scale, shadows, motion timings, arrows)
- `references/checklist.md`: the pre-render checklist. Copy it into the project as `CHECKLIST.md` and tick it.
- `references/learned.md`: what the reference films do (vox-director samples, Vox "Middle East's cold war")

## Rules that never bend
1. **Every number is sourced** (in `facts.md` and the description, not on screen). Fetch the sources (web-fetch agent) and record headline, date and supporting quote. Unverified claims are cut or attributed ("reports say", "?" on screen). No invented headlines.
2. **Every number lands on its spoken word.** Use Whisper word timestamps, never guessed times.
3. **Maps are real geography** (Natural Earth). Disputed territory is handled deliberately; for Pakistan use the official depiction (AJK and Gilgit-Baltistan solid, Indian-administered J&K hatched "DISPUTED TERRITORY") unless the user says otherwise.
4. **Real images only from licensed sources** (Wikimedia Commons, Pexels, Pixabay, NASA/ESA public domain), each logged in `build/credits.csv` and credited on screen. Not Pinterest or Freepik, and no lifting of agency or newspaper photos. News appears as headline cards: outlet, real headline, date.
5. **No Vox (or any outlet) logo or branding.** It's a style reference only.
6. **Sample first.** Render a 20 s sample of the hardest section, get the user's sign-off, then render the full film.
7. **No mention of AI, models or tools, and no credits or source lines on screen** (no newspaper names, map-data notes or photo credits in corners, and no sources on the end card). All credits go in the video description (`assets/credits.md`). Sourcing still happens; it just isn't printed on the film. Set `SHOW_SOURCES = False`. For The Indus films, the outro from `vox/resources/theindus.org/` is appended after the end card.

## Pipeline
1. **Script → narration.** Kokoro (`uvx --python 3.12 --from mlx-audio --with 'misaki[en]' mlx_audio.tts.generate --model mlx-community/Kokoro-82M-bf16 --voice af_heart`), one wav per beat. Fix names with misaki phonemes: `[Reko Diq](/ɹˈAkO dˈik/)`. Then word timestamps: `uvx --python 3.12 mlx_whisper <wav> --model mlx-community/whisper-small-mlx --word-timestamps True --output-format json`. Check the names in the transcript.
2. **Posters** (story beats). `ideogram-local` MCP with `engine: "qwen"`, `enhance: false`, 16:9, and a negative prompt of `text, letters, words, numbers, watermark, logo`. Ideogram itself adds stray text, so use it only when you want text. Base prompt: "Editorial paper-collage illustration, handmade explainer-video look, flat lay on warm off-white cream textured paper. <subject>. Torn white paper edges, soft drop shadows, masking tape, halftone dot texture." Pull full-resolution files with `download_image`. The A40 is shared, so expect 3–4 minutes per poster; send them in waves of about 9.
3. **Music and SFX.** Stable Audio 3 via the local source build (PyPI mlx-audio can't load it):
   `HF_HUB_CACHE=video-gen/models/hf HF_HUB_OFFLINE=1 uv run --python 3.12 --with video-gen/repos/mlx-audio-src --no-project python -m mlx_audio.music.generate --model mlx-community/stable-audio-3-small-music|small-sfx --caption "…" --duration N --negative-prompt "vocals, speech" --output x.wav`
4. **Maps.** Natural Earth 50m countries plus 10m admin-1 (extract the provinces you need, then delete the 40 MB file). Base style: grey shaded relief with dark oceans and tinted country overlays (see `learned.md`). Zoom in steps: country → province → district → pin.
5. **Cut-outs.** `rembg i -m birefnet-general` with `U2NET_HOME=video-gen/models/rembg`, for pieces that fly in.
6. **Render.** Shot functions `fn(img, t_local, shot)` plus overlays (captions, timeline bar, credits) go into `engine.render()`. Render stills of key moments and look at them before the video. About 25 s of render time per 20 s of film.
7. **Mix.** Narration placed per beat; music ducked with `sidechaincompress`; SFX on every visual event; `loudnorm=I=-14:TP=-1.5`.
8. **QA.** Run the `checklist.md` final section: contact sheet of one frame per shot, phone-size viewing, a muted viewing, and the facts table re-checked.

## Engine toolbox (`engine.py`)
- **Posters and labels:** `shot_poster` (living poster: paper base + collage cut-out + camera move + stepped 12 fps wobble), `label_img` / `draw_label` (torn paper strips that pop in).
- **Opening and annotation:** `shot_title`, `draw_arrow` (hand-drawn, curved or straight or dashed, head follows the curve's angle, double-headed option), `draw_circle_mark`.
- **Maps:** `draw_map` / `view_at` / `lerp_view` (log-space zoom between views), `draw_pin`, `draw_band` (route or belt drawn on), `lonlat_xy`.
- **Captions and finish:** `caption_chunks` (script text timed by Whisper words), `draw_caption`, `apply_grain`.
- **Still to add per film:** shaded-relief base, timeline bar, counters, charts, news cards, document highlight, red strings. The specs are in `style-sheet.md`.

## Gotchas
- Two LTX jobs at once don't fit in 48 GB (swap thrash). Check `pgrep -fl ltx-2-mlx` before any LTX image-to-video, and never kill another session's job.
- ffmpeg here has no drawtext or libass, so all text is Pillow.
- Homebrew `python3` (3.15) has Pillow and numpy at user level; run engine scripts with plain `python3`.
- Whisper misspells names ("Rekhodik"), so captions come from the script text, timed by word index.
- Quiet raw mixes come out around -20 LUFS; always finish with `loudnorm`.
