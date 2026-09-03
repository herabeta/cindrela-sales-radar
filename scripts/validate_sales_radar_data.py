import glob, json, re, sys
from datetime import date, datetime

OPP = 'data/opportunities.json'
PLAYS = 'data/event-sales-plays.json'
errors = []

with open(OPP, encoding='utf-8') as f:
    opportunities = json.load(f)
with open(PLAYS, encoding='utf-8') as f:
    plays = json.load(f)

ids = [str(x.get('id')) for x in opportunities]
if len(ids) != len(set(ids)):
    errors.append('Duplicate opportunity IDs found')

titles = [re.sub(r'\W+', ' ', x.get('title','').lower()).strip() for x in opportunities]
if len(titles) != len(set(titles)):
    errors.append('Duplicate opportunity titles found')

months = set()
for o in opportunities:
    d = o.get('start_date', '')
    try:
        dt = datetime.strptime(d, '%Y-%m-%d').date()
        months.add((dt.year, dt.month))
    except ValueError:
        errors.append(f"Invalid start_date: {o.get('title')} -> {d}")
    if not o.get('title') or not o.get('city') or not o.get('url'):
        errors.append(f"Incomplete opportunity fields: {o.get('title')}")

for o in opportunities:
    p = plays.get(str(o.get('id')))
    if not isinstance(p, list) or len(p) < 6 or any(not str(v).strip() for v in p[:6]):
        errors.append(f"Missing/incomplete six-field sales play: {o.get('id')} {o.get('title')}")

# If the master data spans multiple months, no month may silently disappear between first and last.
if months:
    cur = min(months)
    last = max(months)
    while cur <= last:
        if cur not in months:
            errors.append(f"Missing event month in master timeline: {cur[0]}-{cur[1]:02d}")
        y, m = cur
        cur = (y + 1, 1) if m == 12 else (y, m + 1)

# Key event-facing pages must read the master opportunity feed rather than carry their own event list.
for path in ('index.html', 'event-calendar-full.html'):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    if 'opportunities.json' not in text:
        errors.append(f'{path} does not read data/opportunities.json')

if errors:
    print('VALIDATION FAILED')
    for e in errors:
        print('-', e)
    sys.exit(1)

print(f'VALIDATION OK: {len(opportunities)} opportunities, {len(months)} populated months, six-field sales plays present.')
