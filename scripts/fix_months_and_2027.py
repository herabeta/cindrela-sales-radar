import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data' / 'opportunities.json'
PLAYS = ROOT / 'data' / 'event-sales-plays.json'
INDEX = ROOT / 'index.html'

new_events = [
  {"id":156,"title":"CES 2027","start_date":"2027-01-06","city":"Las Vegas, USA","group":"business","products":["Flight","Hotel","Transfers","Business Travel"],"source":"CES","url":"https://www.ces.tech/","sales_market":"Nigeria","sales_reason":"Nigerian technology companies, founders, investors and corporate teams may travel to CES for business, networking and product discovery"},
  {"id":157,"title":"Australian Open 2027","start_date":"2027-01-11","city":"Melbourne, Australia","group":"sports","products":["Flight","Hotel","Transfers","Group Travel","Family Travel"],"source":"Australian Open","url":"https://ausopen.com/","sales_market":"Nigeria","sales_reason":"Nigerian tennis supporters, families and premium leisure travellers may travel to Melbourne for the Grand Slam"},
  {"id":158,"title":"World Economic Forum Annual Meeting 2027","start_date":"2027-01-18","city":"Davos, Switzerland","group":"business","products":["Flight","Hotel","Transfers","Executive Travel"],"source":"Davos Congress Centre / World Economic Forum","url":"https://www.davos.ch/en/experience/events/world-economic-forum-annual-meeting-2027","sales_market":"Nigeria","sales_reason":"Nigerian executives, government leaders, investors and business delegates may travel for the global leadership meeting"},
  {"id":159,"title":"Austin E-Prix 2027","start_date":"2027-02-06","city":"Austin, USA","group":"sports","products":["Flight","Hotel","Transfers","Premium Travel"],"source":"Formula E","url":"https://www.fiaformulae.com/","sales_market":"Nigeria","sales_reason":"Nigerian motorsport fans and premium leisure travellers may travel for the Formula E race weekend"},
  {"id":160,"title":"Super Bowl LXI 2027","start_date":"2027-02-14","city":"Inglewood, USA","group":"sports","products":["Flight","Hotel","Transfers","Premium Travel","Event Travel"],"source":"NFL","url":"https://www.nfl.com/","sales_market":"Nigeria","sales_reason":"Nigerian American-football fans, premium leisure travellers and sports groups may travel for Super Bowl week"},
  {"id":161,"title":"Miami E-Prix 2027","start_date":"2027-02-20","city":"Miami, USA","group":"sports","products":["Flight","Hotel","Transfers","Premium Travel"],"source":"Formula E","url":"https://www.fiaformulae.com/","sales_market":"Nigeria","sales_reason":"Nigerian motorsport fans and premium leisure travellers may travel for the race weekend"},
  {"id":162,"title":"MWC Barcelona 2027","start_date":"2027-03-01","city":"Barcelona, Spain","group":"business","products":["Flight","Hotel","Transfers","Business Travel","Group Booking"],"source":"MWC Barcelona / GSMA","url":"https://www.mwcbarcelona.com/","sales_market":"Nigeria","sales_reason":"Nigerian telecom firms, technology companies, founders and delegates may travel for the global mobile industry event"},
  {"id":163,"title":"ITB Berlin 2027","start_date":"2027-03-16","city":"Berlin, Germany","group":"business","products":["Flight","Hotel","Transfers","Business Travel","Group Booking"],"source":"ITB Berlin","url":"https://www.itb.com/en","sales_market":"Nigeria","sales_reason":"Nigerian travel companies, tourism officials, destination marketers and trade visitors may travel for the leading tourism trade show"},
  {"id":164,"title":"HIMSS27","start_date":"2027-04-05","city":"Chicago, USA","group":"business","products":["Flight","Hotel","Transfers","Business Travel"],"source":"HIMSS","url":"https://www.himss.org/","sales_market":"Nigeria","sales_reason":"Nigerian health-tech companies, hospital leaders, healthcare IT teams and delegates may travel for the healthcare technology event"},
  {"id":165,"title":"Sanya E-Prix 2027","start_date":"2027-04-17","city":"Sanya, China","group":"sports","products":["Flight","Hotel","Transfers","Premium Travel"],"source":"Formula E","url":"https://www.fiaformulae.com/","sales_market":"Nigeria","sales_reason":"Nigerian motorsport fans and premium leisure travellers may travel for the race weekend"},
  {"id":166,"title":"IHIF EMEA 2027","start_date":"2027-05-10","city":"Berlin, Germany","group":"business","products":["Flight","Hotel","Transfers","Executive Travel","Business Travel"],"source":"IHIF EMEA","url":"https://www.ihifemea.com/","sales_market":"Nigeria","sales_reason":"Nigerian hotel owners, investors, developers, tourism officials and hospitality executives may travel for the hospitality investment forum"},
  {"id":167,"title":"Berlin E-Prix 2027","start_date":"2027-05-08","city":"Berlin, Germany","group":"sports","products":["Flight","Hotel","Transfers","Premium Travel"],"source":"Formula E","url":"https://www.fiaformulae.com/","sales_market":"Nigeria","sales_reason":"Nigerian motorsport fans and premium leisure travellers may travel for the Berlin race weekend"}
]

