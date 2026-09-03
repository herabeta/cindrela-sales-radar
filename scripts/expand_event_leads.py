#!/usr/bin/env python3
"""Ensure Lead Finder has a lead for every Sales Opportunity and every distinct
public business contact found on its public event/company source. Never invent data.
"""
import json,re,hashlib,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OPP=ROOT/'data/opportunities.json'; CONTACTS=ROOT/'data/public-lead-contacts.json'
EMAIL_RE=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE=re.compile(r"(?<!\d)(?:\+\d{1,3}[\s().-]*)?(?:\d[\s().-]*){7,14}\d(?!\d)")
GENERIC=('info@','contact@','hello@','sales@','support@','enquiries@','enquiry@','secretariat@','conference@','marketing@','office@')
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Cindrela-Sales-Radar-Lead-Enrichment/1.0'})
    with urllib.request.urlopen(req,timeout=12) as r:return r.read(1200000).decode(r.headers.get_content_charset() or 'utf-8','ignore')
def clean(s):return re.sub(r'<[^>]+>',' ',re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',s,flags=re.I))
def normphone(s):
    d=re.sub(r'\D','',s);return re.sub(r'\s+',' ',s).strip(' .,-') if 8<=len(d)<=15 else ''
def main():
    events=json.loads(OPP.read_text(encoding='utf-8')); contacts=json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    existing={(str(c.get('event','')).lower(),str(c.get('businessEmail','')).lower(),str(c.get('businessPhone','')).lower(),str(c.get('company','')).lower()) for c in contacts}; added=0
    for e in events:
        title=e.get('title','').strip(); url=e.get('url','').strip()
        if not title:continue
        org=(e.get('source') or title).strip()
        if not any(k[0]==title.lower() and k[3]==org.lower() for k in existing):
            contacts.append({'event':title,'company':org,'country':e.get('city') or 'Nigeria','role':'Event Contact Desk / Organizer','contactPerson':'','contactRole':'Public Event Contact','businessEmail':'','businessPhone':'','linkedin':'','source':url,'note':'Official/event source lead. Contact details require public-source verification.'});added+=1
        if not url.startswith(('http://','https://')):continue
        try:text=clean(fetch(url))
        except Exception:continue
        emails=sorted(set(EMAIL_RE.findall(text)),key=lambda x:(0 if x.lower().startswith(GENERIC) else 1,x.lower()))[:12]
        phones=[]
        for x in PHONE_RE.findall(text):
            p=normphone(x)
            if p and p not in phones:phones.append(p)
        for em in emails:
            k=(title.lower(),em.lower(),'','')
            if k in existing:continue
            contacts.append({'event':title,'company':org,'country':e.get('city') or 'Nigeria','role':'Event Contact / Public Business Desk','contactPerson':'','contactRole':'Public Business Contact','businessEmail':em,'businessPhone':'','linkedin':'','source':url,'note':'Public business email extracted from event source. Verify before outreach.'});existing.add(k);added+=1
        for ph in phones[:12]:
            k=(title.lower(),'','',ph.lower())
            if k in existing:continue
            contacts.append({'event':title,'company':org,'country':e.get('city') or 'Nigeria','role':'Event Contact / Public Business Desk','contactPerson':'','contactRole':'Public Business Contact','businessEmail':'','businessPhone':ph,'linkedin':'','source':url,'note':'Public business phone extracted from event source. Verify before outreach.'});existing.add(k);added+=1
    CONTACTS.write_text(json.dumps(contacts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Expanded public lead records: +{added}, total={len(contacts)}')
if __name__=='__main__':main()
