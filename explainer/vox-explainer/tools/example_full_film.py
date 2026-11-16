"""Reko Diq: full 3-minute film. Shots, graphics, overlays and sound cues.

python3 film.py stills      -> contact sheet of key moments
python3 film.py render [N]  -> parallel render in N chunks + audio mix -> ../reko_diq_explainer.mp4
"""
import os
import sys
from engine import *

NAR = json.load(open(ROOT / "narration.json"))
BEATS = {b["id"]: b for b in NAR["beats"]}

# ------------------------------------------------------------------ beat timing
START = {}
t = 1.0
for b in NAR["beats"]:
    START[b["id"]] = t
    if b.get("silent"):
        t += b["silent"]
    else:
        import wave
        with wave.open(str(ROOT / f"vo/{b['id']}.wav")) as wv:
            d = wv.getnframes() / wv.getframerate()
        b["dur"] = d
        t += d + b["gap_after"]
WORDS = {b["id"]: words_of(b["id"]) for b in NAR["beats"] if not b.get("silent")}
END_VO = START["b14"] + BEATS["b14"]["dur"]
TOTAL = END_VO + 7.0


def wt(beat, prefix, nth=0, end=False):
    """Global time of the nth word in a beat starting with prefix."""
    import difflib
    ws = WORDS[beat]
    norm = lambda x: x.strip(" ,.?!:\"'").lower()
    hits = [w for w in ws if norm(w["word"]).startswith(prefix.lower())]
    if len(hits) <= nth:                          # Whisper spelling differs: closest word
        sc = sorted(ws, key=lambda w: -difflib.SequenceMatcher(None, norm(w["word"])[:len(prefix) + 2], prefix.lower()).ratio())
        hits = sorted(sc[:nth + 1], key=lambda w: w["start"])
        print(f"  fuzzy: {beat}/{prefix} -> {hits[nth]['word']}", file=sys.stderr)
    w = hits[nth]
    return START[beat] + (w["end"] if end else w["start"])


def bend(beat):
    return START[beat] + BEATS[beat]["dur"]


SFX = []          # (file, time, gain_db)


def sfx(f, at, db=0):
    SFX.append((f, at, db))


DEEP = (34, 58, 61)
DARK = (24, 24, 24)

# ------------------------------------------------------------------ extra drawing kit
def fill_bg(img, color):
    img.paste(bg_fill(color), (0, 0))


class Confetti:
    """Deterministic confetti: ambient drift + bursts. Shapes: tri, dot, zig, squig, rect."""
    COLS = [COPPER, YELLOW, TEAL, RED, WHITE, INK]

    def __init__(self, seed, n=26, bursts=()):
        r = random.Random(seed)
        self.amb = [dict(x=r.uniform(0, W), y=r.uniform(0, H), vx=r.uniform(-14, 14), vy=r.uniform(-10, 18),
                         s=r.uniform(10, 26), rot=r.uniform(0, 360), vr=r.uniform(-60, 60),
                         shape=r.choice("tdzsr"), col=r.choice(self.COLS)) for _ in range(n)]
        self.bursts = []
        for (bt, bx, by, bn) in bursts:
            for _ in range(bn):
                a = r.uniform(0, math.tau)
                v = r.uniform(300, 900)
                self.bursts.append(dict(t0=bt, x=bx, y=by, vx=math.cos(a) * v, vy=math.sin(a) * v - 350,
                                        s=r.uniform(12, 28), rot=r.uniform(0, 360), vr=r.uniform(-400, 400),
                                        shape=r.choice("tdzsr"), col=r.choice(self.COLS)))

    @staticmethod
    def shape(d, x, y, s, rot, shape, col):
        c = math.cos(math.radians(rot))
        sn = math.sin(math.radians(rot))

        def R(px, py):
            return (x + px * c - py * sn, y + px * sn + py * c)
        if shape == "t":
            d.polygon([R(0, -s), R(-s * 0.9, s * 0.6), R(s * 0.9, s * 0.6)], fill=col + (255,))
        elif shape == "d":
            d.ellipse((x - s * 0.6, y - s * 0.6, x + s * 0.6, y + s * 0.6), fill=col + (255,))
        elif shape == "r":
            d.polygon([R(-s, -s * 0.35), R(s, -s * 0.35), R(s, s * 0.35), R(-s, s * 0.35)], fill=col + (255,))
        elif shape == "z":
            pts = [R(-s + i * s * 0.5, (-1) ** i * s * 0.3) for i in range(5)]
            d.line(pts, fill=col + (255,), width=max(3, int(s * 0.25)))
        else:
            pts = [R(-s + i * s * 0.25, math.sin(i * 1.2) * s * 0.3) for i in range(9)]
            d.line(pts, fill=col + (255,), width=max(3, int(s * 0.22)), joint="curve")

    def draw(self, img, t, amb=True):
        d = ImageDraw.Draw(img)
        ts = stepped(t)
        if amb:
            for p in self.amb:
                x = (p["x"] + p["vx"] * ts) % W
                y = (p["y"] + p["vy"] * ts) % H
                self.shape(d, x, y, p["s"], p["rot"] + p["vr"] * ts, p["shape"], p["col"])
        for p in self.bursts:
            dt = ts - p["t0"]
            if 0 <= dt < 2.2:
                x = p["x"] + p["vx"] * dt * (1 - dt * 0.25)
                y = p["y"] + p["vy"] * dt + 700 * dt * dt
                self.shape(d, x, y, p["s"], p["rot"] + p["vr"] * dt, p["shape"], p["col"])


def sunburst(img, cx, cy, t, col, n=18, alpha=90):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rot = stepped(t) * 8
    R = 1500
    for i in range(n):
        a0 = math.radians(rot + i * 360 / n)
        a1 = math.radians(rot + (i + 0.5) * 360 / n)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=col + (alpha,))
    img.alpha_composite(lay)


def tl_active(t):
    return START["b05"] <= t < bend("b13") + 0.6


def safe_y(t, y):
    return y + 150 if (tl_active(t) and y < 260) else y


def big_text(img, text, cx, cy, size, t, t0, kind="anton", fg=INK, bg=None, slam=False, seed=5, shake=0):
    """Headline text; slam=True scales from 2.4x with impact."""
    if t < t0:
        return
    cy = safe_y(t, cy)
    lab = label_img(text, kind=kind, size=size, fg=fg, bg=bg, pad=(30, 16), rot_seed=seed)
    p = (t - t0) / 0.3
    s = (2.4 - 1.4 * ease_out(p)) if slam else (0.55 + 0.45 * back_out(p, 2.0))
    a = clamp(p * 3)
    dx, dy, dr = jitter(seed, t, 0.7)
    paste_transformed(img, lab, cx + dx, cy + dy, s, dr + random.Random(seed).uniform(-2, 2), a)


def counter(img, val, decimals, cx, cy, t, t0, t1, size=230, fg=WHITE, prefix="", suffix="", seed=9, kind="anton"):
    if t < t0:
        return
    v = val * ease_out((t - t0) / max(0.01, t1 - t0))
    txt = f"{prefix}{v:,.{decimals}f}{suffix}"
    lab = label_img(txt, kind=kind, size=size, fg=fg, bg=None, pad=(20, 10), rot_seed=seed)
    dx, dy, dr = jitter(seed, t, 0.5)
    paste_transformed(img, lab, cx + dx, cy + dy, 1.0, dr, clamp((t - t0) * 6))


def slide_card(img, text, tx, ty, t, t0, side=None, seed=1, t1=None, **kw):
    """Info card sliding in from a random side with overshoot."""
    if t < t0:
        return
    ty = safe_y(t, ty)
    side = side or random.Random(seed).choice("LRTB")
    p = back_out((t - t0) / 0.42, 1.6)
    off = (1 - p)
    dx, dy = {"L": (-1300, 0), "R": (1300, 0), "T": (0, -800), "B": (0, 800)}[side]
    a = 1.0
    if t1 is not None and t > t1:
        a = clamp(1 - (t - t1) / 0.25)
    lab = label_img(text, rot_seed=seed, **kw)
    jx, jy, jr = jitter(seed, t, 0.7)
    paste_transformed(img, lab, tx + dx * off + jx, ty + dy * off + jy, 1.0, random.Random(seed).uniform(-3, 3) + jr, a)


