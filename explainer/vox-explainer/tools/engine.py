"""Paper-collage motion engine for the Reko Diq explainer.

Everything is drawn with Pillow at 1920x1080 and piped to ffmpeg as raw frames.
Shots are functions draw(frame_img, t_local, shot) -> None; persistent overlays
(captions, grain) are applied on top.
"""
import json
import math
import random
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 24

# palette from the pack
PAPER = (244, 239, 230)
INK = (26, 26, 26)
COPPER = (200, 100, 43)
YELLOW = (242, 194, 48)
TEAL = (125, 154, 154)
RED = (210, 59, 46)
WHITE = (252, 250, 245)

F_HEAD = "/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf"
F_SANS = "/System/Library/Fonts/HelveticaNeue.ttc"


FONTS = ROOT / "fonts"


@lru_cache(None)
def font(kind, size):
    """head=DIN Condensed, anton=Anton, oswald=Oswald Bold, serif=Playfair Italic,
    inter/interb=Inter Regular/Bold, reg/bold/med/cond=Helvetica Neue."""
    if kind == "head":
        return ImageFont.truetype(F_HEAD, size)
    if kind == "anton":
        return ImageFont.truetype(str(FONTS / "Anton.ttf"), size)
    if kind in ("oswald", "serif", "inter", "interb"):
        fn = {"oswald": "Oswald.ttf", "serif": "PlayfairDisplay-Italic.ttf", "inter": "Inter.ttf", "interb": "Inter.ttf"}[kind]
        f = ImageFont.truetype(str(FONTS / fn), size)
        want = {"oswald": "Bold", "serif": "SemiBold Italic", "inter": "Regular", "interb": "Bold"}[kind]
        try:
            names = [n.decode() if isinstance(n, bytes) else n for n in f.get_variation_names()]
            pick = next((n for n in names if n.replace(" ", "").lower() == want.replace(" ", "").lower()), None)
            if pick:
                f.set_variation_by_name(pick)
        except Exception:
            pass
        return f
    idx = {"reg": 0, "bold": 1, "med": 10, "cond": 4}[kind]
    return ImageFont.truetype(F_SANS, size, index=idx)


# ---------------------------------------------------------------- easing / helpers
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x, s=1.7):
    x = clamp(x)
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def stepped(t, fps=12):
    """Quantise time for the handmade 12 fps cut-out feel."""
    return math.floor(t * fps) / fps


def jitter(seed, t, amp=1.0):
    """Deterministic stepped wobble (dx, dy, rot) for one element."""
    k = int(stepped(t) * 12)
    r = random.Random(seed * 1000003 + k)
    return (r.uniform(-1, 1) * 2.2 * amp, r.uniform(-1, 1) * 2.2 * amp, r.uniform(-1, 1) * 0.35 * amp)


# ---------------------------------------------------------------- assets
@lru_cache(None)
def paper_bg():
    im = Image.open(ROOT / "posters/p00_paper.png").convert("RGB").resize((W, H), Image.LANCZOS)
    # tint toward the pack's paper colour
    tint = Image.new("RGB", (W, H), PAPER)
    return Image.blend(im, tint, 0.35)


@lru_cache(None)
def bg_fill(color):
    """Bold flat background colour with the paper texture multiplied in."""
    if color is None:
        return paper_bg()
    tex = paper_bg().convert("L")
    flat = Image.new("RGB", (W, H), color)
    lum = tex.point(lambda v: int(200 + (v - 235) * 2.2) if v < 255 else 255)
    return ImageChops.multiply(flat, Image.merge("RGB", (lum, lum, lum)))


@lru_cache(None)
def poster_layer(name):
    """Poster as an RGBA cut-out: paper pixels become transparent, collage stays."""
    im = Image.open(ROOT / f"posters/{name}.png").convert("RGB").resize((W, int(W * 1088 / 1920)), Image.LANCZOS)
    a = np.asarray(im).astype(np.int16)
    border = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    paper = np.median(border, axis=0)
    dist = np.sqrt(((a - paper) ** 2).sum(-1))
    alpha = np.clip((dist - 10) / 22, 0, 1)
    m = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    out = im.convert("RGBA")
    out.putalpha(m)
    return out


