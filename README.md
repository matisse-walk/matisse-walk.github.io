# matisse-walk.github.io

**Matisse's Montparnasse**: a walk through the Paris of Henri Matisse and his friends, as a comic
book you walk through. Made for the MATISSE project meeting in Paris, 21 October 2026.
Live at <https://matisse-walk.github.io/>. Release 1 (the reading version) is kept at
<https://matisse-walk.github.io/v1/>.

A static site, no build step. GitHub Pages serves the `main` branch root.

| Path | What |
|---|---|
| `index.html` · `app.js` · `app.css` · `content.js` | the app: a MapLibre map over OpenFreeMap tiles recoloured into the Jazz palette, stickers for the stops, a station sheet with the camera over the strip, the "look up" flip to the real artwork, the sticker album, the finale |
| `sw.js` | small service worker: the walk stays available once opened |
| `reading.html`, `map.html`, `stop-1.html` … `stop-5.html`, `steins.html`, `luxembourg.html`, `dinner.html` | the reading version: one page per station, no JavaScript needed; also the print source |
| `style.css` | stylesheet of the reading pages |
| `art/` + `art/credits.json` | 36 public-domain artworks and period photographs, licences read from Wikimedia Commons |
| `audio/` | the episodes (MP3), generated with NotebookLM from fact-checked notes |
| `comic/` | eight six-panel pages drawn in paper-cut style with Gemini; captions are HTML, no real person is depicted |
| `map/` | route GeoJSON, and poster renders of the route from OpenStreetMap data (`tools/render_map.py`) |
| `tools/` | the Commons fetcher and the map renderer |

Original idea and concept, product design and direction, content validation, guide of the walk: Andrey Sadovykh. Research, texts, code and briefs written with Claude (Anthropic) under his direction. Texts CC BY 4.0. Code MIT. Artworks public domain; each carries its credit.
Map data © OpenStreetMap contributors (ODbL); tiles by OpenFreeMap.
