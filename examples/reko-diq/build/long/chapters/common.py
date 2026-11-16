"""Places, views and small shared pieces for the chapter files."""
from kit import *  # noqa

# places (lon, lat)
REKO = (62.07, 29.12)
RASKOH = (64.95, 28.80)
QUETTA = (67.00, 30.18)
NOKKUNDI = (62.75, 28.82)
DALBANDIN = (64.40, 28.89)
NUSHKI = (66.02, 29.55)
TAFTAN = (61.59, 28.96)
AFG_PT = (62.10, 29.43)          # ~35 km north (script)
IRN_PT = (61.50, 29.20)          # ~55 km west (script)
ISLAMABAD = (73.05, 33.69)
KARACHI = (67.01, 24.86)
PORTQASIM = (67.34, 24.78)
GWADAR = (62.33, 25.12)
SAINDAK = (61.60, 29.25)
BOREFIELD = (61.62, 29.55)
WASHINGTON = (-77.04, 38.90)
LONDON = (-0.13, 51.50)
BVI = (-64.62, 18.43)
NEWYORK = (-73.98, 40.75)
PARIS = (2.33, 48.87)
RIYADH = (46.68, 24.71)
BEIJING = (116.40, 39.90)
CANBERRA = (149.13, -35.28)
RAIL = [NOKKUNDI, DALBANDIN, NUSHKI, QUETTA, (67.88, 29.54), (68.44, 28.28), (68.90, 27.69), (68.37, 25.39), PORTQASIM]
N40 = [QUETTA, NUSHKI, DALBANDIN, NOKKUNDI]
BELT = [(21.9, 44.1), (24.5, 42.6), (29.0, 40.6), (35.0, 39.6), (42.0, 40.0), (46.7, 38.7), (50.5, 34.6), (55.9, 30.0), REKO]
BELT_MINES = [(22.1, 44.07), (29.3, 38.5), (46.7, 38.7), (55.87, 29.95)]

# views (centre lon, centre lat, span in degrees of longitude)
V_PK = (69.5, 30.4, 24.0)
V_BAL = (65.6, 28.6, 11.0)
V_CHG = (63.0, 29.2, 6.2)
V_SITE = (62.2, 29.2, 2.6)
V_EURASIA = (43.0, 37.0, 64.0)
V_WORLD = (5.0, 30.0, 220.0)
V_SOUTHPK = (65.5, 27.3, 12.5)

BAL_ON = lambda g: 1.0


def burst(seed, at, x=W / 2, y=H / 2, n=50, amb=0):
    return Confetti(seed, amb, bursts=[(at, x, y, n)])
