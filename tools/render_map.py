#!/usr/bin/env python3
"""Render the "Matisse's Montparnasse" walking-route posters (SVG + PNG).

Schematic but geographically exact: every coordinate comes from the route KML
files and from OpenStreetMap (Overpass API, cached in tools/overpass-cache.json).
Nothing is drawn that is not in those two sources.

Usage:
    python -I tools/render_map.py            # uses the cache, fetches once if absent
    python -I tools/render_map.py --refresh  # re-query Overpass
    python -I tools/render_map.py --kml-dir <dir with matisse-walk-{short,long}.kml>

Outputs (in <repo>/map/):
    route-short.svg / .png (1200 px wide) / @2x.png (2400 px wide)
    route-long.svg  / .png / @2x.png
    overlay-check.png  (full bbox, OSM streets in grey under both routes, graticule)

Dependencies: Python 3 + Pillow only (SVG is written by hand, PNG is rasterised with
Pillow at 4x supersampling and downsampled).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAP_DIR = os.path.join(ROOT, "map")
CACHE = os.path.join(HERE, "overpass-cache.json")
DEFAULT_KML_DIR = (r"C:\Users\asadovykh\OneDrive - LA POSTE GROUPE\_work\DOCA_COMM"
                   r"\matisse\paris\social\map")

# --------------------------------------------------------------------------- data
BBOX = (48.834, 2.312, 48.851, 2.340)  # S, W, N, E  (lat/lon)
BBOX_STR = ",".join(str(v) for v in BBOX)
HIGHWAYS = ("primary", "secondary", "tertiary", "residential", "living_street",
            "pedestrian", "unclassified")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = f"""[out:json][timeout:120];
