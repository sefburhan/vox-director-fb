"""Shared kit for the 23-minute film: timing, shot templates, overlays, part render + audio mix.

A chapter file (chapters/cNN.py) defines `build(P)` that adds shots, sfx, music and timeline events
to a Part. `python3 part.py cNN stills|render` renders only that chapter.
"""
import json
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import film as F                                    # noqa: E402  (3-min toolkit: maps, cards, confetti…)
from film import (Confetti, sunburst, big_text, counter, slide_card, stamp, news_card, terrain_map, map_name,  # noqa
                  fill_bg, red_string, inset, DEEP, DARK)
from engine import *                                # noqa

F.tl_active = lambda t: False                       # the 3-min bar is not used; this film has its own
A = ROOT.parent / "assets"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
SCRIPT = {c["id"]: c for c in json.load(open(HERE / "script.json"))}
NEWS = json.load(open(A / "news/meta.json"))

NAVY = (23, 47, 75)
SAND = (214, 190, 150)
OCHRE = (196, 140, 62)
STY = {"ink": dict(fg=WHITE, bg=INK), "yellow": dict(fg=INK, bg=YELLOW), "copper": dict(fg=WHITE, bg=COPPER),
       "red": dict(fg=WHITE, bg=RED), "white": dict(fg=INK, bg=WHITE), "teal": dict(fg=INK, bg=TEAL), "navy": dict(fg=WHITE, bg=NAVY)}
SLOTS = [(W / 2, 150), (W / 2, 840), (1460, 420), (460, 420), (1460, 700), (460, 700)]


# ------------------------------------------------------------------ part timing
class Part:
    CARD = 2.8                                      # chapter card length

    def __init__(self, cid, gap=0.45, card=True):
        self.cid = cid
        self.ch = SCRIPT[cid]
        self.rows = {r["id"]: r for r in self.ch["rows"]}
        self.order = [r["id"] for r in self.ch["rows"]]
        self.start, self.dur, self.words = {}, {}, {}
        self.gaps = {}
        self.card = card
        self.t0 = self.CARD if card else 0.6
        self.default_gap = gap
        self.shots, self.sfx, self.music, self.events = [], [], [], []
        self.timeline = None                         # (year_from, year_to) range shown by the bar, or None
        self.layout()

    def layout(self):
        t = self.t0
        for rid in self.order:
            js = json.load(open(HERE / f"vo/{rid}.json"))
            self.start[rid], self.dur[rid] = t, js["dur"]
            self.words[rid] = js["words"]
            t += js["dur"] + self.gaps.get(rid, self.default_gap)
        self.end_vo = t
        self.total = t + 0.4

    def gap(self, rid, g):
        self.gaps[rid] = g
        self.layout()

    def b(self, n):                                  # beat id by row number (1-based)
        return self.order[n - 1]

    def S(self, n):
        return self.start[self.b(n)]

    def E(self, n):
        return self.start[self.b(n)] + self.dur[self.b(n)]

    def W(self, n, prefix, nth=0, end=False):
        """Global (part) time of the nth word in row n starting with prefix (fuzzy fallback)."""
        import difflib
        rid = self.b(n)
        ws = self.words[rid]
        norm = lambda x: x.strip(" ,.?!:;\"'").lower()
        hits = [w for w in ws if norm(w["word"]).startswith(prefix.lower())]
        if len(hits) <= nth:
            ranked = sorted(ws, key=lambda w: -difflib.SequenceMatcher(None, norm(w["word"]), prefix.lower()).ratio())
            hits = sorted(ranked[:nth + 1], key=lambda w: w["start"])
        w = hits[min(nth, len(hits) - 1)]
        return self.start[rid] + (w["end"] if end else w["start"])

    def add(self, t0, t1, fn, **kw):
        self.shots.append(dict(start=t0, dur=t1 - t0, fn=fn, **kw))

    def fx(self, f, at, db=0):
        self.sfx.append((f, at, db))

    def cue(self, f, a, b, vol=0.3, offset=0.0):
        self.music.append((f, a, b, vol, offset))

    def event(self, at, year, text):
        self.events.append((at, year, text))


# ------------------------------------------------------------------ templates
TL_ON = False


