import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data' / 'opportunities.json'
PLAYS = ROOT / 'data' / 'event-sales-plays.json'

# Keep the future timeline from stopping at June 2027. This is a verified July phase of the FIFA Women's World Cup.
EVENT = {
    'id': 168,
    'title': "FIFA Women's World Cup Brazil 2027 — July Knockout & Finals Phase",
    'start_date': '2027-07-10',
    'city': 'Brazil — multiple host cities',
    'group': 'sports',
    'products': ['Flight', 'Hotel', 'Transfers', 'Visa Assistance', 'Group Travel', 'Family Travel'],
    'source': 'FIFA',
    'url': 'https://www.fifa.com/en/tournaments/womens/womensworldcup/brazil-2027',
    'sales_market': 'Nigeria',
    'sales_reason': 'Nigerian supporters, families, sports groups and delegations may travel during the July knockout and finals phase',
}
PLAY = [
    'Nigerian football supporters, families, sports groups, delegations and premium leisure travellers',
    'Flights + Hotels + Transfers + Visa Assistance + Group Travel + Family Travel',
    'Start active outreach in April–May 2027; prioritise confirmed travellers 4–8 weeks before July travel',
    'EARLY',
    'Follow up weekly in planning stage, then every 2–3 days once dates and match plans are confirmed',
    'The FIFA Women’s World Cup runs through 25 July 2027, with knockout matches and the final in July across Brazil’s host cities',
]

items = json.loads(OPP.read_text(encoding='utf-8'))
by_id = {int(x['id']): x for x in items}
by_id.setdefault(EVENT['id'], EVENT)
items = sorted(by_id.values(), key=lambda x: (x.get('start_date', '9999-99-99'), int(x.get('id', 0))))
OPP.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

plays = json.loads(PLAYS.read_text(encoding='utf-8')) if PLAYS.exists() else {}
plays.setdefault(str(EVENT['id']), PLAY)
PLAYS.write_text(json.dumps(plays, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Future month coverage checked; July 2027 is represented by the verified FIFA knockout/finals phase.')