(
  way["highway"~"^({'|'.join(HIGHWAYS)})$"]({BBOX_STR});
  way["railway"="rail"]({BBOX_STR});
  way["leisure"="park"]["name"~"Luxembourg"]({BBOX_STR});
  relation["leisure"="park"]["name"~"Luxembourg"]({BBOX_STR});
  way["landuse"="cemetery"]({BBOX_STR});
  relation["landuse"="cemetery"]({BBOX_STR});
  way["building"="train_station"]({BBOX_STR});
  relation["building"="train_station"]({BBOX_STR});
);
out body; >; out skel qt;"""

VARIANTS = {
    "short": {"kml": "matisse-walk-short.kml", "subtitle": "short walk · 3.3 km · 1h30"},
    "long": {"kml": "matisse-walk-long.kml", "subtitle": "long walk · 4.4 km · 2h"},
}

# --------------------------------------------------------------------------- style (base units = px at 1200 px width)
BASE_W = 1200
CREAM = "#FAF6EE"
INK = "#111111"
GREEN = "#2E7D4F"
CEMETERY = "#D9D4C7"
STATION = "#BFB9A8"
VERMILION = "#E63312"
COBALT = "#1F3A93"
LEMON = "#F5C518"
PIN_GREY = "#8E887B"
PLAZA = "#EFEAE0"

BOULEVARD_W = 9
STREET_W = 2
STREET_OPACITY = 0.35
RAIL_W = 1.5
RAIL_OPACITY = 0.12
ROUTE_W = 7
STOP_R = 16
RING_W = 3
PIN_R = 6
SHADOW = (2.0, 3.0)          # paper cut-out drop shadow offset
SHADOW_OPACITY = 0.16

FONT_FAMILY = "Arial, 'DejaVu Sans', Helvetica, sans-serif"
F_TITLE, F_SUB = 30, 16
F_STOP_LABEL, F_STOP_NUM = 15, 15
F_STREET, F_FEATURE, F_SMALL = 13, 14, 9

BOULEVARD_NAMES = {  # forced thick even if OSM classes them lower (bd Edgar-Quinet)
    "boulevard du montparnasse", "boulevard raspail", "avenue du maine",
    "rue de rennes", "boulevard edgar quinet",
}
STREET_LABELS = {
    "boulevard du montparnasse": "bd du Montparnasse",
    "boulevard raspail": "bd Raspail",
    "avenue du maine": "av. du Maine",
    "rue de rennes": "rue de Rennes",
}

M_PER_DEG = 111_320.0


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[\s\-']+", " ", s.lower()).strip()


# =========================================================================== KML
@dataclass
class Stop:
    number: int | None      # None for the un-numbered "return" waypoint
    name: str
    label: str
    lon: float
    lat: float


@dataclass
class Walk:
    variant: str
    title: str
    stops: list[Stop]
    route: list[tuple[float, float]]
    bonus: list[tuple[str, float, float]]


def short_label(name: str) -> str:
    """'4 · 18:33 · Carrefour Vavin: Balzac, Dôme…' -> 'Carrefour Vavin' (<= 4 words)."""
    tail = name.split("·")[-1].strip()
    tail = re.sub(r"\s*\(.*?\)", "", tail)
    tail = tail.split(":")[0].strip()
    m = re.search(r"\bvia\s+(.+)$", tail, re.I)   # "Return via rue de la Gaîté"
    if m:
        tail = m.group(1)
    words = tail.split()
    return " ".join(words[:4])


def parse_kml(path: str, variant: str) -> Walk:
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    doc = ET.parse(path).getroot().find("k:Document", ns)
    title = (doc.findtext("k:name", default="", namespaces=ns) or "").strip()
    stops, route, bonus = [], [], []
    for folder in doc.findall("k:Folder", ns):
        fname = (folder.findtext("k:name", default="", namespaces=ns) or "").strip()
        for pm in folder.findall("k:Placemark", ns):
            name = (pm.findtext("k:name", default="", namespaces=ns) or "").strip()
            pt = pm.find("k:Point/k:coordinates", ns)
            ls = pm.find("k:LineString/k:coordinates", ns)
            if fname == "Stops" and pt is not None:
                lon, lat = (float(v) for v in pt.text.strip().split(",")[:2])
                m = re.match(r"^\s*(\d+)\s*·", name)
                stops.append(Stop(int(m.group(1)) if m else None, name, short_label(name), lon, lat))
            elif fname == "Route" and ls is not None:
                for tok in ls.text.split():
                    lon, lat = (float(v) for v in tok.split(",")[:2])
                    route.append((lon, lat))
            elif fname.lower().startswith("bonus") and pt is not None:
                lon, lat = (float(v) for v in pt.text.strip().split(",")[:2])
                bonus.append((name, lon, lat))
    if not stops or len(route) < 2:
        raise SystemExit(f"KML {path}: missing Stops or Route")
    return Walk(variant, title, stops, route, bonus)


# =========================================================================== Overpass
def fetch_overpass(cache: str, refresh: bool) -> dict:
    if os.path.exists(cache) and not refresh:
        with open(cache, "rb") as f:
            data = json.load(f)
        print(f"[osm] cache {cache}: {len(data.get('elements', []))} elements")
        return data
    delay, last = 10, None
    for attempt in range(1, 8):
        try:
            req = urllib.request.Request(
                OVERPASS_URL,
                data=urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode(),
                headers={"User-Agent": "matisse-walk-map/1.0 (tools/render_map.py)",
                         "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read()
            data = json.loads(body)
            n = len(data.get("elements", []))
            if n < 100:
                raise RuntimeError(f"suspiciously small result ({n} elements): {data.get('remark')}")
            with open(cache, "wb") as f:
                f.write(body)
            print(f"[osm] fetched {n} elements from Overpass (attempt {attempt}) -> {cache}")
            return data
        except Exception as e:  # noqa: BLE001 - we report and retry
            last = e
            print(f"[osm] attempt {attempt} failed: {e!r}; retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 240)
    raise SystemExit(f"Overpass API unreachable ({last!r}); no cache at {cache}. "
                     "Refusing to invent streets - stop.")


@dataclass
class Osm:
    nodes: dict
    ways: dict
    relations: dict
    streets: list = field(default_factory=list)     # (pts lonlat, thick: bool, name)
    plazas: list = field(default_factory=list)      # pedestrian areas, polygons
    rails: list = field(default_factory=list)
    garden: list = field(default_factory=list)      # polygons (lonlat rings)
    cemetery: list = field(default_factory=list)
    station: list = field(default_factory=list)


def stitch_rings(seqs: list[list[int]]) -> list[list[int]]:
    segs = [list(s) for s in seqs if len(s) >= 2]
    rings = []
    while segs:
        ring = segs.pop()
        progress = True
        while ring[0] != ring[-1] and progress:
            progress = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]:
                    ring += s[1:]
                elif s[-1] == ring[-1]:
                    ring += s[-2::-1]
                elif s[-1] == ring[0]:
                    ring = s[:-1] + ring
                elif s[0] == ring[0]:
                    ring = s[::-1][:-1] + ring
                else:
                    continue
                segs.pop(i)
                progress = True
                break
        if len(ring) >= 4:
            rings.append(ring)
    return rings


def build_osm(data: dict) -> Osm:
    nodes, ways, rels = {}, {}, {}
    for el in data["elements"]:
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways[el["id"]] = el
        elif el["type"] == "relation":
            rels[el["id"]] = el
    osm = Osm(nodes, ways, rels)

    def pts(way):
        return [nodes[n] for n in way.get("nodes", []) if n in nodes]

    def polygons_of(pred):
        polys = []
        used = set()
        for rel in rels.values():
            if not pred(rel.get("tags", {})):
                continue
            outer = []
            for m in rel.get("members", []):
                if m["type"] == "way" and m.get("role", "outer") in ("outer", "") and m["ref"] in ways:
                    outer.append(ways[m["ref"]].get("nodes", []))
                    used.add(m["ref"])
            for ring in stitch_rings(outer):
                polys.append([nodes[n] for n in ring if n in nodes])
        for wid, w in ways.items():
            t = w.get("tags", {})
            if wid in used or not pred(t):
                continue
            p = pts(w)
            if len(p) >= 4 and p[0] == p[-1]:
                polys.append(p)
        return polys

    for w in ways.values():
        t = w.get("tags", {})
        p = pts(w)
        if len(p) < 2:
            continue
        hw = t.get("highway")
        if hw in HIGHWAYS:
            if t.get("area") == "yes" or (hw == "pedestrian" and p[0] == p[-1] and len(p) > 4):
                osm.plazas.append(p)
                continue
            name = norm(t.get("name", ""))
            thick = hw in ("primary", "secondary") or name in BOULEVARD_NAMES
            osm.streets.append((p, thick, name))
        elif t.get("railway") == "rail":
            osm.rails.append(p)

    osm.garden = polygons_of(lambda t: t.get("leisure") == "park" and "luxembourg" in norm(t.get("name", "")))
    osm.cemetery = polygons_of(lambda t: t.get("landuse") == "cemetery")
    osm.station = polygons_of(lambda t: t.get("building") == "train_station")
    print(f"[osm] streets={len(osm.streets)} (thick={sum(1 for s in osm.streets if s[1])}) "
          f"plazas={len(osm.plazas)} rails={len(osm.rails)} garden={len(osm.garden)} "
          f"cemetery={len(osm.cemetery)} station={len(osm.station)}")
    present = {s[2] for s in osm.streets}
    for n in BOULEVARD_NAMES:
        if n not in present:
            print(f"[osm] WARNING: '{n}' not found in OSM data", file=sys.stderr)
    return osm


# =========================================================================== geometry
def poly_area_centroid(poly):
    a = cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    if abs(a) < 1e-9:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return 0.0, (sum(xs) / n, sum(ys) / n)
    a *= 0.5
    return abs(a), (cx / (6 * a), cy / (6 * a))


def clip_poly_rect(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a polygon against an axis-aligned rectangle."""
    def clip(pts, inside, intersect):
        out = []
        if not pts:
            return out
        prev = pts[-1]
        for cur in pts:
            if inside(cur):
                if not inside(prev):
                    out.append(intersect(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(intersect(prev, cur))
            prev = cur
        return out

    def ix(p, q, x):
        t = (x - p[0]) / (q[0] - p[0])
        return (x, p[1] + t * (q[1] - p[1]))

    def iy(p, q, y):
        t = (y - p[1]) / (q[1] - p[1])
        return (p[0] + t * (q[0] - p[0]), y)

    pts = list(poly)
    pts = clip(pts, lambda p: p[0] >= x0, lambda p, q: ix(p, q, x0))
    pts = clip(pts, lambda p: p[0] <= x1, lambda p, q: ix(p, q, x1))
    pts = clip(pts, lambda p: p[1] >= y0, lambda p, q: iy(p, q, y0))
    pts = clip(pts, lambda p: p[1] <= y1, lambda p, q: iy(p, q, y1))
    return pts


def haversine_m(lon1, lat1, lon2, lat2):
    r = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def densify(pts, step):
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d / step))
        for k in range(n):
            t = k / n
            out.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
    if pts:
        out.append(pts[-1])
    return out