plays = {
  156:["Nigerian tech founders, CTOs, product teams, investors and corporate innovation leaders","Flights + Hotels + Transfers + Business Travel","Start CES prospecting in November–December 2026; intensify 3–4 weeks before 6 Jan","HOT","Follow up within 48h and qualify dates, team size and meeting plans","CES hotel inventory is already bookable and the event is a major global technology business platform"],
  157:["Nigerian tennis fans, families and premium leisure travellers","Flights + Hotels + Transfers + Family Travel + Event Travel","Start planning by October 2026; contact active prospects 3–6 weeks before travel","HOT","Follow up every 3–5 days for active prospects; confirm match dates and hotel needs","AO27 runs 11–31 Jan with finals on 30–31 Jan, creating a defined sports-travel window"],
  158:["Nigerian CEOs, senior executives, investors, government leaders and policy delegates","Flights + Hotels + Transfers + Executive Travel","Start executive outreach in November 2026; prioritise confirmed delegates in December","HOT","Follow up weekly until travel dates and accommodation are confirmed","WEF brings thousands of international leaders to Davos and requires advance executive travel planning"],
  159:["Nigerian Formula E fans, motorsport groups and premium leisure travellers","Flights + Hotels + Transfers + Premium Travel","Begin targeted race-trip outreach in December 2026","PLAN","Follow up every 7 days with serious prospects; lock hotels early","The 2026–27 Formula E calendar confirms Austin for 6 Feb 2027"],
  160:["Nigerian American-football fans, premium travellers and sports groups","Flights + Hotels + Transfers + Premium Travel + Event Travel","Start outreach in November 2026; push confirmed prospects in January","HOT","Follow up every 48–72h for active enquiries","Super Bowl LXI is confirmed for 14 Feb 2027 in Inglewood, creating a short high-value event window"],
  161:["Nigerian motorsport fans, premium leisure travellers and sports groups","Flights + Hotels + Transfers + Premium Travel","Begin targeted outreach in December 2026; qualify February travel plans early","PLAN","Follow up weekly and recheck hotel/race-week requirements","Miami E-Prix is scheduled for 20 Feb 2027"],
  162:["Nigerian telecom operators, ICT companies, founders, CTOs, investors and delegates","Flights + Hotels + Transfers + Business Travel + Group Booking","Start outreach in November 2026; move confirmed teams to booking in January","HOT","Follow up within 48h for companies sending teams","MWC27 runs 1–4 Mar and is a major global mobile/technology industry event"],
  163:["Nigerian travel agencies, tourism boards, hotel groups, destination marketers and senior travel executives","Flights + Hotels + Transfers + Business Travel + Group Booking","Start outreach in December 2026; build exhibitor/delegate lists by January","HOT","Follow up weekly with exhibitors and trade visitors","ITB Berlin is the world’s leading travel trade show and runs 16–18 Mar 2027"],
  164:["Nigerian hospital executives, health-tech firms, healthcare IT teams and medical technology delegates","Flights + Hotels + Transfers + Business Travel","Start prospecting in January 2027; intensify 4–6 weeks before the event","PLAN","Follow up weekly after initial qualification","HIMSS27 is scheduled for 5–9 Apr 2027 in Chicago"],
  165:["Nigerian motorsport fans, premium leisure travellers and sports groups","Flights + Hotels + Transfers + Premium Travel","Start targeted outreach in January 2027; qualify April travel early","PLAN","Follow up every 7 days for active prospects","Formula E confirms Sanya for 17 Apr 2027"],
  166:["Nigerian hotel owners, investors, developers, tourism officials and hospitality executives","Flights + Hotels + Transfers + Executive Travel + Business Travel","Start executive outreach in January 2027; prioritise confirmed delegates by March","HOT","Follow up weekly and confirm meeting schedules before travel","IHIF EMEA brings global hospitality investors and industry leaders to Berlin 10–12 May 2027"],
  167:["Nigerian motorsport fans, premium leisure travellers and sports groups","Flights + Hotels + Transfers + Premium Travel","Start outreach in January 2027; convert serious prospects in March–April","PLAN","Follow up weekly with qualified travellers","Formula E confirms Berlin double-header dates in May 2027"]
}