def cards(img, g, sh):
    for i, c in enumerate(sh.get("cards", [])):
        at = c["at"]
        x, y = c.get("xy", SLOTS[i % len(SLOTS)])
        if TL_ON and y < 260:
            y += 150
        sty = STY[c.get("style", "ink")]
        size = c.get("size", 54)
        if c.get("stamp"):
            stamp(img, c["text"], x, y, g, at, col=c.get("col", RED), size=size, rot=c.get("rot", -8))
        elif c.get("slam"):
            big_text(img, c["text"], x, y, size, g, at, kind=c.get("kind", "anton"), slam=True, seed=c.get("seed", 7 + i), **sty)
        elif c.get("pop"):
            big_text(img, c["text"], x, y, size, g, at, kind=c.get("kind", "anton"), seed=c.get("seed", 7 + i), **sty)
        else:
            slide_card(img, c["text"], x, y, g, at, side=c.get("side"), seed=c.get("seed", 100 + i), t1=c.get("until"),
                       kind=c.get("kind", "anton"), size=size, **sty)


def C(text, at, style="ink", **kw):
    return dict(text=text, at=at, style=style, **kw)


@lru_cache(None)
def photo_card(path, maxw=1300, maxh=760, border=18, seed=1, duotone=False):
    im = Image.open(A / path).convert("RGB")
    im.thumbnail((maxw, maxh), Image.LANCZOS)
    if duotone:
        g_ = im.convert("L")
        im = Image.merge("RGB", [g_.point(lambda v, c=c: int(c[0] + (c[1] - c[0]) * v / 255)) for c in ((23, 244), (40, 239), (64, 230))])
    w, h = im.size
    card = Image.new("RGBA", (w + border * 2, h + border * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    r = random.Random(seed)
    pts = [(x, r.uniform(0, 5)) for x in range(0, card.width + 1, 12)]
    pts += [(card.width - r.uniform(0, 5), y) for y in range(0, card.height + 1, 12)]
    pts += [(x, card.height - r.uniform(0, 5)) for x in range(card.width, -1, -12)]
    pts += [(r.uniform(0, 5), y) for y in range(card.height, -1, -12)]
    d.polygon(pts, fill=(250, 248, 242, 255))
    card.paste(im, (border, border))
    for (tx, ty, ang) in ((0.1, 0.03, -28), (0.9, 0.03, 30)):
        tape = Image.new("RGBA", (170, 48), (232, 220, 186, 205)).rotate(ang, expand=True, resample=Image.BICUBIC)
        card.alpha_composite(tape, (int(max(0, min(card.width - tape.width, card.width * tx - tape.width / 2))), 0))
    return with_shadow(card, (12, 16), 14, 0.45)


def T_photo(path, bg=None, cx=W / 2, cy=H / 2 - 20, z=(1.0, 1.06), maxw=1300, maxh=760, duotone=False, seed=1, extra=None, conf=None):
    def fn(img, t, sh):
        g = sh["start"] + t
        fill_bg(img, bg)
        if conf:
            conf.draw(img, g)
        card = photo_card(path, maxw=maxw, maxh=maxh, seed=seed, duotone=duotone)
        zz = z[0] + (z[1] - z[0]) * ease_io(t / sh["dur"])
        dx, dy, dr = jitter(seed + 50, g, 0.8)
        paste_transformed(img, card, cx + dx, cy + dy, zz, random.Random(seed).uniform(-2.5, 2.5) + dr)
        if extra:
            extra(img, g, t, sh)
        cards(img, g, sh)
    return fn


def T_poster(name, bg, move="push_in", scale=1.0, extra=None, conf=None, seed=7, dy=0):
    def fn(img, t, sh):
        g = sh["start"] + t
        sh2 = dict(sh, poster=name, bg=bg, move=move, labels=[], seed=seed, scale=scale, dy=dy)
        shot_poster(img, t, sh2)
        if conf:
            conf.draw(img, g)
        if extra:
            extra(img, g, t, sh)
        cards(img, g, sh)
    return fn


@lru_cache(None)
def doc_img(path, crop=None, width=900):
    im = Image.open(A / path).convert("RGB")
    if crop:
        im = im.crop(crop)
    return im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)


def T_doc(path, bg=DARK, crop=None, width=900, cx=W / 2, cy=H / 2 + 20, rot=-3, hl=None, hl_at=None, circle=None, extra=None, seed=3):
    """Real document page; hl=(x0,y0,x1,y1) in page px swept yellow at hl_at; circle=(x,y,rx,ry,at) in page px."""
    def fn(img, t, sh):
        g = sh["start"] + t
        fill_bg(img, bg)
        src_w = (crop[2] - crop[0]) if crop else Image.open(A / path).width
        sx = width / src_w
        ox, oy = (crop[0], crop[1]) if crop else (0, 0)
        im = doc_img(path, crop, width).copy().convert("RGBA")
        if hl and hl_at is not None and g > hl_at:
            p = ease_out((g - hl_at) / 0.7)
            x0, y0, x1, y1 = [(v - o) * sx for v, o in zip(hl, (ox, oy, ox, oy))]
            dim = Image.new("RGBA", im.size, (20, 20, 20, int(70 * p)))
            ImageDraw.Draw(dim).rectangle((x0 - 6, y0 - 4, x1 + 6, y1 + 4), fill=(0, 0, 0, 0))
            im.alpha_composite(dim)
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle((x0 - 4, y0 - 2, x0 + (x1 - x0 + 8) * p, y1 + 2), fill=YELLOW + (120,))
            im.alpha_composite(lay)
        if circle:
            x, y, rx, ry, at = circle
            draw_circle_mark(im, (x - ox) * sx, (y - oy) * sx, rx * sx, ry * sx, g, at, color=RED, width=7, seed=seed)
        card = with_shadow(im, (12, 16), 14, 0.45)
        dx, dy, dr = jitter(seed, g, 0.5)
        paste_transformed(img, card, cx + dx, cy + dy, 1.0 + 0.05 * ease_io(t / max(1, sh["dur"])), rot + dr)
        if extra:
            extra(img, g, t, sh)
        cards(img, g, sh)
    return fn


def T_headline(nid, bg=(232, 228, 220), cx=W / 2, cy=H / 2 - 10, width=1250, photo=True, seed=5, extra=None):
    """Real headline crop if we have one, else a clean card from the page's real headline/date, with its lead photo."""
    crop = A / f"news/{nid}__crop.png"
    m = NEWS.get(nid, {})
    ph = next(iter(sorted((A / "news").glob(f"{nid}__photo.*"))), None)

    def fn(img, t, sh):
        g = sh["start"] + t
        fill_bg(img, bg)
        if photo and ph is not None:
            card = photo_card(str(ph.relative_to(A)), maxw=1100, maxh=560, seed=seed + 1)
            paste_transformed(img, card, cx + 330, cy + 120, 0.9 + 0.05 * ease_io(t / sh["dur"]), 2.5 + jitter(seed, g)[2])
        if crop.exists():
            im = Image.open(crop).convert("RGBA")
            im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
            c = with_shadow(im, (10, 14), 12, 0.45)
            p = back_out((g - sh["start"]) / 0.45, 1.4)
            paste_transformed(img, c, cx - 160 - 1400 * (1 - p), cy - 200, 0.9, -2 + jitter(seed + 1, g)[2])
        else:
            outlet = (m.get("site") or "Dawn").replace("DAWN.COM", "Dawn")
            date = (m.get("date") or "")[:10]
            try:
                import datetime
                date = datetime.date.fromisoformat(date).strftime("%-d %B %Y")
            except Exception:
                pass
            news_card(img, outlet, m.get("h1") or m.get("title", ""), date, cx - 300, cy - 120, g, sh["start"], seed=seed, side="L", width=900)
        if extra:
            extra(img, g, t, sh)
        cards(img, g, sh)
    return fn


def T_fill(bg, extra=None, conf=None, burst=None):
    def fn(img, t, sh):
        sh["no_reframe"] = True
        g = sh["start"] + t
        fill_bg(img, bg)
        if burst:
            sunburst(img, *burst, g, (255, 255, 255), alpha=28)
        if conf:
            conf.draw(img, g)
        if extra:
            extra(img, g, t, sh)
        cards(img, g, sh)
    return fn


def T_map(keys, bal=0.0, dark=0.0, extra=None, tint=0.55, insetmap=False, red_iran=0.0):
    """keys: [(t_rel, (lon, lat, span)), ...]; bal: float or callable(g)."""
    def fn(img, t, sh):
        g = sh["start"] + t
        view = F.view_at(keys, t)
        b = bal(g) if callable(bal) else bal
        terrain_map(img, view, bal_fill=b, dark=dark, tint_alpha=tint, red_iran=red_iran)
        if extra:
            extra(img, g, t, sh, view)
        if insetmap and view[2] < 9:
            inset(img, view)
        cards(img, g, sh)
    return fn


def T_black(text=None, size=90):
    def fn(img, t, sh):
        img.paste((8, 8, 8), (0, 0, W, H))
        if text:
            big_text(img, text, W / 2, H / 2, size, sh["start"] + t, sh["start"] + 0.2, fg=WHITE, seed=3)
        cards(img, sh["start"] + t, sh)
    return fn


# ------------------------------------------------------------------ graphic helpers
def ruler(img, view, a, b, g, at, label, col=YELLOW):
    """Distance ruler between two lon/lat points, drawn on."""
    if g < at:
        return
    p = ease_out((g - at) / 0.6)
    x0, y0 = lonlat_xy(view, *a)
    x1, y1 = lonlat_xy(view, *b)
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    d = ImageDraw.Draw(img)
    d.line([(x0 + 3, y0 + 4), (xe + 3, ye + 4)], fill=(0, 0, 0, 90), width=7)
    d.line([(x0, y0), (xe, ye)], fill=col + (255,), width=7)
    ang = math.atan2(y1 - y0, x1 - x0) + math.pi / 2
    for (x, y) in ((x0, y0), (xe, ye)):
        d.line([(x - 16 * math.cos(ang), y - 16 * math.sin(ang)), (x + 16 * math.cos(ang), y + 16 * math.sin(ang))], fill=col + (255,), width=7)
    if p > 0.7:
        big_text(img, label, (x0 + x1) / 2, (y0 + y1) / 2 - 50, 46, g, at + 0.45, fg=INK, bg=col, seed=int(x0) % 97)


def route(img, view, pts, g, at, dur=1.5, col=COPPER, width=9, dashed=False):
    """Polyline route along lon/lat points, drawn on over dur."""
    if g < at:
        return
    p = ease_io((g - at) / dur)
    xy = [lonlat_xy(view, *q) for q in pts]
    seg = [math.hypot(xy[i + 1][0] - xy[i][0], xy[i + 1][1] - xy[i][1]) for i in range(len(xy) - 1)]
    tot = sum(seg) * p
    out = [xy[0]]
    for i, s_ in enumerate(seg):
        if tot <= 0:
            break
        f = min(1, tot / s_) if s_ else 1
        out.append((xy[i][0] + (xy[i + 1][0] - xy[i][0]) * f, xy[i][1] + (xy[i + 1][1] - xy[i][1]) * f))
        tot -= s_
    d = ImageDraw.Draw(img)
    if dashed:
        for k in range(0, len(out) - 1):
            a, b = out[k], out[k + 1]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L / 22))
            for j in range(0, n, 2):
                d.line([(a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n),
                        (a[0] + (b[0] - a[0]) * min(1, (j + 1) / n), a[1] + (b[1] - a[1]) * min(1, (j + 1) / n))], fill=col + (255,), width=width)
    else:
        d.line([(x + 3, y + 4) for x, y in out], fill=(0, 0, 0, 80), width=width, joint="curve")
        d.line(out, fill=col + (255,), width=width, joint="curve")
    if p > 0.02:
        x, y = out[-1]
        d.ellipse((x - width, y - width, x + width, y + width), fill=WHITE + (255,), outline=col + (255,), width=4)


