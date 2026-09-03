import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data' / 'opportunities.json'
PLAYS = ROOT / 'data' / 'event-sales-plays.json'
SPORT_WORDS = ('fifa','fiba','grand prix','prix','e-prix','super bowl','olympic','tennis','basketball','cricket','rugby','golf','football')
TRAVEL_WORDS = ('travel','tourism','hospitality','akwaaba','itb')
TECH_WORDS = ('gitex','tech','cyber','digital','mwc','afrofuture','rise','software')
EDU_WORDS = ('education','university','school','student')
ENERGY_WORDS = ('energy','mining','oil','gas')


def infer_target(item):
    title = item.get('title','').lower(); group = item.get('group','')
    if any(w in title for w in SPORT_WORDS) or group == 'sports':
        if 'tennis' in title or 'open' in title: return 'Nigerian tennis fans, families, player supporters and premium leisure travellers'
        if 'fifa' in title or 'football' in title or 'afcon' in title: return 'Nigerian football supporters, families, sports groups and delegation planners'
        return 'Nigerian sports fans, premium leisure travellers, families and organised groups'
    if any(w in title for w in TECH_WORDS): return 'Nigerian technology companies, founders, IT leaders, investors and corporate teams'
    if any(w in title for w in EDU_WORDS): return 'Students, parents, education agents and families planning study-related travel'
    if any(w in title for w in ENERGY_WORDS): return 'Energy/mining companies, executives, exhibitors, suppliers and technical delegates'
    if any(w in title for w in TRAVEL_WORDS): return 'Travel companies, tourism executives, exhibitors, buyers and visiting delegates'
    if group == 'seasonal': return 'Families, diaspora visitors, holiday travellers and organised leisure groups'
    return 'Exhibitors, speakers, delegates, executives, buyers and visiting company teams'


def dynamic_contact(days):
    if days < 0: return 'Event passed — close active event outreach and move to the next relevant opportunity'
    if days <= 7: return 'Contact today; focus on ready-to-book travellers and immediate availability'
    if days <= 21: return 'Start active outreach now; qualify dates, traveller count and booking readiness'
    if days <= 45: return 'Begin targeted outreach now; move qualified leads toward quotation'
    if days <= 90: return 'Start prospecting now; build the target list and open early conversations'
    if days <= 180: return 'Start planning now; identify Nigerian prospects and prepare travel options'
    return 'Early planning stage; build the target list and monitor for confirmed travel intent'


def dynamic_follow(days):
    if days < 0: return 'No routine follow-up; close or recycle the event lead'
    if days <= 7: return 'Follow up every 24–48 hours on active enquiries'
    if days <= 21: return 'Follow up every 2–3 days with qualified prospects'
    if days <= 45: return 'Follow up every 3–5 days with active prospects'
    if days <= 90: return 'Follow up weekly and update booking status'
    return 'Review every 2–4 weeks until the event enters the active sales window'


def dynamic_priority(days):
    if days < 0: return 'CLOSED'
    if days <= 21: return 'HOT'
    if days <= 90: return 'WARM'
    return 'EARLY'


def dynamic_why(item, days):
    title = item.get('title',''); city = item.get('city','')
    if days < 0: return f'{title} has passed; preserve any converted leads and shift effort to the next travel opportunity'
    if days <= 7: return f'{title} is within one week in {city}; remaining travel enquiries are time-sensitive'
    if days <= 30: return f'{title} is within 30 days in {city}; flight, hotel and transfer decisions should be moving now'
    if days <= 90: return f'{title} is within the next 90 days; early outreach can capture travel demand before customers book elsewhere'
    return f'{title} is a future opportunity in {city}; early lead building gives Cindrela more time to qualify and convert travel demand'


def read_existing():
    if not PLAYS.exists(): return {}
    data = json.loads(PLAYS.read_text(encoding='utf-8'))
    return data.get('plays', data) if isinstance(data, dict) else {}

opportunities = json.loads(OPP.read_text(encoding='utf-8'))
existing = read_existing()
out = {}
for item in opportunities:
    raw = item.get('start_date')
    if not raw: continue
    try: days = (date.fromisoformat(raw) - date.today()).days
    except ValueError: continue
    old = existing.get(str(item.get('id')), [])
    target = old[0] if len(old) > 0 and old[0] else infer_target(item)
    products = old[1] if len(old) > 1 and old[1] else ' + '.join(item.get('products', []))
    out[str(item['id'])] = [target, products, dynamic_contact(days), dynamic_priority(days), dynamic_follow(days), dynamic_why(item, days)]

# Keep the existing UI contract: event id -> six Sales Lead Play fields.
# Metadata is stored under a reserved key that the UI ignores.
out['_engine_meta'] = {
    'generated_at': datetime.utcnow().isoformat() + 'Z',
    'engine': 'dynamic-date-sales-play-v1',
    'reference_date': date.today().isoformat(),
    'rules': 'WHEN TO CONTACT, LEAD PRIORITY, FOLLOW-UP and WHY NOW are recalculated from each event date every run.'
}
PLAYS.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Generated dynamic sales plays for {len(out)-1} opportunities using {date.today().isoformat()}')
