"""Chapters 1–8 and Close. One build_cNN() per chapter; each is rendered independently."""
from chapters.common import *  # noqa
import charts as CH


def pst(name, fallback):
    return name if (ROOT / f"posters/{name}.png").exists() else fallback


def seg(P, n, fn, cards=(), t0=None, t1=None):
    a = P.S(n) - 0.05 if t0 is None else t0
    b = t1 if t1 is not None else (P.S(n + 1) - 0.05 if n < len(P.order) else P.total)
    P.add(a, b, fn, cards=list(cards))
    return b


def K(P, n, text, word, style="ink", nth=0, **kw):
    return C(text, P.W(n, word, nth), style, **kw)


def bars(img, g, rows, x0=360, base=820, w=200, scale=5.0):
    """Vertical bars [(label, value, colour, at)] growing from a baseline."""
    d = ImageDraw.Draw(img)
    for i, (lab, v, col, at) in enumerate(rows):
        p = ease_out((g - at) / 0.8)
        if p <= 0:
            continue
        x = x0 + i * (w + 120)
        h = v * scale * p
        d.rectangle((x + 10, base - h + 12, x + w + 10, base + 12), fill=(40, 30, 20, 70))
        d.rectangle((x, base - h, x + w, base), fill=col + (255,), outline=INK + (255,), width=4)
        d.text((x + w / 2, base + 24), lab, font=font("anton", 40), fill=INK + (255,), anchor="mt")


def gap_chart(img, g, t0, tgap, x0=260, x1=1500, y0=860, y1=300):
    d = ImageDraw.Draw(img)
    ax = ease_out((g - t0) / 0.4)
    d.line([(x0, y0), (x0 + (x1 - x0) * ax, y0)], fill=INK + (255,), width=4)
    d.line([(x0, y0), (x0, y0 - (y0 - y1) * ax)], fill=INK + (255,), width=4)
    for yr in (2025, 2030, 2035):
        d.text((x0 + (x1 - x0) * (yr - 2025) / 10, y0 + 20), str(yr), font=font("interb", 28), fill=INK + (255,), anchor="mt")
    dem = lambda u: 0.40 + 0.55 * u
    sup = lambda u: dem(u) * (1 - 0.3 * u ** 1.6)
    p = ease_io((g - t0 - 0.5) / 2.2)
    pd = [(x0 + (x1 - x0) * i / 60, y0 - (y0 - y1) * dem(i / 60)) for i in range(int(60 * p) + 1)]
    ps = [(x0 + (x1 - x0) * i / 60, y0 - (y0 - y1) * sup(i / 60)) for i in range(int(60 * p) + 1)]
    if len(pd) > 1:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).polygon(pd + ps[::-1], fill=RED + (int(110 * clamp((g - tgap) / 0.5)),))
        img.alpha_composite(gl)
        d.line(ps, fill=(130, 128, 122, 255), width=8, joint="curve")
        d.line(pd, fill=COPPER + (255,), width=10, joint="curve")
    if p > 0.95:
        d.text((x1 + 20, pd[-1][1]), "Demand", font=font("interb", 34), fill=COPPER + (255,), anchor="lm")
        d.text((x1 + 20, ps[-1][1]), "Mine supply", font=font("interb", 34), fill=(110, 108, 102, 255), anchor="lm")


def strike_list(img, g, items, x, y, ats, strike_ats, size=46, gapy=70, col=(120, 120, 120)):
    d = ImageDraw.Draw(img)
    f = font("anton", size)
    for i, (txt, at, st) in enumerate(zip(items, ats, strike_ats)):
        if g < at:
            continue
        yy = y + i * gapy
        d.text((x, yy), txt, font=f, fill=INK + (int(255 * clamp((g - at) / 0.2)),), anchor="lm")
        if st is not None and g > st:
            p = ease_out((g - st) / 0.3)
            d.line([(x - 10, yy), (x - 10 + (f.getlength(txt) + 20) * p, yy)], fill=col + (255,), width=8)


QUOTE_2APR = (279, 665, 1142, 695)


