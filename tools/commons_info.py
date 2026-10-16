"""Print licence/author metadata for Commons files, or list a category.

Usage:
  python -I commons_info.py "File name" ["File name" ...]
  python -I commons_info.py --cat "Category:Name"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I drops the script dir
from fetch_commons import api, file_info, strip_html  # noqa: E402


def list_category(cat, limit=200):
    out = []
    cont = {}
    while True:
        data = api(dict({"action": "query", "list": "categorymembers", "cmtitle": cat,
                         "cmtype": "file", "cmlimit": "500"}, **cont))
        out += [m["title"] for m in data["query"]["categorymembers"]]
        if "continue" in data and len(out) < limit:
            cont = data["continue"]
        else:
            break
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if args and args[0] == "--cat":
        for c in args[1:]:
            print("=== " + c)
            for t in list_category(c):
                print("   " + t)
        return
    for name in args:
        info = file_info(name)
        print("=== " + name)
        if info["missing"]:
            print("   MISSING")
            continue
        e = info["extmetadata"]
        print(f"   canonical: {info['canonical_name']}  {info['original_width']}x{info['original_height']}")
        print(f"   licence: {e.get('LicenseShortName')}  templates: {info['licence_templates']}")
        print(f"   artist: {strip_html(e.get('Artist'))}")
        print(f"   credit: {strip_html(e.get('Credit'))}")
        print(f"   date: {strip_html(e.get('DateTimeOriginal'))}")
        d = strip_html(e.get("ImageDescription"))
        print(f"   desc: {d[:300] if d else None}")
        print("   --- wikitext head ---")
        print("   " + info["wikitext"][:1200].replace("\n", "\n   "))


if __name__ == "__main__":
    main()