def dot(img, view, lonlat, g, at, label=None, col=RED, size=40, side=1):
    if g < at:
        return
    x, y = lonlat_xy(view, *lonlat)
    s, a = pop_in(g, at, 0.3)
    r = 11 * s
    d = ImageDraw.Draw(img)
    d.ellipse((x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=WHITE + (int(255 * a),))
    d.ellipse((x - r, y - r, x + r, y + r), fill=col + (int(255 * a),))
    if label:
        lab = label_img(label, kind="anton", size=size, fg=WHITE, bg=INK, pad=(14, 6))
        paste_transformed(img, lab, x + side * (lab.width / 2 + 24), y - 30, s, -2, a)


def split_bar(img, g, segs, x0=220, x1=W - 220, y0=430, y1=580, frame=True):
    """segs: [(frac_from, frac_to, colour, at, label), ...] filled on their word."""
    d = ImageDraw.Draw(img)
    if frame:
        d.rectangle((x0 + 10, y0 + 14, x1 + 10, y1 + 14), fill=(60, 45, 30, 60))
        d.rectangle((x0, y0, x1, y1), fill=(232, 226, 214, 255), outline=INK, width=4)
    for a0, a1, col, at, lab in segs:
        p = ease_out((g - at) / 0.5)
        if p <= 0:
            continue
        xa = x0 + (x1 - x0) * a0
        d.rectangle((xa, y0, xa + (x1 - x0) * (a1 - a0) * p, y1), fill=col + (255,))
        if p > 0.6:
            d.line([(xa, y0), (xa, y1)], fill=WHITE + (255,), width=6)
            if lab:
                f = font("anton", 44 if (a1 - a0) > 0.12 else 30)
                tw = f.getlength(lab)
                cxm = xa + (x1 - x0) * (a1 - a0) / 2
                d.text((cxm - tw / 2, (y0 + y1) / 2 - 26), lab, font=f, fill=(WHITE if col != YELLOW else INK) + (255,))


def typed(img, text, x, y, g, at, size=46, kind="serif", col=INK, cps=28, anchor="lm"):
    if g < at:
        return
    n = int((g - at) * cps)
    f = font(kind, size)
    ImageDraw.Draw(img).text((x, y), text[:n], font=f, fill=col + (255,), anchor=anchor)


def quote_card(img, quote, who, g, at, cx=W / 2, cy=H / 2, width=1300, seed=9):
    if g < at:
        return
    fq, fw = font("serif", 56), font("interb", 30)
    words, lines, cur = quote.split(), [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if fq.getlength(tst) > width - 120 and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = tst
    lines.append(cur)
    hgt = 90 + len(lines) * 72 + 70
    card = Image.new("RGBA", (width, hgt), (248, 246, 241, 255))
    d = ImageDraw.Draw(card)
    d.text((40, 10), "“", font=font("serif", 140), fill=COPPER + (255,))
    for i, ln in enumerate(lines):
        d.text((70, 70 + i * 72), ln, font=fq, fill=INK + (255,))
    d.text((70, 80 + len(lines) * 72), who.upper(), font=fw, fill=RED + (255,))
    p = back_out((g - at) / 0.45, 1.3)
    paste_transformed(img, with_shadow(card, (10, 14), 12, 0.45), cx, cy + 600 * (1 - p), 1.0, random.Random(seed).uniform(-2, 2) + jitter(seed, g)[2])


def checklist(img, items, x, y, g, ats, size=58, gapy=92):
    d = ImageDraw.Draw(img)
    f = font("anton", size)
    for i, (txt, at) in enumerate(zip(items, ats)):
        if g < at:
            continue
        p = ease_out((g - at) / 0.3)
        yy = y + i * gapy
        d.rectangle((x, yy - 28, x + 56, yy + 28), outline=INK + (255,), width=5, fill=WHITE + (255,))
        if p > 0.4:
            d.line([(x + 10, yy), (x + 24, yy + 16), (x + 50, yy - 22)], fill=COPPER + (255,), width=9)
        d.text((x + 80, yy), txt, font=f, fill=INK + (int(255 * p),), anchor="lm")


# ------------------------------------------------------------------ overlays
def timeline_bar(P, img, t, y0=1990, y1=2030):
    if not P.timeline:
        return
    a = clamp(t / 0.4) * clamp((P.end_vo - t) / 0.4)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1, y = 380, W - 300, 64
    d.line([(x0, y + 2), (x1, y + 2)], fill=(0, 0, 0, 90), width=4)
    d.line([(x0, y), (x1, y)], fill=WHITE + (255,), width=4)
    for yr in range(y0, y1 + 1):
        x = x0 + (x1 - x0) * (yr - y0) / (y1 - y0)
        hgt = 14 if yr % 10 == 0 else 7
        d.line([(x, y - hgt), (x, y)], fill=WHITE + (255,), width=2)
    f = font("interb", 26)
    d.text((x0 - 18, y), str(y0), font=f, fill=WHITE + (255,), anchor="rm")
    d.text((x1 + 18, y), str(y1), font=f, fill=WHITE + (255,), anchor="lm")
    for yr in P.timeline.get("past", []):
        ex = x0 + (x1 - x0) * (yr - y0) / (y1 - y0)
        d.ellipse((ex - 6, y - 6, ex + 6, y + 6), fill=COPPER + (255,))
    past = [e for e in sorted(P.events) if e[0] <= t]
    cur_year = P.timeline.get("start", 1993)
    label = None
    if past:
        prev = past[-2][1] if len(past) > 1 else cur_year
        at, yr, label = past[-1]
        cur_year = prev + (yr - prev) * ease_io((t - at) / 0.6)
        for e in past:
            ex = x0 + (x1 - x0) * (e[1] - y0) / (y1 - y0)
            d.ellipse((ex - 6, y - 6, ex + 6, y + 6), fill=COPPER + (255,))
    x = x0 + (x1 - x0) * (cur_year - y0) / (y1 - y0)
    d.polygon([(x, y + 8), (x - 13, y + 30), (x + 13, y + 30)], fill=WHITE + (255,))
    if label and t - past[-1][0] > 0.25:
        fy, ft = font("interb", 22), font("anton", 32)
        yy = y + 40
        yrtxt = str(past[-1][1])
        d.rectangle((x - 4, yy, x + fy.getlength(yrtxt) + 12, yy + 30), fill=INK + (235,))
        d.text((x + 4, yy + 3), yrtxt, font=fy, fill=WHITE + (255,))
        yy += 32
        tw = ft.getlength(label)
        xx = min(x, x1 - tw)
        d.rectangle((xx - 4, yy, xx + tw + 14, yy + 44), fill=INK + (235,))
        d.text((xx + 5, yy + 3), label, font=ft, fill=WHITE + (255,))
    if a < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)


def chapter_card(P):
    ch = P.ch
    num = {"c00": "", "c09": ""}.get(P.cid, f"CHAPTER {int(P.cid[1:])}")
    cf = Confetti(int(P.cid[1:]) + 500, 24, bursts=[(0.25, W / 2, 470, 40)])

    def fn(img, t, sh):
        fill_bg(img, P.bg)
        sunburst(img, W / 2, 470, t, (255, 255, 255), alpha=22)
        cf.draw(img, t)
        if num:
            big_text(img, num, W / 2, 330, 54, t, 0.1, fg=INK, bg=YELLOW, seed=1)
        big_text(img, ch["title"].upper(), W / 2, 500, 170, t, 0.25, fg=WHITE, slam=True, seed=2)
    return fn


# ------------------------------------------------------------------ render one part
def caption_list(P):
    caps = []
    for rid in P.order:
        caps += caption_chunks(P.rows[rid]["vo"], P.words[rid], P.start[rid])
    return caps


@lru_cache(None)
def logo():
    im = Image.open(ROOT / "icons/_logo_badge.png").convert("RGBA")
    h = 58
    im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    a = im.getchannel("A").point(lambda v: int(v * 0.92))
    im.putalpha(a)
    return with_shadow(im, (3, 4), 6, 0.30)


FRAMES = [(1.0, 0, 0), (1.07, -24, -10), (1.04, 18, 8), (1.08, 22, -12), (1.05, -16, 10)]


def reframe(img, t, sh):
    """Long shots: re-frame every ~5 s on caption boundaries (punch-in / drift), a cut for the eye."""
    cuts = sh.get("cuts")
    if not cuts:
        return img
    k = sum(1 for c in cuts if t >= c)
    if k == 0:
        return img
    z, ox, oy = FRAMES[k % len(FRAMES)]
    seg0 = cuts[k - 1]
    seg1 = cuts[k] if k < len(cuts) else sh["dur"]
    z += 0.025 * ease_io((t - seg0) / max(0.5, seg1 - seg0))
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2 - ox / z
    y0 = (H - ch) / 2 - oy / z
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)


