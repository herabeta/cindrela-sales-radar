#!/usr/bin/env python3
"""Expand Lead Finder using public event-source pages.

Creates organizer, public-contact, participant/team, sponsor/partner, exhibitor,
speaker and delegate-style leads when the public event pages expose them.
Never invents people, emails or phone numbers.
"""
import json,re,hashlib,urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OPP=ROOT/'data/opportunities.json'; CONTACTS=ROOT/'data/public-lead-contacts.json'
EMAIL_RE=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE=re.compile(r"(?<!\d)(?:\+\d{1,3}[\s().-]*)?(?:\d[\s().-]*){7,14}\d(?!\d)")
GENERIC=('info@','contact@','hello@','sales@','support@','enquiries@','enquiry@','secretariat@','conference@','marketing@','office@')
RELEVANT=('team','teams','participant','participants','sponsor','sponsors','partner','partners','exhibitor','exhibitors','speaker','speakers','delegate','delegates','roster','rosters','lineup','federation','association','media','press','vendor','vendors')
BAD_ANCHOR=('home','about','contact','privacy','cookie','login','register','read more','learn more','view all','menu','facebook','instagram','youtube','linkedin','twitter','x')
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.href='';self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=='a':self.href=dict(attrs).get('href','');self.text=[]
    def handle_data(self,data):
        if self.href:self.text.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=='a' and self.href:self.links.append((' '.join(self.text).strip(),self.href));self.href='';self.text=[]
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Cindrela-Sales-Radar-Lead-Enrichment/2.0'})
    with urllib.request.urlopen(req,timeout=12) as r:return r.read(1200000).decode(r.headers.get_content_charset() or 'utf-8','ignore')
