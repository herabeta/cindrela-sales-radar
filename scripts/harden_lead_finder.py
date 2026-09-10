#!/usr/bin/env python3
"""Idempotent Lead Finder hardening patch.

Keeps the existing UI/data model but:
- preserves multiple public contacts for the same company/event;
- only treats a real business email, phone or LinkedIn URL as contactable;
- rejects image/file names, placeholders, dimension-like domains and obvious date/year strings.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'lead-finder.html'
s=PAGE.read_text(encoding='utf-8')

old_upsert="const i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
new_upsert="const contactKey=String(c.businessEmail||c.businessPhone||c.linkedin||c.source||'').toLowerCase().trim(),i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title&&String(x.businessEmail||x.businessPhone||x.linkedin||x.source||'').toLowerCase().trim()===contactKey),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
if old_upsert in s:
    s=s.replace(old_upsert,new_upsert,1)
elif new_upsert not in s and 'contactKey=' not in s:
    raise SystemExit('Expected Lead Finder upsert pattern not found; refusing to modify file.')

new_contact="contactable=x=>{const email=String(x?.businessEmail||'').trim(),phone=String(x?.businessPhone||'').trim(),li=String(x?.linkedin||'').trim(),domain=email.split('@').pop().toLowerCase(),digits=phone.replace(/\\D/g,''),badEmail=/^(?:email@domain\.ext|user@email\.com|test@example\.com|example@example\.com|name@domain\.(?:com|ext))$/i.test(email)||/(?:^|[.])(?:png|jpe?g|gif|webp|svg|ico|pdf|css|js)$/i.test(domain)||/^(?:\\d{2,4}x\\d{2,4}|\\d+x|x\\d+)\\./i.test(domain);return (!!email&&/^[^\\s@]+@[^\\s@]+\\.[A-Za-z]{2,}$/.test(email)&&!badEmail)||((digits.length>=8&&digits.length<=15)&&!/(?:19|20)\\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\\d|3[01])/.test(phone)&&!/(?:19|20)\\d{2}\\s*[-–]\\s*(?:19|20)\\d{2}/.test(phone))||(/^https?:\\/\\/(?:www\\.)?linkedin\\.com\\/(?:company|in)\\/[A-Za-z0-9_./%-]+/i.test(li))}"

# Replace any existing contactable arrow function up to the next helper. This makes the patch
# genuinely idempotent even if an earlier hardening version used a slightly different expression.
if new_contact not in s:
    pattern=r"contactable=x=>\{.*?\},phoneForWhatsApp="
    replacement=new_contact+",phoneForWhatsApp="
    s2,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
    if n!=1:
        old_simple="contactable=x=>!!(x?.businessEmail||x?.businessPhone||x?.linkedin)"
        if old_simple in s:
            s=s.replace(old_simple,new_contact,1)
        else:
            raise SystemExit('Expected Lead Finder contactable pattern not found; refusing to modify file.')
    else:
        s=s2

if 'contactKey=' not in s or new_contact not in s:
    raise SystemExit('Lead Finder hardening verification failed; refusing to modify file.')

PAGE.write_text(s,encoding='utf-8')
print('Lead Finder hardening applied/verified: multiple contacts preserved and contact routes validated.')