# ================================================================== CHAPTER 1: THE DEAD VOLCANO
def build_c01():
    P = Part("c01")
    P.bg = OCHRE
    # 1 route Quetta → Nok Kundi, rulers
    def r1(img, g, t, sh, v):
        route(img, v, N40, g, P.W(1, "drive"), dur=2.2, col=COPPER)
        dot(img, v, QUETTA, g, P.W(1, "quetta"), "QUETTA", col=INK, side=1)
        dot(img, v, NOKKUNDI, g, P.W(1, "nok"), "NOK KUNDI", col=INK, side=-1)
        dot(img, v, REKO, g, P.W(1, "north"), None, col=RED)
        ruler(img, v, REKO, AFG_PT, g, P.W(1, "35"), "35 KM TO AFGHANISTAN")
        ruler(img, v, REKO, IRN_PT, g, P.W(1, "55"), "55 KM TO IRAN", col=WHITE)
        map_name(img, "Iran", v, 60.6, 28.0, g, sh["start"], size=50)
        map_name(img, "Afghanistan", v, 64.0, 30.6, g, sh["start"], size=50)
    seg(P, 1, T_map([(0, V_BAL), (P.W(1, "north") - P.S(1), V_BAL), (P.W(1, "35") - P.S(1) + 0.3, V_SITE)], bal=BAL_ON, extra=r1, insetmap=True),
        [K(P, 1, "QUETTA → NOK KUNDI", "drive", "yellow", xy=(W / 2, 150))])
    P.fx("sfx/pencil.wav", P.W(1, "drive"), 12)
    # 2 sandy peak
    seg(P, 2, T_photo("photos/barrick_aerial_site.jpg", bg=OCHRE, z=(1.05, 1.15), maxw=1500, maxh=880, seed=12),
        [K(P, 2, 'REKO DIQ = "SANDY PEAK"', "means", "copper", xy=(W / 2, 140), size=70), K(P, 2, "WHAT IS LEFT OF A VOLCANO", "volcano", "ink", xy=(W / 2, 860))])
    # 3 Tethys, porphyry cross-section
    xs = pst("L02_crosssection", "p02_cutaway")
    seg(P, 3, T_poster(xs, DEEP, "push_in", seed=13),
        [K(P, 3, "THE TETHYS OCEAN CLOSES", "tethys", "yellow", xy=(W / 2, 140)), K(P, 3, "MAGMA RISES", "magma", "red", xy=(460, 760)),
         K(P, 3, "PORPHYRY: COPPER FROZEN IN ROCK", "porphyry", "copper", xy=(1340, 860), size=50)])
    # 4 belt
    def r4(img, g, t, sh, v):
        draw_band(img, v, BELT, ease_io((g - P.W(4, "balkans") + 0.3) / 2.6), width_deg=2.0)
        for i, (pt, w_) in enumerate(zip(BELT_MINES, ["balkans", "turkey", "iran", "pakistan"])):
            dot(img, v, pt, g, P.W(4, w_) + 0.2, None, col=YELLOW)
        dot(img, v, REKO, g, P.W(4, "pakistan") + 0.4, "REKO DIQ", col=RED)
        for nm, lon, lat, w_ in [("Balkans", 21.5, 46.5, "balkans"), ("Turkey", 33.5, 37.2, "turkey"), ("Iran", 53.5, 33.6, "iran"), ("Pakistan", 69.0, 26.2, "pakistan")]:
            map_name(img, nm, v, lon, lat, g, P.W(4, w_), size=50)
    seg(P, 4, T_map([(0, V_BAL), (1.4, V_EURASIA)], bal=BAL_ON, extra=r4),
        [K(P, 4, "THE TETHYAN BELT", "belt", "copper", xy=(W / 2, 140), size=72), K(P, 4, "TETHYAN COPPER", "tethyan", "ink", xy=(1500, 860))])
    # 5 erosion, <50 m
    def ruler50(img, g, t, sh):
        at = P.W(5, "fifty") if P.W(5, "fifty") > P.S(5) else P.W(5, "50")
        if g > at - 0.2:
            d = ImageDraw.Draw(img)
            p = ease_out((g - at + 0.2) / 0.6)
            d.line([(1640, 360), (1640, 360 + 260 * p)], fill=YELLOW + (255,), width=10)
            for yy in (360, 360 + 260 * p):
                d.line([(1610, yy), (1670, yy)], fill=YELLOW + (255,), width=10)
    seg(P, 5, T_poster(pst("L03_eroded", "p04_peak"), SAND, "pull_out", seed=15, extra=ruler50),
        [K(P, 5, "EROSION", "erosion", "ink", xy=(W / 2, 140)), K(P, 5, "LESS THAN 50 M OF COVER", "barren", "yellow", xy=(1400, 860))])
    # 6 low grade cube
    def grade(img, g, t, sh):
        CH.panel(img, 140, 220, 1780, 900)
        CH.stat(img, g, P.W(6, "half"), 470, 480, "pick", 0.48, "COPPER IN THE ORE", col=COPPER, dec=2, suffix="%", size=130)
        CH.stat(img, g, P.W(6, "quarter"), 470, 790, "coins", 0.26, "GRAMS OF GOLD PER TONNE", col=CH.GOLD, dec=2, suffix=" g/t", size=90)
        CH.hbars(img, g, 820, 430, 760, [("ROCK", 1000, (120, 116, 108), "mountain", P.W(6, "crush"), "1,000 KG"),
                                         ("COPPER", 4.8, COPPER, "pick", P.W(6, "copper", 1), "4.8 KG")], 1000, rowh=200, unit=" kg")
    seg(P, 6, T_fill((226, 214, 190), extra=grade), [K(P, 6, "LOW GRADE", "catch", "red", xy=(W / 2, 150), size=70)])
    # 7 size: 3 billion tonnes, 15 porphyries
    tfif = P.W(7, "fifteen") if P.W(7, "fifteen") > P.S(7) else P.W(7, "15")
    seg(P, 7, T_doc("docs/barrick_technical_report__figure_7_2_p57.png", bg=DEEP, crop=(80, 150, 1360, 1050), width=1200, rot=-2),
        [K(P, 7, "3 BILLION TONNES OF ORE", "three", "copper", xy=(W / 2, 140), size=70), C("15 PORPHYRIES · 5 IN THE PLAN", tfif, "yellow", xy=(W / 2, 880), size=58)])
    P.fx("sfx/pop.wav", tfif, 2)
    # 8 Tanjeel pH
    def ph(img, g, t, sh):
        at = P.W(8, "vinegar")
        cols = [(200, 40, 40), (230, 90, 40), (240, 150, 40), (240, 210, 60), (170, 210, 80), (90, 180, 90), (60, 150, 160), (60, 90, 170)]
        d = ImageDraw.Draw(img)
        for i, c in enumerate(cols):
            d.rectangle((1180 + i * 70, 300, 1240 + i * 70, 640), fill=c + (255,), outline=INK + (255,), width=3)
        if g > at:
            x = 1180 + 2.5 * 70 * ease_out((g - at) / 0.8) + 0
            d.polygon([(x + 30, 660), (x + 10, 700), (x + 50, 700)], fill=INK + (255,))
    seg(P, 8, T_doc("docs/esia_hydrogeology__ph_p31.png", bg=TEAL, crop=(80, 150, 1360, 1300), width=820, cx=560, rot=-3, extra=ph),
        [K(P, 8, "TANJEEL: STILL FORMING", "tanjeel", "ink", xy=(1460, 180)), K(P, 8, "GROUNDWATER pH 3.5", "vinegar", "red", xy=(1460, 800), size=64)])
    # 9 1978
    seg(P, 9, T_poster("p01_desert", SAND, "pull_out", seed=19),
        [K(P, 9, "1978: FIRST SIGNS (DISPUTED)", "1978", "ink", xy=(W / 2, 150), size=64), K(P, 9, "NO MONEY TO DRILL A DESERT", "money", "yellow", xy=(W / 2, 860))])
    P.cue("music/L_curious.wav", P.CARD, P.total, 0.30)
    return P


