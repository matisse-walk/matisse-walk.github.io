"""Add the Matisse places (non-station points of interest) to content.js: geocode, fetch pictures from
Commons with their licences, append to credits.json. Run once from the repo root."""
import json, urllib.request, urllib.parse, io, re, html
from PIL import Image
UA = {'User-Agent': 'matisse-walk/1.0 (andrey.sadovykh@docaposte.fr)'}

def geo(q):
    u = 'https://api-adresse.data.gouv.fr/search/?' + urllib.parse.urlencode({'q': q, 'limit': 1})
    f = json.load(urllib.request.urlopen(u, timeout=20))['features'][0]
    return f['geometry']['coordinates'], f['properties']['label']

def api(params):
    u = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))

def fetch(slug, title):
    r = api({'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'iiurlwidth': 1400, 'format': 'json'})
    p = list(r['query']['pages'].values())[0]
    if 'imageinfo' not in p:
        print('MISSING', title); return None
    ii = p['imageinfo'][0]; m = ii['extmetadata']
    lic = m.get('LicenseShortName', {}).get('value'); artist = re.sub('<[^>]+>', '', html.unescape(m.get('Artist', {}).get('value', ''))).strip()
    data = urllib.request.urlopen(urllib.request.Request(ii.get('thumburl') or ii['url'], headers=UA), timeout=60).read()
    im = Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((1400, 1400)); im.save(f'art/{slug}.jpg', quality=85, optimize=True)
    print(slug, im.size, lic, '|', artist[:60]); return {'lic': lic, 'artist': artist}

PLACES = [
 ('quai-saint-michel', '19 quai Saint-Michel 75005 Paris', '19 quai Saint-Michel', "Matisse's studio, 1895–1907 and 1914–17",
  "His Paris views were all painted from these windows: Notre-Dame and the Pont Saint-Michel, from the naturalistic canvases of 1900–04 to the blue lines of 1914, and the Studio, quai Saint-Michel of 1916–17. A plaque names the painters who worked here, Matisse and Marquet among them.",
  "File:Henri Matisse, 1902, Notre-Dame, une fin d'après-midi, oil on paper mounted on canvas, 72.4 x 54.6 cm, Albright-Knox Art Gallery.jpg", "Henri Matisse, Notre-Dame, une fin d'après-midi, 1902. Buffalo AKG. Public domain."),
 ('couvent-des-oiseaux', '86 rue de Sèvres 75007 Paris', 'Couvent des Oiseaux', 'The Académie Matisse opened here, January 1908',
  "A disused convent at 84–88 rue de Sèvres. Sarah Stein and Hans Purrmann talked Matisse into teaching; Michael Stein paid; the Swede Carl Palme had begged first. The school opened here in January 1908 and moved within months to the Hôtel Biron. The convent was demolished at the end of 1909; nothing survives.",
  'File:Bâtiments dans le jardin du couvent des Oiseaux, 7ème arrondissement, Paris, PH80761.jpg', 'The convent garden, photographed in May 1909, months before demolition. Paris Musées, CC0.'),
 ('hotel-biron', '33 boulevard des Invalides 75007 Paris', 'Hôtel Biron', "The school's second home, 1908–09; Rodin next door",
  "In spring 1908 Matisse moved his family, his studio and the school into the former Sacré-Cœur convent on the Hôtel Biron estate. Rodin had rooms in the mansion: the man who had sent him away in 1899 was now his neighbour. Dance (I) was painted here in early 1909. Matisse left for Issy in July 1909; the mansion is the Musée Rodin today.",
  'File:Hôtel Biron in 1910.jpg', 'The Hôtel Biron around 1910. Public domain.'),
 ('musee-du-luxembourg', '19 rue de Vaugirard 75006 Paris', 'Musée du Luxembourg', "The State's first Matisse for a Paris museum, 1922",
  "The museum of living artists at the garden's corner. From 1897 it showed the Caillebotte bequest, the first Impressionists in a national museum, which drew young painters to this side of the river. In 1922 the State bought Odalisque à la culotte rouge for it, seventeen years after the wild beasts; Matisse agreed by letter on 7 March 1922. The picture is at the Centre Pompidou now.",
  'File:Odalisque à la culotte rouge Henri Matisse 1921 Centre Pompidou.jpg', 'Henri Matisse, Odalisque à la culotte rouge, 1921. Centre Pompidou. Public domain in the EU.'),
 ('hotel-lutetia', '45 boulevard Raspail 75006 Paris', 'Hôtel Lutetia', 'Matisse wrote from here, August 1939',
  "On 19 August 1939, with war days away, Matisse wrote to his dealer Paul Rosenberg on Lutetia letterhead while his paintings in the boulevard du Montparnasse flat were being packed for the vaults of the Banque de France.",
  'File:Hôtel Lutetia, Paris 6e.jpg', 'The Lutetia today. Photo {artist}, {lic}.'),
 ('musee-bourdelle', '18 rue Antoine Bourdelle 75015 Paris', "Bourdelle's studio", 'Where Matisse took sculpture classes, around 1900',
  "Antoine Bourdelle lived and worked here from 1885 to his death in 1929. Around 1900 Rodin, Bourdelle and Desbois ran a free sculpture school, and one of the students was Henri Matisse. Bourdelle's Héraklès archer stands in the street-side garden; the model was a cavalry officer who could hold the pose twenty minutes at a time. Museum open 10–18, free.",
  None, None),
 ('friesz-studio', '73 rue Notre-Dame-des-Champs 75006 Paris', "Othon Friesz's studio", 'A wild beast of 1905, here from 1914 to 1949',
  "The Fauve Othon Friesz hung beside Matisse in the room the press called the cage of wild beasts at the 1905 Salon d'Automne. He worked in this building, Bouguereau's former studio, for thirty-five years and lies in the Montparnasse cemetery. At number 86 across the street, in 1917–20, American sculptors made painted copper masks for soldiers whose faces the war had destroyed.",
  None, None),
 ('rousseau-rue-perrel', '2 bis rue Perrel 75014 Paris', "Douanier Rousseau's last studio", 'The lion that hung beside the wild beasts',
  "Henri Rousseau, the self-taught painter, bought this studio in 1909 with money from sales to the dealer Vollard; he died the next year. At the 1905 Salon d'Automne his Hungry Lion hung alongside Matisse and Derain and may have fed the critic's joke about wild beasts. He paid off his grocer, Père Junier, by painting the man's new horse and cart.",
  'File:Henri Rousseau - La Carriole du Père Junier.jpg', "Henri Rousseau, La Carriole du Père Junier, 1908. Musée de l'Orangerie. Public domain."),
 ('grand-palais', '3 avenue du Général Eisenhower 75008 Paris', 'Grand Palais', 'Where the wild beasts were named, October 1905',
  "The Salon d'Automne of 1905 hung Matisse, Derain, Vlaminck, Marquet, Manguin and Friesz together in Room VII. The critic Louis Vauxcelles, seeing a classical-style bust by Albert Marque in the middle of the room, wrote in Gil Blas on 17 October: Donatello among the wild beasts. Leo Stein bought Woman with a Hat straight out of the show. Across the river and a walk away; the story is told at the station square.",
  "File:Gil Blas Salon d'Automne pA 1905 10 17 Louis Vauxcelles.jpg", 'Gil Blas, 17 October 1905: the review that named the Fauves. Gallica, public domain.'),
]

out = []; creds = json.load(open('art/credits.json', encoding='utf-8'))
for slug, addr, name, sub, text, f, credit in PLACES:
    c, label = geo(addr); img = None
    if f:
        i = fetch(slug, f)
        if i:
            img = f'art/{slug}.jpg'
            credit = credit.replace('{artist}', i['artist']).replace('{lic}', i['lic'] or '')
            creds['saved'].append({'slug': slug, 'file': img, 'title': f[5:], 'licence': i['lic'], 'commons_url': 'https://commons.wikimedia.org/wiki/' + f.replace(' ', '_'), 'photographer_or_uploader_credit': i['artist']})
    o = {'id': slug, 'kind': 'place', 'name': name, 'sub': sub, 'coord': [round(c[0], 6), round(c[1], 6)], 'text': text}
    if img: o.update({'img': img, 'credit': credit})
    out.append(o); print(slug, c, label)
json.dump(creds, open('art/credits.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
s = open('content.js', encoding='utf-8').read()
block = ",\n".join("    " + json.dumps(o, ensure_ascii=False) for o in out)
marker = 'text: "Facing the old station.'
i = s.index(marker); j = s.index('\n  ],', i)
s = s[:j] + ",\n" + block + s[j:]
open('content.js', 'w', encoding='utf-8').write(s); print('places added', len(out))
