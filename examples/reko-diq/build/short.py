"""Reko Diq: 1-minute film (16:9). Real photos, real documents, maps, word-synced stats.

python3 short.py stills | render [N]   ->  ../reko_diq_1min.mp4
"""
import sys
import wave
import film as F
from film import (Confetti, sunburst, big_text, counter, slide_card, stamp, source, news_card, terrain_map,
                  map_name, fill_bg, DEEP, DARK)
from engine import *

F.tl_active = lambda t: False                      # no 3-minute timeline bar in this cut
SH = ROOT / "short"
A = ROOT.parent / "assets"
TEMPO = 1.07                                       # gentle pitch-preserved speed-up in the mix
NAR = json.load(open(SH / "narration.json"))
START, DUR, WORDS = {}, {}, {}
t = 0.6
for b in NAR["beats"]:
    with wave.open(str(SH / f"vo/{b['id']}.wav")) as w:
        d = w.getnframes() / w.getframerate() / TEMPO
    START[b["id"]], DUR[b["id"]] = t, d
    js = json.load(open(SH / f"vo/{b['id']}.json"))
    WORDS[b["id"]] = [dict(word=x["word"], start=x["start"] / TEMPO, end=x["end"] / TEMPO) for s in js["segments"] for x in s["words"]]
    t += d + b["gap"]
END_VO = t
TOTAL = END_VO + 3.6


def wt(beat, prefix, nth=0, end=False):
    import difflib
    ws = WORDS[beat]
    norm = lambda x: x.strip(" ,.?!:\"'").lower()
    hits = [w for w in ws if norm(w["word"]).startswith(prefix.lower())]
    if len(hits) <= nth:
        hits = sorted(sorted(ws, key=lambda w: -difflib.SequenceMatcher(None, norm(w["word"]), prefix.lower()).ratio())[:nth + 1], key=lambda w: w["start"])
    w = hits[nth]
    return START[beat] + (w["end"] if end else w["start"])


SFX = []


def sfx(f, at, db=0):
    SFX.append((f, at, db))