# ================================================================== CHAPTER 2: THE DEAL
def build_c02():
    P = Part("c02")
    P.bg = TEAL
    P.timeline = dict(start=1990, past=[])
    P.event(P.W(1, "1993"), 1993, "CHEJVA SIGNED")
    seg(P, 1, T_poster("p05_contract", TEAL, "push_in", seed=21,
                       extra=lambda img, g, t, sh: draw_circle_mark(img, 640, 300, 230, 70, g, P.W(1, "july"), color=RED, seed=3)),
        [K(P, 1, "23 JULY 1993 · QUETTA", "july", "ink", xy=(1400, 260)), K(P, 1, "CHAGAI HILLS EXPLORATION JOINT VENTURE AGREEMENT", "chagai", "yellow", xy=(W / 2, 860), size=44)])
    P.fx("sfx/stamp.wav", P.W(1, "july"), -4)
    seg(P, 2, T_fill((226, 214, 190), extra=lambda img, g, t, sh: stamp(img, "CARETAKER", W / 2, 480, g, P.W(2, "caretaker"), col=RED, size=190, rot=-6)),
        [K(P, 2, "AN INTERIM ADMINISTRATION", "interim", "ink", xy=(W / 2, 760)), K(P, 2, "BETWEEN ELECTIONS", "elections", "yellow", xy=(W / 2, 860))])
    P.fx("sfx/stamp_heavy.wav", P.W(2, "caretaker"), -4)
    seg(P, 3, T_fill(None, extra=lambda img, g, t, sh: (CH.donut(img, g, 700, 580, 290, [(75, INK, "BHP 75%", "building-factory", P.W(3, "seventy")),
                                                                                          (25, COPPER, "BALOCHISTAN 25%", "flag", P.W(3, "twenty"))], centre="1993", sub="OWNERSHIP"),
                                                         CH.stat(img, g, P.W(3, "royalty"), 1500, 640, "receipt", 2, "ROYALTY", col=CH.GOLD, suffix="%", size=140))),
        [K(P, 3, "THE TERMS", "terms", "ink", xy=(1420, 330), pop=True, size=80), K(P, 3, "BALOCHISTAN PAYS ITS SHARE OF COSTS", "costs", "red", xy=(1450, 880), size=44)])
    seg(P, 4, T_map([(0, V_BAL), (2, V_CHG)], bal=BAL_ON, extra=lambda img, g, t, sh, v: None),
        [K(P, 4, "3.3 MILLION ACRES", "million", "copper", xy=(W / 2, 150), size=72), K(P, 4, "LARGER THAN QATAR", "qatar", "yellow", xy=(W / 2, 860), size=64)])
    def rules(img, g, t, sh):
        items = [f"RULE {i}" for i in range(1, 14)]
        at0 = P.W(5, "relaxed")
        for i, it in enumerate(items):
            x, y = 360 + (i % 5) * 300, 380 + (i // 5) * 140
            big_text(img, it, x, y, 54, g, at0 - 1.2, fg=INK, bg=WHITE, seed=40 + i)
            if g > at0 + i * 0.12:
                p = ease_out((g - at0 - i * 0.12) / 0.2)
                ImageDraw.Draw(img).line([(x - 110, y), (x - 110 + 220 * p, y)], fill=RED + (255,), width=10)
    seg(P, 5, T_fill(YELLOW, extra=rules), [K(P, 5, "13 RULES RELAXED", "thirteen", "red", xy=(W / 2, 170), slam=True, size=110), K(P, 5, "REMEMBER THAT NUMBER", "remember", "ink", xy=(W / 2, 860))])
    P.event(P.W(6, "2000"), 2000, "BHP STEPS BACK")
    seg(P, 6, T_poster("p05_folder", COPPER, "pan", seed=26),
        [K(P, 6, "1996–97: BHP DRILLS", "drills", "ink", xy=(500, 160)), K(P, 6, "PRICES LOW", "prices", "red", xy=(1500, 300)), K(P, 6, "2000: BHP STEPS BACK", "2000", "yellow", xy=(W / 2, 860), size=60)])
    P.event(P.W(7, "2006"), 2006, "ANTOFAGASTA + BARRICK")
    seg(P, 7, T_poster("p11_copper", YELLOW, "push_in", seed=27),
        [K(P, 7, "COPPER TAKES OFF", "takes", "copper", xy=(W / 2, 150), size=70), K(P, 7, "2006: ANTOFAGASTA BUYS TETHYAN", "antofagasta", "ink", xy=(560, 760)),
         K(P, 7, "BARRICK PAYS ~$115M FOR 50%", "115", "red", xy=(1360, 870), size=56)])
    seg(P, 8, T_fill(None, extra=lambda img, g, t, sh: CH.donut(img, g, W / 2, 560, 280, [(37.5, CH.BLUE, "ANTOFAGASTA 37.5%", "building-factory", P.W(8, "antofagasta")),
                                                                                     (37.5, INK, "BARRICK 37.5%", "pick", P.W(8, "barrick")),
                                                                                     (25, COPPER, "BALOCHISTAN 25%", "flag", P.W(8, "balochistan"))], centre="2006", sub="OWNERSHIP")),
        [K(P, 8, "A CONTRACT SIGNED BY A GOVERNMENT NOBODY ELECTED", "nobody", "yellow", xy=(W / 2, 920), size=46)])
    P.event(P.W(9, "same"), 2006, "THE PETITION")
    seg(P, 9, T_headline("profit_2022_02_20", seed=29),
        [K(P, 9, "MAULANA ABDUL HAQ BALOCH", "maulana", "ink", xy=(500, 880), size=48), K(P, 9, "PETITION DISMISSED · APPEAL FILED", "appeals", "red", xy=(1420, 880), size=44)])
    def spend(img, g, t, sh):
        CH.panel(img, 160, 260, 1760, 760)
        CH.hbars(img, g, 220, 380, 1460, [("SPENT", 220, COPPER, "pick", P.W(10, "200"), "$220M+"), ("MINE PLAN", 3300, INK, "building-factory", P.W(10, "plan"), "$3.3B")],
                 3300, rowh=190, prefix="$", unit="M")
    seg(P, 10, T_poster("p06_camp", SAND, "pan", seed=30, extra=spend),
        [
         K(P, 10, "ONE MORE PIECE OF PAPER: THE MINING LEASE", "lease", "yellow", xy=(W / 2, 870), size=48)])
    P.cue("music/L_invest.wav", P.CARD, P.total, 0.28)
    return P


# ================================================================== CHAPTER 3: THE REFUSAL
def build_c03():
    P = Part("c03")
    P.bg = (90, 80, 70)
    P.timeline = dict(start=2006, past=[1993, 2000, 2006])
    P.event(P.W(1, "24") if P.W(1, "24") > P.S(1) else P.W(1, "december"), 2009, "SCRAP THE DEAL")
    seg(P, 1, T_headline("herald_magic_mountains", seed=31),
        [K(P, 1, "NAWAB ASLAM RAISANI · CHIEF MINISTER", "raisani", "ink", xy=(W / 2, 880), size=46), K(P, 1, "24 DEC 2009", "december", "red", xy=(1600, 160), stamp=True, size=80)])
    def q(img, g, t, sh):
        for i, (txt, w_) in enumerate([("WHY 75%?", "three"), ("WHY EXPORT IT RAW?", "ship"), ("WHY NOT US?", "ourselves")]):
            big_text(img, txt, W / 2, 330 + i * 180, 100, g, P.W(2, w_), fg=[WHITE, INK, WHITE][i], bg=[RED, YELLOW, INK][i], seed=60 + i)
    seg(P, 2, T_fill((226, 214, 190), extra=q))
    def face(img, g, t, sh):
        big_text(img, "COMPANY: $100 BILLION", 520, 520, 64, g, P.W(3, "company"), fg=WHITE, bg=INK, seed=71)
        big_text(img, "MUBARAKMAND: $240 BILLION", 1400, 520, 64, g, P.W(3, "worth"), fg=WHITE, bg=COPPER, seed=72)
    seg(P, 3, T_fill(DEEP, extra=face), [K(P, 3, "DR SAMAR MUBARAKMAND", "mubarakmand", "yellow", xy=(W / 2, 200), size=64), K(P, 3, "WE CAN MINE IT ALONE", "alone", "red", xy=(W / 2, 800))])
    P.event(P.W(4, "november"), 2011, "LEASE REJECTED")
    seg(P, 4, T_poster("p06_denied", None, "push_in", seed=34),
        [K(P, 4, "15 FEB 2011: LEASE APPLICATION", "february", "ink", xy=(1400, 200)), C("15 NOV 2011: REJECTED", P.W(4, "november"), "red", xy=(1400, 760), stamp=True, size=90)])
    P.fx("sfx/stamp_heavy.wav", P.W(4, "says"), -2)
    def split(img, g, t, sh):
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, W / 2, H), fill=INK + (255,))
        d.rectangle((W / 2, 0, W, H), fill=COPPER + (255,))
        big_text(img, "TETHYAN: ENTITLED", W / 4, H / 2, 80, g, P.W(5, "tethyan"), fg=WHITE, seed=81)
        big_text(img, "BALOCHISTAN: NOT GUARANTEED", 3 * W / 4, H / 2, 64, g, P.W(5, "balochistan"), fg=WHITE, seed=82)
    seg(P, 5, T_fill(None, extra=split))
    P.event(P.W(6, "january"), 2013, "DEAL VOID")
    seg(P, 6, T_poster(pst("p07_court_pk", "p07_court"), TEAL, "push_in", seed=36),
        [K(P, 6, "7 JAN 2013 · SUPREME COURT", "january", "ink", xy=(W / 2, 150), size=64), K(P, 6, "CHIEF JUSTICE IFTIKHAR CHAUDHRY", "chief", "yellow", xy=(W / 2, 870), size=50)])
    P.fx("sfx/gavel.wav", P.W(6, "january"), -2)
    def stat(img, g, t, sh):
        for i, (txt, w_) in enumerate([("MINERAL DEVELOPMENT ACT 1948", "1948"), ("MINING RULES 1970", "1970"), ("CONTRACT ACT 1872", "1872"), ("13 RULES: UNLAWFUL", "thirteen"), ("BHP → TETHYAN: VOID", "hand")]):
            slide_card(img, txt, 1420, 260 + i * 130, g, P.W(7, w_), side="R", seed=90 + i, kind="anton", size=48, fg=INK, bg=YELLOW)
    seg(P, 7, T_headline("caselaw_ewhc_2021", seed=37, photo=False, cx=700, extra=stat),
        [C("ILLEGAL AND VOID", P.W(7, "illegal"), "red", xy=(560, 820), stamp=True, size=120)])
    seg(P, 8, T_headline("thenews_reko_diq_matter", seed=38), [K(P, 8, "BALOCHISTAN GOES IT ALONE", "own", "copper", xy=(W / 2, 880), size=60)])
    seg(P, 9, T_headline("thenational_500bn", seed=39), [K(P, 9, "RAISANI'S CLAIM", "later", "red", xy=(1550, 160), size=56), K(P, 9, "REMOVED WITHIN WEEKS", "weeks", "ink", xy=(500, 880))])
    seg(P, 10, T_poster(pst("L08_signboard", "p01_desert"), SAND, "pull_out", seed=40), [K(P, 10, "NO MINE GETS BUILT", "mine", "ink", xy=(W / 2, 160), size=70)])
    P.cue("music/L_invest.wav", P.CARD, P.total, 0.28, offset=40)
    return P


