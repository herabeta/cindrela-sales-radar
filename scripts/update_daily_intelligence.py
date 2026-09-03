import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Broad discovery layer: Nigeria-first plus worldwide travel-demand signals.
# Google News is used for discovery; official sources must be checked before quoting dates.
QUERIES = {
    'Nigeria / Abuja events': 'Nigeria Abuja events conference exhibition 2026 2027',
    'Nigeria / Lagos events': 'Nigeria Lagos events conference exhibition festival 2026 2027',
    'Nigeria visa / travel': 'Nigeria visa travel update 2026 2027',
    'Africa exhibitions': 'Africa exhibition conference trade fair 2026 2027',
    'China exhibitions': 'China exhibition trade fair 2026 2027 Nigeria Africa',
    'Middle East exhibitions': 'Dubai Abu Dhabi Doha exhibition conference 2026 2027',
    'Europe exhibitions': 'Europe exhibition conference trade fair 2026 2027',
    'Asia exhibitions': 'Asia exhibition conference trade fair 2026 2027',
    'Americas exhibitions': 'USA Canada Brazil exhibition conference trade fair 2026 2027',
    'World exhibitions': 'international exhibition conference trade fair 2026 2027',
    'FIFA / football': 'FIFA football tournament 2026 2027 upcoming event',
    'Olympics / youth sports': 'Olympics youth olympics international sports 2026 2027 upcoming',
    'Formula 1 / motorsport': 'Formula 1 F1 motorsport race 2026 2027 upcoming',
    'Tennis': 'ATP WTA tennis tournament 2026 2027 upcoming',
    'Basketball': 'FIBA basketball tournament 2026 2027 upcoming',
    'Cricket': 'ICC cricket tournament 2026 2027 upcoming',
    'Rugby': 'rugby world cup international rugby 2026 2027 upcoming',
    'Golf': 'golf major tournament 2026 2027 upcoming',
    'Global festivals': 'major festival carnival music culture 2026 2027 upcoming worldwide',
    'Global conferences': 'major global conference summit 2026 2027 upcoming',
    'Tourism / hospitality': 'tourism travel hospitality event 2026 2027 worldwide',
    'Visa / border / travel rules': 'visa immigration border travel rules Nigeria 2026 latest',
    'Airline / route changes': 'airline route new flight Nigeria Africa Europe Middle East 2026 latest',
    'Seasonal / holidays': 'global holidays festivals travel demand September October November December 2026',
}

