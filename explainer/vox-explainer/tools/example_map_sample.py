"""20-second review sample: title card + "sandy peak" + locator map + Tethyan belt."""
import subprocess
import sys
from engine import *

VO0 = 4.0                     # narration b04 starts here
wb = words_of("b04")


def vo(i):                    # global time of word i of b04
    return VO0 + wb[i]["start"]


def wi(prefix, nth=0):
    hits = [k for k, w in enumerate(wb) if w["word"].strip(" ,.").lower().startswith(prefix.lower())]
    return hits[nth]


T_MEANS = vo(wi("means"))
T_SITS = vo(wi("It")) - 0.1
T_CHAGAI = vo(wi("chagai"))
T_BAL = vo(wi("balochistan"))
T_IRAN = vo(wi("iran"))
T_AFG = vo(wi("afghanistan"))
T_PART = vo(wi("it's"))
T_BELT = vo(wi("belt"))
T_EU = vo(wi("europe"))
T_TR = vo(wi("turkey"))
T_IR2 = vo(wi("iran", 1))
T_PK = vo(wi("pakistan"))
TOTAL = VO0 + wb[-1]["end"] + 0.9

PK = (69.3, 30.2, 24.0)
BAL = (65.6, 28.6, 11.0)
CHG = (63.2, 29.4, 6.2)
BELT = (43.0, 37.0, 64.0)
REKO = (62.07, 29.12)        # approx. site location (Chagai district)
BAND = [(21.9, 44.1), (24.5, 42.6), (29.0, 40.6), (35.0, 39.6), (42.0, 40.0), (46.7, 38.7),
        (50.5, 34.6), (55.9, 30.0), (62.07, 29.12)]


def shot_map(img, t, sh):
    g = sh["start"] + t                              # global time
    keys = [(0, PK), (T_CHAGAI - 0.2 - sh["start"], PK), (T_BAL + 0.2 - sh["start"], BAL),
            (T_IRAN - 0.5 - sh["start"], BAL), (T_AFG + 0.3 - sh["start"], CHG),
            (T_PART - sh["start"], CHG), (T_BELT + 0.9 - sh["start"], BELT)]
    view = view_at(keys, t)
    img.paste(paper_bg(), (0, 0))
    bal = ease_out((g - (T_BAL - 0.35)) / 0.5)
    draw_map(img, view, bal_fill=bal)
    out = T_PART + 0.1                               # locator labels leave as we pull out
    x, y = lonlat_xy(view, 70.6, 30.6)
    draw_label(img, "PAKISTAN", x, y, g, sh["start"] + 0.25, seed=21, t1=T_CHAGAI - 0.1, kind="head", size=64)
    x, y = lonlat_xy(view, 66.4, 27.6)
    draw_label(img, "BALOCHISTAN", x, y, g, T_BAL, seed=22, t1=T_IRAN - 0.6, kind="head", size=58, fg=WHITE, bg=INK)
    if g < out + 0.3:
        px, py = lonlat_xy(view, *REKO)
        draw_pin(img, px, py, g, T_BAL + 0.55)
        draw_label(img, "REKO DIQ", px + 150, py - 120, g, T_BAL + 0.8, seed=23, t1=out, kind="head", size=60,
                   fg=WHITE, bg=COPPER)
        draw_label(img, "CHAGAI, BALOCHISTAN", px + 190, py + 30, g, T_BAL + 1.0, seed=24, t1=out, kind="head", size=40)
        x, y = lonlat_xy(view, 61.25, 28.7)
        draw_label(img, "IRAN", x, y, g, T_IRAN, seed=25, t1=out, kind="head", size=56, bg=(230, 222, 206))
        x, y = lonlat_xy(view, 63.9, 30.45)
        draw_label(img, "AFGHANISTAN", x, y, g, T_AFG, seed=26, t1=out, kind="head", size=56, bg=(230, 222, 206))
    # belt
    p = ease_io((g - (T_EU - 0.4)) / (T_PK + 0.3 - (T_EU - 0.4)))
    draw_band(img, view, BAND, p, width_deg=2.0)
    if g > T_BELT - 0.2:
        draw_label(img, "THE TETHYAN BELT", W / 2, 120, g, T_BELT, seed=27, kind="head", size=84, fg=WHITE, bg=COPPER)
        for name, lon, lat, tt, sd in [("EUROPE", 21.0, 47.2, T_EU, 31), ("TURKEY", 33.5, 37.0, T_TR, 32),
                                      ("IRAN", 53.5, 33.6, T_IR2, 33), ("PAKISTAN", 68.8, 26.4, T_PK, 34)]:
            x, y = lonlat_xy(view, lon, lat)
            draw_label(img, name, x, y, g, tt, seed=sd, kind="head", size=48, bg=(250, 247, 240))
    # source credit
    cr = label_img("Map data: Natural Earth", kind="reg", size=24, fg=INK, bg=None, pad=(4, 2))
    paste_transformed(img, cr, 40 + cr.width / 2, H - 40, 1.0, 0, 0.6)