def red_string(img, p0, p1, t, t0, dur=0.5, sag=0.08, col=RED, width=5):
    if t < t0:
        return
    draw_arrow(img, p0, p1, t, t0, dur=dur, color=col, width=width, bend=sag, head=0, seed=17)
    d = ImageDraw.Draw(img)
    for (x, y) in (p0, p1):
        d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=RED + (255,))
        d.ellipse((x - 4, y - 6, x + 2, y), fill=(255, 180, 170, 255))


def stamp(img, text, cx, cy, t, t0, col=RED, size=96, rot=-8, seed=3):
    """Rubber-stamp slam: outlined text box, slight grunge."""
    if t < t0:
        return
    f = font("anton", size)
    bb = f.getbbox(text)
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 50
    st = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    d.rectangle((6, 6, w - 6, h - 6), outline=col + (235,), width=9)
    d.text((30 - bb[0], 25 - bb[1]), text, font=f, fill=col + (235,))
    r = random.Random(seed)
    for _ in range(int(w * h / 900)):            # grunge: knock out specks
        x, y = r.uniform(0, w), r.uniform(0, h)
        d.ellipse((x, y, x + r.uniform(2, 6), y + r.uniform(2, 6)), fill=(0, 0, 0, 0))
    p = (t - t0) / 0.18
    s = 1.8 - 0.8 * ease_out(p)
    paste_transformed(img, st, cx, cy, s, rot, clamp(p * 4))


SHOW_SOURCES = False   # credits live in the video description, never on screen


def source(img, text):
    if not SHOW_SOURCES:
        return
    lab = label_img(text, kind="inter", size=22, fg=WHITE, bg=(20, 20, 20), pad=(10, 5), torn=False)
    paste_transformed(img, lab, 36 + lab.width / 2, H - 34, 1.0, 0, 0.75)


def news_card(img, outlet, headline, date, cx, cy, t, t0, seed=1, side=None, quote=None, hl_t=None, width=760):
    """Clean news card: outlet, real headline, date; optional quote with highlighter sweep."""
    if t < t0:
        return
    pad = 34
    f_out, f_head, f_date, f_q = font("interb", 26), font("serif", 44), font("inter", 24), font("inter", 30)

    def wrap(text, f, maxw):
        words, lines, cur = text.split(), [], ""
        for w_ in words:
            tst = (cur + " " + w_).strip()
            if f.getlength(tst) > maxw and cur:
                lines.append(cur)
                cur = w_
            else:
                cur = tst
        return lines + [cur]
    hl = wrap(headline, f_head, width - 2 * pad)
    ql = wrap(quote, f_q, width - 2 * pad) if quote else []
    hgt = pad + 34 + 18 + len(hl) * 54 + 14 + 30 + (20 + len(ql) * 40 if ql else 0) + pad
    card = Image.new("RGBA", (width, hgt), (248, 246, 241, 255))
    d = ImageDraw.Draw(card)
    y = pad
    d.text((pad, y), outlet.upper(), font=f_out, fill=RED + (255,))
    y += 34 + 18
    for ln in hl:
        d.text((pad, y), ln, font=f_head, fill=INK + (255,))
        y += 54
    y += 14
    d.text((pad, y), date, font=f_date, fill=(110, 105, 98, 255))
    y += 30
    if ql:
        y += 20
        if hl_t is not None and t > hl_t:
            p = ease_out((t - hl_t) / 0.9)
            tot = sum(f_q.getlength(l_) for l_ in ql)
            done = tot * p
            yy = y
            for l_ in ql:
                lw = f_q.getlength(l_)
                seg = clamp(done / lw) if lw else 0
                d.rectangle((pad - 4, yy + 2, pad + lw * seg + 4, yy + 36), fill=YELLOW + (150,))
                done -= lw
                yy += 40
        for l_ in ql:
            d.text((pad, y), l_, font=f_q, fill=(50, 48, 45, 255))
            y += 40
    card = with_shadow(card, (9, 12), 12, 0.45)
    side = side or random.Random(seed).choice("LRTB")
    p = back_out((t - t0) / 0.45, 1.4)
    dx, dy = {"L": (-1500, 0), "R": (1500, 0), "T": (0, -1000), "B": (0, 1000)}[side]
    jx, jy, jr = jitter(seed, t, 0.5)
    paste_transformed(img, card, cx + dx * (1 - p) + jx, cy + dy * (1 - p) + jy, 1.0, random.Random(seed).uniform(-3, 3) + jr)


# ------------------------------------------------------------------ terrain maps
@lru_cache(None)
def relief():
    im = Image.open(GEO / "relief.png").convert("L")
    return im                                     # lon 0..100E, lat 0..60N, 30 px/deg


@lru_cache(None)
def disputed():
    d = json.load(open(GEO / "disputed.geojson"))
    out = {}
    for f in d["features"]:
        n = f["properties"].get("BRK_NAME")
        if n in ("Jammu and Kashmir", "Gilgit-Baltistan", "Siachen Glacier"):
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            out[n] = [np.array(p[0]) for p in polys]
    return out


@lru_cache(None)
def hatch():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in range(-H, W, 22):
        d.line([(x, H), (x + H, 0)], fill=YELLOW + (200,), width=5)
    return im


def poly_pts(view, ring):
    x, y = proj(view, ring[:, 0], ring[:, 1])
    return list(zip(x.tolist(), y.tolist()))


TINT = {"PAK": (250, 238, 214), "IRN": (125, 154, 154), "AFG": (196, 176, 140), "IND": (170, 168, 160),
        "CHN": (170, 168, 160), "TKM": (170, 168, 160), "OMN": (170, 168, 160)}