# ================================================================== CHAPTER 4: THE BILL
def build_c04():
    P = Part("c04")
    P.bg = NAVY
    P.timeline = dict(start=2013, past=[1993, 2006, 2011, 2013])
    P.event(P.W(1, "1998"), 1998, "TREATY WITH AUSTRALIA")
    seg(P, 1, T_poster(pst("L11_treaty", "p05_contract"), NAVY, "push_in", seed=41), [K(P, 1, "1998: AUSTRALIA–PAKISTAN INVESTMENT TREATY", "treaty", "yellow", xy=(W / 2, 170), size=52)])
    seg(P, 2, T_poster("p08_hall", NAVY, "push_in", seed=42, extra=lambda img, g, t, sh: draw_arrow(img, (300, 860), (1200, 520), g, P.W(2, "skip"), color=YELLOW, bend=-0.3, seed=4)),
        [K(P, 2, "BILATERAL INVESTMENT TREATY", "bilateral", "ink", xy=(W / 2, 170)), K(P, 2, "INVESTOR CAN SUE THE STATE", "international", "red", xy=(1400, 860), size=56)])
    def r3(img, g, t, sh, v):
        dot(img, v, QUETTA, g, P.S(3) + 0.2, "QUETTA", col=INK)
        route(img, v, [QUETTA, WASHINGTON], g, P.W(3, "icsid"), dur=1.0, col=RED, width=6)
        dot(img, v, WASHINGTON, g, P.W(3, "washington"), "ICSID · WASHINGTON", col=RED, side=-1)
        route(img, v, [QUETTA, PARIS], g, P.W(3, "chamber"), dur=1.0, col=YELLOW, width=6)
        dot(img, v, PARIS, g, P.W(3, "chamber") + 0.6, "ICC", col=YELLOW, side=-1)
    seg(P, 3, T_map([(0, (20, 32, 150))], extra=r3, dark=0.3), [K(P, 3, "TETHYAN COPPER COMPANY PTY LIMITED", "australia", "ink", xy=(W / 2, 170), size=50), K(P, 3, "ICSID CASE NO. ARB/12/1", "icsid", "yellow", xy=(W / 2, 870))])
    seg(P, 4, T_fill((226, 214, 190), extra=lambda img, g, t, sh: strike_list(img, g, [f"ALLEGATION {i}" for i in range(1, 9)], 700, 320, [P.W(4, "dozen")] * 8,
                                                                               [P.W(4, "rejects") + i * 0.12 for i in range(8)])),
        [K(P, 4, "CORRUPTION DEFENCE", "corruption", "ink", xy=(W / 2, 200), size=70), K(P, 4, "REJECTED: NO EVIDENCE", "rejects", "red", xy=(W / 2, 900), size=60)])
    P.event(P.W(5, "2017"), 2017, "PAKISTAN LIABLE")
    seg(P, 5, T_fill(NAVY, extra=lambda img, g, t, sh: [big_text(img, w_.upper(), W / 2, 300 + i * 170, 110, g, P.W(5, w_), fg=WHITE, slam=True, seed=50 + i) for i, w_ in enumerate(["broke", "legitimate", "unlawful"])]),
        [K(P, 5, "2017", "2017", "yellow", xy=(W / 2, 140), size=70)])
    seg(P, 6, T_fill((226, 214, 190), extra=lambda img, g, t, sh: CH.vbars(img, g, 700, 800, [("SPENT", 0.22, TEAL, "pick", P.W(6, "spent"), "~$0.22B"),
                                                                                             ("AWARDED", 4.087, RED, "gavel", P.W(6, "worth"), "$4.087B")], 4.087, height=380, bw=220, gap=200, prefix="$", unit="B", dec=2)),
        [K(P, 6, "HOW MUCH?", "much", "ink", xy=(W / 2, 170), pop=True, size=90), K(P, 6, "AWARDED: FAIR MARKET VALUE", "worth", "red", xy=(420, 600), size=46)])
    P.event(P.W(7, "july"), 2019, "$5.9B AWARD")
    P.gap(P.b(7), 1.0)
    seg(P, 7, T_fill(RED, burst=(W / 2, H / 2), conf=burst(47, P.W(7, "total"), n=70),
                     extra=lambda img, g, t, sh: CH.stacked(img, g, 260, 520, 1400, 150, [(4.087, INK, "DAMAGES", P.W(7, "damages")), (1.7, (120, 30, 25), "INTEREST", P.W(7, "interest"))],
                                                            6.0, total=5.787, total_at=P.W(7, "total"), unit="B", dec=2)),
        [K(P, 7, "12 JULY 2019", "july", "white", xy=(W / 2, 200), size=64), K(P, 7, "NEARLY $6 BILLION", "total", "white", xy=(W / 2, 880), slam=True, size=110)])
    P.fx("sfx/boom.wav", P.W(7, "total"), -2)
    def gdp(img, g, t, sh):
        d = ImageDraw.Draw(img)
        cx, cy, r = 600, 540, 280
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=TEAL + (255,))
        p = ease_out((g - P.W(8, "two")) / 0.6)
        off = 140 * p
        d.pieslice((cx - r + 0.12 * off, cy - r - off, cx + r + 0.12 * off, cy + r - off), -90, -82.8, fill=COPPER + (255,), outline=YELLOW, width=6)
    seg(P, 8, T_fill(None, extra=lambda img, g, t, sh: (CH.donut(img, g, 600, 560, 300, [(98, TEAL, "", None, P.S(8)), (2, RED, "~2% OF GDP", "chart-pie", P.W(8, "two"))],
                                                                  centre="GDP", sub="PAKISTAN'S ECONOMY"),
                                                         CH.stat(img, g, P.W(8, "700"), 1450, 760, "clock", 700000, "INTEREST PER DAY (PRESS ACCOUNT)", col=RED, prefix="~$", size=110))),
        [K(P, 8, "≈ THE SIZE OF THE IMF BAILOUT", "imf", "ink", xy=(1450, 300), size=48)])
    P.event(P.W(9, "december"), 2020, "PIA ASSETS FROZEN")
    seg(P, 9, T_headline("dawn_2021_bvi_unfreeze", seed=49),
        [K(P, 9, "ROOSEVELT HOTEL · NEW YORK", "roosevelt", "ink", xy=(500, 880), size=46), K(P, 9, "SCRIBE HOTEL · PARIS", "scribe", "ink", xy=(1420, 880), size=46),
         C("FROZEN", P.W(9, "freezes"), "red", xy=(1500, 200), stamp=True, size=120)])
    P.event(P.W(10, "2021"), 2021, "FREEZE LIFTED")
    seg(P, 10, T_headline("tribune_2022_11b", seed=50), [K(P, 10, "AWARD INTACT", "award", "red", xy=(1550, 180), size=60), K(P, 10, "EXPOSURE ~$11B (PAKISTANI OFFICIALS)", "eleven", "ink", xy=(W / 2, 880), size=46)])
    seg(P, 11, T_poster(pst("L09_phone", "p05_contract"), NAVY, "push_in", seed=51), [K(P, 11, "FIGHT, OR PICK UP THE PHONE", "phone", "yellow", xy=(W / 2, 160), size=64)])
    P.fx("sfx/phone.wav", P.W(11, "phone"), -4)
    P.cue("music/L_thriller.wav", P.CARD, P.W(7, "total") - 0.05, 0.30)
    P.cue("music/L_lowpulse.wav", P.S(8), P.total, 0.30)
    return P


