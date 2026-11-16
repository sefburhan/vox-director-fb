# Pre-render checklist (copy to `<project>/CHECKLIST.md` and tick)
A filled-in example: `video-gen/vox/projects/reko diq/CHECKLIST.md`.

## 1. Facts
- [ ] Every claim has a fetched source: outlet, headline, date, supporting quote, recorded in `build/facts.md`
- [ ] Unverified claims cut or attributed ("reports say", "?" on screen); company claims labelled as such
- [ ] No number on screen that the script doesn't say; units and rounding consistent
- [ ] NO credits or source lines on screen; every source listed in the description (`assets/credits.md`)

## 2. Story and timing
- [ ] Narration generated per beat; Whisper word timestamps checked (names transcribed correctly)
- [ ] Shot list: a cut every 4–6 s, wide shot with headline then detail shot, camera moves varied between neighbours
- [ ] Every graphic lands on its word; text holds ≥ 1 s per 3 words + 0.5 s
- [ ] Chapter cards for each act, same layout, 2–2.5 s

## 3. Look (see style-sheet.md)
- [ ] Palette with colour meanings written down; background colour per act or beat
- [ ] Fonts installed (Anton/Bebas, Oswald, italic serif, Inter); fixed type scale
- [ ] One shadow direction; grain on every frame; ±2–6° rotation on cut-outs
- [ ] Captions burned in (2 lines max) and a clean master plus .srt exported

## 4. Maps
- [ ] Real geography (Natural Earth); disputed areas handled deliberately (Pakistan: official depiction)
- [ ] Shaded-relief base, tinted overlays, subject in accent, Pakistan border yellow
- [ ] Stepped eased zooms, pin drop, labels on their spoken words, inset locator when zoomed in
- [ ] Routes or belts drawn on; map data credit on screen

## 5. Data graphics
- [ ] Counters (ease out, hold 0.5 s), persistent Vox-style timeline bar, charts with direct labels
- [ ] Charts marked "illustrative" where only the endpoints are sourced
- [ ] News cards with real headlines and dates; document highlight on real quotes

## 6. Collage and annotation
- [ ] Posters generated textless (Qwen), checked as a contact sheet before animating
- [ ] Confetti layer, sunburst on payoffs, stickers and badges, halftone hands where useful
- [ ] Arrows at varied angles and bends; marker circles; red strings for "who links to whom"
- [ ] Slide-ins from random sides with overshoot; 12 fps wobble on paper; impact shake on slams

## 7. Real images
- [ ] Only Wikimedia Commons, Pexels, Pixabay or public-domain imagery; every item in `build/credits.csv`
- [ ] No outlet logos or branding; nothing that looks like a real outlet's own video

## 8. Sound
- [ ] Music cues follow the act structure, with hard silences on the reveals
- [ ] SFX on every visual event, levelled
- [ ] Music ducked under the voice; master -14 LUFS, true peak ≤ -1.5 dBTP

## 9. Sign-off and final QA
- [ ] 20 s sample of the hardest section approved by the user
- [ ] Stills sheet (one frame per shot) reviewed
- [ ] Spelling of every name and place; facts table re-checked on the day of publishing
- [ ] Watched once at phone size and once muted
- [ ] H.264, Rec.709, 48 kHz; thumbnail and end-screen space (last 10 s) ready