def terrain_map(img, view, bal_fill=0.0, dark=0.0, tint_alpha=0.55, pk_border=1.0, kashmir=True, red_iran=0.0):
    feats, bal = geo_data()
    cx, cy, span = view
    k = W / span
    c = math.cos(math.radians(cy))
    lon0, lon1 = cx - span / (2 * c), cx + span / (2 * c)
    lat1, lat0 = cy + H / (2 * k), cy - H / (2 * k)
    rel = relief().transform((W, H), Image.EXTENT, (lon0 * 30, (60 - lat1) * 30, lon1 * 30, (60 - lat0) * 30), Image.BILINEAR)
    rel = rel.point(lambda v: int(70 + v * 0.75))
    base = Image.merge("RGB", (rel, rel, rel))
    land = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(land)
    tint = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tint)
    vis = []
    for f in feats:
        bb = f["bb"]
        if bb[2] < lon0 or bb[0] > lon1 or bb[3] < lat0 or bb[1] > lat1:
            continue
        vis.append(f)
        col = TINT.get(f["iso"], (200, 196, 186))
        if f["iso"] == "IRN" and red_iran > 0:
            col = tuple(int(col[i] + (RED[i] - col[i]) * red_iran) for i in range(3))
        for ring in f["rings"]:
            if len(ring) < 3:
                continue
            pts = poly_pts(view, ring)
            ld.polygon(pts, fill=255)
            td.polygon(pts, fill=col + (int(255 * tint_alpha),))
    dsp = disputed() if kashmir else {}
    for ring in dsp.get("Gilgit-Baltistan", []):
        pts = poly_pts(view, ring)
        ld.polygon(pts, fill=255)
        td.polygon(pts, fill=TINT["PAK"] + (int(255 * tint_alpha),))
    ocean = Image.blend(base, Image.new("RGB", (W, H), (18, 34, 38)), 0.78)
    out = Image.composite(base, ocean, land).convert("RGBA")
    out.alpha_composite(tint)
    if bal_fill > 0:
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bl)
        for ring in bal:
            bd.polygon(poly_pts(view, ring), fill=COPPER + (int(205 * bal_fill),))
        out.alpha_composite(bl)
    # disputed J&K: hatched, per Pakistan's official map
    jk = dsp.get("Jammu and Kashmir", []) + dsp.get("Siachen Glacier", [])
    if jk:
        m = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(m)
        for ring in jk:
            md.polygon(poly_pts(view, ring), fill=255)
        hl = Image.new("RGBA", (W, H), TINT["PAK"] + (int(120 * tint_alpha / 0.55),))
        hl.alpha_composite(hatch())
        out.paste(hl, (0, 0), ImageChops.multiply(m, hl.getchannel("A")))
    d = ImageDraw.Draw(out)
    lw = 2 if span > 30 else 3
    for f in vis:
        if f["iso"] == "PAK":
            continue
        for ring in f["rings"]:
            if len(ring) >= 3:
                pts = poly_pts(view, ring)
                d.line(pts + pts[:1], fill=(60, 60, 58, 200), width=lw, joint="curve")
    if bal_fill > 0:
        for ring in bal:
            pts = poly_pts(view, ring)
            d.line(pts + pts[:1], fill=(80, 40, 20, 230), width=lw, joint="curve")
    for ring in jk:                               # dotted outline of the disputed area
        pts = poly_pts(view, ring)
        for i in range(0, len(pts) - 1, 3):
            d.line(pts[i:i + 2], fill=YELLOW + (255,), width=lw + 1)
    if pk_border > 0:                             # Pakistan border: ink under yellow
        pk = [f for f in vis if f["iso"] == "PAK"]
        rings = [r_ for f in pk for r_ in f["rings"]] + dsp.get("Gilgit-Baltistan", [])
        for ring in rings:
            if len(ring) >= 3:
                pts = poly_pts(view, ring)
                d.line(pts + pts[:1], fill=INK + (255,), width=lw + 5, joint="curve")
        for ring in rings:
            if len(ring) >= 3:
                pts = poly_pts(view, ring)
                d.line(pts + pts[:1], fill=YELLOW + (int(255 * pk_border),), width=lw + 2, joint="curve")
    if dark > 0:
        out.alpha_composite(Image.new("RGBA", (W, H), (10, 10, 12, int(170 * dark))))
    img.alpha_composite(out)


def map_name(img, text, view, lon, lat, t, t0, t1=None, size=46, col=WHITE, kind="serif"):
    if t < t0:
        return
    a = clamp((t - t0) / 0.3)
    if t1 is not None and t > t1:
        a *= clamp(1 - (t - t1) / 0.3)
    if a <= 0:
        return
    x, y = lonlat_xy(view, lon, lat)
    lab = label_img(text, kind=kind, size=size, fg=col, bg=None, pad=(8, 4))
    paste_transformed(img, lab, x, y, 1.0, 0, a)


@lru_cache(None)
def inset_base():
    v = (70.5, 30.5, 22.0)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    terrain_map(im, v, bal_fill=1.0, tint_alpha=0.7)
    return im.resize((360, 203), Image.LANCZOS), v


def inset(img, view):
    base, v = inset_base()
    card = base.copy()
    d = ImageDraw.Draw(card)
    cx, cy, span = view
    c = math.cos(math.radians(cy))
    x0, y0 = lonlat_xy(v, cx - span / (2 * c), cy + span * 0.28)
    x1, y1 = lonlat_xy(v, cx + span / (2 * c), cy - span * 0.28)
    sc = 360 / W
    d.rectangle((x0 * sc, y0 * sc, x1 * sc, y1 * sc), outline=RED + (255,), width=3)
    d.rectangle((0, 0, 359, 202), outline=WHITE + (255,), width=4)
    paste_transformed(img, with_shadow(card, (6, 8), 8, 0.5), W - 250, 175, 1.0, 0)


# ------------------------------------------------------------------ persistent overlays
TL_EVENTS = []    # (time, year, text)


def timeline_bar(img, t):
    t0, t1 = START["b05"], bend("b13") + 0.6
    if not (t0 <= t < t1):
        return
    a = clamp((t - t0) / 0.4) * clamp((t1 - t) / 0.4)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1, y = 300, W - 300, 64
    y0, y1 = 1990, 2030
    d.line([(x0, y + 2), (x1, y + 2)], fill=(0, 0, 0, 90), width=4)
    d.line([(x0, y), (x1, y)], fill=WHITE + (255,), width=4)
    for yr in range(y0, y1 + 1):
        x = x0 + (x1 - x0) * (yr - y0) / (y1 - y0)
        hgt = 14 if yr % 10 == 0 else 7
        d.line([(x, y - hgt), (x, y)], fill=WHITE + (255,), width=2)
    f = font("interb", 26)
    for yr, xx, anc in ((y0, x0 - 18, "rm"), (y1, x1 + 18, "lm")):
        d.text((xx + 2, y + 2), str(yr), font=f, fill=(0, 0, 0, 120), anchor=anc)
        d.text((xx, y), str(yr), font=f, fill=WHITE + (255,), anchor=anc)
    past = [e for e in TL_EVENTS if e[0] <= t]
    if past:
        prev = past[-2][1] if len(past) > 1 else past[-1][1]
        cur = past[-1]
        p = ease_io((t - cur[0]) / 0.6)
        yr = prev + (cur[1] - prev) * p
        x = x0 + (x1 - x0) * (yr - y0) / (y1 - y0)
        d.polygon([(x, y + 8), (x - 13, y + 30), (x + 13, y + 30)], fill=WHITE + (255,))
        for e in past:                             # passed events leave copper dots
            ex = x0 + (x1 - x0) * (e[1] - y0) / (y1 - y0)
            d.ellipse((ex - 6, y - 6, ex + 6, y + 6), fill=COPPER + (255,))
        if t - cur[0] > 0.25:
            fy, ft = font("interb", 22), font("anton", 34)
            yy = y + 40
            d.rectangle((x - 4, yy, x + fy.getlength(str(cur[1])) + 12, yy + 30), fill=INK + (235,))
            d.text((x + 4, yy + 3), str(cur[1]), font=fy, fill=WHITE + (255,))
            yy += 32
            tw = ft.getlength(cur[2])
            d.rectangle((x - 4, yy, x + tw + 14, yy + 46), fill=INK + (235,))
            d.text((x + 5, yy + 3), cur[2], font=ft, fill=WHITE + (255,))
    if a < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)


CHAPTERS = []     # (time, text)


def chapter_stamp(img, t):
    for (t0, txt) in CHAPTERS:
        if t0 <= t < t0 + 2.8:
            s, a = pop_in(t, t0, 0.35)
            a *= clamp((t0 + 2.8 - t) / 0.3)
            lab = label_img(txt, kind="anton", size=44, fg=INK, bg=YELLOW, pad=(22, 10))
            paste_transformed(img, lab, 60 + lab.width / 2, 170, s, -3, a)


CAPS = []
for b in NAR["beats"]:
    if not b.get("silent"):
        CAPS += caption_chunks(b["text"], WORDS[b["id"]], START[b["id"]])


def captions(img, t):
    draw_caption(img, t, CAPS, y=972)


# ------------------------------------------------------------------ shots
SHOTS = []


def add(start, end, fn, **kw):
    SHOTS.append(dict(start=start, dur=end - start, fn=fn, **kw))


def poster(start, end, name, bg, move="push_in", labels=(), extra=None, conf=None, seed=7, src=None, scale=1.0):
    def fn(img, t, sh):
        shot_poster(img, t, sh)
        g = sh["start"] + t
        if conf:
            conf.draw(img, g)
        if extra:
            extra(img, g, t, sh)
        if src:
            source(img, src)
    add(start, end, fn, poster=name, bg=bg, move=move, labels=list(labels), seed=seed, scale=scale)


def L(text, x, y, at, start, seed=3, **style):
    return {"text": text, "x": x, "y": y, "t": at - start, "seed": seed, "style": style}