def frame_at(P, caps, t):
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    for sh in P.shots:
        if sh["start"] <= t < sh["start"] + sh["dur"]:
            sh["fn"](img, t - sh["start"], sh)
            img = reframe(img, t - sh["start"], sh)
            break
    timeline_bar(P, img, t)
    img.alpha_composite(logo(), (48 - 14, 40 - 14))
    draw_caption(img, t, caps, y=972)
    return apply_grain(img.convert("RGB"), t)


def _chunk(args):
    cid, i0, i1, out = args
    P, caps = load(cid)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "48", out], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame_at(P, caps, i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


_CACHE = {}


def load(cid):
    if cid not in _CACHE:
        import importlib
        mod = importlib.import_module(f"chapters.{cid}")
        P = mod.build()
        global TL_ON
        TL_ON = bool(P.timeline)
        if P.card:
            P.shots.append(dict(start=0, dur=P.CARD, fn=chapter_card(P)))
            P.fx("sfx/paper_slide.wav", 0.15, 16)
            P.fx("music/hit.wav", 0.25, -8)
        P.shots.sort(key=lambda s_: s_["start"])
        first, last = P.shots[0], max(P.shots, key=lambda s_: s_["start"] + s_["dur"])
        if first["start"] > 0:                       # no uncovered frames at the part edges
            first["dur"] += first["start"]
            first["start"] = 0
        if last["start"] + last["dur"] < P.total:
            last["dur"] = P.total - last["start"] + 0.1
        caps0 = caption_list(P)
        for sh in P.shots:                           # cut points for long shots, on caption boundaries ~5 s apart
            if sh["dur"] > 8.5 and not sh.get("no_reframe") and "T_fill" not in getattr(sh["fn"], "__qualname__", ""):
                marks = [c[0] - sh["start"] for c in caps0 if sh["start"] + 2.5 < c[0] < sh["start"] + sh["dur"] - 2.5]
                cuts, last_c = [], 0.0
                for m in marks:
                    if m - last_c >= 4.5:
                        cuts.append(m)
                        last_c = m
                sh["cuts"] = cuts
        _CACHE[cid] = (P, caption_list(P))
    return _CACHE[cid]


def mix(P, out_wav):
    ins, fc, vl, k = [], [], [], 0
    for rid in P.order:
        ins += ["-i", str(HERE / f"vo/{rid}.wav")]
        ms = int(P.start[rid] * 1000)
        fc.append(f"[{k}:a]aresample=48000,adelay={ms}|{ms}[v{k}]")
        vl.append(f"[v{k}]")
        k += 1
    fc.append(f"{''.join(vl)}amix=inputs={len(vl)}:normalize=0,volume=1.7,apad,asplit=2[vo][sc]")
    ml = []
    for f, a, b_, vol, off in P.music:
        ins += ["-stream_loop", "-1", "-i", str(ROOT / f)]
        dur, ms = b_ - a, int(a * 1000)
        fc.append(f"[{k}:a]aresample=48000,atrim={off}:{off + dur:.2f},asetpts=PTS-STARTPTS,afade=t=in:d=1.0,afade=t=out:st={max(0, dur - 1.0):.2f}:d=1.0,volume={vol},adelay={ms}|{ms}[m{k}]")
        ml.append(f"[m{k}]")
        k += 1
    if ml:
        fc.append(f"{''.join(ml)}amix=inputs={len(ml)}:normalize=0[mus]")
        fc.append("[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[duck]")
    sl = []
    for f, at, db in P.sfx:
        ins += ["-i", str(ROOT / f)]
        ms = int(max(0, at) * 1000)
        fc.append(f"[{k}:a]aresample=48000,volume={db}dB,adelay={ms}|{ms}[s{k}]")
        sl.append(f"[s{k}]")
        k += 1
    base = ["[vo]"] + (["[duck]"] if ml else [])
    fc.append(f"{''.join(base)}{''.join(sl)}amix=inputs={len(base) + len(sl)}:normalize=0,atrim=0:{P.total:.3f}[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "[a]", "-ac", "2", "-ar", "48000",
                    "-c:a", "pcm_s16le", str(out_wav)], check=True)