PLAYBOOK = {
    'Nigeria / Abuja events': ('Exhibitors, speakers, delegates, executives and visiting companies', 'Flight + Hotel + Airport Transfer + Business Travel', 'Find the official event/exhibitor list and start outreach before travel bookings peak.', 'HOT'),
    'Nigeria / Lagos events': ('Exhibitors, delegates, creators, executives and visiting companies', 'Flight + Hotel + Airport Transfer + Business Travel', 'Verify the event and build a target list of exhibitors, speakers and delegates.', 'HOT'),
    'Nigeria visa / travel': ('International travellers, exhibitors and Nigerian business travellers', 'Visa assistance + Flight + Hotel + Airport Transfer', 'Turn the update into a travel checklist and contact affected travellers early.', 'HOT'),
    'Africa exhibitions': ('African exhibitors, buyers, founders and corporate delegates', 'Regional Flights + Hotel + Transfers + Group Travel', 'Build a country/company target list and offer a complete travel package.', 'WARM'),
    'China exhibitions': ('Nigerian importers, exhibitors, sourcing teams and business travellers', 'China Visa Support + Flight + Hotel + Local Transfers', 'Start prospecting Nigerian businesses likely to attend the exhibition.', 'HOT'),
    'Middle East exhibitions': ('Nigerian/African exhibitors, buyers and corporate travellers', 'Visa Support + Flight + Hotel + Transfers + Business Travel', 'Identify exhibitors and attendees from Nigeria/Africa and start early outreach.', 'HOT'),
    'Europe exhibitions': ('Nigerian/African exhibitors, buyers and corporate delegates', 'Schengen/Travel Support + Flight + Hotel + Transfers', 'Identify Nigerian companies attending and prepare early travel options.', 'WARM'),
    'Asia exhibitions': ('Nigerian/African importers, exhibitors and sourcing teams', 'Visa Support + Flight + Hotel + Transfers', 'Identify Nigerian participants and start outreach before travel demand peaks.', 'WARM'),
    'Americas exhibitions': ('Nigerian/African exhibitors, executives and business travellers', 'Visa Support + International Flight + Hotel + Transfers', 'Target Nigerian companies attending international exhibitions and conferences.', 'WARM'),
    'World exhibitions': ('Nigerian companies attending international trade shows', 'International Flight + Visa Support + Hotel + Transfers', 'Identify Nigerian exhibitors/attendees and contact them before registration closes.', 'WARM'),
    'FIFA / football': ('Football fans, clubs, teams, media, sponsors and corporate groups', 'Flights + Hotels + Transfers + Visa Assistance + Group Travel', 'Verify the official tournament page, dates and host cities, then build a group-travel lead list.', 'HOT'),
    'Olympics / youth sports': ('Athletes, families, officials, teams, media and supporters', 'Flights + Hotels + Transfers + Group Travel', 'Track official dates/venues and prepare group travel offers early.', 'WARM'),
    'Formula 1 / motorsport': ('Fans, sponsors, teams, media and corporate hospitality groups', 'Flights + Hotels + Transfers + Group Travel', 'Use the official calendar to identify race weekends and target travellers early.', 'WARM'),
    'Tennis': ('Fans, players, teams, sponsors and corporate travellers', 'Flights + Hotels + Transfers + Group Travel', 'Verify official tournament dates and target Nigerian/African travellers.', 'WARM'),
    'Basketball': ('Fans, teams, officials, sponsors and travelling groups', 'Flights + Hotels + Transfers + Group Travel', 'Track official tournament dates and prepare group travel options.', 'WARM'),
    'Cricket': ('Fans, teams, officials, sponsors and diaspora travellers', 'Flights + Hotels + Transfers + Group Travel', 'Track official fixtures and target group/fan travel from Nigeria/Africa.', 'WARM'),
    'Rugby': ('Fans, teams, officials, sponsors and corporate groups', 'Flights + Hotels + Transfers + Group Travel', 'Track official tournament dates and target international travellers early.', 'WARM'),
    'Golf': ('Golf fans, players, sponsors, executives and hospitality groups', 'Flights + Hotels + Transfers + Business/Leisure Travel', 'Verify tournament dates and target premium/group travellers.', 'WARM'),
    'Global festivals': ('Diaspora visitors, tourists, families, creators and groups', 'Flights + Hotels + Airport Transfers + Holiday Packages', 'Verify the official event calendar and package the destination around the event.', 'WARM'),
    'Global conferences': ('Executives, delegates, speakers, exhibitors and investors', 'Flights + Hotels + Airport Transfers + Business Travel', 'Identify Nigerian/African participants and contact them before bookings peak.', 'WARM'),
    'Tourism / hospitality': ('Tour operators, hotels, travellers, delegates and destination visitors', 'Flights + Hotels + Transfers + Holiday Packages', 'Turn confirmed events into destination packages and lead lists.', 'WARM'),
    'Visa / border / travel rules': ('Travellers, exhibitors, students and corporate delegates', 'Visa Assistance + Flights + Hotels + Transfers', 'Verify the government/embassy source before communicating the change to customers.', 'HOT'),
    'Airline / route changes': ('Travellers, corporate accounts and groups', 'Flights + Hotels + Transfers', 'Verify airline and airport announcements, then identify affected routes and customers.', 'HOT'),
    'Seasonal / holidays': ('Families, corporate travellers, diaspora visitors and holiday planners', 'Flights + Hotels + Weekend Getaways + Transfers', 'Start campaign planning weeks/months before the demand peak.', 'WARM'),
}

def rss(query):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({
        'q': query, 'hl': 'en-NG', 'gl': 'NG', 'ceid': 'NG:en'
    })
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Cindrela-Sales-Radar'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml, category):
    root = ET.fromstring(xml)
    target, products, action, priority = PLAYBOOK[category]
    out = []
    for item in root.findall('./channel/item')[:10]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        source = item.findtext('source') or 'Google News'
        if title and link:
            out.append({
                'category': category,
                'scope': 'Nigeria' if category.startswith('Nigeria') else 'Worldwide',
                'title': title,
                'source': source,
                'published': pub,
                'url': link,
                'priority': priority,
                'target': target,
                'products': products,
                'action': action
            })
    return out

items = []
for category, query in QUERIES.items():
    try:
        items.extend(parse(rss(query), category))
    except Exception as e:
        items.append({
            'category': category,
            'scope': 'Nigeria' if category.startswith('Nigeria') else 'Worldwide',
            'title': 'Feed refresh failed',
            'source': 'System',
            'published': '',
            'url': '',
            'error': str(e),
            'priority': PLAYBOOK[category][3],
            'target': PLAYBOOK[category][0],
            'products': PLAYBOOK[category][1],
            'action': PLAYBOOK[category][2]
        })

seen = set()
clean = []
for x in items:
    key = (x['category'], x['title'])
    if key not in seen:
        seen.add(key)
        clean.append(x)

payload = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'status': 'live',
    'scope': 'Nigeria-first + Worldwide event and travel-demand discovery',
    'sales_rule': 'News is a discovery signal. Verify event dates/details with an official source before quoting customers.',
    'refresh_note': 'This feed refreshes daily. It is designed to surface both major and smaller newly reported event/travel signals; it is not a claim of literally every event worldwide.',
    'items': clean
}
with open('data/daily-intelligence.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
print(f'Wrote {len(clean)} intelligence items across {len(QUERIES)} categories')
