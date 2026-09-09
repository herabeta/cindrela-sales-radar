#!/usr/bin/env python3
"""Find additional public, contactable company leads from event pages.

Rules:
- Use only publicly reachable business information.
- Never invent people, companies, emails or phone numbers.
- Only save a discovered company lead when a valid email, phone or public LinkedIn URL is found.
- Prefer links exposed by official/event source pages and the linked organisation's own public pages.
"""
import hashlib
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data/opportunities.json'
CONTACTS = ROOT / 'data/public-lead-contacts.json'

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s().-]*)?(?:\d[\s().-]*){7,14}\d(?!\d)")
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_./%-]+", re.I)
GENERIC = ('info@','contact@','hello@','sales@','support@','enquiries@','enquiry@','secretariat@','conference@','marketing@','office@','admin@')
RELEVANT = ('exhibitor','exhibitors','sponsor','sponsors','partner','partners','speaker','speakers','delegate','delegates','participant','participants','vendor','vendors','team','teams','company','companies','association','federation','buyer','buyers','supplier','suppliers','member','members','startup','startups','media','press')
BAD = ('home','about','contact','privacy','cookie','login','register','registration','read more','learn more','view all','menu','facebook','instagram','youtube','linkedin','twitter','x.com','whatsapp','terms','exhibitor list','exhibitors list','sponsor list','sponsors list','partner list','partners list','speaker list','speakers list','delegate list','delegates list','participant list','participants list','vendor list','vendors list','company list','companies list','team list','teams list','member list','members list','buyer list','buyers list','supplier list','suppliers list','directory','directories')
SOCIAL_HOSTS = ('facebook.com','instagram.com','youtube.com','linkedin.com','twitter.com','x.com','tiktok.com')

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.href=''
        self.text=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=='a':
            self.href=dict(attrs).get('href','')
            self.text=[]
    def handle_data(self, data):
        if self.href:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=='a' and self.href:
            self.links.append((' '.join(self.text).strip(), self.href))
            self.href=''; self.text=[]

def fetch(url, timeout=8):
    req=urllib.request.Request(url,headers={'User-Agent':'Cindrela-Sales-Radar-Public-Lead-Enrichment/1.0'})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(900000)
        return raw.decode(r.headers.get_content_charset() or 'utf-8','ignore')

def clean(s):
    s=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',s,flags=re.I)
    return re.sub(r'<[^>]+>',' ',s)

def norm(s):
    return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()

def phone(s):
    d=re.sub(r'\D','',s)
    if not 8<=len(d)<=15:return ''
    # Reject obvious years/date ranges and other non-phone numeric labels.
    if re.fullmatch(r'(?:19|20)\d{2}',d) or re.fullmatch(r'(?:19|20)\d{2}(?:19|20)\d{2}',d):return ''
    return re.sub(r'\s+',' ',s).strip(' .,-')

def valid_anchor(label, href):
    text=re.sub(r'\s+',' ',label or '').strip()
    low=(text+' '+href).lower()
    if len(text)<3 or len(text)>120 or re.fullmatch(r'[0-9\W_]+',text):return False
    if any(x in low for x in BAD):return False
    if not href.lower().startswith(('http://','https://')):return False
    host=urlparse(href).netloc.lower()
    if any(h in host for h in SOCIAL_HOSTS):return False
    return any(k in low for k in RELEVANT)

def extract(html):
    emails=sorted(set(EMAIL_RE.findall(html)), key=lambda x:(0 if x.lower().startswith(GENERIC) else 1,x.lower()))
    phones=[]
    for x in PHONE_RE.findall(clean(html)):
        p=phone(x)
        if p and p not in phones: phones.append(p)
    linkedin=[]
    for x in LINKEDIN_RE.findall(html):
        if x not in linkedin: linkedin.append(x.rstrip('.,);'))
    return emails[:12], phones[:12], linkedin[:8]

def candidate_pages(base, html):
    lp=Links(); lp.feed(html)
    out=[]; seen=set()
    for label,href in lp.links:
        if not valid_anchor(label,href):continue
        target=urljoin(base,href)
        if target in seen:continue
        seen.add(target)
        out.append((re.sub(r'\s+',' ',label).strip(),target))
        if len(out)>=12:break
    return out

def contact_pages(url):
    p=urlparse(url)
    root=f'{p.scheme}://{p.netloc}'
    return [url,root+'/contact',root+'/contact-us',root+'/about',root+'/team']

def make_record(event, company, source, email='', phone_value='', linkedin='', role='Public Business Contact'):
    lead_id='auto-'+hashlib.sha1((event+'|'+company+'|'+email+'|'+phone_value+'|'+linkedin+'|'+source).encode()).hexdigest()[:16]
    return {
        'event':event,'company':company,'country':'Nigeria','role':role,'contactPerson':'','contactRole':role,
        'businessEmail':email,'businessPhone':phone_value,'linkedin':linkedin,'source':source,
        'note':'Public business contact discovered from an event-linked organisation page. Verify before outreach.',
        'leadType':'Event-linked public business','contactMethod':'Email + WhatsApp/Phone + LinkedIn',
        'outreachAngle':'Travel support for staff, exhibitors, delegates or business visitors','followUpPlan':'Follow up in 2–3 days',
        'leadId':lead_id,'lastVerified':date.today().isoformat(),'contactReady':True
    }

def key(c):
    return (norm(c.get('event')),norm(c.get('company')),str(c.get('businessEmail','')).lower().strip(),re.sub(r'\D','',str(c.get('businessPhone',''))),str(c.get('linkedin','')).lower().strip())

def process_event(event):
    title=event.get('title','').strip(); source=event.get('url','').strip()
    if not title or not source.startswith(('http://','https://')):return []
    try:html=fetch(source)
    except Exception:return []
    candidates=candidate_pages(source,html)
    records=[]
    for label,url in candidates:
        try: page=fetch(url)
        except Exception:continue
        urls=[(url,page)]
        for cp in contact_pages(url)[1:4]:
            if cp!=url:
                try: urls.append((cp,fetch(cp,timeout=6)))
                except Exception: pass
        emails=[];phones=[];links=[];best_source=url
        for pu,ph in urls:
            e,p,l=extract(ph)
            emails += e; phones += p; links += l
            if e or p or l: best_source=pu
        emails=list(dict.fromkeys(emails)); phones=list(dict.fromkeys(phones)); links=list(dict.fromkeys(links))
        email=next((x for x in emails if x.lower().startswith(GENERIC)), emails[0] if emails else '')
        ph=phones[0] if phones else ''
        li=links[0] if links else ''
        if email or ph or li:
            records.append(make_record(title,label,best_source,email,ph,li))
    return records

def main():
    events=json.loads(OPP.read_text(encoding='utf-8'))
    contacts=json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    existing={key(c) for c in contacts}
    today=date.today(); active=[]
    for e in events:
        try:
            end=date.fromisoformat(e.get('end_date') or e.get('start_date'))
        except Exception:continue
        if end>=today: active.append(e)
    added=0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(process_event,e):e for e in active}
        for fut in as_completed(futures):
            try: rows=fut.result()
            except Exception: continue
            for c in rows:
                k=key(c)
                if k in existing:continue
                contacts.append(c); existing.add(k); added+=1
    CONTACTS.write_text(json.dumps(contacts,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Public company lead expansion: active_events={len(active)}, added={added}, total={len(contacts)}')

if __name__=='__main__':main()
