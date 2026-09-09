#!/usr/bin/env python3
"""Small idempotent Lead Finder hardening patch.

Keeps the existing UI/data model but:
- preserves multiple public contacts for the same company/event;
- only treats a syntactically valid business email, phone or LinkedIn URL as contactable.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'lead-finder.html'
s=PAGE.read_text(encoding='utf-8')

old_upsert="const i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
new_upsert="const contactKey=String(c.businessEmail||c.businessPhone||c.linkedin||c.source||'').toLowerCase().trim(),i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title&&String(x.businessEmail||x.businessPhone||x.linkedin||x.source||'').toLowerCase().trim()===contactKey),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
if old_upsert in s:
    s=s.replace(old_upsert,new_upsert,1)
elif new_upsert not in s:
    raise SystemExit('Expected Lead Finder upsert pattern not found; refusing to modify file.')

old_contact="contactable=x=>!!(x?.businessEmail||x?.businessPhone||x?.linkedin)"
new_contact="contactable=x=>{const email=String(x?.businessEmail||'').trim(),phone=String(x?.businessPhone||'').trim(),li=String(x?.linkedin||'').trim();return (!!email&&/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email))||((phone.replace(/\\D/g,'').length>=8&&phone.replace(/\\D/g,'').length<=15))||(/^https?:\\/\\/(?:www\\.)?linkedin\\.com\\/(?:company|in)\\/[A-Za-z0-9_./%-]+/i.test(li))}"
if old_contact in s:
    s=s.replace(old_contact,new_contact,1)
elif new_contact not in s:
    raise SystemExit('Expected Lead Finder contactable pattern not found; refusing to modify file.')

PAGE.write_text(s,encoding='utf-8')
print('Lead Finder hardening applied: multiple contacts preserved and contact routes validated.')