# ================================================================== CHAPTER 5: THE RESET
def build_c05():
    P = Part("c05")
    P.bg = (196, 160, 85)
    P.timeline = dict(start=2021, past=[1993, 2006, 2011, 2013, 2019])
    P.event(P.W(1, "march"), 2022, "FRAMEWORK AGREED")
    seg(P, 1, T_poster("p09_handshake", TEAL, "push_in", seed=52), [K(P, 1, "MARCH 2022: FRAMEWORK AGREED", "march", "copper", xy=(W / 2, 170), size=64)])
    seg(P, 2, T_headline("dawn_2022_12_12_antofagasta", seed=53), [K(P, 2, "ASKED $1.75B", "asks", "ink", xy=(1550, 180), size=56), C("ANTOFAGASTA: OUT FOR $900M", P.W(2, "900"), "red", xy=(W / 2, 880), size=60)])
    seg(P, 3, T_photo("photos/barrick_press_card.jpg", bg=NAVY, maxw=1100, maxh=620, seed=54),
        [K(P, 3, "GIVES UP ITS HALF OF THE AWARD", "gives", "ink", xy=(W / 2, 160)), K(P, 3, "BARRICK: 50%, OPERATOR", "running", "copper", xy=(W / 2, 880), size=64)])
    seg(P, 4, T_fill(None, extra=lambda img, g, t, sh: CH.donut(img, g, W / 2, 540, 300, [(50, INK, "BARRICK 50%", "pick", P.W(4, "barrick")),
                                                                                       (25, CH.BLUE, "FEDERAL 25% (OGDCL · PPL · GHPL)", "building-bank", P.W(4, "three")),
                                                                                       (15, COPPER, "BALOCHISTAN 15% FUNDED", "flag", P.W(4, "fifteen")),
                                                                                       (10, CH.GOLD, "BALOCHISTAN 10% FREE", "flag", P.W(4, "ten"))], centre="2022", sub="OWNERSHIP")),
        [K(P, 4, "THE PROVINCE PUTS IN NO CASH", "cash", "yellow", xy=(W / 2, 960), size=48)])
    def roy(img, g, t, sh):
        CH.vbars(img, g, 230, 820, [("1993", 2, (120, 116, 108), "receipt", P.S(5) + 0.3, "2%"), ("2022", 5, COPPER, "receipt", P.W(5, "five"), "5%")], 5, height=330, bw=170, gap=90, unit="%")
        CH.vbars(img, g, 1000, 820, [("YEAR 1", 5, CH.GOLD, "coins", P.W(5, "million"), "$5M"), ("YEAR 2", 7.5, CH.GOLD, "coins", P.W(5, "seven"), "$7.5M"),
                                     ("THEN", 10, CH.GOLD, "coins", P.W(5, "ten"), "$10M/YR")], 10, height=330, bw=170, gap=80, prefix="$", unit="M", dec=1)
    seg(P, 5, T_fill((226, 214, 190), extra=roy, conf=burst(55, P.W(5, "five"), 500, 400, 40)),
        [K(P, 5, "ROYALTY", "royalty", "copper", xy=(420, 170), size=64), K(P, 5, "ADVANCE PAYMENTS", "advance", "ink", xy=(1340, 170), size=60)])
    P.fx("sfx/coins.wav", P.W(5, "million"), 2)
    P.fx("sfx/coins.wav", P.W(5, "seven"), 2)
    P.fx("sfx/coins.wav", P.W(5, "ten"), 2)
    seg(P, 6, T_poster(pst("p07_court_pk", "p07_court"), TEAL, "push_in", seed=56),
        [K(P, 6, "PRESIDENTIAL REFERENCE NO. 2 OF 2022", "president", "ink", xy=(W / 2, 160), size=54), K(P, 6, "IS THIS LEGAL?", "legal", "yellow", xy=(500, 870), size=60),
         K(P, 6, "IS A NEW LAW CONSTITUTIONAL?", "constitutional", "yellow", xy=(1400, 870), size=50)])
    P.event(P.W(7, "december"), 2022, "VALID")
    seg(P, 7, T_fill(DEEP, extra=lambda img, g, t, sh: stamp(img, "VALID", W / 2, 560, g, P.W(7, "yes", 1), col=(80, 170, 90), size=220, rot=-6)),
        [K(P, 7, "5 JUDGES · CJ UMAR ATA BANDIAL", "five", "yellow", xy=(W / 2, 200), size=56), K(P, 7, "9 DEC 2022", "december", "white", xy=(W / 2, 860), size=64)])
    P.fx("sfx/stamp_heavy.wav", P.W(7, "yes", 1), -2)
    seg(P, 8, T_poster(pst("L10_padlock", "p05_contract"), YELLOW, "push_in", seed=58),
        [K(P, 8, "FOREIGN INVESTMENT PROMOTION AND PROTECTION ACT", "foreign", "ink", xy=(W / 2, 160), size=46), K(P, 8, "$500M+ INVESTMENTS", "500", "white", xy=(500, 860)),
         K(P, 8, "LOCKED UNTIL 15 DEC 2052", "2052", "red", xy=(1400, 860), size=60)])
    P.fx("sfx/lock.wav", P.W(8, "locked"), 0)
    seg(P, 9, T_headline("tribune_2022_mengal", seed=59,
                         extra=lambda img, g, t, sh: quote_card(img, "an attempt to usurp the rights of the people of Balochistan", "Akhtar Mengal, BNP-M, Dec 2022", g, P.W(9, "attempt"), cy=620, width=1400)))
    seg(P, 10, T_fill(None, extra=lambda img, g, t, sh: (CH.donut(img, g, 520, 520, 230, [(75, INK, "", None, P.S(10) + 0.3), (25, COPPER, "25% · PAYS COSTS", "flag", P.W(10, "twenty"))], centre="1993", labels=True),
                                                          CH.donut(img, g, 1340, 520, 230, [(75, (120, 116, 108), "", None, P.W(10, "again") - 0.4), (25, COPPER, "25% · FREE", "flag", P.W(10, "again"))], centre="2022"))),
        [K(P, 10, "ROYALTY: 2% → 5%  (2.5× BIGGER)", "royalty", "yellow", xy=(W / 2, 880), size=56)])
    P.cue("music/L_warm.wav", P.CARD, P.total, 0.28)
    return P


