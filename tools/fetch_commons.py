"""Fetch public-domain / CC images from Wikimedia Commons for the matisse-walk site.

For every (slug, Commons file name) pair:
  1. query the Commons API for the file page's wikitext + extmetadata
     (licence tag, artist, credit, date, description);
  2. download https://commons.wikimedia.org/wiki/Special:FilePath/<name>?width=1600;
  3. convert to JPEG q85, max 1600 px on the long side, save as <out>/<slug>.jpg;
  4. write <out>/_fetch_report.json with everything found, for the credits file.

Usage:
  python -I fetch_commons.py <out_dir> <wanted.json>
wanted.json: {"slug": "File name without File: prefix", ...}
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image

UA = "matisse-walk/1.0 (andrey.sadovykh@docaposte.fr)"
API = "https://commons.wikimedia.org/w/api.php"
MAX_PX = 1600
QUALITY = 85

LICENCE_TEMPLATES = re.compile(
    r"\{\{\s*((?:PD-Art|PD-old|PD-US|PD-scan|PD-anon|PD-France|PD-1996|PD-100|PD-70|"
    r"PD-Russia|PD-Sweden|PD-Norway|PD-Denmark|PD-Italy|PD-Germany|PD-Portugal|PD-Turkey|PD-Spain|"
    r"PD-because|PD-author|PD-self|PD-ineligible|PD-text|PD-BnF|PD-GallicaScan|PD-Gallica|"
    r"PD-Art-two|PD-old-auto|PD-old-100|PD-old-70|Licensed-PD-Art|Licensed-PD-Art-two|"
    r"PD-US-expired|PD-US-not renewed|PD-US-no notice|PD-1923|"
    r"cc-by[-\w.]*|cc-zero|CC0|cc0|CC-BY[-\w.]*|Cc-by[-\w.]*|Cc-zero|"
    r"Flickr[-\w ]*|Wikimedia Sverige|Nationalmuseum Stockholm|Google Art Project|"
    r"MoMA[-\w ]*|Met-Open-Access|Artwork|Information|Photograph|Art Photo)"
    r"\b[^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
    re.IGNORECASE,
)


def http_get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                return data if binary else data.decode("utf-8")
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def api(params):
    params = dict(params, format="json", formatversion="2")
    return json.loads(http_get(API + "?" + urllib.parse.urlencode(params)))


def file_info(name):
    """Return dict with wikitext, extmetadata, canonical title, original url, size."""
    title = "File:" + name
    data = api({
        "action": "query", "titles": title, "redirects": "1",
        "prop": "imageinfo|revisions",
        "iiprop": "url|size|mime|extmetadata",
        "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|Artist|Credit|"
                               "DateTimeOriginal|ImageDescription|ObjectName|Permission|"
                               "AttributionRequired|Copyrighted|UsageTerms|Attribution",
        "rvprop": "content", "rvslots": "main",
    })
    pages = data["query"]["pages"]
    page = pages[0]
    if page.get("missing"):
        return {"missing": True, "title": title}
    ii = page["imageinfo"][0]
    wikitext = page["revisions"][0]["slots"]["main"]["content"]
    ext = {k: v.get("value") for k, v in ii.get("extmetadata", {}).items()}
    tags = []
    for m in re.finditer(r"\{\{\s*([^{}|\n]+?)\s*(?:\||\}\})", wikitext):
        t = m.group(1).strip()
        if re.match(r"(?i)^(PD|cc|CC|Licensed|Flickr|Art Photo|Attribution|Self|GFDL|"
                    r"Wikimedia|Nationalmuseum|Google|MoMA|Met|Gallica|BnF|Anonymous|"
                    r"Free screenshot|Copyrighted free use)", t):
            tags.append(t)
    # Also catch PD-Art wrapper with inner licence: {{PD-Art|PD-old-100-expired}}
    for m in re.finditer(r"\{\{\s*(PD-Art[^|{}]*)\|([^{}]+?)\}\}", wikitext, re.I):
        tags.append(m.group(1).strip() + "|" + m.group(2).strip())
    for m in re.finditer(r"\{\{\s*(Licensed-PD-Art[^|{}]*)\|([^{}]+?)\}\}", wikitext, re.I):
        tags.append(m.group(1).strip() + "|" + m.group(2).strip())
    seen, uniq = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return {
        "missing": False,
        "title": page["title"],
        "canonical_name": page["title"][len("File:"):],
        "original_url": ii.get("url"),
        "original_width": ii.get("width"),
        "original_height": ii.get("height"),
        "mime": ii.get("mime"),
        "extmetadata": ext,
        "licence_templates": uniq,
        "wikitext": wikitext,
    }


def filepath_url(name):
    return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + urllib.parse.quote(name.replace(" ", "_"), safe="(),'!*-._~")
            + f"?width={MAX_PX}")


def download_convert(name, out_path):
    url = filepath_url(name)
    raw = http_get(url, binary=True)
    im = Image.open(io.BytesIO(raw))
    im.load()
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        rgba = im.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size
    if max(w, h) > MAX_PX:
        scale = MAX_PX / max(w, h)
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    im.save(out_path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return im.size, url


def strip_html(s):
    if not s:
        return s
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out_dir, wanted_path = sys.argv[1], sys.argv[2]
    with open(wanted_path, encoding="utf-8") as f:
        wanted = json.load(f)
    report = {}
    for slug, name in wanted.items():
        print(f"--- {slug}: {name}")
        try:
            info = file_info(name)
        except Exception as e:  # noqa: BLE001
            print(f"    API error: {e}")
            report[slug] = {"file": name, "error": f"api: {e}"}
            continue
        if info["missing"]:
            print("    MISSING on Commons")
            report[slug] = {"file": name, "missing": True}
            continue
        ext = info["extmetadata"]
        entry = {
            "file": info["canonical_name"],
            "commons_url": "https://commons.wikimedia.org/wiki/"
                           + urllib.parse.quote(info["title"].replace(" ", "_"), safe="(),'!*-._~:"),
            "original_px": [info["original_width"], info["original_height"]],
            "licence_short": ext.get("LicenseShortName"),
            "licence_url": ext.get("LicenseUrl"),
            "licence_templates": info["licence_templates"],
            "artist": strip_html(ext.get("Artist")),
            "credit": strip_html(ext.get("Credit")),
            "date": strip_html(ext.get("DateTimeOriginal")),
            "object_name": strip_html(ext.get("ObjectName")),
            "description": strip_html(ext.get("ImageDescription"))[:600] if ext.get("ImageDescription") else None,
            "permission": strip_html(ext.get("Permission"))[:400] if ext.get("Permission") else None,
            "wikitext_head": info["wikitext"][:2500],
        }
        print(f"    licence: {entry['licence_short']}  templates: {entry['licence_templates']}")
        print(f"    artist: {entry['artist']}  date: {entry['date']}")
        try:
            size, url = download_convert(info["canonical_name"], f"{out_dir}/{slug}.jpg")
            entry["saved_px"] = list(size)
            entry["fetched_from"] = url
            print(f"    saved {size[0]}x{size[1]}")
        except Exception as e:  # noqa: BLE001
            print(f"    download error: {e}")
            entry["error"] = f"download: {e}"
        report[slug] = entry
        time.sleep(0.5)
    with open(f"{out_dir}/_fetch_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("report written")


if __name__ == "__main__":
    main()
