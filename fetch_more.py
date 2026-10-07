#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Добирает фото 11-16 (горные курорты) с Wikimedia Commons."""
import json, os, re, subprocess, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "images")
UA = "SchoolPresentationBot/1.0 (educational use)"
BAD = re.compile(r"(map|karte|logo|flag|coat of arms|diagram|chart|sign|poster|stamp|"
                 r"cover|book|screenshot|drawing|painting|engraving|museum|scan|"
                 r"page|plaque|portrait|monument)", re.I)


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    out = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-A", UA, url],
                         capture_output=True, check=True).stdout
    return json.loads(out.decode("utf-8"))


def search(query, limit=30):
    data = api({"action": "query", "format": "json", "generator": "search",
                "gsrnamespace": 6, "gsrsearch": query, "gsrlimit": limit,
                "prop": "imageinfo", "iiprop": "url|size|extmetadata",
                "iiurlwidth": 1600})
    out = []
    for p in data.get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        t = p.get("title", "")
        if not ii.get("thumburl") or BAD.search(t):
            continue
        if not re.search(r"\.(jpe?g)$", t, re.I):
            continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 1300 or h < 800:
            continue
        m = ii.get("extmetadata", {})
        out.append({"title": t, "url": ii["thumburl"].split("?")[0], "w": w, "h": h,
                    "artist": re.sub(r"<[^>]+>", "", (m.get("Artist", {}) or {}).get("value", "") or "").strip(),
                    "lic": (m.get("LicenseShortName", {}) or {}).get("value", ""),
                    "descurl": ii.get("descriptionurl", "")})
    return out


SLOTS = {
    11: (["skiing Alps powder snow", "Ski Zermatt", "skiing Swiss Alps skier",
          "Skifahren Matterhorn"], "wide", "Ski day"),
    12: (["Swiss cheese fondue", "Fondue Schweiz", "Swiss restaurant raclette"],
          "wide", "Fondue night"),
    13: (["Zermatt Kirchbrücke", "Zermatt old town street", "Zermatt Bahnhofstrasse"],
          "wide", "Old town"),
    14: (["glacier ice Alps", "glacier ice cave Switzerland", "Gorner glacier ice",
          "Alpen Gletscher"], "wide", "Glacier"),
    15: (["hiking trail Alps Switzerland", "Bergwanderung Schweiz", "alpine hiking path"],
          "wide", "Hiking"),
    16: (["wooden balcony mountain view cafe Switzerland", "Sonnenterrasse Berge",
          "mountain terrace chairlift view"], "wide", "Balcony"),
}

manifest = {}
for slot, (queries, want, cap) in SLOTS.items():
    print(f"\n=== {slot} {cap} ===")
    picked = []
    for q in queries:
        for c in search(q):
            r = c["w"] / c["h"]
            if want == "wide" and not (1.25 <= r <= 2.4):
                continue
            if any(c["title"] == p["title"] for p in picked):
                continue
            picked.append(c)
        if len(picked) >= 6:
            break
    for i, c in enumerate(picked[:6], 1):
        fn = f"cand_{slot}_{i}.jpg"
        subprocess.run(["curl", "-s", "-L", "--max-time", "90", "-A", UA,
                        "-o", os.path.join(OUT, fn), c["url"]], check=True)
        manifest[fn] = c
        print(f"  {fn}  {c['w']}x{c['h']}  {c['lic']:<12} {c['title'][:62]}")

with open(os.path.join(OUT, "cand.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
