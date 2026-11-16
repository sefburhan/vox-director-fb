# Reko Diq: a local Vox-style explainer (worked example)

Build code for a 21-minute documentary explainer on the Reko Diq copper-gold project (Balochistan, Pakistan), made with the `explainer/vox-explainer` skill: Pillow + ffmpeg rendering, Kokoro narration, Whisper word timing, Natural Earth maps, animated charts, paper-collage posters.

Only code, scripts, timing data and docs are here. Media (narration audio, posters, photos, music, renders) is kept out of git.

| Path | What |
|---|---|
| `build/long/` | the long film, built in parts (one per chapter) — see `build/long/README.md` |
| `build/film.py`, `build/short.py` | the 3-minute and 1-minute cuts |
| `build/engine.py` | rendering engine (maps, posters, labels, arrows, captions) |
| `build/long/charts.py` | animated donuts, bars, stacked bars and counters with icons |
| `DESIGN.md`, `CHECKLIST.md`, `GAP_ANALYSIS.md` | plan, pre-render checklist, review |
| `credits.md` / `credits.csv` | sources, for the video description |
