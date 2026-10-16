"""Search Wikimedia Commons (namespace File) for candidate file names.

Usage: python -I commons_search.py "query 1" "query 2" ...
"""
import json
import sys
import urllib.parse
import urllib.request

UA = "matisse-walk/1.0 (andrey.sadovykh@docaposte.fr)"
API = "https://commons.wikimedia.org/w/api.php"


def api(params):
    params = dict(params, format="json")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def search(q, limit=15):
    data = api({
        "action": "query", "list": "search", "srsearch": q,
        "srnamespace": "6", "srlimit": str(limit),
    })
    return [hit["title"] for hit in data["query"]["search"]]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for q in sys.argv[1:]:
        print("=== " + q)
        for t in search(q):
            print("   " + t)