def render_part(cid, n=10):
    from multiprocessing import Pool
    P, caps = load(cid)
    nf = int(round(P.total * FPS))
    step = (nf + n - 1) // n
    jobs = [(cid, i, min(nf, i + step), str(OUT / f"{cid}_chunk{j:02d}.mp4")) for j, i in enumerate(range(0, nf, step))]
    with Pool(len(jobs)) as pool:
        outs = pool.map(_chunk, jobs)
    lst = OUT / f"{cid}_chunks.txt"
    lst.write_text("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(OUT / f"{cid}.mp4")], check=True)
    mix(P, OUT / f"{cid}.wav")
    json.dump(dict(total=nf / FPS, caps=caps), open(OUT / f"{cid}.json", "w"))
    for o in outs:
        Path(o).unlink()
    return OUT / f"{cid}.mp4"


def stills(cid, times=None):
    P, caps = load(cid)
    times = times or [s_["start"] + s_["dur"] * 0.75 for s_ in P.shots]
    tiles = [frame_at(P, caps, tt).resize((480, 270)) for tt in times]
    cols = 6
    sheet = Image.new("RGB", (cols * 480, 270 * ((len(tiles) + cols - 1) // cols)), "white")
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 480, (i // cols) * 270))
    out = OUT / f"{cid}_stills.jpg"
    sheet.save(out, quality=82)
    return out