def clean(s):return re.sub(r'<[^>]+>',' ',re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',s,flags=re.I))
def normphone(s):
    d=re.sub(r'\D','',s);return re.sub(r'\s+',' ',s).strip(' .,-') if 8<=len(d)<=15 else ''
def norm(s):return re.sub(r'[^a-z0-9]+',' ',str(s or '').lower()).strip()
def stable_id(event,company,source):return 'auto-'+hashlib.sha1((event+'|'+company+'|'+source).encode()).hexdigest()[:16]
def classify(text):
    n=norm(text)
    if any(k in n for k in ('sponsor','sponsorship')):return 'Sponsor / Partner'
    if any(k in n for k in ('exhibitor','exhibition','vendor')):return 'Exhibitor / Vendor'
    if any(k in n for k in ('speaker','speakers','panelist')):return 'Speaker / Expert'
    if any(k in n for k in ('team','teams','roster','federation','association','participant')):return 'Participant / Team / Association'
    if any(k in n for k in ('delegate','delegates','attendee')):return 'Delegate / Attendee'
    if any(k in n for k in ('media','press')):return 'Media / PR'
    return 'Event Partner / Public Business'
def strategy(role,event):
    r=role.lower()
    if 'sponsor' in r:return ('Email + LinkedIn','Partnership/event travel support for staff, guests and VIPs','Follow up in 2–3 days')
    if 'exhibitor' in r or 'vendor' in r:return ('Email + WhatsApp + LinkedIn','Exhibitor flights, hotel blocks, airport transfers and team travel','Follow up in 2–3 days')
    if 'speaker' in r:return ('Email + LinkedIn','Speaker flight, hotel and airport transfer coordination','Follow up in 48 hours')
    if 'participant' in r or 'team' in r or 'association' in r:return ('Email + LinkedIn','Team/delegation flights, hotels, transfers and group booking','Follow up in 48–72 hours')
    if 'delegate' in r or 'attendee' in r:return ('Email + WhatsApp + LinkedIn','Delegate flight, hotel and transfer package','Follow up in 2–3 days')
    return ('Email + Phone + LinkedIn','Event travel planning: flights, hotels and airport transfers','Follow up in 2–3 days')
def make_record(event,city,company,role,source,email='',phone='',note=''):
    method,angle,follow=strategy(role,event)
    return {'event':event,'company':company,'country':city or 'Nigeria','role':role,'contactPerson':'','contactRole':role,'businessEmail':email,'businessPhone':phone,'linkedin':'','source':source,'note':note,'leadType':role,'contactMethod':method,'outreachAngle':angle,'followUpPlan':follow}
def main():
    events=json.loads(OPP.read_text(encoding='utf-8'));contacts=json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    existing={(norm(c.get('event')),norm(c.get('company')),str(c.get('businessEmail','')).lower(),str(c.get('businessPhone','')).lower(),norm(c.get('source'))) for c in contacts};added=0
    for e in events:
        title=e.get('title','').strip(); url=e.get('url','').strip(); city=e.get('city') or 'Nigeria'
        if not title:continue
        org=(e.get('source') or title).strip()
        orgkey=(norm(title),norm(org),'','','')
        if orgkey not in existing:
            contacts.append(make_record(title,city,org,'Event Contact Desk / Organizer',url,note='Official/event source lead. Contact details require public-source verification.'));existing.add(orgkey);added+=1
        if not url.startswith(('http://','https://')):continue
        pages=[]
        try:
            html=fetch(url);pages.append((url,html))
        except Exception:continue
        # Discover public sub-pages for teams, sponsors, exhibitors, speakers, partners, etc.
        lp=Links();lp.feed(html)
        seen_pages={url}
        for text,href in lp.links:
            label=(text+' '+href).strip(); low=label.lower()
            if not any(k in low for k in RELEVANT):continue
            if not href or href.startswith(('#','mailto:','tel:','javascript:')):continue
            target=urljoin(url,href)
            if urlparse(target).netloc!=urlparse(url).netloc or target in seen_pages:continue
            seen_pages.add(target);pages.append((target,''))
            if len(pages)>=8:break
        for page_url,page_html in pages:
            if not page_html:
                try:page_html=fetch(page_url)
                except Exception:continue
            emails=sorted(set(EMAIL_RE.findall(page_html)),key=lambda x:(0 if x.lower().startswith(GENERIC) else 1,x.lower()))[:12]
            phones=[]
            for x in PHONE_RE.findall(clean(page_html)):
                p=normphone(x)
                if p and p not in phones:phones.append(p)
            for em in emails:
                role='Event Contact / Public Business Desk' if page_url==url else classify(page_url)
                rec=make_record(title,city,org,role,page_url,email=em,note='Public business email extracted from event source. Verify before outreach.')
                key=(norm(title),norm(org),em.lower(),'','')
                if key not in existing:contacts.append(rec);existing.add(key);added+=1
            for ph in phones[:12]:
                role='Event Contact / Public Business Desk' if page_url==url else classify(page_url)
                rec=make_record(title,city,org,role,page_url,phone=ph,note='Public business phone extracted from event source. Verify before outreach.')
                key=(norm(title),norm(org),'',ph.lower(),'')
                if key not in existing:contacts.append(rec);existing.add(key);added+=1
            # Extract named participant/sponsor/exhibitor links from this page.
            sub=Links();sub.feed(page_html)
            count=0
            for anchor,href in sub.links:
                label=re.sub(r'\s+',' ',anchor).strip()
                low=(label+' '+href).lower()
                if len(label)<3 or len(label)>100 or any(b==norm(label) for b in BAD_ANCHOR):continue
                if not any(k in low for k in RELEVANT):continue
                if re.fullmatch(r'[0-9\W_]+',label):continue
                target=urljoin(page_url,href)
                if target.startswith(('mailto:','tel:')):continue
                role=classify(low)
                # Avoid navigation-like labels that are clearly section names.
                if norm(label) in {norm(x) for x in RELEVANT}:continue
                key=(norm(title),norm(label),'','','')
                if key in existing:continue
                contacts.append(make_record(title,city,label,role,target,note='Public organization/participant link discovered from event source. Verify before outreach.'));existing.add(key);added+=1;count+=1
                if count>=40:break
    CONTACTS.write_text(json.dumps(contacts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Expanded multi-role public lead records: +{added}, total={len(contacts)}')
if __name__=='__main__':main()
