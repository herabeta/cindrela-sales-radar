#!/usr/bin/env python3
"""Small idempotent Lead Finder hardening patch.

Keeps the existing UI/data model but stops upsert() from collapsing multiple
public contacts for the same company/event into one browser record.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'lead-finder.html'
s=PAGE.read_text(encoding='utf-8')
old="const i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
new="const contactKey=String(c.businessEmail||c.businessPhone||c.linkedin||c.source||'').toLowerCase().trim(),i=leads.findIndex(x=>norm(x.company)===norm(c.company)&&x.event===e.title&&String(x.businessEmail||x.businessPhone||x.linkedin||x.source||'').toLowerCase().trim()===contactKey),x={id:i>=0?leads[i].id:Date.now()+Math.random(),"
if old in s:
    s=s.replace(old,new,1)
    print('Lead Finder upsert hardening applied.')
else:
    if new in s:
        print('Lead Finder upsert hardening already present.')
    else:
        raise SystemExit('Expected Lead Finder upsert pattern not found; refusing to modify file.')
PAGE.write_text(s,encoding='utf-8')
