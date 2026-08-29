import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

QUERIES = {
    'Nigeria / Abuja events': 'Nigeria Abuja events conference exhibition 2026 2027',
    'Nigeria visa / travel': 'Nigeria visa travel update 2026 2027',
    'Africa exhibitions': 'Africa exhibition conference 2026 2027 Nigeria',
    'China exhibitions': 'China exhibition trade fair 2026 2027 Africa Nigeria',
    'World exhibitions': 'world exhibition conference 2026 2027 Nigeria business',
    'Sports opportunities': 'Nigeria Africa sports event 2026 2027',
    'Seasonal / holidays': 'Nigeria holidays observances 2026 2027 Mothering Sunday Fathers Day',
}

PLAYBOOK = {
    'Nigeria / Abuja events': {
        'target': 'Exhibitors, speakers, delegates, executives and visiting companies',
        'products': 'Flight + Hotel + Airport Transfer + Business Travel',
        'action': 'Find the official event/exhibitor list and start outreach before travel bookings peak.',
        'priority': 'HOT'
    },
    'Nigeria visa / travel': {
        'target': 'International travellers, exhibitors and Nigerian business travellers',
        'products': 'Visa assistance + Flight + Hotel + Airport Transfer',
        'action': 'Turn the update into a travel checklist and contact affected travellers early.',
        'priority': 'HOT'
    },
    'Africa exhibitions': {
        'target': 'African exhibitors, buyers, founders and corporate delegates',
        'products': 'Regional Flights + Hotel + Transfers + Group Travel',
        'action': 'Build a country/company target list and offer a complete travel package.',
        'priority': 'WARM'
    },
    'China exhibitions': {
        'target': 'Nigerian importers, sourcing teams and China-bound business travellers',
        'products': 'China Visa Support + Flight + Hotel + Local Transfers',
        'action': 'Start prospecting Nigerian businesses likely to attend the exhibition.',
        'priority': 'HOT'
    },
    'World exhibitions': {
        'target': 'Nigerian companies attending international trade shows',
        'products': 'International Flight + Visa Support + Hotel + Transfers',
        'action': 'Identify Nigerian exhibitors/attendees and contact them before registration closes.',
        'priority': 'WARM'
    },
    'Sports opportunities': {
        'target': 'Teams, officials, sponsors, media and travelling fans',
        'products': 'Flights + Hotel + Transfers + Group Travel',
        'action': 'Track official dates/venues and prepare group travel offers early.',
        'priority': 'WARM'
    },
    'Seasonal / holidays': {
        'target': 'Families, corporate travellers and holiday planners',
        'products': 'Flights + Hotel + Weekend Getaways + Transfers',
        'action': 'Start campaign planning weeks/months before the holiday date.',
        'priority': 'WARM'
    },
}

def rss(query):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl':'en-NG', 'gl':'NG', 'ceid':'NG:en'})
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 Cindrela-Sales-Radar'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml, category):
    root = ET.fromstring(xml)
    out=[]
    for item in root.findall('./channel/item')[:10]:
        title=(item.findtext('title') or '').strip()
        link=(item.findtext('link') or '').strip()
        pub=(item.findtext('pubDate') or '').strip()
        source=item.findtext('source') or 'Google News'
        if title and link:
            play=PLAYBOOK[category]
            out.append({
                'category': category,
                'title': title,
                'source': source,
                'published': pub,
                'url': link,
                'priority': play['priority'],
                'target': play['target'],
                'products': play['products'],
                'action': play['action']
            })
    return out

items=[]
for category, query in QUERIES.items():
    try:
        items.extend(parse(rss(query), category))
    except Exception as e:
        items.append({'category':category,'title':'Feed refresh failed','source':'System','published':'','url':'','error':str(e), **PLAYBOOK[category]})

seen=set(); clean=[]
for x in items:
    key=(x['category'],x['title'])
    if key not in seen:
        seen.add(key); clean.append(x)

payload={
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'status': 'live',
    'sales_rule': 'News is a discovery signal. Verify event dates/details with an official source before quoting customers.',
    'items': clean
}
with open('data/daily-intelligence.json','w',encoding='utf-8') as f:
    json.dump(payload,f,ensure_ascii=False,indent=2)
print(f'Wrote {len(clean)} intelligence items')