# ------------------------------------------------------------------ real photo as a taped cut-out
@lru_cache(None)
def photo_card(path, maxw=1300, maxh=760, border=18, seed=1, duotone=False):
    im = Image.open(A / path).convert("RGB")
    im.thumbnail((maxw, maxh), Image.LANCZOS)
    if duotone:
        g = im.convert("L")
        im = Image.merge("RGB", [g.point(lambda v, c=c: int(c[0] + (c[1] - c[0]) * v / 255)) for c in ((24, 244), (34, 239), (52, 230))])
    w, h = im.size
    card = Image.new("RGBA", (w + border * 2, h + border * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    r = random.Random(seed)
    pts = []
    for x in range(0, card.width + 1, 12):
        pts.append((x, r.uniform(0, 5)))
    for y in range(0, card.height + 1, 12):
        pts.append((card.width - r.uniform(0, 5), y))
    for x in range(card.width, -1, -12):
        pts.append((x, card.height - r.uniform(0, 5)))
    for y in range(card.height, -1, -12):
        pts.append((r.uniform(0, 5), y))
    d.polygon(pts, fill=(250, 248, 242, 255))
    card.paste(im, (border, border))
    for (tx, ty, ang) in ((0.08, 0.0, -28), (0.92, 0.0, 30), (0.5, 1.0, 4)):   # masking tape
        tape = Image.new("RGBA", (190, 54), (232, 220, 186, 205))
        tape = tape.rotate(ang, expand=True, resample=Image.BICUBIC)
        card.alpha_composite(tape, (int(card.width * tx - tape.width / 2), int(card.height * ty - tape.height / 2)) if 0 <= int(card.width * tx - tape.width / 2) and 0 <= int(card.height * ty - tape.height / 2) and int(card.height * ty - tape.height / 2) + tape.height <= card.height else (max(0, min(card.width - tape.width, int(card.width * tx - tape.width / 2))), max(0, min(card.height - tape.height, int(card.height * ty - tape.height / 2)))))
    return with_shadow(card, (12, 16), 14, 0.45)


def draw_photo(img, path, g, t, dur, cx=W / 2, cy=H / 2 - 20, z0=1.0, z1=1.06, seed=1, t0=None, **kw):
    card = photo_card(path, seed=seed, **kw)
    z = z0 + (z1 - z0) * ease_io(t / dur)
    s, a = (1.0, 1.0) if t0 is None else pop_in(g, t0, 0.4)
    dx, dy, dr = jitter(seed + 50, g, 0.8)
    paste_transformed(img, card, cx + dx, cy + dy, z * s, random.Random(seed).uniform(-2.5, 2.5) + dr, a)


@lru_cache(None)
def doc_page(path, crop=None, width=900):
    im = Image.open(A / path).convert("RGB")
    if crop:
        im = im.crop(crop)
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    return im


def draw_doc(img, path, g, t, cx, cy, crop=None, width=900, rot=-4, hl=None, hl_t=None, seed=3):
    """Document page at an angle; hl = (x0,y0,x1,y1) in source-page px, swept in yellow from hl_t."""
    im = doc_page(path, crop, width).copy().convert("RGBA")
    sx = width / ((crop[2] - crop[0]) if crop else Image.open(A / path).width)
    if hl and hl_t is not None and g > hl_t:
        p = ease_out((g - hl_t) / 0.7)
        ox, oy = (crop[0], crop[1]) if crop else (0, 0)
        x0, y0, x1, y1 = [(v - o) * sx for v, o in zip(hl, (ox, oy, ox, oy))]
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rectangle((x0 - 4, y0 - 2, x0 + (x1 - x0 + 8) * p, y1 + 2), fill=YELLOW + (120,))
        im.alpha_composite(lay)
    card = with_shadow(im, (12, 16), 14, 0.45)
    dx, dy, dr = jitter(seed, g, 0.5)
    paste_transformed(img, card, cx + dx, cy + dy, 1.0 + 0.04 * ease_io(t / 4), rot + dr)


SHOTS = []


def add(start, end, fn, **kw):
    SHOTS.append(dict(start=start, dur=end - start, fn=fn, **kw))


CAPS = []
for b in NAR["beats"]:
    CAPS += caption_chunks(b["text"], WORDS[b["id"]], START[b["id"]])

# ------------------------------------------------------------------ s01: 28 May 1998, map into Chagai
RASKOH = (64.95, 28.80)
REKO = (62.07, 29.12)
PKV = (69.5, 30.4, 24.0)
CHV = (63.8, 29.2, 7.5)
T_WHITE = wt("s01", "white")
T_PAK = wt("s01", "pakistan")


def s01(img, t, sh):
    g = sh["start"] + t
    view = F.view_at([(0, PKV), (2.4, PKV), (5.0, CHV)], t)
    terrain_map(img, view, bal_fill=0.0, dark=0.15)
    x, y = lonlat_xy(view, *RASKOH)
    if g > T_WHITE - 0.2:                                   # the mountain turns white
        p = clamp((g - T_WHITE + 0.2) / 1.2)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        for k in range(6):
            rr = 30 + 160 * p * (1 + k * 0.25)
            dd.ellipse((x - rr, y - rr * 0.6, x + rr, y + rr * 0.6), fill=(255, 255, 255, int(110 * (1 - p * 0.6) / (k + 1))))
        img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
    map_name(img, "Pakistan", view, 70.6, 29.0, g, 0.3, 2.6, size=64, col=INK)
    map_name(img, "Chagai", view, 63.2, 29.75, g, 3.6, size=56, col=WHITE)
    map_name(img, "Ras Koh", view, RASKOH[0], RASKOH[1] - 0.45, g, T_WHITE - 0.4, size=40, col=WHITE)
    slide_card(img, "28 MAY 1998 · RAS KOH, CHAGAI", 560, 150, g, sh["start"] + 0.35, side="L", seed=301, kind="anton", size=58, fg=WHITE, bg=INK)
    big_text(img, "PAKISTAN'S FIRST NUCLEAR TESTS", W / 2, 860, 70, g, T_PAK, fg=INK, bg=YELLOW, seed=302)
    source(img, "Map data: Natural Earth · Kashmir shown per Pakistan's official map")


add(0, START["s02"] - 0.05, s01)
sfx("sfx/wind.wav", 0, -6)
sfx("sfx/boom.wav", T_WHITE - 0.15, -6)
sfx("sfx/paper_slide.wav", T_PAK, 14)

# ------------------------------------------------------------------ s02: what was already in the ground
T15, T26 = wt("s02", "15"), wt("s02", "26")
cf = Confetti(41, 12, bursts=[(wt("s02", "copper"), 960, 420, 40), (wt("s02", "gold"), 960, 420, 40)])


def s02(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DEEP)
    paste_transformed(img, poster_layer("p02_cutaway"), W / 2, H / 2 + 120, 0.92 + 0.05 * ease_io(t / sh["dur"]), jitter(5, g)[2])
    p = ease_io((g - (sh["start"] + 0.3)) / 1.0)
    if p < 1:
        paste_transformed(img, poster_layer("p01_desert"), W / 2 - 900 * p, H / 2 - 700 * p * p + 40, 1 - 0.3 * p, -25 * p)
    cf.draw(img, g, amb=False)
    counter(img, 15, 0, 560, 200, g, T15, wt("s02", "copper", end=True), size=200, fg=WHITE)
    big_text(img, "MILLION TONNES OF COPPER", 560, 330, 50, g, wt("s02", "million"), fg=INK, bg=YELLOW, seed=311)
    counter(img, 26, 0, 1360, 200, g, T26, wt("s02", "gold", end=True), size=200, fg=YELLOW)
    big_text(img, "MILLION OUNCES OF GOLD", 1360, 330, 50, g, wt("s02", "ounces"), fg=WHITE, bg=COPPER, seed=312)
    source(img, "Metal in reserves · Barrick, Reko Diq Technical Report, 2025")


add(START["s02"] - 0.05, START["s03"] - 0.1, s02)
sfx("sfx/ring.wav", T15, -4)
sfx("sfx/ring.wav", T26, -4)

# ------------------------------------------------------------------ s03: title over the real site
def s03(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, COPPER)
    draw_photo(img, "photos/barrick_aerial_site.jpg", g, t, sh["dur"], cy=H / 2, z0=1.12, z1=1.2, seed=11, maxw=1500, maxh=900)
    big_text(img, "REKO DIQ", W / 2, 470, 260, g, wt("s03", "called") + 0.2, kind="anton", fg=WHITE, slam=True, seed=321)
    big_text(img, "CHAGAI, BALOCHISTAN", W / 2, 650, 50, g, wt("s03", "called") + 0.7, fg=INK, bg=YELLOW, seed=322)
    source(img, "Photo: Barrick Mining Corporation")


add(START["s03"] - 0.1, START["s04"] - 0.1, s03)
sfx("music/hit.wav", wt("s03", "called") + 0.2, -4)

# ------------------------------------------------------------------ s04: 1993, 75%
T93, T75 = wt("s04", "1993"), wt("s04", "75")


def s04(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, TEAL)
    paste_transformed(img, poster_layer("p05_contract"), 640, 560, 0.82, jitter(8, g)[2])
    stamp(img, "23 JULY 1993", 600, 300, g, T93, col=RED, size=96, rot=-8)
    slide_card(img, "CARETAKER GOVERNMENT", 1400, 230, g, wt("s04", "caretaker"), side="R", seed=331, kind="anton", size=56, fg=WHITE, bg=INK)
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = 1050, 1780, 470, 600
    p = ease_out((g - T75) / 0.6)
    d.rectangle((x0, y0, x1, y1), fill=(232, 226, 214, 255), outline=INK, width=4)
    if p > 0:
        d.rectangle((x0, y0, x0 + (x1 - x0) * 0.75 * p, y1), fill=INK + (255,))
        d.rectangle((x0 + (x1 - x0) * 0.75, y0, x0 + (x1 - x0) * (0.75 + 0.25 * p), y1), fill=COPPER + (255,))
    big_text(img, "BHP 75%", 1310, 680, 60, g, T75, fg=WHITE, bg=INK, seed=332)
    big_text(img, "BALOCHISTAN 25%", 1640, 400, 44, g, T75 + 0.3, fg=WHITE, bg=COPPER, seed=333)
    source(img, "Chagai Hills Exploration Joint Venture Agreement, 1993 · Dawn, 2013")


add(START["s04"] - 0.1, START["s05"] - 0.1, s04)
sfx("sfx/stamp.wav", T93, -2)
sfx("sfx/pop.wav", T75, 2)

# ------------------------------------------------------------------ s05: 2011 refusal, 2013 void
T11, T13 = wt("s05", "2011"), wt("s05", "2013")


def s05a(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, None)
    paste_transformed(img, poster_layer("p06_denied"), W / 2 - 120, H / 2 + 40, 0.9, jitter(9, g)[2])
    stamp(img, "LEASE REFUSED", 1350, 300, g, wt("s05", "refused"), col=RED, size=110, rot=-10)
    big_text(img, "15 NOV 2011", 1350, 160, 70, g, T11, fg=WHITE, bg=INK, seed=341)


def s05b(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, TEAL)
    paste_transformed(img, poster_layer("p07_court_pk"), 760, 560, 0.78, jitter(10, g)[2])
    big_text(img, "7 JAN 2013 · SUPREME COURT", 760, 150, 64, g, T13, fg=WHITE, bg=INK, seed=342)
    stamp(img, "VOID", 1500, 520, g, wt("s05", "voided"), col=RED, size=170, rot=12)
    crop = Image.open(A / "news/caselaw_ewhc_2021__crop.png")
    paste_transformed(img, with_shadow(crop.convert("RGBA").resize((760, int(crop.height * 760 / crop.width))), (8, 10), 10, 0.4),
                      1440, 860, 1.0, 2, clamp((g - wt("s05", "whole")) / 0.3))
    source(img, "Supreme Court order of 7 Jan 2013 · cited in UK High Court judgment [2021] EWHC 1884")


add(START["s05"] - 0.1, T13 - 0.15, s05a)
add(T13 - 0.15, START["s06"] - 0.1, s05b)
sfx("sfx/stamp_heavy.wav", wt("s05", "refused"), -2)
sfx("sfx/gavel.wav", T13, -2)
sfx("sfx/stamp_heavy.wav", wt("s05", "voided"), -4)

# ------------------------------------------------------------------ s06: treaty → tribunal → $5.9B
T19 = wt("s06", "2019")
T6 = wt("s06", "$6") if any(w["word"].startswith("$6") for w in WORDS["s06"]) else wt("s06", "nearly")
WASH = (-77.04, 38.90)


def s06a(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DEEP)
    paste_transformed(img, poster_layer("p08_hall"), W / 2, H / 2 + 40, 0.9, jitter(12, g)[2])
    slide_card(img, "1998 · AUSTRALIA–PAKISTAN INVESTMENT TREATY", 760, 150, g, wt("s06", "treaty"), side="L", seed=351, kind="anton", size=50, fg=INK, bg=YELLOW)
    slide_card(img, "ICSID · WORLD BANK, WASHINGTON", 1300, 880, g, wt("s06", "world"), side="R", seed=352, kind="anton", size=52, fg=WHITE, bg=INK)
    draw_arrow(img, (420, 300), (1150, 820), g, wt("s06", "sent"), color=YELLOW, bend=-0.25, seed=31)


cf6 = Confetti(42, 0, bursts=[(T6, 960, 520, 70)])


def s06b(img, t, sh):
    g = sh["start"] + t
    shake = math.exp(-max(0, g - T6) * 6) * 24
    fill_bg(img, RED)
    sunburst(img, W / 2, H / 2, g, (240, 120, 100), alpha=70)
    cf6.draw(img, g, amb=False)
    big_text(img, "12 JULY 2019", W / 2, 230, 70, g, T19, fg=INK, bg=WHITE, seed=353)
    lab = label_img("$5.9 BILLION", kind="anton", size=280, fg=WHITE, bg=None, pad=(20, 10))
    p = (g - T6) / 0.25
    if p > 0:
        paste_transformed(img, lab, W / 2 + math.sin(g * 90) * shake, H / 2 + math.cos(g * 77) * shake, 2.4 - 1.4 * ease_out(p), -3, clamp(p * 4))
    big_text(img, "$4.087BN DAMAGES + ~$1.7BN INTEREST", W / 2, 760, 46, g, T6 + 0.6, fg=WHITE, bg=INK, seed=354)
    source(img, "ICSID award, 12 Jul 2019 · UK High Court judgment [2021] EWHC 1884")


add(START["s06"] - 0.1, T19 - 0.2, s06a)
add(T19 - 0.2, START["s07"] - 0.1, s06b)
sfx("sfx/whoosh.wav", wt("s06", "sent"), -10)
sfx("sfx/boom.wav", T6, 0)
sfx("music/hit.wav", T6, -6)

# ------------------------------------------------------------------ s07: 2022 reset + law
T22 = wt("s07", "2022")


def s07(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, (226, 214, 190))
    draw_photo(img, "news/dawn_2022_12_12_antofagasta__photo.jpg", g, t, sh["dur"], cx=700, cy=520, seed=21, maxw=1050, maxh=620)
    big_text(img, "DECEMBER 2022: THE RESET", 700, 130, 66, g, T22, fg=WHITE, bg=COPPER, seed=361)
    slide_card(img, "PENALTY DROPPED", 1500, 330, g, wt("s07", "penalty"), side="R", seed=362, kind="anton", size=60, fg=WHITE, bg=RED)
    slide_card(img, "BARRICK 50% · PAKISTAN 50%", 1480, 500, g, wt("s07", "partnership"), side="R", seed=363, kind="anton", size=50, fg=INK, bg=WHITE)
    slide_card(img, "NEW LAW: TERMS LOCKED TO 2052", 1450, 690, g, wt("s07", "law"), side="B", seed=364, kind="anton", size=50, fg=WHITE, bg=INK)
    source(img, "Photo: Dawn, 12 Dec 2022 · Foreign Investment (Promotion and Protection) Act, 2022")


add(START["s07"] - 0.1, START["s08"] - 0.1, s07)
for w_ in ("penalty", "partnership", "law"):
    sfx("sfx/pop.wav", wt("s07", w_), 2)

# ------------------------------------------------------------------ s08: copper + lenders
def s08(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, YELLOW)
    draw_photo(img, "news/iea_gcmo_2025__photo.jpg", g, t, sh["dur"], cx=620, cy=540, seed=22, maxw=980, maxh=640)
    big_text(img, "COPPER: 30% SHORT BY 2035", 620, 140, 58, g, wt("s08", "copper"), fg=WHITE, bg=RED, seed=371)
    for i, (nm, col) in enumerate([("US EXIM  $1.25B", RED), ("IFC  $700M", TEAL), ("ADB  $300M", COPPER)]):
        slide_card(img, nm, 1480, 760 - i * 170, g, wt("s08", "lenders") + i * 0.22, seed=372 + i, kind="anton", size=70, fg=WHITE, bg=col)
    source(img, "IEA, Global Critical Minerals Outlook 2025 · Dawn, 11 Dec 2025 · Profit, 28 Nov 2025")


add(START["s08"] - 0.1, START["s09"] - 0.1, s08)
for i in range(3):
    sfx("sfx/click.wav", wt("s08", "lenders") + i * 0.22, 4)

# ------------------------------------------------------------------ s09: 2026 slowdown, 2030?
T26b, T2030 = wt("s09", "2026"), wt("s09", "2030")
QUOTE = (279, 665, 1142, 695)


def s09(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DARK)
    draw_doc(img, "docs/barrick_statement_2apr2026__page_1_p1.png", g, t, 640, 600, crop=(120, 80, 1330, 1100), width=980, rot=-4,
             hl=QUOTE, hl_t=wt("s09", "slowed"), seed=7)
    big_text(img, "2 APRIL 2026", 640, 120, 64, g, T26b, fg=INK, bg=YELLOW, seed=381)
    lab = label_img("2028", kind="anton", size=200, fg=WHITE, bg=None, pad=(10, 6))
    p = ease_io((g - T2030 + 0.4) / 0.9)
    paste_transformed(img, lab, 1500, 420, 1.0, 0, 1 - 0.6 * p)
    if p > 0.2:
        ImageDraw.Draw(img).line([(1390, 420), (1390 + 230 * clamp((p - 0.2) / 0.3), 420)], fill=RED + (255,), width=14)
    lab2 = label_img("2030?", kind="anton", size=200, fg=RED, bg=None, pad=(10, 6))
    paste_transformed(img, lab2, 1500, 650, 1.0, 0, clamp((p - 0.4) / 0.4))
    big_text(img, "REPORTS, NOT OFFICIAL", 1500, 820, 40, g, T2030 + 0.5, fg=INK, bg=WHITE, seed=382)
    source(img, "Barrick Mining Corporation, 2 Apr 2026 · Dawn, 13 Nov 2026")


add(START["s09"] - 0.1, START["s10"] - 0.1, s09)
sfx("sfx/paper_slide.wav", T26b, 16)
sfx("sfx/slide_slow.wav", T2030, 10)

# ------------------------------------------------------------------ s10: zero + end card
def s10(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, COPPER)
    draw_photo(img, "photos/barrick_aerial_site.jpg", g, t, sh["dur"], cy=H / 2, z0=1.2, z1=1.1, seed=11, maxw=1500, maxh=900)
    big_text(img, "COPPER PRODUCED", W / 2, 300, 70, g, wt("s10", "copper"), fg=INK, bg=YELLOW, seed=391)
    stamp(img, "0", W / 2, 560, g, wt("s10", "zero"), col=WHITE, size=300, rot=-4)


def endcard(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DARK)
    big_text(img, "REKO DIQ", W / 2, 400, 200, g, sh["start"] + 0.1, fg=WHITE, seed=401)
    big_text(img, "Thirty years. Nearly $6 billion. Zero tonnes.", W / 2, 580, 46, g, sh["start"] + 0.5, kind="serif", fg=WHITE, seed=402)


add(START["s10"] - 0.1, END_VO + 0.2, s10)
add(END_VO + 0.2, TOTAL, endcard)
sfx("sfx/stamp_heavy.wav", wt("s10", "zero"), 0)
sfx("sfx/wind.wav", wt("s10", "zero") + 0.3, -8)
SHOTS.sort(key=lambda s_: s_["start"])


def frame_at(t):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    for sh in SHOTS:
        if sh["start"] <= t < sh["start"] + sh["dur"]:
            sh["fn"](img, t - sh["start"], sh)
            break
    draw_caption(img, t, CAPS, y=972)
    return apply_grain(img.convert("RGB"), t)


def render_chunk(args):
    i0, i1, out = args
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def mix(video, out):
    cues = [("music/m1_drone.wav", 0.0, START["s03"], 0.40), ("music/m2_investigate.wav", START["s03"] + 0.2, T6 - 0.05, 0.30),
            ("music/m3_bright.wav", START["s07"] - 0.3, START["s09"], 0.32), ("music/m4_pulse.wav", START["s09"] - 0.1, START["s10"], 0.42),
            ("music/m5_chord.wav", START["s10"] - 0.2, TOTAL, 0.40)]
    ins, fc, vl, k = ["-i", video], [], [], 1
    for b in NAR["beats"]:
        ins += ["-i", str(SH / f"vo/{b['id']}.wav")]
        ms = int(START[b["id"]] * 1000)
        fc.append(f"[{k}:a]atempo={TEMPO},adelay={ms}|{ms}[v{k}]")
        vl.append(f"[v{k}]")
        k += 1
    fc.append(f"{''.join(vl)}amix=inputs={len(vl)}:normalize=0,volume=1.7,apad,asplit=2[vo][sc]")
    ml = []
    for f, a, b_, vol in cues:
        ins += ["-i", str(ROOT / f)]
        dur, ms = b_ - a, int(a * 1000)
        fc.append(f"[{k}:a]atrim=0:{dur:.2f},afade=t=in:d=0.8,afade=t=out:st={max(0, dur - 0.6):.2f}:d=0.6,volume={vol},adelay={ms}|{ms}[m{k}]")
        ml.append(f"[m{k}]")
        k += 1
    fc.append(f"{''.join(ml)}amix=inputs={len(ml)}:normalize=0[mus]")
    fc.append("[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]")
    sl = []
    for f, at, db in SFX:
        ins += ["-i", str(ROOT / f)]
        ms = int(max(0, at) * 1000)
        fc.append(f"[{k}:a]volume={db}dB,adelay={ms}|{ms}[s{k}]")
        sl.append(f"[s{k}]")
        k += 1
    fc.append(f"[vo][duck]{''.join(sl)}amix=inputs={2 + len(sl)}:normalize=0,atrim=0:{TOTAL:.2f},loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    print(f"TOTAL {TOTAL:.1f}s, {len(SHOTS)} shots, {len(SFX)} sfx")
    if mode == "stills":
        times = [s_["start"] + s_["dur"] * 0.8 for s_ in SHOTS]
        tiles = [frame_at(tt).resize((640, 360)) for tt in times]
        sheet = Image.new("RGB", (1920, 360 * ((len(tiles) + 2) // 3)), "white")
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % 3) * 640, (i // 3) * 360))
        sheet.save(ROOT / "cut/short_stills.jpg", quality=85)
        print(ROOT / "cut/short_stills.jpg")
    else:
        from multiprocessing import Pool
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        nf = int(round(TOTAL * FPS))
        step = (nf + n - 1) // n
        jobs = [(i, min(nf, i + step), str(ROOT / f"cut/short_{j:02d}.mp4")) for j, i in enumerate(range(0, nf, step))]
        with Pool(len(jobs)) as pool:
            outs = pool.map(render_chunk, jobs)
        lst = ROOT / "cut/short_chunks.txt"
        lst.write_text("".join(f"file '{o}'\n" for o in outs))
        silent = str(ROOT / "cut/short_video.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", silent], check=True)
        final = str(ROOT.parent / "reko_diq_1min.mp4")
        mix(silent, final)
        with open(ROOT.parent / "reko_diq_1min.srt", "w") as f:
            for i, (s_, e_, tx) in enumerate(CAPS, 1):
                ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}".replace(".", ",")
                f.write(f"{i}\n{ts(s_)} --> {ts(e_)}\n{tx}\n\n")
        print(final)
