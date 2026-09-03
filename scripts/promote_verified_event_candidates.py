import hashlib, json, re
from datetime import datetime

CANDIDATES = 'data/event-candidates.json'
OPPORTUNITIES = 'data/opportunities.json'

NIGERIA_TERMS = ('nigeria', 'abuja', 'lagos', 'port harcourt', 'ibadan', 'kano')
EVENT_WORDS = ('conference', 'summit', 'expo', 'exhibition', 'festival', 'carnival', 'fair', 'forum', 'championship', 'cup', 'grand prix', 'open', 'meeting', 'congress', 'trade show')
OFFICIAL_DOMAINS = (
    'fifa.com', 'formula1.com', 'fiaformulae.com', 'atptour.com',
    'wtatennis.com', 'fiba.basketball', 'icc-cricket.com', 'cibng.org',
    'nitda.gov.ng', 'arcon.gov.ng', 'gov.ng', 'accinigeria.com',
    'nigeriaminingweek.com', 'nigeriaenergy-ng.com', 'big5constructnigeria.com',
    'propakwestafrica.com', 'akwaabatravelmarket.com', 'agriculturalsocietynigeria.org',
    'lekside.com', 'etiosacarnival.com', 'dettydecfest.com', 'aftifest.com',
    'team-cymru.com', 'n-imex.ng', 'luminik.io', 'ng-plantbreeders.com',
    'aci-africa.aero', 'eventhive.ng',
)
DATE_RE = re.compile(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:[-–]\d{1,2})?[,]?\s+(20(?:26|27))\b', re.I)


def parse_date(text):
    m = DATE_RE.search(text or '')
    if not m:
        return ''
    month_day = re.match(r'([A-Za-z]+)\s+(\d{1,2})', m.group(0))
    if not month_day:
        return ''
    month_name, day, year = month_day.group(1), int(month_day.group(2)), int(m.group(2))
    for fmt in ('%B %d %Y', '%b %d %Y'):
        try:
            return datetime.strptime(f'{month_name} {day} {year}', fmt).date().isoformat()
        except ValueError:
            pass
    return ''


def stable_id(title, used):
    key = re.sub(r'\W+', ' ', title.lower()).strip().encode('utf-8')
    candidate = 10000 + (int(hashlib.sha1(key).hexdigest()[:8], 16) % 900000)
    while candidate in used:
        candidate += 1
    return candidate


with open(CANDIDATES, encoding='utf-8') as f:
    payload = json.load(f)
with open(OPPORTUNITIES, encoding='utf-8') as f:
    opportunities = json.load(f)

existing_titles = {re.sub(r'\W+', ' ', x.get('title', '').lower()).strip() for x in opportunities}
used_ids = {int(x.get('id')) for x in opportunities if str(x.get('id', '')).isdigit()}
promoted = 0

for item in payload.get('items', []):
    title = item.get('title', '').strip()
    low = title.lower()
    if not title or item.get('status') == 'promoted':
        continue

    start_date = parse_date(item.get('detected_date_text') or '') or parse_date(title)
    source_text = f"{item.get('source', '')} {item.get('discovery_url', '')}".lower()
    official = any(domain in source_text for domain in OFFICIAL_DOMAINS)
    nigeria = any(term in low for term in NIGERIA_TERMS)
    event_like = any(word in low for word in EVENT_WORDS)

    item['verification'] = {
        'date_confirmed': bool(start_date),
        'location_confirmed': nigeria,
        'official_source_confirmed': official,
        'nigeria_sales_relevance_confirmed': nigeria or ('nigeria' in (item.get('query') or '').lower()),
    }

    if not (start_date and nigeria and official and event_like):
        item['status'] = 'needs_verification'
        continue

    key = re.sub(r'\W+', ' ', low).strip()
    if key in existing_titles:
        item['status'] = 'duplicate'
        continue

    city = 'Abuja, Nigeria' if 'abuja' in low else 'Lagos, Nigeria' if 'lagos' in low else 'Nigeria'
    group = 'sports' if any(w in low for w in ('championship', 'cup', 'grand prix', 'open')) else 'business'
    products = ['Flight', 'Hotel', 'Airport Transfer', 'Business Travel'] if group == 'business' else ['Flight', 'Hotel', 'Transfers', 'Group Travel']
    new_id = stable_id(title, used_ids)
    opportunities.append({
        'id': new_id,
        'title': title,
        'start_date': start_date,
        'city': city,
        'group': group,
        'products': products,
        'source': item.get('source') or 'Verified discovery source',
        'url': item.get('discovery_url', ''),
        'auto_discovered': True,
        'verification_status': 'auto_verified_nigeria_event',
    })
    used_ids.add(new_id)
    existing_titles.add(key)
    item['status'] = 'promoted'
    item['promoted_at'] = datetime.utcnow().isoformat() + 'Z'
    promoted += 1

with open(CANDIDATES, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
with open(OPPORTUNITIES, 'w', encoding='utf-8') as f:
    json.dump(opportunities, f, ensure_ascii=False, indent=2)
print(f'Promoted {promoted} verified Nigeria event candidates; total opportunities: {len(opportunities)}')