# ================================================================== CHAPTER 6: THE COPPER RACE
def build_c06():
    P = Part("c06")
    P.bg = COPPER
    seg(P, 1, T_poster("p11_copper", COPPER, "push_in", seed=61, conf=Confetti(61, 20)))
    seg(P, 2, T_fill(None, extra=lambda img, g, t, sh: gap_chart(img, g, sh["start"], P.W(2, "thirty") if P.W(2, "thirty") > P.S(2) else P.W(2, "30"))),
        [K(P, 2, "EVERY MOTOR · LINE · CHARGER", "every", "ink", xy=(700, 170), size=52), K(P, 2, "30% SHORTFALL BY 2035", "short", "red", xy=(1100, 380), size=64)])
    def icons(img, g, t, sh):
        for i, (txt, w_) in enumerate([("LOWER GRADES", "grades"), ("HIGHER COSTS", "costs"), ("FEW DISCOVERIES", "discoveries"), ("LONG LEAD TIMES", "years")]):
            slide_card(img, txt, 300 + i * 440, 540, g, P.W(3, w_), side="B", seed=110 + i, kind="anton", size=56, fg=WHITE, bg=[RED, INK, TEAL, COPPER][i])
    seg(P, 3, T_fill(YELLOW, extra=icons), [K(P, 3, "WHY IT'S STUBBORN", "stubborn", "ink", xy=(W / 2, 200), size=70)])
    def flow(img, g, t, sh):
        steps = ["PIT", "CRUSHER", "MILL", "FLOTATION", "CONCENTRATE"]
        for i, s_ in enumerate(steps):
            slide_card(img, s_, 220 + i * 370, 320, g, sh["start"] + 0.3 + i * 0.35, side="T", seed=120 + i, kind="anton", size=46, fg=WHITE, bg=INK)
            if i:
                draw_arrow(img, (220 + (i - 1) * 370 + 120, 320), (220 + i * 370 - 120, 320), g, sh["start"] + 0.5 + i * 0.35, color=COPPER, bend=0.1, head=26, seed=i)
        CH.vbars(img, g, 700, 880, [("PHASE 1", 45, COPPER, "building-factory", P.W(4, "45"), "45 MTPA"), ("PHASE 2", 90, RED, "building-factory", P.W(4, "doubles"), "90 MTPA")],
                 90, height=300, bw=200, gap=140, unit="")
    seg(P, 4, T_fill((226, 214, 190), extra=flow),
        [K(P, 4, "~200,000 T COPPER · ~250,000 OZ GOLD A YEAR", "200", "ink", xy=(W / 2, 470), size=44)])
    seg(P, 5, T_photo("news/miningcom_manara__photo.jpeg", bg=COPPER, maxw=1200, maxh=680, seed=65),
        [K(P, 5, "TOP 5 BY ORE THROUGHPUT", "five", "yellow", xy=(W / 2, 150), size=64), K(P, 5, "~$74B FREE CASH FLOW OVER 37 YEARS (BARRICK)", "74", "ink", xy=(W / 2, 880), size=44)])
    P.timeline = dict(start=2022, past=[1993, 2011, 2013, 2019, 2022])
    P.event(P.W(6, "april"), 2025, "FEASIBILITY + FLUOR")
    seg(P, 6, T_headline("miningweekly_2025_fluor", seed=66), [K(P, 6, "8–9 APRIL 2025 · PAKISTAN MINERALS INVESTMENT FORUM", "april", "ink", xy=(W / 2, 880), size=40)])
    def lenders(img, g, t, sh):
        for i, (nm, w_, col) in enumerate([("IFC  $700M", "700", TEAL), ("ADB  $300M", "300", COPPER)]):
            slide_card(img, nm, 1450, 700 - i * 160, g, P.W(7, w_), seed=130 + i, kind="anton", size=70, fg=WHITE, bg=col)
    def lend(img, g, t, sh):
        CH.panel(img, 140, 330, 1780, 760)
        CH.stacked(img, g, 220, 480, 1480, 130, [(0.7, CH.BLUE, "IFC", P.W(7, "700")), (0.3, COPPER, "ADB", P.W(7, "300")), (1.25, RED, "US EXIM (DEC 2025)", P.W(7, "canada") + 0.8)],
                   3.5, total=3.5, total_at=P.W(7, "canada"), unit="B", dec=1, total_label="TARGET ~")
    seg(P, 7, T_fill((226, 214, 190), extra=lend), [K(P, 7, "THE MONEY ARRIVES", "money", "ink", xy=(W / 2, 170), size=70), K(P, 7, "CANADA · JAPAN · EUROPEAN EXPORT AGENCIES", "canada", "yellow", xy=(W / 2, 880), size=44)])
    P.event(P.W(8, "december"), 2025, "US EXIM $1.25B")
    seg(P, 8, T_photo("news/dawn_2025_12_11_exim__photo.webp", bg=NAVY, maxw=1200, maxh=680, seed=68),
        [K(P, 8, "US EXIM: $1.25B · DEC 2025", "1.25", "red", xy=(W / 2, 150), size=64), K(P, 8, "UP TO $2B OF US MINING EQUIPMENT", "equipment", "ink", xy=(W / 2, 880), size=52)])
    def caps3(img, g, t, sh, v):
        for pt, nm, w_ in [(WASHINGTON, "WASHINGTON", "washington"), (RIYADH, "RIYADH", "riyadh"), (BEIJING, "BEIJING", "beijing")]:
            route(img, v, [pt, REKO], g, P.W(9, w_), dur=0.9, col=RED, width=6)
            dot(img, v, pt, g, P.W(9, w_), nm, col=RED, side=(-1 if pt[0] < 0 else 1))
        dot(img, v, REKO, g, P.S(9), "REKO DIQ", col=COPPER)
    seg(P, 9, T_map([(0, (30, 32, 170))], extra=caps3, dark=0.25),
        [K(P, 9, "MANARA: STAKE REPORTED (NOT CONFIRMED)", "manara", "yellow", xy=(W / 2, 160), size=46), K(P, 9, "CHINA RUNS SAINDAK NEXT DOOR", "saindak", "ink", xy=(W / 2, 880), size=50)])
    seg(P, 10, T_fill((226, 214, 190), extra=lambda img, g, t, sh: checklist(img, ["CONTRACT", "LAW", "COURT", "BUILDER", "FINANCE"], 760, 300, g,
                                                                             [P.W(10, w_) for w_ in ["contract", "law", "court", "builder", "money"]])),
        [K(P, 10, "BY THE END OF 2025", "end", "copper", xy=(W / 2, 170), size=64)])
    P.cue("music/L_bright.wav", P.CARD, P.total, 0.30)
    return P


# ================================================================== CHAPTER 7: THE GROUND
def build_c07():
    P = Part("c07")
    P.bg = SAND
    def clim(img, g, t, sh):
        CH.panel(img, 200, 300, 1720, 820)
        CH.stat(img, g, P.W(1, "35"), 560, 640, "droplet", 35, "MM OF RAIN A YEAR", col=CH.BLUE, prefix="<", size=130)
        CH.stat(img, g, P.W(1, "minus"), 1060, 640, "temperature", -9, "°C IN WINTER", col=TEAL, size=130)
        CH.stat(img, g, P.W(1, "forty"), 1480, 640, "temperature", 45, "°C IN SUMMER", col=RED, size=130)
    seg(P, 1, T_poster("p01_desert", SAND, "push_in", seed=71, extra=clim))
    def r2(img, g, t, sh, v):
        route(img, v, [BOREFIELD, REKO], g, P.W(2, "seventy") if P.W(2, "seventy") > P.S(2) else P.W(2, "70"), dur=1.2, col=TEAL, width=10)
        dot(img, v, BOREFIELD, g, P.W(2, "aquifer"), "BOREFIELD", col=TEAL, side=-1)
        dot(img, v, REKO, g, P.S(2), "MINE", col=RED)
    tun = P.W(2, "un")
    seg(P, 2, T_map([(0, V_SITE)], bal=BAL_ON, extra=r2), [K(P, 2, "70 KM PIPELINE", "kilometres", "yellow", xy=(W / 2, 160), size=64)], t1=tun - 0.1)
    seg(P, 2, T_doc("docs/un_experts_letter__page_1_p1.png", bg=DARK, crop=(60, 60, 1380, 1100), width=900, cx=560, rot=-3),
        [C("UN EXPERTS: RISK TO WATER SECURITY", tun, "red", xy=(1420, 360), size=48), C("COMPANY: NO DEPENDENT COMMUNITIES", P.W(2, "barrick") if P.W(2, "barrick") < tun else tun + 1, "white", xy=(1420, 560), size=44)],
        t0=tun - 0.1)
    seg(P, 3, T_poster(pst("L06_microgrid", "p11_pylons"), YELLOW, "pan", seed=73), [K(P, 3, "NO GRID", "grid", "red", xy=(500, 170), size=70), K(P, 3, "HYBRID MICROGRID", "solar", "ink", xy=(1400, 870), size=64)])
    def r4(img, g, t, sh, v):
        route(img, v, RAIL, g, P.W(4, "travel"), dur=3.5, col=COPPER, width=10)
        dot(img, v, NOKKUNDI, g, P.S(4), "NOK KUNDI", col=INK, side=-1)
        dot(img, v, PORTQASIM, g, P.W(4, "qasim"), "PORT QASIM", col=RED)
    seg(P, 4, T_map([(0, V_SOUTHPK)], bal=BAL_ON, extra=lambda img, g, t, sh, v: (r4(img, g, t, sh, v),
                                                                                   CH.stat(img, g, P.W(4, "travel"), 1560, 760, "train", 1350, "KM BY RAIL", col=COPPER, size=110, dur=3.5))))
    P.fx("sfx/train.wav", P.W(4, "travel"), -6)
    seg(P, 5, T_headline("bloom_2026_11_15_rail", seed=75, extra=lambda img, g, t, sh: [stamp(img, "DEFERRED", 1500, 280 + i * 160, g, P.W(5, "three") + i * 0.35, col=RED, size=70, rot=-8 + i * 5) for i in range(3)]),
        [K(P, 5, "$390M BRIDGE LOAN", "390", "copper", xy=(480, 880), size=60)])
    for i in range(3):
        P.fx("sfx/stamp.wav", P.W(5, "three") + i * 0.35, -4)
    def r6(img, g, t, sh, v):
        route(img, v, [REKO, (62.6, 27.4), GWADAR], g, P.W(6, "gwadar"), dur=1.0, col=RED, width=9, dashed=True)
        route(img, v, RAIL, g, P.S(6), dur=0.1, col=(80, 160, 90), width=9)
        dot(img, v, GWADAR, g, P.W(6, "gwadar"), "GWADAR", col=RED, side=-1)
        dot(img, v, PORTQASIM, g, P.S(6), "PORT QASIM", col=(80, 160, 90))
    seg(P, 6, T_map([(0, V_SOUTHPK)], bal=BAL_ON, extra=r6), [K(P, 6, "GWADAR: CLOSER, RISKIER", "riskier", "red", xy=(W / 2, 160), size=64)])
    seg(P, 7, T_poster("p12_pit", SAND, "pan", seed=77), [K(P, 7, "SAINDAK: CHINESE-OPERATED SINCE 2002", "saindak", "ink", xy=(W / 2, 160), size=54), K(P, 7, "WHAT DOES CHAGAI HAVE TO SHOW?", "show", "yellow", xy=(W / 2, 870), size=50)])
    def jobs(img, g, t, sh):
        CH.panel(img, 960, 160, 1820, 900)
        CH.donut(img, g, 1180, 480, 170, [(77, COPPER, "", None, P.W(8, "77")), (23, (190, 184, 172), "", None, P.W(8, "77"))], centre="77%", sub="STAFF FROM BALOCHISTAN", labels=False)
        CH.vbars(img, g, 1420, 720, [("BUILD", 7500, CH.GOLD, "hammer", P.W(8, "7"), "7,500"), ("RUNNING", 4000, CH.BLUE, "briefcase", P.W(8, "4"), "4,000")], 7500, height=380, bw=130, gap=60)
        text = "COMPANY FIGURES"
        CH.text(img, text, 1390, 870, 28, "interb", (110, 105, 98))
    seg(P, 8, T_photo("photos/barrick_community_children.jpg", bg=COPPER, cx=500, maxw=820, maxh=760, seed=78, extra=jobs))
    tb = P.W(9, "barrick")
    seg(P, 9, T_doc("docs/open_letter_csos__page_1_p1.png", bg=(70, 72, 74), crop=(60, 60, 1380, 1100), width=880, cx=560, rot=-3),
        [K(P, 9, "36 GROUPS: PAUSE THE FUNDING", "36", "red", xy=(1420, 300), size=52), K(P, 9, "CONSENT AS AN INDIGENOUS PEOPLE", "indigenous", "ink", xy=(1420, 480), size=44)], t1=tb - 0.1)
    seg(P, 9, T_headline("barrick_response_open_letter", seed=79, photo=False, cx=900),
        [C("BARRICK: CLAIMS UNSUBSTANTIATED", tb, "copper", xy=(W / 2, 760), size=56), K(P, 9, "2.5 YEARS OF IMPACT STUDY", "two", "ink", xy=(W / 2, 880), size=46)], t0=tb - 0.1)
    seg(P, 10, T_doc("docs/barrick_technical_report__table_1_4_p30.png", bg=DARK, crop=(80, 100, 1360, 1300), width=1150, cy=H / 2 + 40),
        [K(P, 10, "RISK AFTER MITIGATION: HIGH", "high", "red", xy=(W / 2, 150), size=60), K(P, 10, "TERRORISM · LOSS OF GOVERNMENT SUPPORT", "terrorism", "yellow", xy=(W / 2, 880), size=46)])
    P.cue("music/L_sparse.wav", P.CARD, P.total, 0.30)
    return P


