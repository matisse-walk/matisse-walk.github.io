"""Merge tools/places2.json (verified Matisse places) into content.js as kind 'place' points of interest,
fetching each Commons image into art/ and appending its licence to art/credits.json. Run from the repo root."""
import json, urllib.request, urllib.parse, io, re, html
from PIL import Image
UA = {'User-Agent': 'matisse-walk/1.0 (andrey.sadovykh@docaposte.fr)'}

def api(params):
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))

def fetch(slug, title):
    if not title.startswith('File:'): title = 'File:' + title
    r = api({'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'iiurlwidth': 1400, 'format': 'json'})
    p = list(r['query']['pages'].values())[0]
    if 'imageinfo' not in p:
        print('MISSING', title); return None
    ii = p['imageinfo'][0]; m = ii['extmetadata']
    lic = m.get('LicenseShortName', {}).get('value'); artist = re.sub('<[^>]+>', '', html.unescape(m.get('Artist', {}).get('value', ''))).strip()[:80]
    data = urllib.request.urlopen(urllib.request.Request(ii.get('thumburl') or ii['url'], headers=UA), timeout=60).read()
    im = Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((1400, 1400)); im.save(f'art/{slug}.jpg', quality=85, optimize=True)
    print(slug, im.size, lic, '|', artist[:50]); return {'lic': lic, 'artist': artist, 'title': title}

places = json.load(open('tools/places2.json', encoding='utf-8'))
creds = json.load(open('art/credits.json', encoding='utf-8'))
existing = set(re.findall(r'"id": "([^"]+)"', open('content.js', encoding='utf-8').read()))
out = []
for p in places:
    slug = p['id']
    if slug in existing: print('skip existing', slug); continue
    o = {'id': slug, 'kind': 'place', 'name': p['name'], 'sub': p['sub'], 'coord': [round(p['coord'][0], 6), round(p['coord'][1], 6)], 'text': p['text']}
    if str(p.get('address', '')).lower().find('unverified') >= 0 or 'unverified' in json.dumps(p).lower():
        o['sub'] = p['sub'] + ' (location approximate)'
    if p.get('commons_file'):
        i = fetch(slug, p['commons_file'])
        if i:
            o['img'] = f'art/{slug}.jpg'
            o['credit'] = p.get('image_credit_line') or (f"{i['artist']}, {i['lic']}" if i['lic'] and not i['lic'].startswith('Public') else 'Public domain')
            creds['saved'].append({'slug': slug, 'file': o['img'], 'title': i['title'][5:], 'licence': i['lic'], 'commons_url': 'https://commons.wikimedia.org/wiki/' + i['title'].replace(' ', '_'), 'photographer_or_uploader_credit': i['artist'], 'sources': p.get('source_urls', [])})
    out.append(o)
json.dump(creds, open('art/credits.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
s = open('content.js', encoding='utf-8').read()
i = s.index('"id": "grand-palais"'); j = s.index('\n  ],', i)
s = s[:j] + ",\n" + ",\n".join("    " + json.dumps(o, ensure_ascii=False) for o in out) + s[j:]
open('content.js', 'w', encoding='utf-8').write(s)
print('merged', len(out))
