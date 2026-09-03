#!/usr/bin/env python3
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data/opportunities.json'
CONTACTS = ROOT / 'data/public-lead-contacts.json'

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s().-]*)?(?:\d[\s().-]*){7,14}\d(?!\d)")
GENERIC_LOCAL = ('info@', 'contact@', 'hello@', 'sales@', 'support@', 'enquiries@', 'enquiry@', 'secretariat@', 'conference@', 'marketing@', 'office@')


def clean_html(text):
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Cindrela-Sales-Radar-Contact-Refresh/1.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read(1_500_000)
        charset = r.headers.get_content_charset() or 'utf-8'
        return raw.decode(charset, errors='ignore')


def normalize_phone(value):
    value = re.sub(r'\s+', ' ', value).strip(' .,-')
    digits = re.sub(r'\D', '', value)
    if len(digits) < 8 or len(digits) > 15:
        return ''
    return value


def main():
    opportunities = json.loads(OPP.read_text(encoding='utf-8'))
    contacts = json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    by_event = {str(x.get('event')): x for x in contacts if x.get('event')}
    added = 0
    updated = 0

    for event in opportunities:
        title = event.get('title', '').strip()
        url = event.get('url', '').strip()
        if not title or not url or not url.startswith(('http://', 'https://')):
            continue
        try:
            html = fetch(url)
        except Exception:
            continue
        text = clean_html(html)
        emails = sorted(set(EMAIL_RE.findall(text)), key=str.lower)
        phones = []
        for match in PHONE_RE.findall(text):
            p = normalize_phone(match)
            if p and not re.fullmatch(r'20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}', p):
                phones.append(p)
        phones = list(dict.fromkeys(phones))

        generic = [e for e in emails if e.lower().startswith(GENERIC_LOCAL)]
        chosen_email = generic[0] if generic else (emails[0] if emails else '')
        chosen_phone = phones[0] if phones else ''
        if not chosen_email and not chosen_phone:
            continue

        record = by_event.get(title)
        if record:
            changed = False
            if not record.get('businessEmail') and chosen_email:
                record['businessEmail'] = chosen_email
                changed = True
            if not record.get('businessPhone') and chosen_phone:
                record['businessPhone'] = chosen_phone
                changed = True
            if changed:
                record['source'] = record.get('source') or url
                note = record.get('note', '').strip()
                extra = 'Automated public-contact extraction from the event source; verify before outreach.'
                record['note'] = (note + ' ' + extra).strip()
                updated += 1
            continue

        record = {
            'event': title,
            'company': event.get('source') or title,
            'country': 'Nigeria' if 'nigeria' in (event.get('city', '') + ' ' + title).lower() else (event.get('city') or 'International'),
            'role': 'Event Contact Desk / Organizer',
            'contactPerson': '',
            'contactRole': 'Public Event Contact',
            'businessEmail': chosen_email,
            'businessPhone': chosen_phone,
            'linkedin': '',
            'source': url,
            'note': 'Automated public-contact extraction from the official/event source; verify before outreach.'
        }
        contacts.append(record)
        by_event[title] = record
        added += 1

    CONTACTS.write_text(json.dumps(contacts, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Public lead contacts refreshed: added={added}, updated={updated}, total={len(contacts)}')


if __name__ == '__main__':
    main()
