# Reko Diq: long film, built in parts

Each chapter is its own part. Change one, re-render only that one, then join (about 15 seconds; no re-encode).

| Part | Chapter | Code |
|---|---|---|
| c00 | Cold open | `chapters/c00.py` |
| c01–c08 | Chapters 1–8 | `chapters/rest.py` → `build_c01()` … `build_c08()` |
| c09 | Close | `chapters/rest.py` → `build_c09()` |

## Common changes
```zsh
cd "vox/projects/reko diq/build/long"
python3 part.py c04 stills          # look at one frame per shot  -> out/c04_stills.jpg
python3 part.py c04 render          # re-render chapter 4 only (~1–2 min)
python3 join.py                     # rebuild the full film       -> ../../reko_diq_long.mp4 (+ .srt, chapters.txt)
```
- **Change a narration line:** edit the row's `vo` in `script.json`, delete `vo/<beat>.wav`, run `vo_long.py` (it re-voices only missing beats), then render that part and join.
- **Change on-screen text or timing:** edit the chapter's `build_cNN()`. Cards are `K(P, row, "TEXT", "word")` and land on that word.
- **Change music:** the `P.cue(...)` lines at the end of each chapter.
- **Swap a picture:** replace the file in `assets/` (same name), or change the path in the chapter.
- **Outro:** `python3 join.py` will append it once the outro exists (The Indus kit: `vox/resources/theindus.org`).

Outputs per part: `out/cNN.mp4` (video), `out/cNN.wav` (mix), `out/cNN.json` (length + captions).
