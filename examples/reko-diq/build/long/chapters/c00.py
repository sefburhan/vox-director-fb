"""Cold open: 28 May 1998 → what was already in the ground → zero → title."""
from chapters.common import *  # noqa
import charts as CH


def build():
    P = Part("c00", card=False)
    P.bg = DARK
    P.gap(P.b(3), 1.4)                                   # one beat of silence after "already in it"
    P.gap(P.b(7), 0.9)

    # 1 · 28 May 1998, Ras Koh turns white
    tw = P.W(1, "white")

    def flash(img, g, t, sh, view):
        x, y = lonlat_xy(view, *RASKOH)
        if g > tw - 0.3:
            p = clamp((g - tw + 0.3) / 1.4)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            for k in range(6):
                rr = 30 + 190 * p * (1 + k * 0.25)
                dd.ellipse((x - rr, y - rr * 0.6, x + rr, y + rr * 0.6), fill=(255, 255, 255, int(120 * (1 - p * 0.6) / (k + 1))))
            img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
        map_name(img, "Chagai", view, 63.4, 29.8, g, 1.8, size=60, col=WHITE)
        map_name(img, "Ras Koh", view, RASKOH[0], RASKOH[1] - 0.5, g, tw - 0.4, size=44, col=WHITE)
    P.add(0, P.S(2) - 0.1, T_map([(0, V_PK), (1.2, V_PK), (3.6, V_CHG)], dark=0.1, extra=flash),
          cards=[C("28 MAY 1998 · RAS KOH, CHAGAI", 0.5, "ink", xy=(560, 160), side="L")])
    P.fx("sfx/wind.wav", 0, -6)
    P.fx("sfx/boom.wav", tw - 0.2, -4)

    # 2 · five devices, celebration, panic → map push
    wp = P.W(2, "world")
    P.add(P.S(2) - 0.1, P.W(2, "and", 0) - 0.1 if P.W(2, "and") > wp else wp + 1.6,
          T_poster("p13_news", (60, 62, 64), "push_in", conf=burst(11, P.W(2, "celebrated"), 600, 500, 40)),
          cards=[C("PAKISTAN'S FIRST NUCLEAR TESTS", P.S(2) + 0.2, "yellow", pop=True, xy=(W / 2, 140), size=70),
                 C("5 DEVICES", P.W(2, "five"), "red", xy=(1500, 420), stamp=True, size=110, col=RED),
                 C("THE COUNTRY CELEBRATED", P.W(2, "celebrated"), "copper", xy=(480, 760), side="L"),
                 C("THE WORLD PANICKED", P.W(2, "panicked"), "ink", xy=(1440, 760), side="R")])
    P.fx("sfx/paper_slide.wav", P.S(2), 16)
    P.fx("sfx/stamp_heavy.wav", P.W(2, "five"), -4)
    s2b = P.W(2, "and", 0) - 0.1 if P.W(2, "and") > wp else wp + 1.6
    P.add(s2b, P.S(3) - 0.05, T_map([(0, V_BAL), (3.5, V_CHG)], bal=BAL_ON, dark=0.15,
                                    extra=lambda img, g, t, sh, v: map_name(img, "Chagai", v, 63.4, 29.8, g, sh["start"] + 0.3, size=64)),
          cards=[C("FAMOUS FOR WHAT WAS PUT INTO ITS GROUND", P.W(2, "famous"), "ink", xy=(W / 2, 160), size=50)])

    # 3 · hard cut to black, silence
    P.add(P.S(3) - 0.05, P.S(4) - 0.05, T_black())

    # 4 · 1996 drilling, cores laced with copper and gold
    rig = "L01_drillrig" if (ROOT / "posters/L01_drillrig.png").exists() else "p06_camp"
    tc = P.W(4, "cores")
    P.add(P.S(4) - 0.05, tc - 0.1, T_poster(rig, OCHRE, "push_in", seed=41), cards=[C("1996: FIRST DRILLING", P.W(4, "earlier"), "ink", xy=(W / 2, 150), size=64)])
    P.add(tc - 0.1, P.S(5) - 0.05, T_poster("p06_cores", YELLOW, "pan", seed=42,
                                            extra=lambda img, g, t, sh: draw_circle_mark(img, 1000, 520, 360, 120, g, P.W(4, "copper"), color=RED, seed=5)),
          cards=[C("COPPER + GOLD", P.W(4, "copper"), "copper", xy=(1450, 860), side="B")])
    P.fx("sfx/paper_slide.wav", tc, 14)

    # 5 · 15 Mt / 26 Moz cutaway
    t15, t26 = P.W(5, "15"), P.W(5, "26")
    cf = burst(51, P.W(5, "copper"), 560, 300, 40)
    cf2 = burst(52, P.W(5, "gold"), 1360, 300, 40)

    def cut(img, g, t, sh):
        fill_bg(img, DEEP)
        paste_transformed(img, poster_layer("p02_cutaway"), W / 2, H / 2 + 130, 0.9 + 0.05 * ease_io(t / sh["dur"]), jitter(5, g)[2])
        p = ease_io((g - sh["start"] - 0.4) / 1.0)
        if p < 1:
            paste_transformed(img, poster_layer("p01_desert"), W / 2 - 900 * p, H / 2 - 700 * p * p + 40, 1 - 0.3 * p, -25 * p)
        cf.draw(img, g, amb=False)
        cf2.draw(img, g, amb=False)
        counter(img, 15, 0, 560, 200, g, t15, P.W(5, "copper", end=True), size=210, fg=WHITE)
        big_text(img, "MILLION TONNES OF COPPER", 560, 335, 50, g, P.W(5, "million"), fg=INK, bg=YELLOW, seed=11)
        counter(img, 26, 0, 1360, 200, g, t26, P.W(5, "gold", end=True), size=210, fg=YELLOW)
        big_text(img, "MILLION OUNCES OF GOLD", 1360, 335, 50, g, P.W(5, "ounces"), fg=WHITE, bg=COPPER, seed=12)
        CH.badge(img, "pick", 380, 200, g, t15, COPPER, r=62)
        CH.badge(img, "coins", 1180, 200, g, t26, CH.GOLD, r=62)
    tl = P.W(5, "largest")
    P.add(P.S(5) - 0.05, tl - 0.2, lambda img, t, sh: cut(img, sh["start"] + t, t, sh))
    P.add(tl - 0.2, P.S(6) - 0.05, T_doc("docs/barrick_technical_report__table_1_2_p21.png", bg=DEEP, crop=(80, 140, 1360, 900), width=1300, cy=H / 2 + 60),
          cards=[C("ONE OF THE LARGEST UNTOUCHED DEPOSITS ON EARTH", tl, "yellow", xy=(W / 2, 140), size=48)])
    P.fx("sfx/ring.wav", t15, -4)
    P.fx("sfx/ring.wav", t26, -4)

    # 6 · signed away, taken back; city hops; $6B; a law
    cities = [(ISLAMABAD, "ISLAMABAD", P.W(6, "islamabad")), (WASHINGTON, "WASHINGTON", P.W(6, "washington")),
              (LONDON, "LONDON", P.W(6, "london")), (BVI, "BRITISH VIRGIN ISLANDS", P.W(6, "british"))]
    tp = P.W(6, "tribunal")

    def hops(img, g, t, sh, view):
        for i, (pt, nm, at) in enumerate(cities):
            if i:
                route(img, view, [cities[i - 1][0], pt], g, at - 0.5, dur=0.6, col=RED, width=6)
            dot(img, view, pt, g, at, nm, col=RED, size=34, side=(-1 if pt[0] < -20 else 1))
    P.add(P.S(6) - 0.05, tp - 0.15, T_map([(0, (40, 30, 110)), (2.0, V_WORLD)], extra=hops, dark=0.25),
          cards=[C("SIGNED AWAY · TAKEN BACK", P.S(6) + 0.1, "yellow", xy=(W / 2, 140), size=56)])
    for _, _, at in cities:
        P.fx("sfx/pop.wav", at, 0)
    tlaw = P.W(6, "law")
    P.add(tp - 0.15, P.S(7) - 0.05, T_fill(RED, burst=(W / 2, H / 2), conf=burst(61, P.W(6, "six"), n=60)),
          cards=[C("~$6 BILLION", P.W(6, "six"), "red", xy=(W / 2, 470), slam=True, size=240),
                 C("A LAW JUST TO RESTART IT", tlaw, "ink", xy=(W / 2, 760), size=60, side="B")])
    P.fx("sfx/boom.wav", P.W(6, "six"), -2)

    # 7 · produced: zero
    def zero(img, g, t, sh):
        counter_val = 15 * (1 - ease_io((g - sh["start"] - 0.3) / 1.6))
        lab = label_img(f"{counter_val:,.0f}" if counter_val > 0.5 else "0", kind="anton", size=300, fg=WHITE, bg=None, pad=(20, 10))
        paste_transformed(img, lab, W / 2, 560, 1.0, 0)
    P.add(P.S(7) - 0.05, P.S(8) - 0.05, T_photo("photos/barrick_aerial_site.jpg", bg=COPPER, cy=H / 2, z=(1.15, 1.22), maxw=1500, maxh=900, seed=11, extra=zero),
          cards=[C("TONNES PRODUCED", P.S(7) + 0.2, "yellow", xy=(W / 2, 300), pop=True, size=70)])
    P.fx("sfx/slide_slow.wav", P.S(7) + 0.3, 8)
    P.fx("sfx/wind.wav", P.W(7, "zero"), -6)

    # 8 · the story… title hit
    tt = P.E(8) - 0.2
    P.add(P.S(8) - 0.05, P.total, T_photo("photos/barrick_aerial_site.jpg", bg=COPPER, cy=H / 2, z=(1.25, 1.0), maxw=1500, maxh=900, seed=11,
                                          extra=lambda img, g, t, sh: big_text(img, "REKO DIQ", W / 2, 470, 270, g, tt, fg=WHITE, slam=True, seed=81)))
    P.fx("music/hit.wav", tt, -2)
    P.total = P.end_vo + 2.4

    P.cue("music/L_cold.wav", P.S(2), P.S(3), 0.35)
    P.cue("music/L_cold.wav", P.S(4), P.total, 0.35, offset=20)
    return P
