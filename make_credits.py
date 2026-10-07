#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Пересобирает images/credits.json по фактическим файлам (метаданные Commons)."""
import json, os, re, subprocess, time, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "images")
UA = "SchoolPresentationBot/1.0 (educational use)"

# слот -> (подпись на слайде, Commons File: title)
MANIFEST = {
    1:  ("Zermatt village",           "File:Matterhorn in winter with Zermatt village.jpg"),
    2:  ("The Matterhorn",            "File:0 106 Walliser Alpen - Matterhorn.jpg"),
    3:  ("Zermatt valley in spring",  "File:3974 - Zermatt viewed from Riffelberg.JPG"),
    4:  ("Zermatt chalets",           "File:00 106 0604 Zmutt - Zermatt (CH).jpg"),
    5:  ("Winter in Zermatt",         "File:Zermatt (132078539).jpeg"),
    6:  ("Riffelsee lake",            "File:Matterhorn and Riffelhorn reflection in the Riffelsee at sunset and a red sky.jpg"),
    7:  ("Sunrise over Zermatt",      "File:Matterhorn im Sonnenaufgang.jpg"),
    8:  ("Gornergrat Railway",        "File:GGB 3051 Gornergrat Bahnhof 1 2021-08-21.jpg"),
    9:  ("Zermatt panorama",          "File:CH.VS.Zermatt 2019-12-27 Mount-Matterhorn 7227 16x9-R 10K.jpg"),
    10: ("Sunset in Zermatt",         "File:Brilliant Sunset over the Matterhorn.jpg"),
    11: ("Cable car to the slopes",   "File:CH.VS.Zermatt 2022-07-16 Air-Zermatt 5926 16x9-R 11K.jpg"),
    12: ("Fondue night",              "File:Cheese Fondue with bread and white mushroom.jpg"),
    13: ("Old village street",        "File:Bahnhofstrasse, Zermatt 2.jpg"),
    14: ("Aletsch glacier",           "File:Aletsch Glacier.jpg"),
    15: ("Hiking above Zermatt",      "File:CH.VS.Zermatt 2021-10-17 Matterhorn 8726.jpg"),
    16: ("Fresh snow",                "File:2010 01 01 zermatt 761.jpg"),
}


def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    last = ""
    for _ in range(4):
        out = subprocess.run(["curl", "-s", "-L", "--max-time", "40", "-A", UA, url],
                             capture_output=True).stdout
        last = out.decode("utf-8", "replace")
        if last.strip().startswith("{"):
            return json.loads(last)
        time.sleep(1.5)
    raise RuntimeError("bad API response: " + last[:120])


credits = {}
# один пакетный запрос — Wikimedia не любит частые обращения
data = api({"action": "query", "format": "json",
            "titles": "|".join(t for _, t in MANIFEST.values()),
            "prop": "imageinfo", "iiprop": "url|extmetadata"})
pages = {p["title"]: p for p in data.get("query", {}).get("pages", {}).values()}

for slot, (caption, title) in sorted(MANIFEST.items()):
    page = pages.get(title, {})
    ii = (page.get("imageinfo") or [{}])[0]
    m = ii.get("extmetadata", {})
    artist = re.sub(r"<[^>]+>", "", (m.get("Artist", {}) or {}).get("value", "") or "").strip()
    if artist.lower().startswith("note:"):
        artist = artist.split("consisting")[0].strip(" ,.")
    credits[str(slot)] = {
        "caption": caption,
        "file": f"{slot}.jpg",
        "title": title.replace("File:", ""),
        "artist": artist or "Unknown",
        "license": (m.get("LicenseShortName", {}) or {}).get("value", "?"),
        "source": ii.get("descriptionurl", ""),
        "exists": os.path.exists(os.path.join(IMG, f"{slot}.jpg")),
    }
    c = credits[str(slot)]
    print(f"{slot:>2}  {c['license']:<14} {c['artist'][:44]:<44} "
          f"{'OK' if c['exists'] else 'MISSING'}  {c['title'][:44]}")

with open(os.path.join(IMG, "credits.json"), "w", encoding="utf-8") as f:
    json.dump(credits, f, ensure_ascii=False, indent=2)

# markdown для учителя
lines = ["# Источники фотографий", "",
         "Все фотографии — с Wikimedia Commons, под свободными лицензиями",
         "(CC BY / CC BY-SA / CC0 / Public Domain). Для школьной презентации",
         "можно использовать свободно, а авторов принято указать.", "",
         "| № | Подпись на слайде | Файл на Commons | Автор | Лицензия |", "|---|---|---|---|---|"]
for k in sorted(credits, key=int):
    c = credits[k]
    lines.append(f"| {k} | {c['caption']} | [{c['title']}]({c['source']}) | {c['artist']} | {c['license']} |")
with open(os.path.join(BASE, "CREDITS.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\nwritten: images/credits.json, CREDITS.md")
