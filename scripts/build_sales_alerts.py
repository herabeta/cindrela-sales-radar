import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rules = json.loads((ROOT / 'data' / 'alert-rules.json').read_text(encoding='utf-8'))['rules']
# Keep this generator data-driven. It enriches opportunities that include an ISO start_date.
source = ROOT / 'data' / 'opportunities.json'
out = []
if source.exists():
    opportunities = json.loads(source.read_text(encoding='utf-8'))
    for item in opportunities:
        raw = item.get('start_date')
        if not raw:
            continue
        try:
            start = date.fromisoformat(raw)
        except ValueError:
            continue
        days = (start - date.today()).days
        matching = [r for r in rules if days <= r['days_before'] and days >= 0]
        if matching:
            rule = min(matching, key=lambda r: r['days_before'])
            out.append({**item, 'days_until': days, 'alert': rule})

payload = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'rules': rules,
    'alerts': out,
}
(ROOT / 'data' / 'sales-alerts.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Generated {len(out)} sales alerts')