# ---- ACT 1 -------------------------------------------------------------------
CHAPTERS.append((START["b01"] + 0.3, "PART 1 · THE TREASURE"))
s, e = 0.0, wt("b01", "no")
poster(s, e, "p01_desert", YELLOW, "push_in", seed=11, scale=1.05)
s2, e2 = e, START["b02"]
poster(s2, e2, "p01_desert", YELLOW, "pan", seed=12, scale=1.35,
       extra=lambda img, g, t, sh: draw_circle_mark(img, 960, 560, 240, 120, g, wt("b01", "barely"), color=RED, seed=4))
sfx("sfx/wind.wav", 0.0, -6)

# G1 cutaway + copper counter
cut_s, cut_e = START["b02"], wt("b02", "nearly")
cf1 = Confetti(21, 18, bursts=[(wt("b02", "copper"), 960, 420, 40)])


def g1(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DEEP)
    lay = poster_layer("p02_cutaway")
    paste_transformed(img, lay, W / 2, H / 2 + 60, 0.95 + 0.04 * ease_io(t / sh["dur"]), jitter(31, g)[2])
    p = ease_io((g - (cut_s + 0.25)) / 0.9)       # desert surface peels away
    top = poster_layer("p01_desert")
    if p < 1:
        paste_transformed(img, top, W / 2 - 900 * p, H / 2 - 700 * p * p + 40, 1.0 - 0.3 * p, -25 * p, 1.0)
    cf1.draw(img, g, amb=False)
    counter(img, 13.1, 1, W / 2, 190, g, wt("b02", "13"), wt("b02", "copper", end=True), size=210, fg=WHITE)
    big_text(img, "MILLION TONNES OF COPPER", W / 2, 330, 64, g, wt("b02", "million"), kind="anton", fg=INK, bg=YELLOW, seed=32)
    source(img, "Expected life-of-mine output, 2025 feasibility study · Dawn, 26 Mar 2025")


add(cut_s, cut_e, g1)
sfx("sfx/paper_slide.wav", cut_s + 0.2, 16)
sfx("sfx/ring.wav", wt("b02", "13"), -4)
sfx("sfx/pop.wav", wt("b02", "million"), 2)

gold_e = wt("b02", "people")
cf2 = Confetti(22, 14, bursts=[(wt("b02", "gold"), 1250, 560, 36)])
poster(cut_e, gold_e, "p02_gold", COPPER, "push_in", seed=13, conf=cf2,
       extra=lambda img, g, t, sh: (counter(img, 17.9, 1, 520, 400, g, wt("b02", "18"), wt("b02", "gold", end=True), size=200, fg=WHITE),
                                    big_text(img, "MILLION OUNCES OF GOLD", 520, 540, 56, g, wt("b02", "ounces"), fg=INK, bg=YELLOW, seed=33)),
       src="Expected life-of-mine output, 2025 feasibility study · Dawn, 26 Mar 2025")
sfx("sfx/ring.wav", wt("b02", "18"), -4)

why = wt("b02", "why")
poster(gold_e, why + 0.35, "p02_cart", None, "push_in", seed=14,
       extra=lambda img, g, t, sh: (big_text(img, "TONNES SOLD:", 1380, 420, 90, g, wt("b02", "not"), fg=INK, bg=WHITE, seed=34),
                                    stamp(img, "0", 1380, 610, g, wt("b02", "sold"), col=RED, size=230, rot=-6)))
sfx("sfx/stamp_heavy.wav", wt("b02", "sold"), -2)


def black(img, t, sh):
    img.paste((8, 8, 8), (0, 0, W, H))


add(why + 0.35, START["b03"], black)

# G2 title
cf3 = Confetti(23, 30, bursts=[(START["b03"] + 0.2, 960, 420, 60)])


def g2(img, t, sh):
    fill_bg(img, None)
    g = sh["start"] + t
    cf3.draw(img, g)
    sunburst(img, W / 2, 430, g, YELLOW, alpha=40)
    big_text(img, "REKO DIQ", W / 2, 420, 300, g, sh["start"] + 0.15, kind="anton", fg=INK, slam=True, seed=41)
    p = ease_out((g - sh["start"] - 0.7) / 0.7)
    if p > 0:
        d = ImageDraw.Draw(img)
        r = random.Random(5)
        pts = [(560 + 800 * i / 40, 620 + math.sin(i * 0.7) * 4 + r.uniform(-2, 2)) for i in range(int(40 * p) + 1)]
        if len(pts) > 1:
            d.line(pts, fill=COPPER, width=18, joint="curve")
    a2 = clamp((g - sh["start"] - 1.3) / 0.5)
    if a2 > 0:
        lab = label_img("Why Pakistan's biggest treasure is still underground", kind="serif", size=58, fg=INK, bg=None, pad=(10, 6))
        paste_transformed(img, lab, W / 2, 720 + (1 - ease_out(a2)) * 20, 1.0, 0, a2)


add(START["b03"], START["b04"], g2)
sfx("music/hit.wav", START["b03"] + 0.1, -3)
sfx("sfx/paper_slide.wav", START["b03"] + 0.15, 18)

# b04: sandy peak + locator map with Kashmir + Tethyan belt
sits = wt("b04", "it") - 0.1
poster(START["b04"], sits, "p04_peak", YELLOW, "push_in", seed=15,
       labels=[L('REKO DIQ = "SANDY PEAK"', W / 2, 110, wt("b04", "means"), START["b04"], seed=42, kind="anton", size=88, fg=WHITE, bg=COPPER)],
       conf=Confetti(24, 16))
sfx("sfx/pop.wav", wt("b04", "means"), 4)

PK = (70.0, 30.6, 24.0)
BAL = (65.6, 28.6, 11.0)
CHG = (63.2, 29.4, 6.2)
BELT = (43.0, 37.0, 64.0)
REKO = (62.07, 29.12)
BAND = [(21.9, 44.1), (24.5, 42.6), (29.0, 40.6), (35.0, 39.6), (42.0, 40.0), (46.7, 38.7), (50.5, 34.6), (55.9, 30.0), (62.07, 29.12)]
T_CH, T_BA, T_IR, T_AF = wt("b04", "chagai"), wt("b04", "balochistan"), wt("b04", "iran"), wt("b04", "afghanistan")
T_PT, T_BT = wt("b04", "it's"), wt("b04", "belt")
T_EU, T_TR, T_IR2, T_PK = wt("b04", "europe"), wt("b04", "turkey"), wt("b04", "iran", 1), wt("b04", "pakistan")


def g34(img, t, sh):
    g = sh["start"] + t
    st = sh["start"]
    keys = [(0, PK), (T_CH - 0.2 - st, PK), (T_BA + 0.2 - st, BAL), (T_IR - 0.5 - st, BAL), (T_AF + 0.3 - st, CHG),
            (T_PT - st, CHG), (T_BT + 0.9 - st, BELT)]
    view = view_at(keys, t)
    terrain_map(img, view, bal_fill=ease_out((g - (T_BA - 0.35)) / 0.5))
    out = T_PT + 0.1
    map_name(img, "Pakistan", view, 71.5, 29.2, g, st + 0.2, T_CH - 0.1, size=64, col=INK)
    map_name(img, "Disputed territory", view, 76.2, 33.8, g, st + 0.4, T_CH - 0.1, size=30, col=INK)
    map_name(img, "India", view, 76.5, 26.0, g, st + 0.2, T_CH - 0.1, size=44)
    draw_label(img, "BALOCHISTAN", *lonlat_xy(view, 66.4, 27.6), g, T_BA, seed=22, t1=T_IR - 0.6, kind="anton", size=56, fg=WHITE, bg=INK)
    if g < out + 0.3:
        px, py = lonlat_xy(view, *REKO)
        draw_pin(img, px, py, g, T_BA + 0.55)
        draw_label(img, "REKO DIQ", px + 150, py - 120, g, T_BA + 0.8, seed=23, t1=out, kind="anton", size=58, fg=WHITE, bg=COPPER)
        draw_label(img, "CHAGAI, BALOCHISTAN", px + 200, py + 34, g, T_BA + 1.0, seed=24, t1=out, kind="anton", size=38)
        map_name(img, "Iran", view, 61.0, 28.6, g, T_IR, out, size=58)
        map_name(img, "Afghanistan", view, 63.9, 30.5, g, T_AF, out, size=58)
        draw_arrow(img, (px + 330, py + 300), (px + 25, py + 45), g, T_IR + 0.1, color=YELLOW, bend=0.3, seed=8)
        if view[2] < 9:
            inset(img, view)
    p = ease_io((g - (T_EU - 0.4)) / (T_PK + 0.3 - (T_EU - 0.4)))
    draw_band(img, view, BAND, p, width_deg=2.0)
    if g > T_BT - 0.2:
        draw_label(img, "THE TETHYAN BELT", W / 2, 120, g, T_BT, seed=27, kind="anton", size=80, fg=WHITE, bg=COPPER)
        for nm, lon, lat, tt in [("Europe", 21.0, 47.2, T_EU), ("Turkey", 33.5, 37.2, T_TR), ("Iran", 53.5, 33.6, T_IR2), ("Pakistan", 69.0, 26.2, T_PK)]:
            map_name(img, nm, view, lon, lat, g, tt, size=50)
    source(img, "Map data: Natural Earth · Kashmir shown per Pakistan's official map")


