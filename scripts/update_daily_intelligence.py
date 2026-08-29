import json, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

QUERIES = {
    'Nigeria / Abuja events': 'Nigeria Abuja events conference exhibition 2026',
    'Nigeria visa / travel': 'Nigeria visa travel update 2026',
    'Africa exhibitions': 'Africa exhibition conference 2026 Nigeria',
    'China exhibitions': 'China exhibition trade fair 2026 Africa Nigeria',
    'World exhibitions': 'world exhibition conference 2026 Nigeria business',
    'Sports opportunities': 'Nigeria Africa sports event 2026 2027',
}

def rss(query):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl':'en-NG', 'gl':'NG', 'ceid':'NG:en'})
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 Cindrela-Sales-Radar'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml, category):
    root = ET.fromstring(xml)
    out=[]
    for item in root.findall('./channel/item')[:8]:
        title=(item.findtext('title') or '').strip()
        link=(item.findtext('link') or '').strip()
        pub=(item.findtext('pubDate') or '').strip()
        source=item.findtext('source') or 'Google News'
        if title and link:
            out.append({'category':category,'title':title,'source':source,'published':pub,'url':link})
    return out

items=[]
for category, query in QUERIES.items():
    try:
        items.extend(parse(rss(query), category))
    except Exception as e:
        items.append({'category':category,'title':'Feed refresh failed','source':'System','published':'','url':'','error':str(e)})

seen=set(); clean=[]
for x in items:
    key=(x['category'],x['title'])
    if key not in seen:
        seen.add(key); clean.append(x)

payload={
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'status':'live',
 'items':clean
}
with open('data/daily-intelligence.json','w',encoding='utf-8') as f:
    json.dump(payload,f,ensure_ascii=False,indent=2)
print(f"Wrote {len(clean)} intelligence items")
