#!/usr/bin/env python3
"""Remove malformed/placeholder public contact values without inventing replacements.

This is deliberately conservative: valid-looking business contacts are preserved; only
obvious image filenames, placeholders, date-like numbers and invalid contact routes are removed.
"""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'data/public-lead-contacts.json'

IMAGE_EXT=re.compile(r'\.(?:png|jpe?g|gif|webp|svg|ico|pdf|css|js)$',re.I)
DIMENSION_DOMAIN=re.compile(r'^(?:\d{2,4}x\d{2,4}|\d+x|x\d+)\.',re.I)
PLACEHOLDER_EMAIL=re.compile(r'^(?:email@domain\.ext|user@email\.com|test@example\.com|example@example\.com|name@domain\.(?:com|ext))$',re.I)
EMAIL_RE=re.compile(r'^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$')
DATE_RE=re.compile(r'(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])')
YEAR_RANGE_RE=re.compile(r'(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}')

def clean_email(value):
    email=str(value or '').strip()
    if not email:return ''
    domain=email.rsplit('@',1)[-1].lower() if '@' in email else ''
    if not EMAIL_RE.fullmatch(email) or PLACEHOLDER_EMAIL.fullmatch(email):return ''
    if IMAGE_EXT.search(domain) or DIMENSION_DOMAIN.match(domain):return ''
    return email

def clean_phone(value):
    phone=str(value or '').strip()
    if not phone:return ''
    digits=re.sub(r'\D','',phone)
    if not 8<=len(digits)<=15:return ''
    if DATE_RE.search(phone) or YEAR_RANGE_RE.search(phone):return ''
    if re.fullmatch(r'(?:19|20)\d{2}',digits) or re.fullmatch(r'(?:19|20)\d{2}(?:19|20)\d{2}',digits):return ''
    return phone

def clean_linkedin(value):
    li=str(value or '').strip()
    if not li:return ''
    return li if re.fullmatch(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9_./%-]+',li,re.I) else ''

def clean_record(row):
    if not isinstance(row,dict):return None
    out=dict(row)
    out['businessEmail']=clean_email(row.get('businessEmail'))
    out['businessPhone']=clean_phone(row.get('businessPhone'))
    out['linkedin']=clean_linkedin(row.get('linkedin'))
    if not (out['businessEmail'] or out['businessPhone'] or out['linkedin']):
        return None
    out['contactReady']=True
    return out

def main():
    rows=json.loads(MASTER.read_text(encoding='utf-8'))
    if not isinstance(rows,list):raise SystemExit('Lead contact master is not a JSON list; refusing to modify.')
    cleaned=[];removed=0;changed=0
    for row in rows:
        if not isinstance(row,dict):
            removed+=1;continue
        out=clean_record(row)
        if out is None:
            removed+=1;continue
        if out!=row:changed+=1
        cleaned.append(out)
    if removed or changed:
        MASTER.write_text(json.dumps(cleaned,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'Lead contact cleanup: input={len(rows)}, output={len(cleaned)}, removed={removed}, sanitized={changed}')

if __name__=='__main__':main()
