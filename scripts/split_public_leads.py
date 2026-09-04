import json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data' / 'public-lead-contacts.json'
MANUAL = ROOT / 'data' / 'manual-public-leads.json'
OUT = ROOT / 'data' / 'leads-by-event'
INDEX = ROOT / 'data' / 'public-lead-index.json'

# Event-wise split keeps Lead Finder fast without removing the master dataset.
# manual-public-leads.json is a small supplemental layer for freshly verified
# public contacts; the master dataset remains untouched and preserved.

def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
    return s[:90] or 'event'

contacts = json.loads(MASTER.read_text(encoding='utf-8')) if MASTER.exists() else []
manual = json.loads(MANUAL.read_text(encoding='utf-8')) if MANUAL.exists() else []
opps = json.loads((ROOT / 'data' / 'opportunities.json').read_text(encoding='utf-8'))
OUT.mkdir(parents=True, exist_ok=True)

for p in OUT.glob('*.json'):
    p.unlink()

by_event = {str(e.get('title','')): [] for e in opps if e.get('title')}
seen = set()
for c in contacts + manual:
    title = str(c.get('event') or '').strip()
    if title not in by_event:
        continue
    key = (title, str(c.get('leadId') or ''), str(c.get('company') or ''), str(c.get('contactPerson') or ''), str(c.get('businessEmail') or ''), str(c.get('businessPhone') or ''))
    if key in seen:
        continue
    seen.add(key)
    by_event[title].append(c)

index = {}
used = set()
for e in opps:
    title = str(e.get('title') or '').strip()
    if not title:
        continue
    base = slug(title)
    name = base
    n = 2
    while name in used:
        name = f'{base}-{n}'; n += 1
    used.add(name)
    rows = by_event.get(title, [])
    (OUT / f'{name}.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    index[str(e.get('id'))] = {'title': title, 'file': f'/data/leads-by-event/{name}.json', 'count': len(rows)}

INDEX.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'Split {len(contacts)} master + {len(manual)} supplemental contacts across {len(index)} events')
