#!/usr/bin/env python3
"""Multi-source public lead enrichment layer.

This layer never fabricates contact data. It builds a normalized enrichment
record for every upcoming opportunity and combines existing verified contacts
with contacts discoverable from the event's public source page. It also stores
safe discovery targets for additional public sources so Lead Finder can surface
where a human can continue research when a source is not machine-readable.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data/opportunities.json'
CONTACTS = ROOT / 'data/public-lead-contacts.json'
OUT = ROOT / 'data/lead-enrichment.json'

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s().-]*)?(?:\d[\s().-]*){7,14}\d(?!\d)")
GENERIC = ('info@', 'contact@', 'hello@', 'sales@', 'support@', 'enquiries@', 'enquiry@', 'secretariat@', 'conference@', 'marketing@', 'office@')


def fetch_text(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Cindrela-Sales-Radar-MultiSource/1.0'})
    with urllib.request.urlopen(req, timeout=12) as r:
        raw = r.read(1_200_000)
        charset = r.headers.get_content_charset() or 'utf-8'
        text = raw.decode(charset, errors='ignore')
    text = re.sub(r'<script[\s\S]*?</script>', ' ', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', ' ', text, flags=re.I)
    return re.sub(r'<[^>]+>', ' ', text)


def clean_phone(value):
    value = re.sub(r'\s+', ' ', value).strip(' .,-')
    digits = re.sub(r'\D', '', value)
    return value if 8 <= len(digits) <= 15 else ''


def source_targets(company, event, city):
    q = urllib.parse.quote_plus(f'{company} {event} {city}'.strip())
    return {
        'website': event,
        'google_search': f'https://www.google.com/search?q={q}',
        'google_maps': f'https://www.google.com/maps/search/?api=1&query={q}',
        'linkedin_search': f'https://www.linkedin.com/search/results/all/?keywords={q}',
        'instagram_search': f'https://www.google.com/search?q={q}+site%3Ainstagram.com',
        'facebook_search': f'https://www.google.com/search?q={q}+site%3Afacebook.com',
        'x_search': f'https://www.google.com/search?q={q}+site%3Ax.com',
        'youtube_search': f'https://www.google.com/search?q={q}+site%3Ayoutube.com',
        'directory_search': f'https://www.google.com/search?q={q}+business+directory',
    }


def main():
    opportunities = json.loads(OPP.read_text(encoding='utf-8'))
    contacts = json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    by_event = {str(x.get('event', '')).strip().lower(): x for x in contacts if x.get('event')}
    records = []
    today = date.today()

    for event in opportunities:
        title = str(event.get('title', '')).strip()
        if not title:
            continue
        try:
            days = (date.fromisoformat(event['start_date']) - today).days
        except Exception:
            days = None
        existing = by_event.get(title.lower(), {})
        company = existing.get('company') or event.get('source') or title
        email = existing.get('businessEmail', '')
        phone = existing.get('businessPhone', '')
        person = existing.get('contactPerson', '')
        role = existing.get('contactRole') or existing.get('role', '')
        sources_checked = []

        url = str(event.get('url', '')).strip()
        if url.startswith(('http://', 'https://')):
            sources_checked.append('official_event_source')
            try:
                text = fetch_text(url)
                emails = sorted(set(EMAIL_RE.findall(text)), key=str.lower)
                phones = list(dict.fromkeys(filter(None, (clean_phone(x) for x in PHONE_RE.findall(text)))))
                generic = [x for x in emails if x.lower().startswith(GENERIC)]
                if not email and (generic or emails):
                    email = (generic or emails)[0]
                if not phone and phones:
                    phone = phones[0]
            except Exception:
                pass

        targets = source_targets(company, title, event.get('city', ''))
        if email or phone:
            verification = 'public_business_contact'
            confidence = 'high' if existing.get('source') else 'medium'
        else:
            verification = 'discovery_targets_only'
            confidence = 'unverified'

        records.append({
            'event': title,
            'eventId': event.get('id'),
            'startDate': event.get('start_date'),
            'daysUntil': days,
            'company': company,
            'contactPerson': person,
            'contactRole': role,
            'businessEmail': email,
            'businessPhone': phone,
            'linkedin': existing.get('linkedin', ''),
            'verification': verification,
            'confidence': confidence,
            'sourcesChecked': sources_checked,
            'sourceUrl': existing.get('source') or url,
            'discoveryTargets': targets,
            'nextAction': 'Use verified contact for outreach' if (email or phone) else 'Open public-source discovery targets and verify a business contact before outreach',
        })

    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Multi-source lead enrichment built: records={len(records)}')


if __name__ == '__main__':
    main()
