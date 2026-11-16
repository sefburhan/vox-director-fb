"""Collect every real image/document the Reko Diq documentary needs, with credits.

uv run --python 3.12 --with playwright --with pymupdf --with requests python assets.py [direct|wiki|pdf|news|all]
Writes ../assets/{photos,docs,news,wiki} and ../assets/credits.csv (+ credits.md for the description).
"""
import csv
import json
import re
import sys
import time
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()      # use the macOS trust store (verification stays on)
except ImportError:
    pass
import requests

ROOT = Path(__file__).resolve().parent.parent / "assets"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
S = requests.Session()
S.headers["User-Agent"] = UA
CREDITS = ROOT / "credits.csv"
FIELDS = ["id", "file", "kind", "what", "source", "url", "author", "licence", "date", "use"]


def credit(**row):
    rows = []
    if CREDITS.exists():
        rows = [r for r in csv.DictReader(open(CREDITS)) if r["id"] != row["id"]]
    rows.append({k: row.get(k, "") for k in FIELDS})
    with open(CREDITS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def get(url, dest, **kw):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    try:
        r = S.get(url, timeout=120, **kw)
    except Exception as e:
        print(f"  ! {type(e).__name__} {url[:90]}")
        return False
    if r.status_code != 200:
        print(f"  ! {r.status_code} {url}")
        return False
    dest.write_bytes(r.content)
    return True


# ------------------------------------------------------------------ 1. direct images (Barrick / RDMC)
Q4 = "https://s25.q4cdn.com/322814910/files/images"
DIRECT = [
    ("barrick_aerial_site", f"{Q4}/reko_diq/11_reko_diq_water_management.jpg", "Aerial view of the country around the Reko Diq site", "Ch1 2:05"),
    ("barrick_community_children", f"{Q4}/reko_diq/10_reko_diq_transformative_impact.jpg", "Children in a Chagai community programme", "Ch7 19:25"),
    ("rdmc_logo", f"{Q4}/reko_diq/reko_diq_mining_company.png", "Reko Diq Mining Company logo", "titles/credits"),
    ("barrick_press_card", f"{Q4}/news/2026/barrick_card.jpg", "Barrick press card, 2026", "Ch8 20:55"),
]


def do_direct():
    for id_, url, what, use in DIRECT:
        ext = url.rsplit(".", 1)[-1]
        ok = get(url, ROOT / f"photos/{id_}.{ext}")
        print(("ok " if ok else "FAIL ") + id_)
        if ok:
            credit(id=id_, file=f"photos/{id_}.{ext}", kind="photo", what=what, source="Barrick Mining Corporation / Reko Diq Mining Company",
                   url=url, author="Barrick Mining Corporation", licence="Company media (credit; permission advised)", use=use)


# ------------------------------------------------------------------ 2. Wikipedia lead images (real photos, licensed)
WIKI = [
    ("Chagai-I", "Ras Koh hills, 28 May 1998 nuclear test", "Cold open 0:00"),
    ("Reko Diq", "Reko Diq article lead image", "Ch1"),
    ("Chagai District", "Chagai district", "Ch1"),
    ("Ras Koh Hills", "Ras Koh hills", "Cold open"),
    ("Quetta", "Quetta, Balochistan", "Ch1 / Ch2 1993"),
    ("Nok Kundi", "Nok Kundi railway town", "Ch1 / Ch7"),
    ("Saindak Copper Gold Project", "Saindak mine, Chagai", "Ch7 Saindak"),
    ("Supreme Court of Pakistan", "Supreme Court of Pakistan building, Islamabad", "Ch3 2013 / Ch5 2022"),
    ("International Centre for Settlement of Investment Disputes", "ICSID / World Bank, Washington", "Ch4"),
    ("World Bank Group", "World Bank headquarters, Washington", "Ch4"),
    ("The Roosevelt Hotel (Manhattan)", "Roosevelt Hotel, New York (PIA-owned)", "Ch4 11:40"),
    ("Hôtel Scribe", "Hôtel Scribe, Paris (PIA-owned)", "Ch4 11:40"),
    ("Pakistan International Airlines", "PIA aircraft", "Ch4"),
    ("Iftikhar Muhammad Chaudhry", "Chief Justice Iftikhar Chaudhry", "Ch3 2013"),
    ("Aslam Raisani", "Nawab Aslam Raisani", "Ch3 2009"),
    ("Samar Mubarakmand", "Dr Samar Mubarakmand", "Ch3"),
    ("Umar Ata Bandial", "Chief Justice Umar Ata Bandial", "Ch5 2022"),
    ("Akhtar Mengal", "Akhtar Mengal, BNP-M", "Ch5 2022"),
    ("Shehbaz Sharif", "Prime Minister Shehbaz Sharif", "Ch8 forum"),
    ("Asim Munir", "Field Marshal Asim Munir", "Ch8 forum"),
    ("Robert Friedland", "Robert Friedland, Ivanhoe Mines", "Ch8 forum"),
    ("John L. Thornton", "John Thornton, Barrick chairman", "Ch8 forum"),
    ("Mark Bristow", "Mark Bristow, former Barrick CEO", "Ch6 2025"),
    ("Jinnah Convention Centre", "Jinnah Convention Centre, Islamabad", "Ch8 forum"),
    ("Port Qasim", "Port Qasim, Karachi", "Ch7 rail"),
    ("Gwadar Port", "Gwadar port", "Ch7"),
    ("Pakistan Railways", "Pakistan Railways train", "Ch7 rail"),
    ("Quetta–Taftan Railway Line", "Quetta–Taftan railway line", "Ch7 rail"),
    ("Antofagasta plc", "Antofagasta plc", "Ch2 2006"),
    ("Barrick Mining", "Barrick", "Ch2 / Ch5"),
    ("BHP", "BHP", "Ch2 1993"),
    ("Copper", "Native copper / copper metal", "Ch6"),
    ("Porphyry copper deposit", "Porphyry copper deposit", "Ch1 geology"),
    ("Escondida", "Escondida, world's largest copper mine (scale)", "Ch6 top-5"),
    ("Balochistan", "Balochistan landscape", "Ch7"),
]
API = "https://en.wikipedia.org/w/api.php"
CAPI = "https://commons.wikimedia.org/w/api.php"


def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def jget(api, params, tries=6):
    for k in range(tries):
        try:
            return S.get(api, params=params, timeout=30).json()
        except Exception:
            time.sleep(2 + 3 * k)
    raise RuntimeError("wiki unreachable")


def do_wiki():
    for title, what, use in WIKI:
        id_ = "wiki_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        if any((ROOT / "wiki").glob(id_ + ".*")):
            continue
        id_ = "wiki_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        try:
            r = jget(API, dict(action="query", format="json", titles=title, redirects=1, prop="pageimages", piprop="original|name"))
            page = next(iter(r["query"]["pages"].values()))
            orig = page.get("original", {}).get("source")
            name = page.get("pageimage")
            if not orig:
                print(f"  - no lead image: {title}")
                continue
            # licence + author: try Commons first, then the local file page
            meta = {}
            for api in (CAPI, API):
                m = jget(api, dict(action="query", format="json", titles=f"File:{name}", prop="imageinfo",
                                   iiprop="extmetadata|url|size", iiurlwidth=2400))
                pg = next(iter(m["query"]["pages"].values()))
                if "imageinfo" in pg:
                    meta = pg["imageinfo"][0]
                    break
            em = meta.get("extmetadata", {})
            lic = clean(em.get("LicenseShortName", {}).get("value", ""))
            if "fair use" in lic.lower() or "non-free" in lic.lower() or em.get("NonFree", {}).get("value") == "true":
                lic = (lic or "Non-free") + " (non-free: licence needed)"
            url = meta.get("thumburl") or orig
            ext = url.rsplit(".", 1)[-1].split("?")[0].lower()
            if ext == "svg":
                url = meta.get("thumburl") or orig
                ext = "png"
            dest = ROOT / f"wiki/{id_}.{ext}"
            ok = False
            for k in range(5):
                if get(url, dest):
                    ok = True
                    break
                time.sleep(3 + 3 * k)
            print(("ok " if ok else "FAIL ") + f"{id_}  [{lic}]")
            if ok:
                credit(id=id_, file=f"wiki/{dest.name}", kind="photo", what=what, source="Wikimedia Commons / Wikipedia",
                       url=meta.get("descriptionurl", f"https://en.wikipedia.org/wiki/File:{name}"),
                       author=clean(em.get("Artist", {}).get("value", ""))[:120], licence=lic,
                       date=clean(em.get("DateTimeOriginal", {}).get("value", ""))[:40], use=use)
            time.sleep(0.4)
        except Exception as e:
            print(f"  ! {title}: {e}")


# ------------------------------------------------------------------ 3. document pages (PDFs)
TR = "https://s25.q4cdn.com/322814910/files/doc_downloads/reko_diq/Barrick_RekoDiq_TechnicalReport_20241231.pdf"
PDFS = [
    ("barrick_technical_report", TR, "Barrick, Reko Diq Technical Report (31 Dec 2024)",
     [("Table 1-2", "reserve statement", "Ch1 1:00"), ("Figure 4-1", "property location map", "Ch1 1:40"),
      ("Figure 4-2", "lease map", "Ch1 3:20"), ("Figure 7-2", "15 porphyry bodies", "Ch1 3:20"),
      ("Figure 2-1", "holding structure", "Ch5 13:05"), ("Figure 18-1", "regional logistics / rail", "Ch7 18:35"),
      ("Table 1-4", "risk table", "Ch7 20:00")]),
    ("esia_hydrogeology", "https://s25.q4cdn.com/322814910/files/doc_downloads/reko_diq/esia/Appendix-P-Mine-Site-Hydrogeological-Assessment.pdf",
     "ESIA Appendix P, Mine Site Hydrogeological Assessment", [("pH", "Tanjeel groundwater pH", "Ch1 3:35")]),
    ("esia_exec_summary", "https://www3.dfc.gov/environment/eia/rekodiq/Reko_Diq_ESIA_Executive_Summary.pdf",
     "Reko Diq ESIA Executive Summary (DFC)", [("Port Qasim", "rail route to Port Qasim", "Ch7 18:35"), (None, "cover", "Ch7")]),
    ("barrick_statement_2apr2026", "https://s25.q4cdn.com/322814910/files/doc_news/2026/04/Barrick-Provides-an-Update-on-Reko-Diq.pdf",
     "Barrick, 'Barrick Provides an Update on Reko Diq', 2 Apr 2026", [(None, "page 1", "Ch8 20:55")]),
    ("open_letter_csos", "https://re-course.org/wp-content/uploads/2025/08/Open-letter_-Balochistans-Reko-Diq-copper-mine-FINAL.pdf",
     "Civil society open letter on Reko Diq, Aug 2025", [(None, "page 1", "Ch7 19:40")]),
    ("un_experts_letter", "https://spcommreports.ohchr.org/TMResultsBase/DownLoadPublicCommunicationFile?gId=30467",
     "UN Special Procedures communication to Barrick, Dec 2025", [(None, "page 1", "Ch7 18:00")]),
]


def do_pdf():
    import fitz
    for id_, url, what, wants in PDFS:
        pdf = ROOT / f"docs/src/{id_}.pdf"
        if not get(url, pdf):
            print(f"FAIL {id_}")
            continue
        doc = fitz.open(pdf)
        print(f"ok {id_}: {doc.page_count} pages")
        for needle, label, use in wants:
            pno = 0
            if needle:
                hits = [i for i in range(doc.page_count) if needle in doc[i].get_text()]
                # prefer the page where the caption (not a list-of-figures entry) sits: skip the first pages
                hits = [h for h in hits if h > 12] or hits
                if not hits:
                    print(f"   - '{needle}' not found")
                    continue
                pno = hits[0]
            pix = doc[pno].get_pixmap(dpi=170)
            slug = re.sub(r"[^a-z0-9]+", "_", (needle or label).lower()).strip("_")
            out = ROOT / f"docs/{id_}__{slug}_p{pno + 1}.png"
            pix.save(out)
            print(f"   page {pno + 1} -> {out.name}")
            credit(id=f"{id_}__{slug}", file=f"docs/{out.name}", kind="document page", what=f"{what}: {label} (p.{pno + 1})",
                   source=what, url=url, author=what.split(",")[0], licence="Public document (quote/credit)", use=use)


# ------------------------------------------------------------------ 4. news headlines (screenshot + lead photo)
NEWS = [
    ("dawn_2019_07_15_camp", "https://www.dawn.com/news/1494099", "Cold open 0:45 (camp photo)"),
    ("dawn_2013_saga", "https://dawn.com/news/780568/the-reko-diq-saga", "Ch2 4:00"),
    ("profit_2022_02_20", "https://profit.pakistantoday.com.pk/2022/02/20/barrick-gold-is-coming-back-to-reko-diq", "Ch2 5:55"),
    ("herald_magic_mountains", "https://herald.dawn.com/news/1153283", "Ch3 6:30"),
    ("bolnews_reko_diq_affair", "https://www.bolnews.com/latest-news/the-reko-diq-affair/", "Ch3 7:20"),
    ("thenews_reko_diq_matter", "https://www.thenews.com.pk/print/507421-the-reko-diq-matter", "Ch3 8:10"),
    ("thenational_500bn", "https://www.thenationalnews.com/business/pakistan-s-500bn-gold-mine-kept-under-wraps-1.606927", "Ch3 9:00"),
    ("caselaw_ewhc_2021", "https://caselaw.nationalarchives.gov.uk/ewhc/comm/2021/1884", "Ch3 8:10 / Ch4"),
    ("dawn_2021_assets_unfrozen", "https://www.dawn.com/news/1625937/assets-unfrozen", "Ch4 11:20"),
    ("dawn_2021_bvi_unfreeze", "https://www.dawn.com/news/1625648/british-virgin-islands-court-unfreezes-pia-assets-in-reko-diq-award-enforcement-case", "Ch4 11:40"),
    ("tribune_2022_11b", "https://tribune.com.pk/story/2348850/pakistan-evades-11b-reko-diq-penalty", "Ch4 12:05"),
    ("dawn_2022_12_12_antofagasta", "https://www.dawn.com/news/1725908", "Ch5 12:45"),
    ("tribune_2022_mengal", "https://tribune.com.pk/story/2391016/rift-emerges-in-coalition-over-reko-diq-deal", "Ch5 14:35"),
    ("iea_gcmo_2025", "https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary", "Ch6 15:10"),
    ("miningweekly_2025_fluor", "https://www.miningweekly.com/article/reko-diq-jv-shareholders-approve-updated-feasibility-study-select-fluor-as-epcm-2025-04-08", "Ch6 16:10"),
    ("profit_2025_09_financing", "https://profit.pakistantoday.com.pk/2025/09/17/reko-diq-secures-over-5-5-billion-in-financing-commitments-from-international-financial-institutions-report/", "Ch6 16:30"),
    ("dawn_2025_12_11_exim", "https://www.dawn.com/news/1960428/us-exim-bank-okays-12bn-for-reko-diq", "Ch6 16:55"),
    ("miningcom_manara", "https://www.mining.com/manara-minerals-to-buy-stake-in-barricks-reko-diq-gold-project-ft-reports/", "Ch6 17:15"),
    ("dawn_2025_09_package", "https://www.dawn.com/news/1943039/77bn-package-for-reko-diq-approved", "Ch7 19:00"),
    ("barrick_response_open_letter", "https://www.barrick.com/English/operations/reko-diq/response-to-open-letter-from-civil-society-organizations/default.aspx", "Ch7 19:40"),
    ("brecorder_2026_02_06_review", "https://www.brecorder.com/news/40405908/barrick-reviews-reko-diq-project-amid-security-concerns", "Ch8 20:25"),
    ("barrick_news_2026_04_02", "https://www.barrick.com/English/news/news-details/2026/barrick-provides-an-update-on-reko-diq/default.aspx", "Ch8 20:55"),
    ("dawn_2026_11_13_2030", "https://www.dawn.com/news/2044302/barrick-mining-expresses-interest-in-mineral-processing-industries-in-karachi-gwadar", "Ch8 21:20"),
    ("tribune_2026_11_13_13deals", "https://tribune.com.pk/story/2640146/pakistan-announces-13-mineral-cooperation-deals", "Ch8 21:30"),
    ("pakistantoday_2026_11_14_forum", "https://www.pakistantoday.com.pk/2026/11/14/pm-cdf-vow-security-push-foreign-miners-to-process-pakistans-mineral-wealth-at-home", "Ch8 21:30"),
    ("bloom_2026_11_15_rail", "https://bloompakistan.com/pakistan-delays-reko-diq-railway-project/", "Ch8 22:10"),
]


def do_news():
    from playwright.sync_api import sync_playwright
    (ROOT / "news").mkdir(parents=True, exist_ok=True)
    meta_all = {}
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome", headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, user_agent=UA, locale="en-GB")
        only = set(sys.argv[2:])
        for id_, url, use in NEWS:
            if only and id_ not in only:
                continue
            shot = ROOT / f"news/{id_}__headline.png"
            try:
                pg = ctx.new_page()
                resp = pg.goto(url, wait_until="domcontentloaded", timeout=45000)
                status = resp.status if resp else 0
                pg.wait_for_timeout(2500)
                # hide cookie/consent overlays and sticky ads
                pg.add_style_tag(content="[id*=cookie],[class*=cookie],[id*=consent],[class*=consent],[class*=popup],[id*=popup],.modal,[class*=newsletter]{display:none!important}")
                m = pg.evaluate("""() => {
                    const g = s => (document.querySelector(s) || {}).content || '';
                    const h1 = (document.querySelector('h1') || {}).innerText || '';
                    return {title: g('meta[property="og:title"]') || document.title, h1: h1.trim(),
                            image: g('meta[property="og:image"]'), site: g('meta[property="og:site_name"]'),
                            date: g('meta[property="article:published_time"]') || g('meta[name="publish-date"]') || g('meta[itemprop="datePublished"]')};
                }""")
                pg.evaluate("""() => { const h = [...document.querySelectorAll('h1')].find(e => e.offsetParent !== null);
                                       if (h) { h.scrollIntoView({block: 'start'}); window.scrollBy(0, -260); } }""")
                pg.wait_for_timeout(600)
                pg.screenshot(path=str(shot))
                box = pg.evaluate("""() => { const h = [...document.querySelectorAll('h1')].find(e => e.offsetParent !== null);
                                             if (!h) return null; const r = h.getBoundingClientRect();
                                             return {x: r.x, y: r.y, w: r.width, h: r.height}; }""")
                if box and box["w"] > 50:
                    x0 = max(0, box["x"] - 40); y0 = max(0, box["y"] - 60)
                    pg.screenshot(path=str(ROOT / f"news/{id_}__crop.png"),
                                  clip={"x": x0, "y": y0, "width": min(1440 - x0, max(box["w"] + 80, 900)), "height": min(900 - y0, box["h"] + 170)})
                m["status"] = status
                meta_all[id_] = m
                img_ok = False
                if m.get("image"):
                    ext = m["image"].split("?")[0].rsplit(".", 1)[-1].lower()
                    ext = ext if ext in ("jpg", "jpeg", "png", "webp") else "jpg"
                    img_ok = get(m["image"], ROOT / f"news/{id_}__photo.{ext}", headers={"Referer": url})
                    if img_ok:
                        credit(id=f"{id_}__photo", file=f"news/{id_}__photo.{ext}", kind="news photo", what=f"Lead photo: {m.get('title', '')[:90]}",
                               source=m.get("site") or url.split("/")[2], url=url, author="(see source caption)", licence="News photo (credit; licence needed)",
                               date=m.get("date", "")[:10], use=use)
                credit(id=f"{id_}__headline", file=f"news/{shot.name}", kind="headline screenshot", what=m.get("h1") or m.get("title", ""),
                       source=m.get("site") or url.split("/")[2], url=url, author="", licence="Screenshot of headline (quotation, credited)",
                       date=m.get("date", "")[:10], use=use)
                print(f"ok {status} {id_}: {(m.get('h1') or m.get('title', ''))[:70]} | photo={'y' if img_ok else 'n'}")
                pg.close()
            except Exception as e:
                print(f"FAIL {id_}: {str(e)[:120]}")
        br.close()
    old = json.loads((ROOT / "news/meta.json").read_text()) if (ROOT / "news/meta.json").exists() else {}
    old.update(meta_all)
    (ROOT / "news/meta.json").write_text(json.dumps(old, indent=1, ensure_ascii=False))


def write_md():
    rows = list(csv.DictReader(open(CREDITS)))
    lines = ["# Image and document credits (for the video description)", ""]
    for r in sorted(rows, key=lambda r: r["kind"]):
        who = f" — {r['author']}" if r["author"] else ""
        lic = f" ({r['licence']})" if r["licence"] else ""
        lines.append(f"- {r['what']}{who}. {r['source']}{lic}. {r['url']}")
    (ROOT / "credits.md").write_text("\n".join(lines) + "\n")
    print(f"credits: {len(rows)} items -> {ROOT / 'credits.md'}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    ROOT.mkdir(parents=True, exist_ok=True)
    for name, fn in [("direct", do_direct), ("wiki", do_wiki), ("pdf", do_pdf), ("news", do_news)]:
        if what in (name, "all"):
            print(f"== {name}")
            fn()
    write_md()