add(sits, START["b05"], g34)
for tt, f, db in [(T_BA + 0.85, "sfx/pin.wav", 2), (T_IR, "sfx/pop.wav", 0), (T_AF, "sfx/pop.wav", 0), (sits - 0.1, "sfx/whoosh.wav", -10),
                  (T_PT + 0.2, "sfx/whoosh.wav", -10), (T_EU - 0.3, "sfx/pencil.wav", 14), (T_BT, "sfx/pop.wav", 2)]:
    sfx(f, tt, db)

# ---- ACT 2 -------------------------------------------------------------------
CHAPTERS.append((START["b05"] + 0.2, "PART 2 · THE CURSE"))
TL_EVENTS.append((wt("b05", "1993"), 1993, "DEAL SIGNED"))
rights = wt("b05", "rights")
poster(START["b05"], rights, "p05_contract", TEAL, "push_in", seed=16,
       extra=lambda img, g, t, sh: (stamp(img, "1993", 600, 560, g, wt("b05", "1993"), col=RED, size=150, rot=-10),
                                    slide_card(img, "EXPLORATION DEAL SIGNED", 1300, 860, g, wt("b05", "exploration"), seed=51, kind="anton", size=58, fg=WHITE, bg=INK),
                                    slide_card(img, "BHP · AUSTRALIA", 1450, 300, g, wt("b05", "bhp") if any(w["word"].strip(" ,.").lower().startswith("bhp") for w in WORDS["b05"]) else wt("b05", "australian"), seed=52, kind="anton", size=50, fg=INK, bg=YELLOW)),
       src="The News, 10 Dec 2022")
sfx("sfx/stamp.wav", wt("b05", "1993"), -2)
sfx("sfx/whoosh.wav", wt("b05", "exploration"), -14)


def org(img, g, t, sh):
    tb = (1240, 420)
    slide_card(img, "BHP", 1040, 230, g, sh["start"] + 0.1, side="L", seed=61, kind="anton", size=52, fg=INK, bg=WHITE)
    draw_arrow(img, (1110, 260), (1210, 370), g, wt("b05", "pass"), color=YELLOW, bend=0.3, seed=9)
    slide_card(img, "TETHYAN COPPER", tb[0] + 140, tb[1], g, wt("b05", "tethyan"), side="R", seed=62, kind="anton", size=60, fg=WHITE, bg=COPPER)
    slide_card(img, "ANTOFAGASTA · CHILE", 1120, 700, g, wt("b05", "antofagasta"), side="B", seed=63, kind="anton", size=46, fg=INK, bg=WHITE)
    slide_card(img, "BARRICK · CANADA", 1580, 700, g, wt("b05", "barrick"), side="B", seed=64, kind="anton", size=46, fg=INK, bg=WHITE)
    red_string(img, (1160, 650), (1300, 470), g, wt("b05", "antofagasta") + 0.3)
    red_string(img, (1560, 650), (1440, 470), g, wt("b05", "barrick") + 0.3)


poster(rights, START["b06"], "p05_folder", COPPER, "pan", seed=17, extra=org, src="The News, 10 Dec 2022")
for w_ in ("tethyan", "antofagasta", "barrick"):
    sfx("sfx/pop.wav", wt("b05", w_), 0)

T11 = wt("b06", "2011")
TL_EVENTS.append((T11, 2011, "LICENCE DENIED"))
poster(START["b06"], T11 - 0.35, "p06_cores", YELLOW, "push_in", seed=18, conf=Confetti(25, 10),
       extra=lambda img, g, t, sh: (counter(img, 220, 0, 560, 300, g, wt("b06", "$200"), wt("b06", "million", end=True), size=200, fg=INK, prefix="$", suffix="M+"),
                                    big_text(img, "SPENT EXPLORING", 560, 440, 60, g, wt("b06", "drilling"), fg=WHITE, bg=INK, seed=71)),
       src="Figure according to Tethyan Copper · Profit, 20 Feb 2022")
sfx("sfx/ring.wav", wt("b06", "$200"), -4)
off = wt("b06", "officials")
poster(T11 - 0.35, off, "p06_denied", None, "push_in", seed=19,
       extra=lambda img, g, t, sh: (big_text(img, "2011: LICENCE DENIED", 1350, 190, 84, g, T11, fg=WHITE, bg=RED, seed=72),
                                    draw_circle_mark(img, 760, 540, 260, 210, g, wt("b06", "no"), color=YELLOW, seed=6)))
sfx("sfx/stamp_heavy.wav", wt("b06", "no"), -2)


def smelt(img, g, t, sh):
    slide_card(img, "WHAT OFFICIALS WANTED: REFINE IN PAKISTAN", 520, 150, g, wt("b06", "smelted"), side="T", seed=81, kind="anton", size=44, fg=INK, bg=YELLOW)
    draw_arrow(img, (520, 200), (460, 380), g, wt("b06", "smelted") + 0.2, color=YELLOW, bend=0.25, seed=12)
    slide_card(img, "NOT RAW CONCENTRATE SHIPPED OUT", 1420, 950 - 120, g, wt("b06", "raw"), side="B", seed=82, kind="anton", size=44, fg=WHITE, bg=RED)
    draw_arrow(img, (1420, 780), (1450, 640), g, wt("b06", "raw") + 0.2, color=RED, bend=-0.2, seed=13)


poster(off, START["b07"], "p06_smelt", TEAL, "pan", seed=20, extra=smelt, src="The News timeline, 2 Aug 2019")

T13 = wt("b07", "2013")
TL_EVENTS.append((T13, 2013, "DEAL DECLARED VOID"))


def ruling(img, g, t, sh):
    d = ImageDraw.Draw(img)
    f = font("serif", 46)
    z = 1.0 + 0.06 * ease_io(t / sh["dur"])
    x0, y0 = W / 2 - 400 * z, 380
    txt = "The 1993 agreement is declared void."
    tp = clamp((g - wt("b07", "struck")) / 1.2)
    shown = txt[:int(len(txt) * tp)]
    if wt("b07", "struck") + 1.3 < g:
        p = ease_out((g - wt("b07", "struck") - 1.3) / 0.5)
        d.rectangle((x0 - 10, y0 - 4, x0 - 10 + (f.getlength(txt) + 20) * p, y0 + 60), fill=YELLOW + (150,))
    d.text((x0, y0), shown, font=f, fill=INK + (255,))
    stamp(img, "VOID", 1450, 300, g, wt("b07", "entire"), col=RED, size=120, rot=12)
    big_text(img, "2013: SUPREME COURT", 560, 140, 70, g, T13, fg=WHITE, bg=INK, seed=91)


