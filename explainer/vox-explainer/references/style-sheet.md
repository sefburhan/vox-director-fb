# Style sheet (fixed values: never eyeball per scene)

1920×1080, 24 fps, Rec.709, 48 kHz. Double the pixel sizes for 4K. Key text stays inside the centre ~90% and clear of the bottom 120 px (YouTube progress bar), apart from captions.

## Palette and colour meaning (one meaning per colour, for the whole film)
| Role | Hex | Meaning |
|---|---|---|
| Paper | #F4EFE6 | base background |
| Ink | #1A1A1A | text, neutral lines (never pure black) |
| Accent | #C8642B copper (topic colour) | the subject: the place, resource or main actor |
| Look-here | #F2C230 highlighter yellow | arrows, circles, highlights, the Pakistan border |
| Alert | #D23B2E signal red | blocked, penalty, danger, slipping dates, red strings |
| Data | #7D9A9A teal-grey | neighbours, comparison series, neutral regions |

Change the accent per topic; keep the roles. A different background colour per act or beat (refs do this) is allowed, using the palette only. Check text contrast at phone size.

## Type
| Level | Font | Size |
|---|---|---|
| Chapter card | Anton / Bebas Neue (fallback DIN Condensed Bold) | 120 px |
| Heading / headline banner | same | 72 px |
| Callout / stat card | Oswald Bold (tabular digits for counters) | 46 px |
| Labels / map text | DIN Condensed Bold caps, or italic serif for country names | 32 px |
| Roles, country names (Vox pairing) | Playfair Display Italic / Libre Caslon Italic | 32–40 px |
| Captions | Helvetica Neue Medium, white on a dark strip, 2 lines max | 42 px |

Caps tracked +5%. Max 6 words per line. Hold time ≥ 1 s per 3 words + 0.5 s. Every text element has a backing (paper strip, box or shadow).

## Depth and texture
- One light direction: all shadows fall down-right, offset (5–10, 7–12) px, blur 6–10, opacity 0.35–0.4.
- Paper grain overlay on every frame (σ≈7), a subtle vignette, and rotation of ±2–6° on every cut-out.
- Photos: white sticker border or torn edge, plus the same shadow.

## Annotation kit
- **Arrow** (`draw_arrow`): 10 px stroke, head 52 px at 30° ±4°, drawn on over 0.45 s with ease-out; the head appears as the stroke arrives. Colour by role (yellow = look here, red = danger, ink = neutral). Bend between -0.5 and 0.5; vary the bend and approach angle between neighbouring arrows so they never look stamped. Dashed for routes. Double-headed for "between".
- **Marker circle** (`draw_circle_mark`): 9 px, overshoots its start by about 12%.
- **Highlighter sweep:** yellow at 55% opacity, left to right over 0.4 s; the rest of the page is dimmed 25% and blurred 1.5 px.
- **Pins:** one red pin design with a white centre and shadow; drops in with a bounce and a ripple.
- **Red string:** 4 px, slight sag (quadratic bend 0.08), shadow offset, drawn pin to pin.
- **Circle cut-outs (Vox):** photo or icon in a circle of the actor's colour, name in bold sans, role in italic serif, connector lines to what they back.

## Motion
- In 10 frames, out 7 frames. Easing: ease-out cubic for entrances, back-out (overshoot 1.7–2.2) for paper pops, ease-in-out for camera.
- Slide-ins enter from a random side (L, R, T, B) per card, seeded so a re-render gives the same result.
- Paper elements wobble in 12 fps steps; the camera stays smooth at 24 fps.
- Camera: one move per shot (push, pull, pan, tilt), varied between neighbours; impact shake on slams; whip-pan with blur between acts.
- Transitions: cut, paper wipe, camera push/whip. Nothing else.
- Cadence: a cut every 4–6 s; never hold more than 7 s except the open and close.

## Maps
- Base: grey shaded relief, oceans dark teal-black, countries as tinted overlays (relief shows through).
- Subject region in the accent colour; everything else muted. Pakistan border yellow over a thin ink line.
- Zooms are eased and stepped, in log space; never cut between zoom levels.
- Inset locator in a corner when zoomed in past province level; scale label only when distance matters and is sourced.

## Charts
- Thin axes, minimal gridlines, direct labels (no legends); key series in accent, others grey.
- Build axes → data → highlight, on the narration.
- Counters ease out and hold 0.5 s on the final value.
- No source lines on screen (they go in the description); keep chart shapes faithful to the sourced end values.

## Audio
- Narration levelled. Music ducks under the voice (sidechain, threshold 0.03, ratio 6), changes at chapter breaks, and cuts to silence on the big reveals.
- SFX on every visual event, kept subtle: paper slide or pop, pin tap, stamp, gavel, boom, crumple, whoosh, marker scratch, counter tick.
- Master at -14 LUFS, true peak ≤ -1.5 dBTP.
