#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Скачивает свободные фото Швейцарии (Zermatt / Matterhorn) с Wikimedia Commons."""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)

UA = {"User-Agent": "SchoolPresentationBot/1.0 (educational use)"}

# slot -> (список поисковых запросов, желаемое соотношение сторон: 'wide' | 'tall', подпись)
SLOTS = [
    (1,  ["Zermatt village Matterhorn", "Zermatt village snow", "Zermatt Switzerland village"],
         "wide", "Zermatt village"),
    (2,  ["Matterhorn Zermatt mountain", "Matterhorn peak snow", "Matterhorn Zermatt sunrise"],
         "tall", "The Matterhorn"),
    (3,  ["Zermatt spring meadow flowers", "alpine meadow spring flowers Switzerland",
          "Swiss mountain pasture wildflowers spring", "Alpenblumen Frühlingswiese Schweiz"],
         "wide", "Spring in the valley"),
    (4,  ["Swiss chalet interior wood stove", "chalet interior Switzerland",
          "Berghaus Interieur Holz", "Swiss chalet room interior"],
         "tall", "Inside a chalet"),
    (5,  ["Zermatt winter snow village street", "Zermatt winter", "Swiss village winter snow"],
         "tall", "Winter in Zermatt"),
    (6,  ["Riffelsee Matterhorn reflection", "Stellisee Matterhorn reflection",
          "mountain lake reflection Matterhorn"],
         "wide", "Riffelsee lake"),
    (7,  ["mountain hut sunrise Alps terrace", "Berghütte Gipfelpanorama",
          "Alpine hut summit view sunrise", "mountain refuge Alps view"],
         "tall", "Sunrise from the hut"),
    (8,  ["Swiss train mountain railway viaduct", "Matterhorn Gotthard Bahn",
          "Swiss mountain railway train", "Zermatt train Gornergrat"],
         "tall", "Train in the Alps"),
    (9,  ["Zermatt panorama village evening", "Zermatt panorama", "Zermatt village night",
          "Zermatt aerial view"],
         "wide", "Zermatt panorama"),
    (10, "Matterhorn sunset alpenglow",            "wide", "Sunset in Zermatt"),
]

BAD = re.compile(r"(map|karte|logo|flag|coat of arms|diagram|chart|sign|poster|"
                 r"stamp|cover|book|screenshot|drawing|painting|engraving|portrait of)",
                 re.I)


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    out = subprocess.run(["curl", "-s", "-L", "--max-time", "40",
                          "-A", UA["User-Agent"], url],
                         capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def download(url, path):
    subprocess.run(["curl", "-s", "-L", "--max-time", "120",
                    "-A", UA["User-Agent"], "-o", path, url], check=True)


def search(query, limit=40):
    try:
        data = api({
            "action": "query", "format": "json", "generator": "search",
            "gsrnamespace": 6, "gsrsearch": query, "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 1800,
        })
    except Exception as e:
        print("  ! search failed:", e)
        return []
    pages = data.get("query", {}).get("pages", {})
    out = []
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        title = p.get("title", "")
        if not ii.get("thumburl"):
            continue
        if BAD.search(title):
            continue
        if not re.search(r"\.(jpe?g|png)$", title, re.I):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 1200 or h < 800:
            continue
        meta = ii.get("extmetadata", {})
        out.append({
            "title": title,
            "url": ii["thumburl"].split("?")[0],
            "w": w, "h": h,
            "ratio": w / h,
            "artist": re.sub(r"<[^>]+>", "", (meta.get("Artist", {}) or {}).get("value", "") or "").strip(),
            "lic": (meta.get("LicenseShortName", {}) or {}).get("value", ""),
            "descurl": ii.get("descriptionurl", ""),
        })
    return out


def pick(cands, want):
    if not cands:
        return None
    if want == "wide":
        good = [c for c in cands if 1.25 <= c["ratio"] <= 2.6]
    else:
        good = [c for c in cands if 0.55 <= c["ratio"] <= 1.05]
    pool = good or cands
    pool.sort(key=lambda c: -(min(c["w"], 4000) * min(c["h"], 4000)))
    return pool[0]


credits = {}
if os.path.exists(os.path.join(OUT, "credits.json")):
    with open(os.path.join(OUT, "credits.json"), encoding="utf-8") as f:
        credits = json.load(f)

for slot, queries, want, caption in SLOTS:
    dest = os.path.join(OUT, f"{slot}.jpg")
    if os.path.exists(dest) and str(slot) in credits:
        print(f"[{slot}] already downloaded -> skip")
        continue
    print(f"[{slot}] {caption}")
    c = None
    for q in queries:
        c = pick(search(q), want)
        if c:
            print(f"   query ok: {q}")
            break
    if not c:
        print("   !! nothing found")
        continue
    ext = ".jpg"
    path = dest
    try:
        download(c["url"], path)
        size = os.path.getsize(path) // 1024
        if size < 20:
            raise RuntimeError("file too small")
        print(f"   -> {os.path.basename(path)}  {c['w']}x{c['h']}  {size} KB  | {c['lic']}")
        credits[slot] = {"caption": caption, "file": os.path.basename(path),
                         "title": c["title"], "artist": c["artist"],
                         "lic": c["lic"], "source": c["descurl"]}
    except Exception as e:
        print("   !! download failed:", e)
    time.sleep(0.4)

with open(os.path.join(OUT, "credits.json"), "w", encoding="utf-8") as f:
    json.dump(credits, f, ensure_ascii=False, indent=2)
print("\ncredits written:", os.path.join(OUT, "credits.json"))