court = "p07_court_pk" if (ROOT / "posters/p07_court_pk.png").exists() else "p07_ruling"
cs = wt("b07", "struck") - 0.3
poster(START["b07"], cs, court, TEAL, "push_in", seed=21,
       extra=lambda img, g, t, sh: big_text(img, "2013: SUPREME COURT OF PAKISTAN", W / 2, 120, 66, g, T13, fg=WHITE, bg=INK, seed=92))
poster(cs, START["b08"], "p07_ruling", None, "push_in", seed=22, extra=ruling,
       src="Supreme Court order of 7 Jan 2013 · cited in UK High Court judgment, 2021")
sfx("sfx/gavel.wav", T13, -2)
sfx("sfx/stamp_heavy.wav", wt("b07", "entire"), -4)

T19 = wt("b08", "2019")
TL_EVENTS.append((T19, 2019, "$5.9B AWARD"))
six = wt("b08", "$6") if any(w["word"].startswith("$6") for w in WORDS["b08"]) else wt("b08", "nearly")
poster(START["b08"], six - 0.1, "p08_hall", TEAL, "push_in", seed=23,
       extra=lambda img, g, t, sh: (slide_card(img, "WORLD BANK TRIBUNAL (ICSID)", 1300, 200, g, wt("b08", "world"), side="R", seed=101, kind="anton", size=56, fg=WHITE, bg=INK),
                                    slide_card(img, "JUL 2019 · WASHINGTON", 420, 820, g, T19, side="L", seed=102, kind="anton", size=44, fg=INK, bg=YELLOW)))
cf4 = Confetti(26, 0, bursts=[(six, 960, 500, 70)])


def g6(img, t, sh):
    g = sh["start"] + t
    shake = math.exp(-max(0, g - six) * 6) * 26
    ox, oy = math.sin(g * 90) * shake, math.cos(g * 77) * shake
    fill_bg(img, RED)
    sunburst(img, W / 2, H / 2, g, (240, 120, 100), alpha=70)
    cf4.draw(img, g, amb=False)
    lab = label_img("$5.9 BILLION", kind="anton", size=280, fg=WHITE, bg=None, pad=(20, 10))
    p = (g - six) / 0.25
    paste_transformed(img, lab, W / 2 + ox, H / 2 - 30 + oy, 2.4 - 1.4 * ease_out(p), -3, clamp(p * 4))
    big_text(img, "ORDERED TO PAY", W / 2, 250, 70, g, six + 0.3, fg=INK, bg=WHITE, seed=111)
    source(img, "$4.087bn + ~$1.7bn interest, award of 12 Jul 2019 · UK High Court judgment, 2021")


gdp_t = wt("b08", "about")
add(six - 0.1, gdp_t - 0.1, g6)
sfx("sfx/boom.wav", six, 0)
sfx("music/hit.wav", six, -6)


def gdp(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, None)
    d = ImageDraw.Draw(img)
    cx, cy, r = 760, 520, 300
    d.ellipse((cx - r + 12, cy - r + 16, cx + r + 12, cy + r + 16), fill=(60, 45, 30, 70))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=TEAL + (255,))
    p = ease_out((g - wt("b08", "2")) / 0.6)
    ang = 360 * 0.02
    off_ = 150 * p
    mx, my = math.cos(math.radians(-90 + ang / 2)), math.sin(math.radians(-90 + ang / 2))
    d.pieslice((cx - r, cy - r, cx + r, cy + r), -90, -90 + ang, fill=DEEP + (255,))
    d.pieslice((cx - r + mx * off_, cy - r + my * off_, cx + r + mx * off_, cy + r + my * off_), -90, -90 + ang, fill=COPPER + (255,), outline=YELLOW, width=6)
    big_text(img, "PAKISTAN'S ECONOMY", cx, cy + 20, 54, g, sh["start"] + 0.1, fg=WHITE, bg=None, seed=121)
    big_text(img, "ABOUT 2% OF GDP", 1450, 380, 76, g, wt("b08", "2"), fg=WHITE, bg=COPPER, seed=122)
    draw_arrow(img, (1300, 440), (cx + 60, cy - r - 30), g, wt("b08", "2") + 0.3, color=COPPER, bend=0.35, seed=14)
    source(img, "The News, 10 Dec 2022")


fm = wt("b08", "for", 0) if False else wt("b08", "mine") - 0.25
add(gdp_t - 0.1, fm, gdp)
sfx("sfx/pop.wav", wt("b08", "2"), 2)


def empty(img, t, sh):
    shot_poster(img, t, sh)
    img.alpha_composite(Image.new("RGBA", (W, H), (30, 30, 30, 90)))


add(fm, START["b09"], empty, poster="p01_desert", bg=(90, 86, 80), move="push_in", labels=[], seed=24, scale=1.15)
sfx("sfx/wind.wav", fm, -4)

# b09 reset + crumple
T22 = wt("b09", "2022")
TL_EVENTS.append((T22, 2022, "THE RESET"))
pen = wt("b09", "penalty")
poster(START["b09"], pen - 0.1, "p09_handshake", TEAL, "push_in", seed=25, conf=Confetti(27, 14),
       extra=lambda img, g, t, sh: big_text(img, "2022: THE RESET", W / 2, 130, 92, g, T22, fg=WHITE, bg=COPPER, seed=131))


def crumple(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, None)
    p = ease_io((g - pen - 0.2) / 0.8)
    ball = poster_layer("p09_crumple")
    if p > 0:
        paste_transformed(img, ball, W / 2 - 300, H / 2, 0.6 + 0.4 * p, 0, p)
    lab = label_img("$5.9 BILLION", kind="anton", size=200, fg=RED, bg=WHITE, pad=(30, 14))
    paste_transformed(img, lab, W / 2 - 300, H / 2, 1.0 - 0.9 * p, 200 * p, 1 - p)
    big_text(img, "PENALTY DROPPED", W / 2 - 300, 200, 70, g, pen + 0.5, fg=WHITE, bg=INK, seed=141)
    slide_card(img, "BARRICK IS BACK", 1420, 560, g, wt("b09", "barrick"), side="R", seed=142, kind="anton", size=90, fg=WHITE, bg=COPPER)


add(pen - 0.1, START["b10"], crumple)
sfx("sfx/crumple.wav", pen + 0.2, 14)
sfx("sfx/whoosh.wav", wt("b09", "barrick"), -10)

# G7 ownership bar
TB, TF, TBal, TPay = wt("b10", "barrick"), wt("b10", "federal"), wt("b10", "balochistan"), wt("b10", "pays")


def g7(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, None)
    big_text(img, "WHO OWNS REKO DIQ", W / 2, 170, 84, g, sh["start"] + 0.1, fg=INK, bg=YELLOW, seed=151)
    x0, x1, y0, y1 = 220, W - 220, 420, 600
    d = ImageDraw.Draw(img)
    d.rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), fill=(60, 45, 30, 60))
    d.rectangle((x0, y0, x1, y1), fill=(232, 226, 214, 255), outline=INK, width=4)
    segs = [(0, 0.5, INK, TB, "BARRICK 50%"), (0.5, 0.75, TEAL, TF, "FEDERAL STATE COMPANIES 25%"), (0.75, 1.0, COPPER, TBal, "BALOCHISTAN 25%")]
    for a0, a1, col, tt, lab in segs:
        p = ease_out((g - tt) / 0.5)
        if p <= 0:
            continue
        xa = x0 + (x1 - x0) * a0
        xb = xa + (x1 - x0) * (a1 - a0) * p
        d.rectangle((xa, y0, xb, y1), fill=col + (255,))
        if p > 0.6:
            d.line([(xa, y0), (xa, y1)], fill=WHITE + (255,), width=6)
    slide_card(img, "BARRICK 50%", 640, 700, g, TB, side="B", seed=152, kind="anton", size=60, fg=WHITE, bg=INK)
    slide_card(img, "FEDERAL 25%", 1180, 720, g, TF, side="B", seed=153, kind="anton", size=52, fg=INK, bg=TEAL)
    slide_card(img, "BALOCHISTAN 25%", 1560, 330, g, TBal, side="T", seed=154, kind="anton", size=52, fg=WHITE, bg=COPPER)
    slide_card(img, "PAYS NOTHING TO BUILD IT", 1480, 830, g, TPay, side="R", seed=155, kind="anton", size=48, fg=INK, bg=YELLOW)
    draw_arrow(img, (1480, 790), (1560, 610), g, TPay + 0.2, color=YELLOW, bend=-0.3, seed=15)
    source(img, "Barrick, Reko Diq project page")