shots = [
    {"start": 0.0, "dur": VO0, "fn": shot_title},
    {"start": VO0, "dur": T_SITS - VO0, "fn": shot_poster, "poster": "p04_peak", "move": "push_in", "seed": 41,
     "labels": [{"text": 'REKO DIQ = "SANDY PEAK"', "x": W / 2, "y": 110, "t": T_MEANS - VO0, "seed": 42,
                 "style": {"kind": "head", "size": 92, "fg": WHITE, "bg": COPPER}}]},
    {"start": T_SITS, "dur": TOTAL - T_SITS, "fn": shot_map},
]

caps = caption_chunks(json.load(open(ROOT / "narration.json"))["beats"][3]["text"], wb, VO0)
overlays = [lambda img, t: draw_caption(img, t, caps)]

if __name__ == "__main__":
    silent = ROOT / "cut/sample_video.mp4"
    render(shots, overlays, silent, TOTAL)
    # ---- audio mix
    sfx = [("sfx/paper_slide.wav", 0.15, 18), ("music/hit.wav", 0.1, -4), ("sfx/pop.wav", T_MEANS, 4),
           ("sfx/whoosh.wav", T_SITS - 0.15, -10), ("sfx/pin.wav", T_BAL + 0.85, 2), ("sfx/pop.wav", T_IRAN, 2),
           ("sfx/pop.wav", T_AFG, 2), ("sfx/whoosh.wav", T_PART + 0.2, -10), ("sfx/pencil.wav", T_EU - 0.3, 14),
           ("sfx/pop.wav", T_BELT, 2), ("sfx/pop.wav", T_TR, 0), ("sfx/pop.wav", T_PK, 0)]
    ins = ["-i", str(silent), "-i", str(ROOT / "vo/b04.wav"), "-i", str(ROOT / "music/m2_investigate.wav")]
    for f, _, _ in sfx:
        ins += ["-i", str(ROOT / f)]
    fc = [f"[1:a]adelay={int(VO0*1000)}|{int(VO0*1000)},apad,volume=1.6,asplit=2[vo][sc]",
          f"[2:a]atrim=0:{TOTAL},afade=t=in:st=0:d=1.5,afade=t=out:st={TOTAL-1.5}:d=1.5,volume=0.32[mus]",
          "[mus][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck]"]
    mix = ["[vo]", "[duck]"]
    for k, (f, at, db) in enumerate(sfx):
        fc.append(f"[{k+3}:a]volume={db}dB,adelay={int(at*1000)}|{int(at*1000)}[s{k}]")
        mix.append(f"[s{k}]")
    fc.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0,atrim=0:{TOTAL},alimiter=limit=0.95[a]")
    out = ROOT.parent / "reko_diq_sample_20s.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(fc), "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)], check=True)
    print(out, TOTAL)
