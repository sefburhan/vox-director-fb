"""Animated data charts with icons. Every value is drawn to scale; each series animates on its word."""
from kit import *  # noqa

ICON_DIR = ROOT / "icons"
GOLD = (212, 170, 60)
GREEN = (80, 160, 100)
BLUE = (74, 125, 176)
SERIES = [COPPER, BLUE, GOLD, RED, GREEN, TEAL]


@lru_cache(None)
def icon(name, size=96, col=WHITE):
    im = Image.open(ICON_DIR / f"{name}.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    solid = Image.new("RGBA", im.size, col + (255,))
    solid.putalpha(im.getchannel("A"))
    return solid


def badge(img, name, x, y, g, at, col=COPPER, r=58):
    """Coloured disc with a white icon; pops in."""
    if g < at:
        return
    s, a = pop_in(g, at, 0.35)
    rr = r * s
    d = ImageDraw.Draw(img)
    d.ellipse((x - rr + 5, y - rr + 7, x + rr + 5, y + rr + 7), fill=(30, 25, 20, int(70 * a)))
    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col + (int(255 * a),))
    ic = icon(name, int(r * 1.15))
    paste_transformed(img, ic, x, y, s, 0, a)


def text(img, s, x, y, size=40, kind="anton", col=INK, anchor="mm", a=1.0):
    ImageDraw.Draw(img).text((x, y), s, font=font(kind, size), fill=col + (int(255 * a),), anchor=anchor)


def fmt(v, dec=0, prefix="", suffix=""):
    return f"{prefix}{v:,.{dec}f}{suffix}"


def stat(img, g, at, x, y, name, value, label, col=COPPER, dec=0, prefix="", suffix="", size=120, dur=1.2, fg=INK):
    """Icon badge + counting number + label underneath."""
    if g < at:
        return
    badge(img, name, x, y - size * 0.95, g, at, col, r=int(size * 0.45))
    v = value * ease_out((g - at) / dur)
    a = clamp((g - at) * 5)
    text(img, fmt(v, dec, prefix, suffix), x, y + 4, size, "anton", fg, a=a)
    text(img, label, x, y + size * 0.72, int(size * 0.3), "interb", col, a=clamp((g - at - 0.3) * 4))


def donut(img, g, cx, cy, r, segs, centre=None, sub=None, thick=0.42, labels=True, start_at=None):
    """segs: [(value, colour, label, icon, at)]; sweeps clockwise from 12 o'clock, each segment on its word."""
    tot = sum(s[0] for s in segs)
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r + 8, cy - r + 12, cx + r + 8, cy + r + 12), fill=(30, 25, 20, 60))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(226, 220, 208, 255))
    a0 = -90.0
    for val, col, lab, ic, at in segs:
        span = 360 * val / tot
        p = ease_out((g - at) / 0.7)
        if p > 0:
            d.pieslice((cx - r, cy - r, cx + r, cy + r), a0, a0 + span * p, fill=col + (255,))
            d.pieslice((cx - r, cy - r, cx + r, cy + r), a0, a0 + span * p, outline=(250, 248, 242, 255), width=4)
            if labels and p > 0.85:
                mid = math.radians(a0 + span / 2)
                ex, ey = cx + math.cos(mid) * (r + 60), cy + math.sin(mid) * (r + 60)
                d.line([(cx + math.cos(mid) * r * 0.85, cy + math.sin(mid) * r * 0.85), (ex, ey)], fill=INK + (255,), width=3)
                side = 1 if math.cos(mid) >= 0 else -1
                if ic:
                    badge(img, ic, ex + side * 46, ey, g, at + 0.5, col, r=36)
                text(img, lab, ex + side * 96, ey, 40, "anton", INK, anchor="lm" if side > 0 else "rm", a=clamp((g - at - 0.55) * 4))
        a0 += span
    ri = r * (1 - thick)
    d.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=(250, 248, 242, 255))
    if centre:
        text(img, centre, cx, cy - (16 if sub else 0), int(ri * 0.55), "anton", INK, a=clamp((g - (start_at or segs[0][4])) * 3))
    if sub:
        text(img, sub, cx, cy + ri * 0.42, int(ri * 0.18), "interb", (100, 96, 90), a=clamp((g - (start_at or segs[0][4])) * 3))