# =========================================================================== projection
class Projection:
    """Equirectangular, x scaled by cos(mid-latitude of the data bbox)."""

    def __init__(self, window, width_px):
        self.lonW, self.latS, self.lonE, self.latN = window
        self.k = math.cos(math.radians((BBOX[0] + BBOX[2]) / 2))
        w_m = (self.lonE - self.lonW) * self.k * M_PER_DEG
        h_m = (self.latN - self.latS) * M_PER_DEG
        self.ppm = width_px / w_m                       # px per metre
        self.W = width_px
        self.H = int(round(h_m * self.ppm))

    def xy(self, lon, lat):
        return ((lon - self.lonW) * self.k * M_PER_DEG * self.ppm,
                (self.latN - lat) * M_PER_DEG * self.ppm)

    def lonlat(self, x, y):
        return (self.lonW + x / (self.ppm * M_PER_DEG * self.k),
                self.latN - y / (self.ppm * M_PER_DEG))

    def visible(self, lon, lat, pad=0.0):
        x, y = self.xy(lon, lat)
        return -pad <= x <= self.W + pad and -pad <= y <= self.H + pad


def fit_window(content, margin=0.04):
    """Smallest 3:4 (portrait) or 4:3 (landscape) window inside BBOX that encloses
    `content` (lon/lat points) with `margin` on every side. Returns (window, note)."""
    S, W, N, E = BBOX
    k = math.cos(math.radians((S + N) / 2))

    def mx(lon):
        return (lon - W) * k * M_PER_DEG

    def my(lat):
        return (lat - S) * M_PER_DEG

    xs = [mx(lon) for lon, _ in content]
    ys = [my(lat) for _, lat in content]
    cw, ch = max(xs) - min(xs), max(ys) - min(ys)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    portrait = ch >= cw
    ratio = 4 / 3 if portrait else 3 / 4            # h / w
    w, h = cw / (1 - 2 * margin), ch / (1 - 2 * margin)
    if h / w < ratio:
        h = w * ratio
    else:
        w = h / ratio
    bw, bh = mx(E), my(N)
    note = "portrait 3:4" if portrait else "landscape 4:3"
    if w > bw or h > bh:
        w, h = min(w, bw), min(h, bh)
        note += " (clamped to data bbox, aspect freed)"
    x0 = min(max(cx - w / 2, 0.0), bw - w)
    y0 = min(max(cy - h / 2, 0.0), bh - h)
    win = (W + x0 / (k * M_PER_DEG), S + y0 / M_PER_DEG,
           W + (x0 + w) / (k * M_PER_DEG), S + (y0 + h) / M_PER_DEG)
    return win, note


# =========================================================================== fonts / text metrics
FONT_FILES = {
    True: ["arialbd.ttf", "DejaVuSans-Bold.ttf", "segoeuib.ttf"],
    False: ["arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"],
}
FONT_DIRS = [r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF",
             "/Library/Fonts", os.path.expanduser("~/.fonts")]
_font_cache: dict = {}


def get_font(bold: bool, size: float) -> ImageFont.FreeTypeFont:
    key = (bold, round(size, 2))
    if key in _font_cache:
        return _font_cache[key]
    for d in FONT_DIRS:
        for name in FONT_FILES[bold]:
            p = os.path.join(d, name)
            if os.path.exists(p):
                f = ImageFont.truetype(p, size)
                _font_cache[key] = f
                if ("path", bold) not in _font_cache:
                    _font_cache[("path", bold)] = p
                return f
    f = ImageFont.load_default(size)
    _font_cache[key] = f
    return f


def text_w(text: str, size: float, bold: bool) -> float:
    return float(get_font(bold, size).getlength(text))


# =========================================================================== label placement
def rect_corners(cx, cy, w, h, angle_deg):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    out = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        out.append((cx + dx * c - dy * s, cy + dx * s + dy * c))
    return out