@lru_cache(None)
def grain_frames():
    rng = np.random.default_rng(3)
    frames = []
    for _ in range(4):
        n = rng.normal(0, 7, (H // 2, W // 2)).astype(np.int16)
        g = Image.fromarray(np.clip(n + 128, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        frames.append(g)
    return frames


def apply_grain(img, t):
    g = grain_frames()[int(stepped(t) * 12) % 4]
    base = np.asarray(img).astype(np.int16)
    d = (np.asarray(g).astype(np.int16) - 128)[..., None]
    return Image.fromarray(np.clip(base + d, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- compositing
def paste_transformed(dst, src, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    """Paste RGBA src centred at (cx, cy) with scale/rotation/alpha."""
    if alpha <= 0.01 or scale <= 0.01:
        return
    w, h = src.size
    if scale != 1.0:
        src = src.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BICUBIC)
    if abs(rot) > 0.01:
        src = src.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = src.getchannel("A").point(lambda v: int(v * alpha))
        src = src.copy()
        src.putalpha(a)
    dst.alpha_composite(src, (int(cx - src.width / 2), int(cy - src.height / 2))) if dst.mode == "RGBA" else dst.paste(src, (int(cx - src.width / 2), int(cy - src.height / 2)), src)


def with_shadow(layer, offset=(10, 12), blur=10, opacity=0.35):
    """Return RGBA with a soft drop shadow under the layer (padded)."""
    pad = blur * 2 + max(offset)
    w, h = layer.size
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    a = layer.getchannel("A").point(lambda v: int(v * opacity))
    shadow = Image.new("RGBA", layer.size, (40, 30, 20, 0))
    shadow.putalpha(a)
    sh.paste(shadow, (pad + offset[0], pad + offset[1]), shadow)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(sh)
    out.alpha_composite(layer, (pad, pad))
    return out


@lru_cache(None)
def label_img(text, kind="head", size=72, fg=INK, bg=WHITE, pad=(26, 14), rot_seed=0, torn=True):
    """A cut-out paper strip with text, with a torn edge and drop shadow."""
    f = font(kind, size)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = tw + pad[0] * 2, th + pad[1] * 2 + (8 if kind == "head" else 0)
    strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    if bg is not None:
        r = random.Random(hash(text) + rot_seed)
        pts = []
        step = 14
        for x in range(0, w + 1, step):
            pts.append((x, r.uniform(0, 4) if torn else 0))
        for y in range(0, h + 1, step):
            pts.append((w - (r.uniform(0, 3) if torn else 0), y))
        for x in range(w, -1, -step):
            pts.append((x, h - (r.uniform(0, 4) if torn else 0)))
        for y in range(h, -1, -step):
            pts.append(((r.uniform(0, 3) if torn else 0), y))
        d.polygon(pts, fill=bg + (255,))
    d.text((pad[0] - bbox[0], pad[1] - bbox[1] + (4 if kind == "head" else 0)), text, font=f, fill=fg + (255,))
    return with_shadow(strip, offset=(5, 7), blur=6, opacity=0.4)


def pop_in(t, t0, dur=0.35):
    """Scale + alpha for a paper pop (0 before t0)."""
    if t < t0:
        return 0.0, 0.0
    x = (t - t0) / dur
    return (0.55 + 0.45 * back_out(x, 2.2)), clamp(x * 2.5)


def draw_label(img, text, cx, cy, t, t0, seed=1, t1=None, **kw):
    s, a = pop_in(t, t0)
    if t1 is not None and t > t1:
        a *= clamp(1 - (t - t1) / 0.25)
    if a <= 0:
        return
    lab = label_img(text, rot_seed=seed, **kw)
    dx, dy, dr = jitter(seed, t, 0.8)
    base_rot = random.Random(seed).uniform(-2.2, 2.2)
    paste_transformed(img, lab, cx + dx, cy + dy, s, base_rot + dr, a)


# ---------------------------------------------------------------- shots
def shot_poster(img, t, sh):
    """Living poster: paper base + cut-out collage with camera move + stepped wobble."""
    dur = sh["dur"]
    p = ease_io(t / dur)
    move = sh.get("move", "push_in")
    z0, z1 = {"push_in": (1.0, 1.08), "pull_out": (1.1, 1.0), "pan": (1.06, 1.06), "static": (1.02, 1.02)}[move]
    z = z0 + (z1 - z0) * p
    px = (-40 + 80 * p) if move == "pan" else 0
    bg = bg_fill(sh.get("bg"))
    bgz = 1 + (z - 1) * 0.5
    b = bg.resize((int(W * bgz), int(H * bgz)), Image.BILINEAR)
    img.paste(b, (int((W - b.width) / 2 + px * 0.4), int((H - b.height) / 2)))
    lay = poster_layer(sh["poster"])
    dx, dy, dr = jitter(sh.get("seed", 7), t, 1.0)
    paste_transformed(img, lay, W / 2 + px + dx, H / 2 + dy + sh.get("dy", 0), z * sh.get("scale", 1.0), dr)
    for lab in sh.get("labels", []):
        draw_label(img, lab["text"], lab["x"], lab["y"], t, lab["t"], seed=lab.get("seed", 3), t1=lab.get("t1"),
                   **lab.get("style", {}))


def shot_title(img, t, sh):
    img.paste(paper_bg(), (0, 0))
    d = ImageDraw.Draw(img)
    # big title, slapped in
    s, a = pop_in(t, 0.15, 0.4)
    title = label_img("REKO DIQ", kind="head", size=300, fg=INK, bg=None, pad=(20, 10))
    dx, dy, dr = jitter(11, t, 0.6)
    paste_transformed(img, title, W / 2 + dx, 420 + dy, 1.6 - 0.6 * back_out((t - 0.15) / 0.45, 1.4) if t > 0.15 else 0, dr, a)
    # hand-drawn copper underline
    p = ease_out((t - 0.7) / 0.7)
    if p > 0:
        r = random.Random(5)
        x0, x1, y = 640, 1280, 585
        pts = []
        n = 40
        for i in range(int(n * p) + 1):
            x = x0 + (x1 - x0) * i / n
            pts.append((x, y + math.sin(i * 0.7) * 3 + r.uniform(-2, 2)))
        if len(pts) > 1:
            d.line(pts, fill=COPPER, width=16, joint="curve")
    sub = "Why Pakistan's biggest treasure is still underground"
    a2 = clamp((t - 1.3) / 0.5)
    if a2 > 0:
        lab = label_img(sub, kind="med", size=50, fg=INK, bg=None, pad=(10, 6))
        paste_transformed(img, lab, W / 2, 680 + (1 - ease_out(a2)) * 20, 1.0, 0, a2)


# ---------------------------------------------------------------- maps
GEO = ROOT / "geo"


@lru_cache(None)
def geo_data():
    c = json.load(open(GEO / "countries.geojson"))
    feats = []
    for f in c["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [np.array(p[0]) for p in polys]
        allpts = np.concatenate(rings)
        bb = (allpts[:, 0].min(), allpts[:, 1].min(), allpts[:, 0].max(), allpts[:, 1].max())
        feats.append({"name": f["properties"]["NAME"], "iso": f["properties"]["ADM0_A3"], "rings": rings, "bb": bb})
    b = json.load(open(GEO / "balochistan.geojson"))["features"][0]["geometry"]
    bpolys = b["coordinates"] if b["type"] == "MultiPolygon" else [b["coordinates"]]
    bal = [np.array(p[0]) for p in bpolys]
    return feats, bal


def proj(view, lon, lat):
    cx, cy, span = view  # span = degrees of longitude across the frame
    k = W / span
    lat0 = math.radians(cy)
    x = (np.asarray(lon) - cx) * math.cos(lat0) * k + W / 2
    y = -(np.asarray(lat) - cy) * k + H / 2
    return x, y


def lerp_view(a, b, p):
    """Interpolate views, zooming in log space."""
    return (a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * p))


def view_at(keys, t):
    """keys: list of (t, view); eased hold-and-move between them."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp_view(v0, v1, ease_io((t - t0) / (t1 - t0)))
    return keys[-1][1]


def draw_map(img, view, highlight=None, bal_fill=0.0, outline_pk=True, dim_others=0.0):
    feats, bal = geo_data()
    cx, cy, span = view
    lon0, lon1 = cx - span * 0.8, cx + span * 0.8
    lat0, lat1 = cy - span * 0.5, cy + span * 0.5
    sea = Image.new("RGBA", (W, H), TEAL + (70,))
    img.alpha_composite(sea) if img.mode == "RGBA" else img.paste(Image.blend(img, Image.new("RGB", (W, H), TEAL), 0.28))
    land = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(land)
    lw = max(2, int(3 * 18 / span)) if span < 40 else 2
    for f in feats:
        bb = f["bb"]
        if bb[2] < lon0 or bb[0] > lon1 or bb[3] < lat0 or bb[1] > lat1:
            continue
        is_pk = f["iso"] == "PAK"
        fill = WHITE if is_pk else (234, 226, 211)
        if highlight and f["iso"] in highlight:
            fill = highlight[f["iso"]]
        for ring in f["rings"]:
            if len(ring) < 3:
                continue
            x, y = proj(view, ring[:, 0], ring[:, 1])
            pts = list(zip(x.tolist(), y.tolist()))
            ld.polygon(pts, fill=fill + (255,))
    # shadow for the paper-cut feel (computed small, upscaled)
    small = land.getchannel("A").resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))
    sh = Image.new("RGBA", (W, H), (60, 45, 30, 0))
    sh.putalpha(small.resize((W, H), Image.BILINEAR).point(lambda v: int(v * 0.35)))
    img.alpha_composite(sh, (7, 9))
    img.alpha_composite(land)
    d = ImageDraw.Draw(img)
    # Balochistan fill
    if bal_fill > 0:
        bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bl)
        for ring in bal:
            x, y = proj(view, ring[:, 0], ring[:, 1])
            bd.polygon(list(zip(x.tolist(), y.tolist())), fill=COPPER + (int(235 * bal_fill),))
        img.alpha_composite(bl)
    # outlines
    for f in feats:
        bb = f["bb"]
        if bb[2] < lon0 or bb[0] > lon1 or bb[3] < lat0 or bb[1] > lat1:
            continue
        is_pk = f["iso"] == "PAK"
        for ring in f["rings"]:
            if len(ring) < 3:
                continue
            x, y = proj(view, ring[:, 0], ring[:, 1])
            pts = list(zip(x.tolist(), y.tolist()))
            d.line(pts + pts[:1], fill=INK if is_pk else (120, 112, 100), width=(lw + 2) if is_pk else max(1, lw - 1), joint="curve")
    if bal_fill > 0:
        for ring in bal:
            x, y = proj(view, ring[:, 0], ring[:, 1])
            pts = list(zip(x.tolist(), y.tolist()))
            d.line(pts + pts[:1], fill=INK, width=lw, joint="curve")


def draw_pin(img, x, y, t, t0):
    if t < t0:
        return
    p = (t - t0) / 0.45
    drop = (1 - back_out(p, 1.2)) * -220 if p < 1 else 0
    a = clamp(p * 3)
    pin = Image.new("RGBA", (90, 130), (0, 0, 0, 0))
    d = ImageDraw.Draw(pin)
    d.polygon([(22, 52), (68, 52), (45, 124)], fill=RED + (255,))
    d.ellipse((8, 4, 82, 78), fill=RED + (255,))
    d.ellipse((30, 26, 60, 56), fill=WHITE + (255,))
    pin = with_shadow(pin, (6, 6), 5, 0.4)
    paste_transformed(img, pin, x, y - 62 + drop, 1.0, 0, a)
    # ripple
    if 0.3 < p < 1.6:
        r = (p - 0.3) * 70
        ImageDraw.Draw(img).ellipse((x - r, y - r * 0.45, x + r, y + r * 0.45), outline=RED + (int(255 * clamp(1.6 - p)),), width=4)


def draw_band(img, view, pts_lonlat, p, width_deg=1.6):
    """Progressive hand-drawn orange band along a lon/lat polyline."""
    if p <= 0:
        return
    lon = np.array([q[0] for q in pts_lonlat])
    lat = np.array([q[1] for q in pts_lonlat])
    # densify
    seg = np.hypot(np.diff(lon), np.diff(lat))
    cum = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, cum[-1] * p, max(2, int(200 * p)))
    L = np.interp(s, cum, lon)
    A = np.interp(s, cum, lat)
    r = np.random.default_rng(4)
    A = A + np.sin(s * 1.3) * 0.25
    x, y = proj(view, L, A)
    k = W / view[2]
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.line(list(zip(x.tolist(), y.tolist())), fill=COPPER + (200,), width=int(width_deg * k), joint="curve")
    for xi, yi in [(x[0], y[0]), (x[-1], y[-1])]:
        rr = width_deg * k / 2
        bd.ellipse((xi - rr, yi - rr, xi + rr, yi + rr), fill=COPPER + (200,))
    # halftone-ish texture: knock out a dot grid
    img.alpha_composite(band)


def lonlat_xy(view, lon, lat):
    x, y = proj(view, lon, lat)
    return float(x), float(y)


# ---------------------------------------------------------------- captions
def caption_chunks(text, words, offset, max_words=7):
    """Split script text into caption chunks timed by Whisper word starts."""
    import re
    clean = re.sub(r"\[([^\]]+)\]\(/[^)]+/\)", r"\1", text)
    toks = clean.split()
    chunks, cur = [], []
    for tk in toks:
        cur.append(tk)
        if len(cur) >= max_words or tk.endswith((".", "?", ",", ":")) and len(cur) >= 3:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    i = 0
    n = len(words)
    ratio = n / max(1, len(toks))
    for ch in chunks:
        a = min(n - 1, int(round(i * ratio)))
        b = min(n - 1, int(round((i + len(ch)) * ratio)) - 1)
        out.append((offset + words[a]["start"], offset + words[max(a, b)]["end"] + 0.15, " ".join(ch)))
        i += len(ch)
    # make each end at the next start
    fixed = []
    for k, (s, e, tx) in enumerate(out):
        if k + 1 < len(out):
            e = min(e + 0.6, out[k + 1][0])
        fixed.append((s, e, tx))
    return fixed


def draw_caption(img, t, caps, y=968):
    for s, e, tx in caps:
        if s <= t < e:
            lab = label_img(tx, kind="med", size=42, fg=WHITE, bg=(30, 28, 26), pad=(22, 12), torn=False)
            a = clamp((t - s) / 0.12) * clamp((e - t) / 0.12)
            paste_transformed(img, lab, W / 2, y, 1.0, 0, a)
            return


def words_of(beat):
    d = json.load(open(ROOT / f"vo/{beat}.json"))
    return [w for s in d["segments"] for w in s["words"]]


# ---------------------------------------------------------------- render
def render(shots, overlays, out_path, total, grain=True):
    """shots: list of dict(start, dur, fn, ...). overlays: list of fn(img, t)."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nframes = int(round(total * FPS))
    for i in range(nframes):
        t = i / FPS
        img = Image.new("RGBA", (W, H), PAPER + (255,))
        for sh in shots:
            if sh["start"] <= t < sh["start"] + sh["dur"]:
                sh["fn"](img, t - sh["start"], sh)
                break
        for ov in overlays:
            ov(img, t)
        rgb = img.convert("RGB")
        if grain:
            rgb = apply_grain(rgb, t)
        p.stdin.write(rgb.tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------- arrows
def draw_arrow(img, p0, p1, t, t0, dur=0.45, color=YELLOW, width=10, bend=0.25, seed=1,
               head=52, head_angle=30, style="marker", double=False):
    """Hand-drawn arrow drawn on from p0 to p1.

    bend: curvature as a fraction of length (+ curves left, - right, 0 straight).
    The head follows the path tangent, so it lands at whatever angle the curve arrives.
    style: "marker" (solid stroke) or "dashed" (route line). double: heads at both ends.
    """
    if t < t0:
        return
    p = ease_out((t - t0) / dur)
    r = random.Random(seed)
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L                       # normal
    cx, cy = (x0 + x1) / 2 + nx * L * bend, (y0 + y1) / 2 + ny * L * bend
    n = 48
    pts = []
    for i in range(int(n * p) + 1):
        s = i / n
        bx = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s * s * x1
        by = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cy + s * s * y1
        wob = math.sin(s * 9 + seed) * 1.6 + r.uniform(-0.8, 0.8)   # hand wobble
        pts.append((bx + nx * wob, by + ny * wob))
    if len(pts) < 2:
        return
    d = ImageDraw.Draw(img)
    # shadow first, same light direction as every other object (down-right)
    sh = [(x + 4, y + 5) for x, y in pts]
    if style == "dashed":
        for k in range(0, len(pts) - 1, 2):
            d.line(pts[k:k + 2], fill=(40, 30, 20, 70), width=width)
        for k in range(0, len(pts) - 1, 2):
            d.line([(a + 0, b + 0) for a, b in pts[k:k + 2]], fill=color + (255,), width=width)
    else:
        d.line(sh, fill=(40, 30, 20, 70), width=width, joint="curve")
        d.line(pts, fill=color + (255,), width=width, joint="curve")

    def arrowhead(tip, prev):
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        a = math.radians(head_angle + r.uniform(-4, 4))
        for side in (-1, 1):
            hx = tip[0] - head * math.cos(ang + side * a)
            hy = tip[1] - head * math.sin(ang + side * a)
            d.line([(hx + 4, hy + 5), (tip[0] + 4, tip[1] + 5)], fill=(40, 30, 20, 70), width=width)
            d.line([(hx, hy), tip], fill=color + (255,), width=width)

    if p > 0.85:                                    # head pops in as the stroke arrives
        arrowhead(pts[-1], pts[-4] if len(pts) > 4 else pts[0])
    if double and p > 0.85:
        arrowhead(pts[0], pts[3] if len(pts) > 3 else pts[-1])


def draw_circle_mark(img, cx, cy, rx, ry, t, t0, dur=0.5, color=YELLOW, width=9, seed=2):
    """Hand-drawn ellipse that overshoots its start, like a marker circle."""
    if t < t0:
        return
    p = ease_out((t - t0) / dur)
    r = random.Random(seed)
    start = r.uniform(0, math.tau)
    pts = []
    n = 60
    for i in range(int(n * 1.12 * p) + 1):
        a = start + math.tau * i / n
        k = 1 + 0.04 * math.sin(i * 0.3 + seed) + (0.06 * i / n)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    if len(pts) > 1:
        d = ImageDraw.Draw(img)
        d.line([(x + 4, y + 5) for x, y in pts], fill=(40, 30, 20, 70), width=width, joint="curve")
        d.line(pts, fill=color + (255,), width=width, joint="curve")
