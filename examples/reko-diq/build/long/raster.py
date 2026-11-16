"""Rasterise the The Indus logo and Tabler icons (MIT) to PNG via headless Chrome."""
import urllib.request, pathlib
from playwright.sync_api import sync_playwright
B = pathlib.Path(__file__).resolve().parent.parent
R = pathlib.Path("/Volumes/Data/Claude.io/Video/video-gen/vox/resources/theindus.org")
ICONS = ["coins", "currency-dollar", "building-bank", "scale", "gavel", "pick", "truck", "train", "droplet", "temperature",
         "users", "briefcase", "bolt", "car", "plug", "flag", "world", "percentage", "calendar", "lock", "building-factory",
         "mountain", "diamond", "file-text", "chart-pie", "trending-up", "alert-triangle", "map-pin", "clock", "school", "hammer", "receipt"]
with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=True)
    pg = br.new_page(viewport={"width": 1200, "height": 300}, device_scale_factor=2)
    mark = (R / "indus-icon-transparent.svg").read_text()
    pg.set_content(f"""<html><head><style>@font-face{{font-family:Plex;src:url('file://{R}/fonts/IBMPlexMono-Medium.ttf')}}
      body{{margin:0;background:transparent}} #b{{display:inline-flex;align-items:center;gap:22px;padding:14px 28px 14px 18px;background:#F7F5F2;border-radius:14px}}
      #b svg{{width:76px;height:76px}} #b span{{font:500 34px Plex;letter-spacing:.14em;color:#172F4B}}</style></head>
      <body><div id=b>{mark}<span>THE INDUS</span></div></body></html>""")
    pg.wait_for_timeout(500)
    pg.locator("#b").screenshot(path=str(B / "icons/_logo_badge.png"), omit_background=True)
    for n in ICONS:
        out = B / f"icons/{n}.png"
        if out.exists():
            continue
        try:
            svg = urllib.request.urlopen(f"https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{n}.svg", timeout=30).read().decode()
        except Exception as e:
            print("miss", n, e); continue
        svg = svg.replace('stroke="currentColor"', 'stroke="#ffffff"').replace('width="24"', 'width="256"').replace('height="24"', 'height="256"').replace('stroke-width="2"', 'stroke-width="1.8"')
        pg.set_content(f"<html><body style='margin:0;background:transparent'><div id=i style='width:256px;height:256px'>{svg}</div></body></html>")
        pg.locator("#i").screenshot(path=str(out), omit_background=True)
    br.close()
print("done")