def polys_overlap(a, b):
    """Separating-axis test for two convex polygons."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            nx, ny = y0 - y1, x1 - x0
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def points_in_rect(points, cx, cy, w, h, angle_deg, pad=2.0):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    hw, hh = w / 2 + pad, h / 2 + pad
    n = 0
    for x, y in points:
        dx, dy = x - cx, y - cy
        u = dx * c + dy * s
        v = -dx * s + dy * c
        if -hw <= u <= hw and -hh <= v <= hh:
            n += 1
    return n


class Placer:
    """Greedy label placement with a cost function (overlaps / route / canvas)."""

    def __init__(self, W, H, route_px, boulevard_px, discs):
        self.W, self.H = W, H
        self.route = route_px          # densified
        self.boulevards = boulevard_px  # densified
        self.discs = discs             # (cx, cy, r)
        self.placed = []               # corner polygons

    def cost(self, cx, cy, w, h, angle=0.0):
        corners = rect_corners(cx, cy, w, h, angle)
        c = 0.0
        for x, y in corners:
            if not (6 <= x <= self.W - 6 and 6 <= y <= self.H - 6):
                c += 1000
        for p in self.placed:
            if polys_overlap(corners, p):
                c += 200
        for dx, dy, r in self.discs:
            if polys_overlap(corners, rect_corners(dx, dy, 2 * r + 2, 2 * r + 2, 0)):
                c += 120
        c += 25 * points_in_rect(self.route, cx, cy, w, h, angle)
        c += 6 * points_in_rect(self.boulevards, cx, cy, w, h, angle)
        return c, corners

    def commit(self, corners):
        self.placed.append(corners)


# =========================================================================== scene
# Primitive dicts, coordinates in base units (px at 1200 wide). Two back-ends below.

def P_rect(x, y, w, h, fill, rx=0, opacity=1.0):
    return {"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "rx": rx, "opacity": opacity}


def P_poly(pts, fill, opacity=1.0):
    return {"t": "poly", "pts": pts, "fill": fill, "opacity": opacity}


def P_line(pts, stroke, w, opacity=1.0):
    return {"t": "line", "pts": pts, "stroke": stroke, "w": w, "opacity": opacity}


def P_circle(cx, cy, r, fill, stroke=None, sw=0.0, opacity=1.0):
    return {"t": "circle", "cx": cx, "cy": cy, "r": r, "fill": fill, "stroke": stroke, "sw": sw,
            "opacity": opacity}


def P_text(x, y, s, size, bold=False, fill=INK, anchor="start", angle=0.0, halo=None, italic=False):
    return {"t": "text", "x": x, "y": y, "s": s, "size": size, "bold": bold, "fill": fill,
            "anchor": anchor, "angle": angle, "halo": halo, "italic": italic}


def P_group(items, opacity=1.0):
    return {"t": "group", "items": items, "opacity": opacity}


def shift(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


# =========================================================================== build the poster scene
@dataclass
class Scene:
    W: int
    H: int
    items: list
    proj: Projection


def build_scene(walk: Walk, osm: Osm, subtitle: str) -> tuple[Scene, dict]:
    # ---- content to fit: route, stops, bonus pins, feature anchors
    content = list(walk.route) + [(s.lon, s.lat) for s in walk.stops] + [(b[1], b[2]) for b in walk.bonus]
    anchors = {}
    if osm.garden:
        g = max(osm.garden, key=lambda p: poly_area_centroid(p)[0])
        lons = [p[0] for p in g]
        _, (gx, gy) = poly_area_centroid(g)
        anchors["garden"] = (min(lons) + 0.25 * (max(lons) - min(lons)), gy)
    if osm.cemetery:
        c = max(osm.cemetery, key=lambda p: poly_area_centroid(p)[0])
        anchors["cemetery"] = poly_area_centroid(c)[1]
    if osm.station:
        st = max(osm.station, key=lambda p: poly_area_centroid(p)[0])
        anchors["station"] = poly_area_centroid(st)[1]
    content += list(anchors.values())
    window, note = fit_window(content)
    proj = Projection(window, BASE_W)
    W, H = proj.W, proj.H
    print(f"[{walk.variant}] window lon {window[0]:.5f}..{window[2]:.5f} lat {window[1]:.5f}..{window[3]:.5f} "
          f"-> {W}x{H} base px, {proj.ppm:.3f} px/m, {note}")

    xy = proj.xy
    items = [P_rect(0, 0, W, H, CREAM)]

    # ---- pedestrian plazas (subtle)
    for p in osm.plazas:
        items.append(P_poly([xy(*q) for q in p], PLAZA))

    # ---- paper shapes: cemetery, garden, station (with cut-out shadow)
    def paper(polys, fill):
        shapes = [[xy(*q) for q in p] for p in polys if len(p) >= 3]
        if not shapes:
            return
        items.append(P_group([P_poly(shift(s, *SHADOW), "#000000") for s in shapes], SHADOW_OPACITY))
        for s in shapes:
            items.append(P_poly(s, fill))

    paper(osm.cemetery, CEMETERY)
    paper(osm.garden, GREEN)
    paper(osm.station, STATION)

    # ---- railway (very faint)
    items.append(P_group([P_line([xy(*q) for q in r], INK, RAIL_W) for r in osm.rails], RAIL_OPACITY))

    # ---- streets
    thin = [P_line([xy(*q) for q in p], INK, STREET_W) for p, thick, _ in osm.streets if not thick]
    items.append(P_group(thin, STREET_OPACITY))
    boulevards_px = []
    for p, thick, _ in osm.streets:
        if thick:
            pts = [xy(*q) for q in p]
            boulevards_px.append(pts)
            items.append(P_line(pts, INK, BOULEVARD_W))

    # ---- route ribbon
    route_px = [xy(*q) for q in walk.route]
    items.append(P_group([P_line(shift(route_px, *SHADOW), "#000000", ROUTE_W)], SHADOW_OPACITY))
    items.append(P_line(route_px, VERMILION, ROUTE_W))

    # ---- placer (obstacles)
    discs = []
    numbered = [s for s in walk.stops if s.number is not None]
    for s in numbered:
        x, y = xy(s.lon, s.lat)
        discs.append((x, y, STOP_R + RING_W))
    placer = Placer(W, H, densify(route_px, 6),
                    [q for b in boulevards_px for q in densify(b, 6)], discs)

    # ---- bonus / return pins
    pins = [(b[1], b[2]) for b in walk.bonus] + [(s.lon, s.lat) for s in walk.stops if s.number is None]
    for lon, lat in pins:
        if not proj.visible(lon, lat, pad=-PIN_R):
            print(f"[{walk.variant}] pin at {lon:.5f},{lat:.5f} outside window - dropped")
            continue
        x, y = xy(lon, lat)
        items.append(P_group([P_circle(x + 1, y + 1.5, PIN_R, "#000000")], SHADOW_OPACITY))
        items.append(P_circle(x, y, PIN_R, PIN_GREY, CREAM, 1.5))
        placer.discs.append((x, y, PIN_R))

    # ---- feature labels (fixed at the visible centroid)
    def feature_label(polys, text, two_line_if_narrow=True):
        if not polys:
            return
        best = None
        for p in polys:
            clipped = clip_poly_rect([xy(*q) for q in p], 0, 0, W, H)
            if len(clipped) >= 3:
                a, c = poly_area_centroid(clipped)
                if best is None or a > best[0]:
                    xs = [q[0] for q in clipped]
                    best = (a, c, max(xs) - min(xs))
        if best is None:
            print(f"[{walk.variant}] feature '{text}' not visible - label skipped")
            return
        _, (cx, cy), vis_w = best
        lines = [text]
        if two_line_if_narrow and text_w(text, F_FEATURE, True) + 12 > vis_w and " du " in text:
            a, b = text.split(" du ", 1)
            lines = [a + " du", b]
        lh = F_FEATURE * 1.2
        y0 = cy - lh * (len(lines) - 1) / 2
        for i, ln in enumerate(lines):
            tw = text_w(ln, F_FEATURE, True)
            yy = y0 + i * lh
            cost, corners = placer.cost(cx, yy, tw, F_FEATURE, 0)
            placer.commit(corners)
            items.append(P_text(cx, yy + 0.35 * F_FEATURE, ln, F_FEATURE, True, INK, "middle"))

    feature_label(osm.garden, "Jardin du Luxembourg")
    feature_label(osm.cemetery, "Cimetière du Montparnasse")
    feature_label(osm.station, "Gare Montparnasse")

    # ---- stop discs + numbers
    stop_px = {}
    for s in numbered:
        x, y = xy(s.lon, s.lat)
        stop_px[s.number] = (x, y)
        items.append(P_group([P_circle(x + SHADOW[0], y + SHADOW[1], STOP_R + RING_W / 2, "#000000")],
                             SHADOW_OPACITY))
        if s.number == 0:
            items.append(P_circle(x, y, STOP_R, LEMON))
            items.append(P_text(x, y + 0.36 * F_STOP_NUM, "H", F_STOP_NUM + 1, True, INK, "middle"))
        else:
            items.append(P_circle(x, y, STOP_R, COBALT, LEMON, RING_W))
            items.append(P_text(x, y + 0.36 * F_STOP_NUM, str(s.number), F_STOP_NUM, True, CREAM, "middle"))

    # ---- stop labels (choose the cheapest of 8 positions around the disc)
    for s in numbered:
        x, y = stop_px[s.number]
        tw, th = text_w(s.label, F_STOP_LABEL, True), F_STOP_LABEL
        g = STOP_R + RING_W + 7
        cands = [
            ("start", x + g, y),                        # right
            ("end", x - g, y),                          # left
            ("middle", x, y - g - th * 0.3),            # above
            ("middle", x, y + g + th * 0.3),            # below
            ("start", x + g * 0.8, y - g * 0.8),        # NE
            ("start", x + g * 0.8, y + g * 0.8),        # SE
            ("end", x - g * 0.8, y - g * 0.8),          # NW
            ("end", x - g * 0.8, y + g * 0.8),          # SW
        ]
        best = None
        for i, (anchor, ax, ay) in enumerate(cands):
            cx = ax + tw / 2 if anchor == "start" else ax - tw / 2 if anchor == "end" else ax
            cost, corners = placer.cost(cx, ay, tw, th, 0)
            cost += i * 2  # mild preference for the order above
            if best is None or cost < best[0]:
                best = (cost, anchor, ax, ay, corners)
        _, anchor, ax, ay, corners = best
        placer.commit(corners)
        items.append(P_text(ax, ay + 0.35 * th, s.label, F_STOP_LABEL, True, INK, anchor, halo=CREAM))

    # ---- street labels along the boulevards
    rcx = sum(p[0] for p in route_px) / len(route_px)
    rcy = sum(p[1] for p in route_px) / len(route_px)
    for key, text in STREET_LABELS.items():
        tw, th = text_w(text, F_STREET, False), F_STREET
        off = BOULEVARD_W / 2 + th * 0.55 + 2
        best = None
        for p, thick, name in osm.streets:
            if name != key:
                continue
            pts = [xy(*q) for q in p]
            # split into straight runs
            runs, start = [], 0
            for i in range(1, len(pts) - 1):
                a1 = math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0])
                a2 = math.atan2(pts[i + 1][1] - pts[i][1], pts[i + 1][0] - pts[i][0])
                d = abs((math.degrees(a2 - a1) + 180) % 360 - 180)
                if d > 14:
                    runs.append(pts[start:i + 1])
                    start = i
            runs.append(pts[start:])
            for run in runs:
                dense = densify(run, 4)
                length = sum(math.hypot(dense[i + 1][0] - dense[i][0], dense[i + 1][1] - dense[i][1])
                             for i in range(len(dense) - 1))
                if length < tw + 14:
                    continue
                ang = math.degrees(math.atan2(run[-1][1] - run[0][1], run[-1][0] - run[0][0]))
                # never upside down; near-vertical streets read bottom-to-top (map convention)
                if ang > 80 or ang <= -100:
                    ang += 180 if ang <= -100 else -180
                a = math.radians(ang)
                nx, ny = -math.sin(a), math.cos(a)
                for t in (0.5, 0.35, 0.65, 0.2, 0.8):
                    idx = min(len(dense) - 1, int(t * (len(dense) - 1)))
                    mx, my = dense[idx]
                    for side in (-1, 1):
                        cx, cy = mx + side * off * nx, my + side * off * ny
                        cost, corners = placer.cost(cx, cy, tw, th, ang)
                        cost -= min(length, 400) * 0.05          # prefer long straight runs
                        cost += 0.03 * math.hypot(cx - rcx, cy - rcy)  # ...near the walk, not the edge
                        if best is None or cost < best[0]:
                            best = (cost, cx, cy, ang, corners)
        if best is None:
            print(f"[{walk.variant}] no room for street label '{text}'")
            continue
        _, cx, cy, ang, corners = best
        placer.commit(corners)
        items.append(P_text(cx, cy + 0.35 * th, text, F_STREET, False, INK, "middle", angle=ang, halo=CREAM))

    # ---- title card (top-left)
    pad = 16
    tw_title = text_w("Matisse's Montparnasse", F_TITLE, True)
    tw_sub = text_w(subtitle, F_SUB, False)
    cw = max(tw_title, tw_sub) + 2 * pad
    ch = pad + F_TITLE + 10 + F_SUB + pad
    cx0, cy0 = 24, 24
    items.append(P_group([P_rect(cx0 + 3, cy0 + 4, cw, ch, "#000000", 3)], 0.18))
    items.append(P_rect(cx0, cy0, cw, ch, CREAM, 3))
    items.append(P_rect(cx0, cy0, 6, ch, VERMILION, 0))            # paper tab
    items.append(P_text(cx0 + pad + 4, cy0 + pad + F_TITLE * 0.78, "Matisse's Montparnasse", F_TITLE, True))
    items.append(P_text(cx0 + pad + 4, cy0 + pad + F_TITLE + 10 + F_SUB * 0.78, subtitle, F_SUB, False))

    # ---- scale bar (500 m) + north arrow, bottom-right
    L = 500 * proj.ppm
    bx1, by = W - 60, H - 34
    bx0 = bx1 - L
    items.append(P_line([(bx0, by), (bx1, by)], CREAM, 10))
    items.append(P_line([(bx0, by), (bx1, by)], INK, 4))
    for x in (bx0, (bx0 + bx1) / 2, bx1):
        items.append(P_line([(x, by - 7), (x, by + 3)], INK, 2))
    items.append(P_text(bx0, by - 12, "0", F_SMALL + 2, False, INK, "middle", halo=CREAM))
    items.append(P_text(bx1, by - 12, "500 m", F_SMALL + 2, True, INK, "middle", halo=CREAM))
    nx, ny = W - 30, H - 30
    items.append(P_poly([(nx, ny - 26), (nx - 8, ny), (nx, ny - 6), (nx + 8, ny)], CREAM))
    items.append(P_poly([(nx, ny - 24), (nx - 6, ny - 2), (nx, ny - 7)], INK))
    items.append(P_poly([(nx, ny - 24), (nx + 6, ny - 2), (nx, ny - 7)], "#777777"))
    items.append(P_text(nx, ny - 30, "N", F_SMALL + 3, True, INK, "middle", halo=CREAM))

    # ---- attribution (required by the ODbL)
    items.append(P_text(12, H - 10, "Map data © OpenStreetMap contributors (ODbL) · route & stops: MATISSE walk KML",
                        F_SMALL, False, "#555555", "start", halo=CREAM))

    meta = {"window": window, "note": note, "stop_px": stop_px, "route_px": route_px}
    return Scene(W, H, items, proj), meta


# =========================================================================== SVG back-end
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".") if abs(v) >= 0.05 else "0"


def svg_item(it) -> str:
    t = it["t"]
    op = "" if it.get("opacity", 1.0) >= 1 else f' opacity="{it["opacity"]}"'
    if t == "rect":
        rx = f' rx="{it["rx"]}"' if it["rx"] else ""
        return (f'<rect x="{fmt(it["x"])}" y="{fmt(it["y"])}" width="{fmt(it["w"])}" height="{fmt(it["h"])}"'
                f' fill="{it["fill"]}"{rx}{op}/>')
    if t == "poly":
        if len(it["pts"]) < 3:
            return ""
        d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in it["pts"]) + " Z"
        return f'<path d="{d}" fill="{it["fill"]}"{op}/>'
    if t == "line":
        if len(it["pts"]) < 2:
            return ""
        d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in it["pts"])
        return (f'<path d="{d}" fill="none" stroke="{it["stroke"]}" stroke-width="{it["w"]}"'
                f' stroke-linecap="round" stroke-linejoin="round"{op}/>')
    if t == "circle":
        st = f' stroke="{it["stroke"]}" stroke-width="{it["sw"]}"' if it["stroke"] else ""
        return f'<circle cx="{fmt(it["cx"])}" cy="{fmt(it["cy"])}" r="{it["r"]}" fill="{it["fill"]}"{st}{op}/>'
    if t == "text":
        fw = ' font-weight="bold"' if it["bold"] else ""
        fs = ' font-style="italic"' if it["italic"] else ""
        halo = (f' stroke="{it["halo"]}" stroke-width="{max(2.0, it["size"] * 0.22):.1f}" stroke-linejoin="round"'
                f' paint-order="stroke"') if it["halo"] else ""
        tr = f' transform="rotate({it["angle"]:.1f} {fmt(it["x"])} {fmt(it["y"] - 0.35 * it["size"])})"' \
            if abs(it["angle"]) > 0.01 else ""
        return (f'<text x="{fmt(it["x"])}" y="{fmt(it["y"])}" font-size="{it["size"]}" text-anchor="{it["anchor"]}"'
                f'{fw}{fs} fill="{it["fill"]}"{halo}{tr}>{esc(it["s"])}</text>')
    if t == "group":
        inner = "\n".join(svg_item(i) for i in it["items"])
        return f'<g{op}>\n{inner}\n</g>'
    raise ValueError(t)


def write_svg(scene: Scene, path: str, title: str):
    body = "\n".join(svg_item(i) for i in scene.items)
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene.W}" height="{scene.H}" '
           f'viewBox="0 0 {scene.W} {scene.H}" font-family="{FONT_FAMILY}">\n'
           f'<title>{esc(title)}</title>\n'
           f'<desc>Generated by tools/render_map.py from KML + OpenStreetMap (ODbL). Equirectangular projection.</desc>\n'
           f'{body}\n</svg>\n')
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


# =========================================================================== Pillow back-end
def hex_rgba(color: str, alpha: float = 1.0):
    c = color.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(round(255 * alpha)))


class Painter:
    def __init__(self, W, H, S):
        self.S = S
        self.size = (int(round(W * S)), int(round(H * S)))
        self.img = Image.new("RGBA", self.size, hex_rgba(CREAM))

    def sc(self, v):
        return v * self.S

    def pts(self, pts):
        return [(x * self.S, y * self.S) for x, y in pts]

    def draw_items(self, items, target):
        d = ImageDraw.Draw(target)
        for it in items:
            t = it["t"]
            op = it.get("opacity", 1.0)
            if t == "group":
                layer = Image.new("RGBA", self.size, (0, 0, 0, 0))
                self.draw_items(it["items"], layer)
                if op < 1:
                    layer.putalpha(layer.getchannel("A").point(lambda v, o=op: int(v * o)))
                target.alpha_composite(layer)
                d = ImageDraw.Draw(target)
            elif t == "rect":
                x, y, w, h = (self.sc(it[k]) for k in ("x", "y", "w", "h"))
                d.rounded_rectangle([x, y, x + w, y + h], radius=self.sc(it["rx"]), fill=hex_rgba(it["fill"], op))
            elif t == "poly":
                p = self.pts(it["pts"])
                if len(p) >= 3:
                    d.polygon(p, fill=hex_rgba(it["fill"], op))
            elif t == "line":
                p = self.pts(it["pts"])
                if len(p) < 2:
                    continue
                w = max(1, int(round(self.sc(it["w"]))))
                col = hex_rgba(it["stroke"], op)
                d.line(p, fill=col, width=w, joint="curve")
                r = w / 2
                for x, y in (p[0], p[-1]):
                    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
            elif t == "circle":
                cx, cy, r = self.sc(it["cx"]), self.sc(it["cy"]), self.sc(it["r"])
                if it["stroke"]:
                    sw = self.sc(it["sw"])
                    d.ellipse([cx - r - sw / 2, cy - r - sw / 2, cx + r + sw / 2, cy + r + sw / 2],
                              fill=hex_rgba(it["stroke"], op))
                    d.ellipse([cx - r + sw / 2, cy - r + sw / 2, cx + r - sw / 2, cy + r - sw / 2],
                              fill=hex_rgba(it["fill"], op))
                else:
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hex_rgba(it["fill"], op))
            elif t == "text":
                self.text(target, it)

    def text(self, target, it):
        size = self.sc(it["size"])
        font = get_font(it["bold"], size)
        x, y = self.sc(it["x"]), self.sc(it["y"])
        anchor = {"start": "ls", "middle": "ms", "end": "rs"}[it["anchor"]]
        halo = it["halo"]
        sw = int(round(max(2.0, it["size"] * 0.22) * self.S / 2)) if halo else 0
        kw = dict(font=font, fill=hex_rgba(it["fill"]), anchor=anchor)
        if halo:
            kw.update(stroke_width=sw, stroke_fill=hex_rgba(halo))
        if abs(it["angle"]) < 0.01:
            ImageDraw.Draw(target).text((x, y), it["s"], **kw)
            return
        # rotated: draw on a small layer around the text's centre, rotate, paste
        tw = font.getlength(it["s"])
        pad = int(size * 1.5) + sw
        lw, lh = int(tw + 2 * pad), int(size * 2 + 2 * pad)
        layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((lw / 2, lh / 2 + 0.35 * size), it["s"],
                                   **{**kw, "anchor": "ms"})
        rot = layer.rotate(-it["angle"], resample=Image.BICUBIC, expand=True)
        cx, cy = x, y - 0.35 * size
        target.alpha_composite(rot, (int(round(cx - rot.width / 2)), int(round(cy - rot.height / 2))))

    def render(self, items):
        self.draw_items(items, self.img)
        return self.img


def write_pngs(scene: Scene, out_1x: str, out_2x: str, supersample=4):
    big = Painter(scene.W, scene.H, supersample).render(scene.items)
    for path, width in ((out_2x, 2 * BASE_W), (out_1x, BASE_W)):
        h = int(round(big.height * width / big.width))
        im = big.resize((width, h), Image.LANCZOS).convert("RGB")
        im.save(path, optimize=True)
        print(f"[png] {path}: {width}x{h}")


# =========================================================================== credibility checks
def check_stops(walk: Walk, scene: Scene, meta: dict) -> bool:
    ok = True
    proj = scene.proj
    print(f"[{walk.variant}] credibility check (tolerance 25 m):")
    for s in walk.stops:
        if s.number is None:
            continue
        x, y = meta["stop_px"][s.number]
        # the disc as it is actually rasterised at 1200 px: pixel-rounded centre
        lon, lat = proj.lonlat(round(x), round(y))
        d_disc = haversine_m(s.lon, s.lat, lon, lat)
        # how far the stop lies from the route ribbon (informative)
        d_route_px = min(seg_dist((x, y), meta["route_px"][i], meta["route_px"][i + 1])
                         for i in range(len(meta["route_px"]) - 1))
        d_route = d_route_px / proj.ppm
        inside = 0 <= x <= scene.W and 0 <= y <= scene.H
        status = "OK " if d_disc <= 25 and inside else "FAIL"
        ok &= status == "OK "
        print(f"   {status} stop {s.number} {s.label!r:32} disc->KML {d_disc:5.1f} m   "
              f"route->stop {d_route:5.1f} m   px=({x:.0f},{y:.0f})")
    return ok


def overlay_check(osm: Osm, walks: list[Walk], windows: dict, path: str):
    """Full data bbox at 1200 px: OSM streets grey, routes on top, stops numbered, graticule."""
    S, Wb, N, E = BBOX
    proj = Projection((Wb, S, E, N), BASE_W)
    xy = proj.xy
    W, H = proj.W, proj.H
    items = [P_rect(0, 0, W, H, "#FFFFFF")]
    for polys, col in ((osm.cemetery, "#DDDDDD"), (osm.garden, "#CFE8D4"), (osm.station, "#CCCCCC"),
                       (osm.plazas, "#EEEEEE")):
        for p in polys:
            items.append(P_poly([xy(*q) for q in p], col))
    items.append(P_group([P_line([xy(*q) for q in r], "#444444", 1) for r in osm.rails], 0.5))
    for p, thick, _ in osm.streets:
        items.append(P_line([xy(*q) for q in p], "#8A8A8A", 3 if thick else 1.2))
    # graticule every 0.005 deg
    lon = math.ceil(Wb / 0.005) * 0.005
    while lon < E:
        x = xy(lon, S)[0]
        items.append(P_line([(x, 0), (x, H)], "#5B9BD5", 0.8, 0.8))
        items.append(P_text(x + 3, 12, f"{lon:.3f}E", F_SMALL, False, "#2F6DB5"))
        lon += 0.005
    lat = math.ceil(S / 0.005) * 0.005
    while lat < N:
        y = xy(Wb, lat)[1]
        items.append(P_line([(0, y), (W, y)], "#5B9BD5", 0.8, 0.8))
        items.append(P_text(4, y - 3, f"{lat:.3f}N", F_SMALL, False, "#2F6DB5"))
        lat += 0.005
    colors = {"short": VERMILION, "long": COBALT}
    for w in walks:
        col = colors.get(w.variant, INK)
        items.append(P_line([xy(*q) for q in w.route], col, 3 if w.variant == "short" else 2, 0.9))
        win = windows[w.variant]
        x0, y0 = xy(win[0], win[3])
        x1, y1 = xy(win[2], win[1])
        items.append(P_line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], col, 1.2, 0.7))
        items.append(P_text(x0 + 4, y0 + (12 if w.variant == "short" else 26),
                            f"{w.variant} poster window", F_SMALL, True, col))
    for w in walks:
        for s in w.stops:
            if s.number is None:
                continue
            x, y = xy(s.lon, s.lat)
            items.append(P_circle(x, y, 7, colors.get(w.variant, INK), "#FFFFFF", 1.5))
            items.append(P_text(x, y + 3.5, str(s.number), 9, True, "#FFFFFF", "middle"))
            items.append(P_text(x + 10, y + 4, s.label, F_SMALL, False, "#333333", "start", halo="#FFFFFF"))
        for name, lon, lat in w.bonus:
            x, y = xy(lon, lat)
            items.append(P_circle(x, y, 4, "#777777"))
    items.append(P_text(10, H - 10,
                        f"Overlay check - OSM data (grey) vs routes - bbox {S}..{N} N, {Wb}..{E} E - "
                        f"compare with https://www.openstreetmap.org/#map=16/{(S + N) / 2:.4f}/{(Wb + E) / 2:.4f}",
                        F_SMALL, False, "#333333", "start", halo="#FFFFFF"))
    big = Painter(W, H, 2).render(items)
    big.resize((BASE_W, int(round(big.height * BASE_W / big.width))), Image.LANCZOS).convert("RGB").save(path)
    print(f"[png] {path}: {BASE_W}x{int(round(big.height * BASE_W / big.width))}")


# =========================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kml-dir", default=DEFAULT_KML_DIR)
    ap.add_argument("--out-dir", default=MAP_DIR)
    ap.add_argument("--refresh", action="store_true", help="re-query Overpass even if a cache exists")
    ap.add_argument("--no-png", action="store_true")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):          # Windows consoles default to cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    os.makedirs(args.out_dir, exist_ok=True)
    osm = build_osm(fetch_overpass(CACHE, args.refresh))
    print(f"[font] bold={_font_cache.get(('path', True)) or get_font(True, 12) and _font_cache.get(('path', True))} "
          f"regular={get_font(False, 12) and _font_cache.get(('path', False))}")

    all_ok, walks, windows = True, [], {}
    for variant, cfg in VARIANTS.items():
        walk = parse_kml(os.path.join(args.kml_dir, cfg["kml"]), variant)
        walks.append(walk)
        scene, meta = build_scene(walk, osm, cfg["subtitle"])
        windows[variant] = meta["window"]
        svg_path = os.path.join(args.out_dir, f"route-{variant}.svg")
        write_svg(scene, svg_path, f"Matisse's Montparnasse - {cfg['subtitle']}")
        print(f"[svg] {svg_path}: {scene.W}x{scene.H} (viewBox)")
        if not args.no_png:
            write_pngs(scene, os.path.join(args.out_dir, f"route-{variant}.png"),
                       os.path.join(args.out_dir, f"route-{variant}@2x.png"))
        all_ok &= check_stops(walk, scene, meta)

    overlay_check(osm, walks, windows, os.path.join(args.out_dir, "overlay-check.png"))
    print("[check] ALL STOPS WITHIN 25 m" if all_ok else "[check] SOME STOPS FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