def hbars(img, g, x, y, w, rows, maxv, rowh=110, unit="", dec=0, prefix="", grid=None):
    """rows: [(label, value, colour, icon, at, value_text or None)]; bars grow from the left to scale."""
    d = ImageDraw.Draw(img)
    lw = 360
    if grid:
        for gv in grid:
            gx = x + lw + (w - lw) * gv / maxv
            d.line([(gx, y - 40), (gx, y + rowh * len(rows) - 20)], fill=(150, 145, 135, 120), width=2)
            text(img, fmt(gv, 0, prefix, unit), gx, y - 60, 24, "interb", (110, 105, 98))
    for i, (lab, val, col, ic, at, vt) in enumerate(rows):
        yy = y + i * rowh + rowh * 0.35
        a = clamp((g - (at - 0.6)) * 3)
        if ic:
            badge(img, ic, x + 40, yy, g, at - 0.6, col, r=36)
        text(img, lab, x + 92, yy, 38, "anton", INK, anchor="lm", a=a)
        p = ease_out((g - at) / 0.9)
        bw = (w - lw) * val / maxv * p
        if bw > 1:
            d.rectangle((x + lw + 6, yy - 30 + 8, x + lw + bw + 6, yy + 30 + 8), fill=(30, 25, 20, int(60 * a)))
            d.rectangle((x + lw, yy - 30, x + lw + bw, yy + 30), fill=col + (int(255 * a),))
        if p > 0.05:
            txt = vt if (vt and p > 0.98) else fmt(val * p, dec, prefix, unit)
            text(img, txt, x + lw + bw + 18, yy, 46, "anton", col, anchor="lm")


def vbars(img, g, x0, base, rows, maxv, height=480, bw=170, gap=110, dec=0, prefix="", unit=""):
    """rows: [(label, value, colour, icon, at, value_text or None)]; columns grow from the baseline."""
    d = ImageDraw.Draw(img)
    n = len(rows)
    d.line([(x0 - 30, base), (x0 + n * (bw + gap) - gap + 30, base)], fill=INK + (255,), width=4)
    for i, (lab, val, col, ic, at, vt) in enumerate(rows):
        x = x0 + i * (bw + gap)
        p = ease_out((g - at) / 0.9)
        h = height * val / maxv * p
        if p > 0:
            if h > 12:
                d.rectangle((x + 8, base - h + 10, x + bw + 8, base), fill=(30, 25, 20, 60))
            d.rectangle((x, base - h, x + bw, base), fill=col + (255,))
            txt = vt if (vt and p > 0.98) else fmt(val * p, dec, prefix, unit)
            text(img, txt, x + bw / 2, base - h - 40, 50, "anton", col)
        text(img, lab, x + bw / 2, base + 40, 34, "anton", INK, a=clamp((g - at + 0.6) * 3))
        if ic:
            badge(img, ic, x + bw / 2, base + 110, g, at - 0.6, col, r=34)


def stacked(img, g, x, y, w, h, parts, maxv, total=None, total_at=None, unit="", prefix="$", dec=1, total_label="TOTAL"):
    """parts: [(value, colour, label, at)] stacked left→right to scale; optional dashed target/total marker."""
    d = ImageDraw.Draw(img)
    d.rectangle((x, y, x + w, y + h), fill=(232, 226, 214, 255), outline=INK, width=3)
    cx = x
    for val, col, lab, at in parts:
        p = ease_out((g - at) / 0.8)
        seg = w * val / maxv
        if p > 0:
            d.rectangle((cx, y, cx + seg * p, y + h), fill=col + (255,))
            if p > 0.9:
                d.line([(cx, y), (cx, y + h)], fill=WHITE + (255,), width=5)
                text(img, fmt(val, dec, prefix, unit), cx + seg / 2, y + h / 2, int(h * 0.42), "anton", WHITE)
                text(img, lab, cx + seg / 2, y + h + 40, 34, "anton", col)
        cx += seg
    if total is not None and total_at is not None and g > total_at:
        tx = x + w * total / maxv
        a = clamp((g - total_at) * 3)
        for yy in range(int(y - 50), int(y + h + 20), 18):
            d.line([(tx, yy), (tx, yy + 9)], fill=INK + (int(255 * a),), width=4)
        text(img, f"{total_label} {fmt(total, dec, prefix, unit)}", tx, y - 80, 50, "anton", INK, a=a)


def panel(img, x0, y0, x1, y1, col=(250, 248, 242)):
    """Paper card behind a chart."""
    card = Image.new("RGBA", (int(x1 - x0), int(y1 - y0)), col + (255,))
    paste_transformed(img, with_shadow(card, (10, 14), 14, 0.35), (x0 + x1) / 2, (y0 + y1) / 2, 1.0, 0)
