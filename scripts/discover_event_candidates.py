import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Phase 2: discover newly reported future events without polluting Sales Opportunities.
# Candidates remain unverified until a source/date/location can be confirmed.
QUERIES = [
    'Nigeria Abuja new event conference exhibition 2026 2027',
    'Nigeria Lagos new event conference exhibition festival 2026 2027',
    'Africa new conference exhibition trade fair 2026 2027',
    'international conference exhibition summit 2026 2027 Nigeria attendees',
    'FIFA football tournament 2026 2027 upcoming',
    'F1 Formula 1 race 2026 2027 upcoming',
    'ATP WTA tennis 2026 2027 upcoming',
    'FIBA basketball 2026 2027 upcoming',
    'ICC cricket 2026 2027 upcoming',
    'major festival carnival 2026 2027 upcoming',
    'global business conference summit 2026 2027 upcoming',
    'tourism travel event 2026 2027 upcoming',
]

OFFICIAL_HINTS = ('gov', 'org', 'fifa.com', 'formula1.com', 'fiaformulae.com', 'atptour.com', 'wtatennis.com', 'fiba.basketball', 'icc-cricket.com')
MONTHS = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
DATE_RE = re.compile(rf'\b{MONTHS}\s+\d{{1,2}}(?:[-–]\d{{1,2}})?[,]?\s+20(?:26|27)\b', re.I)


def rss(query):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl': 'en-NG', 'gl': 'NG', 'ceid': 'NG:en'})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Cindrela-Sales-Radar'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def parse(xml, query):
    root = ET.fromstring(xml)
    out = []
    for item in root.findall('./channel/item')[:15]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        source = (item.findtext('source') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        if not title or not link:
            continue
        low = title.lower()
        # Candidate must look event/travel relevant and preferably mention a future year.
        event_words = ('conference', 'summit', 'expo', 'exhibition', 'festival', 'carnival', 'fair', 'forum', 'championship', 'cup', 'grand prix', 'open', 'meeting', 'congress', 'trade show')
        if not any(w in low for w in event_words):
            continue
        year = re.search(r'20(?:26|27)', title)
        if not year:
            continue
        official_hint = any(h in link.lower() or h in source.lower() for h in OFFICIAL_HINTS)
        out.append({
            'title': title,
            'source': source or 'Google News',
            'discovery_url': link,
            'published': pub,
            'query': query,
            'detected_date_text': (DATE_RE.search(title).group(0) if DATE_RE.search(title) else ''),
            'official_source_hint': official_hint,
            'status': 'needs_verification',
            'verification': {
                'date_confirmed': False,
                'location_confirmed': False,
                'official_source_confirmed': False,
                'nigeria_sales_relevance_confirmed': False
            }
        })
    return out

items = []
for q in QUERIES:
    try:
        items.extend(parse(rss(q), q))
    except Exception as e:
        print('Discovery feed failed:', q, e)

seen = set()
clean = []
for x in items:
    key = re.sub(r'\W+', ' ', x['title'].lower()).strip()
    if key and key not in seen:
        seen.add(key)
        clean.append(x)

payload = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'engine': 'Phase 2 event discovery inbox',
    'status': 'discovery_only',
    'rule': 'Discovered news is never promoted directly to Sales Opportunities. Verify official source, date, location and Nigeria travel-sales relevance first.',
    'items': clean
}
with open('data/event-candidates.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print(f'Wrote {len(clean)} event candidates')