# ================================================================== CHAPTER 8: THE STALL
def build_c08():
    P = Part("c08")
    P.bg = DARK
    P.timeline = dict(start=2025, past=[1993, 2011, 2013, 2019, 2022, 2025])
    P.event(P.W(1, "january"), 2026, "ATTACKS")
    def r1(img, g, t, sh, v):
        d = ImageDraw.Draw(img)
        for i, pt in enumerate([(66.9, 30.2), (62.4, 25.2), (65.2, 26.9), (68.1, 28.3), (64.4, 28.9), (67.0, 27.0)]):
            x, y = lonlat_xy(v, *pt)
            tt = sh["start"] + 0.5 + i * 0.5
            if g > tt:
                ph = ((g - tt) % 1.4) / 1.4
                rr = 12 + 60 * ph
                d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=RED + (int(255 * (1 - ph)),), width=5)
                d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=RED + (255,))
    seg(P, 1, T_map([(0, V_BAL)], bal=BAL_ON, dark=0.45, extra=r1), [K(P, 1, "29 JAN – 5 FEB 2026", "january", "red", xy=(W / 2, 170), size=64)])
    seg(P, 2, T_headline("brecorder_2026_02_06_review", seed=82),
        [K(P, 2, '5 FEB: "REVIEWING ALL ASPECTS"', "february", "ink", xy=(500, 880), size=48), K(P, 2, "7 FEB: SPECIAL SECURITY FORCE", "special", "red", xy=(1420, 880), size=48)])
    def r3(img, g, t, sh, v):
        ruler(img, v, REKO, IRN_PT, g, P.W(3, "55") if P.W(3, "55") > P.S(3) else P.W(3, "fifty"), "55 KM", col=RED)
        map_name(img, "Iran", v, 60.8, 28.6, g, P.S(3), size=56)
    seg(P, 3, T_map([(0, V_CHG), (2.0, V_SITE)], bal=BAL_ON, red_iran=0.6, extra=r3), [K(P, 3, "WAR: UNITED STATES AND IRAN", "war", "red", xy=(W / 2, 170), size=60)])
    P.event(P.W(4, "april"), 2026, "SLOWDOWN")
    seg(P, 4, T_doc("docs/barrick_statement_2apr2026__page_1_p1.png", bg=DARK, crop=(120, 80, 1330, 1100), width=1000, cx=700, rot=-3, hl=QUOTE_2APR, hl_at=P.W(4, "slowed")),
        [K(P, 4, "2 APRIL 2026", "april", "yellow", xy=(1520, 260), size=64), K(P, 4, "REVIEW TO MID-2027", "middle", "red", xy=(1520, 460), size=56), K(P, 4, "COST AND SCHEDULE COULD RISE", "cost", "ink", xy=(1500, 660), size=44)])
    seg(P, 5, T_poster(pst("L12_camp_quiet", "p06_camp"), DARK, "push_in", seed=85), [K(P, 5, "~700 STAFF + ~2,000 CONTRACTORS (PRESS REPORTS)", "700", "ink", xy=(W / 2, 160), size=44), K(P, 5, "THE BIG BUILD HAS STOPPED", "stopped", "red", xy=(W / 2, 880), size=60)])
    def slip(img, g, t, sh):
        p = ease_io((g - P.W(6, "2030") + 0.3) / 0.9)
        paste_transformed(img, label_img("2028", kind="anton", size=200, fg=WHITE, bg=None, pad=(10, 6)), 1500, 380, 1.0, 0, 1 - 0.6 * p)
        if p > 0.2:
            ImageDraw.Draw(img).line([(1390, 380), (1390 + 230 * clamp((p - 0.2) / 0.3), 380)], fill=RED + (255,), width=14)
        paste_transformed(img, label_img("2030?", kind="anton", size=200, fg=RED, bg=None, pad=(10, 6)), 1500, 620, 1.0, 0, clamp((p - 0.4) / 0.4))
    def cost(img, g, t, sh):
        slip(img, g, t, sh)
        CH.stacked(img, g, 200, 740, 1000, 90, [(450, (150, 60, 50), "LOW ESTIMATE", P.W(6, "900") - 0.4), (450, RED, "+ UP TO", P.W(6, "900"))], 900, prefix="$", unit="M", dec=0,
                   total=900, total_at=P.W(6, "900") + 0.6, total_label="UP TO")
    seg(P, 6, T_headline("dawn_2026_11_13_2030", seed=86, photo=False, cx=700, extra=cost), [K(P, 6, "DELAY COST (REPORTED ESTIMATE)", "insider", "ink", xy=(560, 610), size=44)])
    P.fx("sfx/slide_slow.wav", P.W(6, "2030"), 8)
    def counter10(img, g, t, sh):
        CH.panel(img, 420, 640, 1500, 960)
        CH.stat(img, g, P.W(7, "ten"), 720, 860, "users", 10000, "ATTENDEES (ORGANISERS)", col=COPPER, suffix="+", size=100, dur=1.6)
        CH.stat(img, g, P.W(7, "sixty"), 1220, 860, "world", 60, "COUNTRIES", col=CH.BLUE, suffix="+", size=100)
    seg(P, 7, T_photo("news/tribune_2026_11_13_13deals__photo.webp", bg=NAVY, maxw=1300, maxh=640, cy=420, seed=87, extra=counter10),
        [K(P, 7, "12–13 NOV 2026 · JINNAH CONVENTION CENTRE", "november", "yellow", xy=(W / 2, 120), size=48)])
    P.fx("sfx/crowd.wav", P.S(7), -8)
    seg(P, 8, T_photo("news/pakistantoday_2026_11_14_forum__photo.jpg", bg=NAVY, maxw=1300, maxh=700, seed=88),
        [K(P, 8, "PAKISTAN: THE NEXT CRITICAL MINERALS DESTINATION", "next", "yellow", xy=(W / 2, 120), size=44),
         K(P, 8, "SHEHBAZ SHARIF", "prime", "ink", xy=(380, 860), size=44), K(P, 8, "FIELD MARSHAL ASIM MUNIR", "army", "ink", xy=(900, 860), size=40),
         K(P, 8, "JOHN THORNTON · BARRICK", "chairman", "ink", xy=(1400, 860), size=40), K(P, 8, "ROBERT FRIEDLAND · IVANHOE", "friedland", "ink", xy=(1520, 760), size=40)])
    def sp(img, g, t, sh):
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, W / 2, H), fill=(226, 214, 190, 255))
        stamp(img, "2011: LEASE REFUSED", W / 4, 400, g, sh["start"] + 0.3, col=RED, size=70, rot=-8)
        big_text(img, "LOCAL SMELTING DEMANDED", W / 4, 620, 50, g, sh["start"] + 0.6, fg=INK, bg=YELLOW, seed=91)
        quote_card(img, "Mine in Pakistan, process in Pakistan, manufacture in Pakistan.", "PM Shehbaz Sharif, Nov 2026", g, P.W(9, "mine"), cx=3 * W / 4, cy=430, width=860)
        big_text(img, "2026: GOVERNMENT POLICY", 3 * W / 4, 780, 54, g, P.W(9, "policy"), fg=WHITE, bg=COPPER, seed=92)
    seg(P, 9, T_fill(NAVY, extra=sp))
    def r10(img, g, t, sh, v):
        dot(img, v, KARACHI, g, P.W(10, "karachi"), "KARACHI", col=COPPER)
        dot(img, v, GWADAR, g, P.W(10, "gwadar"), "GWADAR", col=COPPER, side=-1)
    seg(P, 10, T_map([(0, V_SOUTHPK)], bal=BAL_ON, extra=r10,),
        [K(P, 10, "SECURITY FOR INVESTORS", "security", "ink", xy=(W / 2, 160), size=56)])
    def blocks(img, g, t, sh, v):
        d = ImageDraw.Draw(img)
        for i, (lo, la) in enumerate([(61.7, 29.4), (62.5, 28.9), (63.1, 29.5), (61.9, 28.7), (62.8, 29.8)]):
            if g > P.W(11, "chagai") + i * 0.25:
                x0, y0 = lonlat_xy(v, lo - 0.3, la + 0.2)
                x1, y1 = lonlat_xy(v, lo + 0.3, la - 0.2)
                d.rectangle((x0, y0, x1, y1), outline=YELLOW + (255,), width=5, fill=YELLOW + (50,))
        dot(img, v, REKO, g, P.S(11), "REKO DIQ", col=RED)
    seg(P, 11, T_map([(0, V_CHG)], bal=BAL_ON, extra=blocks),
        [K(P, 11, "13 AGREEMENTS", "thirteen", "copper", xy=(500, 160), size=64), K(P, 11, "IVANHOE + MARI MINERALS: CHAGAI", "ivanhoe", "ink", xy=(1350, 160), size=46),
         K(P, 11, "NATIONAL MINERALS DATA CENTRE", "data", "yellow", xy=(W / 2, 880), size=50)])
    P.event(P.W(12, "deferred"), 2026, "RAIL DEFERRED ×3")
    seg(P, 12, T_poster(pst("L05_railway", "p13_rail"), DARK, "push_in", seed=92),
        [K(P, 12, "1,350 RAIL KM FROM ITS PORT", "1", "ink", xy=(W / 2, 170), size=56), C("15 NOV 2026: DEFERRED ×3", P.W(12, "third"), "red", xy=(W / 2, 860), stamp=True, size=90)])
    P.fx("sfx/stamp_heavy.wav", P.W(12, "third"), -2)
    P.cue("music/L_lowpulse.wav", P.CARD, P.S(7), 0.32)
    P.cue("music/L_bright.wav", P.S(7), P.S(12), 0.26, offset=30)
    return P


