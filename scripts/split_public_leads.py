import json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'data' / 'public-lead-contacts.json'
OUT = ROOT / 'data' / 'leads-by-event'
INDEX = ROOT / 'data' / 'public-lead-index.json'

# Event-wise split keeps Lead Finder fast without removing the master dataset.

def slug(s):
    s = re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')
    return s[:90] or 'event'

contacts = json.loads(MASTER.read_text(encoding='utf-8')) if MASTER.exists() else []
opps = json.loads((ROOT / 'data' / 'opportunities.json').read_text(encoding='utf-8'))
OUT.mkdir(parents=True, exist_ok=True)

for p in OUT.glob('*.json'):
    p.unlink()

by_event = {str(e.get('title','')): [] for e in opps if e.get('title')}
for c in contacts:
    title = str(c.get('event') or '').strip()
    if title in by_event:
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
print(f'Split {len(contacts)} master contacts across {len(index)} events')