add(START["b10"], START["b11"], g7)
for tt in (TB, TF, TBal, TPay):
    sfx("sfx/pop.wav", tt, 2)

# ---- ACT 3 -------------------------------------------------------------------
CHAPTERS.append((START["b11"] + 0.2, "PART 3 · THE RACE"))
ev, pl, iea = wt("b11", "every"), wt("b11", "every", 1), wt("b11", "international")
poster(START["b11"], ev, "p11_copper", YELLOW, "push_in", seed=26, conf=Confetti(28, 18, bursts=[(wt("b11", "copper"), 960, 500, 50)]),
       extra=lambda img, g, t, sh: big_text(img, "COPPER", W / 2, 180, 200, g, wt("b11", "copper"), fg=WHITE, bg=None, slam=True, seed=161))
sfx("sfx/boom.wav", wt("b11", "copper"), -8)
poster(ev, pl, "p11_ev", TEAL, "pan", seed=27,
       extra=lambda img, g, t, sh: slide_card(img, "EVERY ELECTRIC CAR", 520, 170, g, ev, side="L", seed=162, kind="anton", size=70, fg=INK, bg=YELLOW))
poster(pl, iea - 0.1, "p11_pylons", COPPER, "pan", seed=28,
       extra=lambda img, g, t, sh: slide_card(img, "EVERY POWER LINE", 1380, 220, g, pl, side="R", seed=163, kind="anton", size=70, fg=WHITE, bg=INK))
sfx("sfx/hum.wav", ev, -4)
sfx("sfx/whoosh.wav", pl, -10)
T30 = wt("b11", "30") if any(w["word"].strip(" ,.%").startswith("30") for w in WORDS["b11"]) else wt("b11", "thirty")


def g8(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, None)
    d = ImageDraw.Draw(img)
    x0, x1, y0, y1 = 260, 1500, 860, 300
    ax = ease_out((g - sh["start"]) / 0.4)
    d.line([(x0, y0), (x0 + (x1 - x0) * ax, y0)], fill=INK + (255,), width=4)
    d.line([(x0, y0), (x0, y0 - (y0 - y1) * ax)], fill=INK + (255,), width=4)
    f = font("interb", 28)
    for yr in (2025, 2030, 2035):
        x = x0 + (x1 - x0) * (yr - 2025) / 10
        d.text((x, y0 + 20), str(yr), font=f, fill=INK + (255,), anchor="mt")
    dem = lambda u: 0.40 + 0.55 * u
    sup = lambda u: dem(u) * (1 - 0.3 * u ** 1.6)
    p = ease_io((g - sh["start"] - 0.5) / 2.2)
    N = 60
    pd, ps = [], []
    for i in range(int(N * p) + 1):
        u = i / N
        x = x0 + (x1 - x0) * u
        pd.append((x, y0 - (y0 - y1) * dem(u)))
        ps.append((x, y0 - (y0 - y1) * sup(u)))
    if len(pd) > 1:
        gap = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gap).polygon(pd + ps[::-1], fill=RED + (int(110 * clamp((g - T30) / 0.5)),))
        img.alpha_composite(gap)
        d.line(ps, fill=(130, 128, 122, 255), width=8, joint="curve")
        d.line(pd, fill=COPPER + (255,), width=10, joint="curve")
    if p > 0.95:
        d.text((x1 + 20, pd[-1][1]), "Demand", font=font("interb", 34), fill=COPPER + (255,), anchor="lm")
        d.text((x1 + 20, ps[-1][1]), "Mine supply", font=font("interb", 34), fill=(110, 108, 102, 255), anchor="lm")
    big_text(img, "30% SHORTFALL BY 2035", 700, 470, 76, g, T30, fg=WHITE, bg=RED, seed=171)
    big_text(img, "COPPER", 420, 230, 60, g, sh["start"] + 0.2, fg=INK, bg=YELLOW, seed=172)
    source(img, "IEA, Global Critical Minerals Outlook 2025 · curve shape illustrative")


add(iea - 0.1, START["b12"], g8)
sfx("sfx/pencil.wav", iea + 0.4, 12)
sfx("sfx/pop.wav", T30, 2)

TW, TI, TA = wt("b12", "washington"), wt("b12", "ifc"), wt("b12", "asian")
TL_EVENTS.append((TW, 2025, "FINANCING"))
plan = wt("b12", "plan")


def g9a(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DEEP)
    big_text(img, "WHO IS LENDING", W / 2, 200, 84, g, sh["start"] + 0.1, fg=INK, bg=YELLOW, seed=181)
    chips = [("US EXIM", "$1.25B", TW + 0.6, RED), ("IFC (WORLD BANK)", "$700M", TI, TEAL), ("ASIAN DEV. BANK", "$300M", TA, COPPER)]
    for i, (nm, amt, tt, col) in enumerate(chips):
        slide_card(img, f"{nm}   {amt}", W / 2, 760 - i * 150, g, tt, seed=191 + i, kind="anton", size=72, fg=WHITE, bg=col)
    source(img, "Dawn, 11 Dec 2025 · Profit, 28 Nov 2025")


add(START["b12"], plan - 0.1, g9a)
for tt in (TW + 0.6, TI, TA):
    sfx("sfx/click.wav", tt, 4)
T37, T28 = wt("b12", "37") if any(w["word"].startswith("37") for w in WORDS["b12"]) else wt("b12", "least"), wt("b12", "2028")


def life(img, g, t, sh):
    d = ImageDraw.Draw(img)
    x0, x1, y = 200, 1720, 820
    p = ease_out((g - T37) / 1.0)
    d.rectangle((x0 + 8, y - 34 + 10, x0 + (x1 - x0) * p + 8, y + 34 + 10), fill=(40, 30, 20, 90))
    d.rectangle((x0, y - 34, x0 + (x1 - x0) * p, y + 34), fill=COPPER + (255,))
    f = font("interb", 30)
    if p > 0.05:
        d.text((x0, y - 50), "2028", font=f, fill=INK + (255,), anchor="lb")
    if p > 0.95:
        d.text((x1, y - 50), "2065+", font=f, fill=INK + (255,), anchor="rb")
    big_text(img, "37+ YEARS OF MINING", W / 2, y, 60, g, T37 + 0.4, fg=WHITE, bg=None, seed=201)
    slide_card(img, "FIRST PRODUCTION: END OF 2028", 600, 160, g, T28, side="T", seed=202, kind="anton", size=56, fg=WHITE, bg=INK)


poster(plan - 0.1, START["b13"], "p12_pit", YELLOW, "pull_out", seed=29, extra=life, src="Barrick, Reko Diq project page")
sfx("sfx/slide_slow.wav", T37, 10)

# b13 risk
ppl, T26, rep = wt("b13", "people"), wt("b13", "2026"), wt("b13", "reports")
TL_EVENTS.append((T26, 2026, "SLOWDOWN"))
RISK = (64.5, 28.8, 13.0)


def g13a(img, t, sh):
    g = sh["start"] + t
    terrain_map(img, RISK, bal_fill=1.0, dark=0.45, red_iran=0.0)
    map_name(img, "Balochistan", RISK, 66.0, 27.6, g, sh["start"] + 0.2, size=64)
    map_name(img, "Iran", RISK, 59.6, 29.5, g, sh["start"] + 0.4, size=58)
    d = ImageDraw.Draw(img)
    for i, (lon, lat) in enumerate([(66.9, 30.2), (62.4, 25.2), (65.2, 26.9), (68.1, 28.3)]):
        x, y = lonlat_xy(RISK, lon, lat)
        tt = sh["start"] + 0.6 + i * 0.7
        if g > tt:
            ph = ((g - tt) % 1.4) / 1.4
            rr = 12 + 60 * ph
            d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=RED + (int(255 * (1 - ph)),), width=5)
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=RED + (255,))
    source(img, "Map data: Natural Earth · pulses mark the province, not specific incidents")