# ================================================================== CLOSE
def build_c09():
    P = Part("c09", card=False)
    P.bg = DARK
    def stack(img, g, t, sh):
        items = [("1993 AGREEMENT", "agreements"), ("1998 TREATY", "treaty"), ("ICSID TRIBUNAL", "tribunal"), ("$5.9B, CANCELLED", "cancelled"), ("2022 LAW", "law"), ("BILLIONS IN LOANS", "loans")]
        for i, (txt, w_) in enumerate(items):
            slide_card(img, txt, W / 2 + random.Random(i).uniform(-60, 60), 760 - i * 95, g, P.W(1, w_), side="T", seed=200 + i, kind="anton", size=60, fg=WHITE, bg=[INK, NAVY, RED, COPPER, TEAL, INK][i])
    seg(P, 1, T_fill((226, 214, 190), extra=stack), [K(P, 1, "1993 → 2026", "thirty", "yellow", xy=(W / 2, 120), size=60)])
    def cut(img, g, t, sh):
        fill_bg(img, DEEP)
        paste_transformed(img, poster_layer("p02_cutaway"), W / 2, H / 2 + 120, 0.95, jitter(5, g)[2])
        stamp(img, "0", W / 2, 260, g, P.W(2, "exactly"), col=WHITE, size=220, rot=-4)
    seg(P, 2, lambda img, t, sh: cut(img, sh["start"] + t, t, sh), [K(P, 2, "TONNES PRODUCED", "copper", "yellow", xy=(W / 2, 120), size=60)])
    tw = P.W(3, "whether")
    seg(P, 3, T_photo("photos/barrick_community_children.jpg", bg=DARK, maxw=1200, maxh=700, seed=93, duotone=True), t1=P.W(3, "railway"))
    seg(P, 3, T_poster(pst("L05_railway", "p13_rail"), DARK, "push_in", seed=94), t0=P.W(3, "railway"), t1=P.W(3, "province"))
    seg(P, 3, T_poster(pst("p07_court_pk", "p07_court"), DARK, "push_in", seed=95), t0=P.W(3, "province"), t1=P.W(3, "people"))
    seg(P, 3, T_poster(pst("L12_camp_quiet", "p06_camp"), DARK, "pull_out", seed=96), t0=P.W(3, "people"))
    P.gap(P.b(4), 3.0)
    t30 = P.W(4, "2030")
    seg(P, 4, T_poster("p14_dusk", COPPER, "pull_out", seed=97,
                       extra=lambda img, g, t, sh: (big_text(img, "2030", W / 2, 200, 120, g, t30, fg=WHITE, bg=None, seed=98),
                                                    big_text(img, "REKO DIQ", W / 2, 520, 220, g, P.E(4) + 0.6, fg=WHITE, slam=True, seed=99))))
    P.fx("sfx/wind.wav", P.S(4), -6)
    P.fx("music/hit.wav", P.E(4) + 0.6, -4)
    P.total = P.end_vo + 1.5
    P.cue("music/L_close.wav", 0, P.total, 0.34)
    return P