# Add only missing events, then keep the database itself chronologically ordered.
items = json.loads(OPP.read_text(encoding='utf-8'))
by_id = {int(x['id']): x for x in items}
for e in new_events:
    by_id.setdefault(e['id'], e)
items = sorted(by_id.values(), key=lambda x: (x.get('start_date','9999-99-99'), int(x.get('id',0))))
OPP.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Extend existing event-sales-play mappings without disturbing existing plays.
if PLAYS.exists():
    existing = json.loads(PLAYS.read_text(encoding='utf-8'))
else:
    existing = {}
for k,v in plays.items():
    existing.setdefault(str(k), v)
PLAYS.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Make the All view render every calendar month between the earliest and latest opportunity,
# so a missing event never causes the month heading itself to disappear.
html = INDEX.read_text(encoding='utf-8')
start = html.find('function render(){')
end = html.find('function counts(){', start)
if start == -1 or end == -1:
    raise SystemExit('render function markers not found')
new_render = '''function render(){const q=document.getElementById('search').value.toLowerCase().trim();const filtered=opportunities.filter(o=>(current==='all'||o.type===current||o.group===current)&&(!q||(`${o.title} ${o.city} ${o.products} ${o.target}`).toLowerCase().includes(q))).sort((a,b)=>dateObj(a.start_date)-dateObj(b.start_date));if(!filtered.length){cards.innerHTML='<div class="panel">No matching opportunity found.</div>';return}let html='',lastMonth='',monthKeys=[];if(current==='all'&&!q){const dates=opportunities.map(o=>dateObj(o.start_date)).filter(d=>!isNaN(d));if(dates.length){let d=new Date(dates.reduce((a,b)=>a<b?a:b));const max=new Date(dates.reduce((a,b)=>a>b?a:b));d.setDate(1);max.setDate(1);while(d<=max){monthKeys.push(d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0'));d.setMonth(d.getMonth()+1)}}}else{monthKeys=[...new Set(filtered.map(o=>{const d=dateObj(o.start_date);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')}))]}monthKeys.forEach(key=>{const [y,m]=key.split('-').map(Number);const monthDate=new Date(y,m-1,1);const monthName=monthDate.toLocaleDateString('en-GB',{month:'long',year:'numeric'});const monthItems=filtered.filter(o=>{const d=dateObj(o.start_date);return d.getFullYear()===y&&d.getMonth()===m-1});html+=`<h3 class="month-title">📅 ${esc(monthName)}</h3><div class="cards">`;if(!monthItems.length){html+='<div class="panel" style="margin:0">No sales opportunity loaded for this month yet.</div>'}else{monthItems.forEach(o=>{html+=`<article class="card ${o.type}"><div class="top"><span class="badge">${esc(o.tag)}</span><span class="score">${o.score}/100</span></div><h3>${esc(o.title)}</h3><div class="meta">📅 ${esc(dateLabel(o.start_date))}<br>📍 ${esc(o.city)}<br>🎯 ${esc(o.target)}</div><div class="sellbox"><strong>💰 Cindrela can sell:</strong>${esc(o.products)}</div><div class="action">Action: <b>${esc(o.contact)}</b></div><button class="leadbtn" onclick="openModal(${o.id})">🎯 Open Sales Lead Play</button></article>`})}html+='</div>'});cards.innerHTML=html}'''
html = html[:start] + new_render + html[end:]
INDEX.write_text(html, encoding='utf-8')