add(START["b13"], ppl - 0.1, g13a)
poster(ppl - 0.1, T26 - 0.2, "p13_people", DARK, "pan", seed=30,
       extra=lambda img, g, t, sh: slide_card(img, "WHO BENEFITS?", W / 2, 150, g, wt("b13", "how"), side="T", seed=211, kind="anton", size=80, fg=INK, bg=YELLOW))


def g13c(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, (60, 62, 64))
    news_card(img, "Barrick Mining Corporation", "Barrick Provides an Update on Reko Diq", "2 April 2026", 640, 470, g, sh["start"] + 0.05, seed=221, side="L",
              quote="“slow the development activity and continue the project review until mid-2027”", hl_t=wt("b13", "review"))
    news_card(img, "Dawn", "Barrick Mining expresses interest in mineral processing industries in Karachi, Gwadar", "13 November 2026", 1360, 560, g, rep - 0.15, seed=222, side="R",
              quote="“production … could be delayed by two years to 2030”", hl_t=rep + 0.6, width=700)
    slide_card(img, "FEB 2026: REVIEW", 330, 900 - 40, g, wt("b13", "slowed") - 0.2, side="B", seed=223, kind="anton", size=44, fg=WHITE, bg=INK, t1=rep - 0.2)
    slide_card(img, "APR 2026: SLOWDOWN", 760, 900 - 40, g, wt("b13", "slowed"), side="B", seed=224, kind="anton", size=44, fg=WHITE, bg=RED, t1=rep - 0.2)


add(T26 - 0.2, rep + 2.2, g13c)
sfx("sfx/paper_slide.wav", T26, 16)
sfx("sfx/paper_slide.wav", rep, 16)


def g9b(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DARK)
    big_text(img, "FIRST PRODUCTION", W / 2, 260, 80, g, sh["start"] + 0.05, fg=INK, bg=YELLOW, seed=231)
    p = ease_io((g - sh["start"] - 0.5) / 1.4)
    x = 760 + 420 * p
    lab = label_img("2028", kind="anton", size=220, fg=WHITE, bg=None, pad=(10, 6))
    paste_transformed(img, lab, 760, 560, 1.0, 0, 1 - 0.55 * p)
    if p > 0.2:
        d = ImageDraw.Draw(img)
        d.line([(640, 560), (640 + 240 * clamp((p - 0.2) / 0.3), 560)], fill=RED + (255,), width=14)
    lab2 = label_img("2030?", kind="anton", size=220, fg=RED, bg=None, pad=(10, 6))
    paste_transformed(img, lab2, x + 160, 560, 1.0, 0, clamp((p - 0.4) / 0.4))
    draw_arrow(img, (840, 720), (1260, 720), g, sh["start"] + 0.6, color=RED, bend=-0.15, seed=21)
    source(img, "Barrick has not announced a new date · “reports” per Dawn, 13 Nov 2026")


add(rep + 2.2, START["b14"], g9b)
sfx("sfx/slide_slow.wav", rep + 2.6, 10)

# b14 close + end card
poster(START["b14"], END_VO + 0.4, "p14_dusk", COPPER, "pull_out", seed=31,
       extra=lambda img, g, t, sh: draw_circle_mark(img, 960, 600, 300, 110, g, wt("b14", "who"), color=YELLOW, seed=7))
sfx("sfx/wind.wav", START["b14"] + 2, -8)


def endcard(img, t, sh):
    g = sh["start"] + t
    fill_bg(img, DARK)
    big_text(img, "REKO DIQ", W / 2, 400, 220, g, sh["start"] + 0.1, fg=WHITE, slam=False, seed=241)
    big_text(img, "Why Pakistan's biggest treasure is still underground", W / 2, 600, 46, g, sh["start"] + 0.6, kind="serif", fg=WHITE, bg=None, seed=242)


add(END_VO + 0.4, TOTAL, endcard)

SHOTS.sort(key=lambda s_: s_["start"])
TL_EVENTS.sort()
OVERLAYS = [timeline_bar, chapter_stamp, captions]


# ------------------------------------------------------------------ render / mix
def frame_at(t):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    for sh in SHOTS:
        if sh["start"] <= t < sh["start"] + sh["dur"]:
            sh["fn"](img, t - sh["start"], sh)
            break
    for ov in OVERLAYS:
        ov(img, t)
    return apply_grain(img.convert("RGB"), t)


def render_chunk(args):
    i0, i1, out = args
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def mix(video, out):
    cues = [("music/m1_drone.wav", START["b02"] - 0.5, why, 0.45),
            ("music/m2_investigate.wav", START["b03"] + 0.6, six - 0.05, 0.30),
            ("music/m3_bright.wav", START["b09"] - 0.2, START["b13"], 0.30),
            ("music/m4_pulse.wav", START["b13"], START["b14"], 0.40),
            ("music/m5_chord.wav", START["b14"] - 0.3, TOTAL, 0.38)]
    ins = ["-i", video]
    fc = []
    vo_labels = []
    k = 1
    for b in NAR["beats"]:
        if b.get("silent"):
            continue
        ins += ["-i", str(ROOT / f"vo/{b['id']}.wav")]
        ms = int(START[b["id"]] * 1000)
        fc.append(f"[{k}:a]adelay={ms}|{ms}[v{k}]")
        vo_labels.append(f"[v{k}]")
        k += 1
    fc.append(f"{''.join(vo_labels)}amix=inputs={len(vo_labels)}:normalize=0,volume=1.7,apad,asplit=2[vo][sc]")
    mus = []
    for f, a, b_, vol in cues:
        ins += ["-i", str(ROOT / f)]
        dur = b_ - a
        ms = int(a * 1000)
        fc.append(f"[{k}:a]atrim=0:{dur:.2f},afade=t=in:d=1.0,afade=t=out:st={max(0, dur - 0.8):.2f}:d=0.8,volume={vol},adelay={ms}|{ms}[m{k}]")
        mus.append(f"[m{k}]")
        k += 1
    fc.append(f"{''.join(mus)}amix=inputs={len(mus)}:normalize=0[mus]")
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


def write_srt(path):
    def ts(x):
        h, m = int(x // 3600), int(x % 3600 // 60)
        return f"{h:02d}:{m:02d}:{x % 60:06.3f}".replace(".", ",")
    with open(path, "w") as f:
        for i, (s_, e_, tx) in enumerate(CAPS, 1):
            f.write(f"{i}\n{ts(s_)} --> {ts(e_)}\n{tx}\n\n")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    print(f"TOTAL {TOTAL:.2f}s, {len(SHOTS)} shots, {len(SFX)} sfx")
    if mode == "stills":
        times = [float(x) for x in sys.argv[2:]] or [s_["start"] + s_["dur"] * 0.7 for s_ in SHOTS]
        tiles = [frame_at(tt).resize((480, 270)) for tt in times]
        cols = 6
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 480, rows * 270), "white")
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
        sheet.save(ROOT / "cut/stills.jpg", quality=85)
        print(ROOT / "cut/stills.jpg")
    elif mode == "render":
        from multiprocessing import Pool
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        nf = int(round(TOTAL * FPS))
        step = (nf + n - 1) // n
        jobs = [(i, min(nf, i + step), str(ROOT / f"cut/chunk_{j:02d}.mp4")) for j, i in enumerate(range(0, nf, step))]
        with Pool(len(jobs)) as pool:
            outs = pool.map(render_chunk, jobs)
        lst = ROOT / "cut/chunks.txt"
        lst.write_text("".join(f"file '{o}'\n" for o in outs))
        silent = str(ROOT / "cut/film_video.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", silent], check=True)
        final = str(ROOT.parent / "reko_diq_explainer.mp4")
        mix(silent, final)
        write_srt(ROOT.parent / "reko_diq_explainer.srt")
        print(final)
