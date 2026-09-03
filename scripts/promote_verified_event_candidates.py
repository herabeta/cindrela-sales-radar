import json, re
from datetime import datetime

CANDIDATES = 'data/event-candidates.json'
OPPORTUNITIES = 'data/opportunities.json'

NIGERIA_TERMS = ('nigeria', 'abuja', 'lagos', 'port harcourt', 'ph', 'ibadan', 'kano')
EVENT_WORDS = ('conference', 'summit', 'expo', 'exhibition', 'festival', 'carnival', 'fair', 'forum', 'championship', 'cup', 'grand prix', 'open', 'meeting', 'congress', 'trade show')
OFFICIAL_DOMAINS = ('fifa.com', 'formula1.com', 'fiaformulae.com', 'atptour.com', 'wtatennis.com', 'fiba.basketball', 'icc-cricket.com')
DATE_RE = re.compile(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:[-–](\d{1,2}))?[,]?\s+(20(?:26|27))\b', re.I)


def parse_date(text):
    m = DATE_RE.search(text or '')
    if not m:
        return ''
    raw = m.group(0).replace('–', '-')
    for fmt in ('%B %d, %Y', '%b %d, %Y'):
        try:
            return datetime.strptime(raw.replace(',', ''), fmt.replace(',', '')).date().isoformat()
        except ValueError:
            pass
    return ''


def slug_id(title):
    return abs(hash(re.sub(r'\W+', ' ', title.lower()).strip())) % 1000000 + 10000

with open(CANDIDATES, encoding='utf-8') as f:
    payload = json.load(f)
with open(OPPORTUNITIES, encoding='utf-8') as f:
    opportunities = json.load(f)

existing_titles = {re.sub(r'\W+', ' ', x.get('title','').lower()).strip() for x in opportunities}
changed = False
promoted = 0
for item in payload.get('items', []):
    title = item.get('title', '').strip()
    low = title.lower()
    if not title or item.get('status') == 'promoted':
        continue
    date_text = item.get('detected_date_text') or ''
    start_date = parse_date(date_text) or parse_date(title)
    official = bool(item.get('official_source_hint')) or any(d in item.get('discovery_url','').lower() for d in OFFICIAL_DOMAINS)
    nigeria = any(term in low for term in NIGERIA_TERMS)
    event_like = any(w in low for w in EVENT_WORDS)

    item['verification'] = {
        'date_confirmed': bool(start_date),
        'location_confirmed': nigeria,
        'official_source_confirmed': official,
        'nigeria_sales_relevance_confirmed': nigeria or ('nigeria' in (item.get('query') or '').lower())
    }

    # Conservative auto-promotion: all verification gates must pass and the event must be Nigeria-local.
    if not (start_date and nigeria and official and event_like):
        item['status'] = 'needs_verification'
        continue

    key = re.sub(r'\W+', ' ', title.lower()).strip()
    if key in existing_titles:
        item['status'] = 'duplicate'
        continue

    city = 'Abuja, Nigeria' if 'abuja' in low else 'Lagos, Nigeria' if 'lagos' in low else 'Nigeria'
    group = 'sports' if any(w in low for w in ('championship', 'cup', 'grand prix', 'open')) else 'business'
    products = ['Flight', 'Hotel', 'Airport Transfer', 'Business Travel'] if group == 'business' else ['Flight', 'Hotel', 'Transfers', 'Group Travel']
    opportunities.append({
        'id': slug_id(title),
        'title': title,
        'start_date': start_date,
        'city': city,
        'group': group,
        'products': products,
        'source': item.get('source') or 'Verified discovery source',
        'url': item.get('discovery_url',''),
        'auto_discovered': True,
        'verification_status': 'auto_verified_nigeria_event'
    })
    existing_titles.add(key)
    item['status'] = 'promoted'
    item['promoted_at'] = datetime.utcnow().isoformat() + 'Z'
    promoted += 1
    changed = True

with open(CANDIDATES, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
with open(OPPORTUNITIES, 'w', encoding='utf-8') as f:
    json.dump(opportunities, f, ensure_ascii=False, indent=2)
print(f'Promoted {promoted} verified Nigeria event candidates; total opportunities: {len(opportunities)}')
