#!/usr/bin/env python3
"""Build a lead pool for every Sales Opportunity from verified/public event contacts.
Never invent a person or private contact. One event always gets an organizer lead when the
opportunity itself has a public source URL; additional leads are created from distinct public
contact records. Each lead receives an event-specific outreach strategy.
"""
import json
import hashlib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPP = ROOT / 'data/opportunities.json'
CONTACTS = ROOT / 'data/public-lead-contacts.json'
OUT = ROOT / 'data/event-lead-pool.json'


def hid(*parts):
    raw = '|'.join(str(x or '') for x in parts).encode()
    return 'auto-' + hashlib.sha1(raw).hexdigest()[:12]


def priority(start):
    try:
        d = (date.fromisoformat(start) - date.today()).days
    except Exception:
        d = 9999
    if d < 0: return 'CLOSED'
    if d <= 21: return 'HOT'
    if d <= 90: return 'WARM'
    return 'EARLY'


def strategy(event, lead):
    title = event.get('title', '')
    group = (event.get('group') or '').lower()
    city = event.get('city') or 'Nigeria'
    p = priority(event.get('start_date', ''))
    if 'sports' in group or any(k in title.lower() for k in ('fifa','grand prix','formula','olympic','afcon','super bowl','basketball','tennis','cricket')):
        target = lead.get('contactRole') or lead.get('role') or 'Team manager / delegation / sports group'
        opener = f"Hi [Name], I’m Devanshu from Cindrela Travel. Are you or your team planning travel for {title} in {city}? We can handle flights, hotels, transfers and group travel."
        channel = 'Email first; LinkedIn/phone follow-up; WhatsApp only if publicly listed as business contact.'
    elif 'exhibition' in title.lower() or 'expo' in title.lower() or 'trade' in title.lower() or 'fair' in title.lower():
        target = lead.get('contactRole') or lead.get('role') or 'Exhibitor / organiser / operations / delegate'
        opener = f"Hi [Name], I’m Devanshu from Cindrela Travel. Are your team or delegates attending {title}? We can arrange flights, hotels, airport transfers and business/group travel."
        channel = 'Email first; call public business line; LinkedIn follow-up; WhatsApp only on a public business number.'
    else:
        target = lead.get('contactRole') or lead.get('role') or 'Organizer / exhibitor / delegate / operations'
        opener = f"Hi [Name], I’m Devanshu from Cindrela Travel. I’m reaching out regarding {title}. Would you like a quick travel plan/quote for your team or delegates?"
        channel = 'Email or public business phone first; LinkedIn follow-up; WhatsApp only where business WhatsApp is publicly listed.'
    days = None
    try: days = (date.fromisoformat(event['start_date']) - date.today()).days
    except Exception: pass
    if days is not None and days <= 7: cadence = 'Follow up in 24–48 hours.'
    elif days is not None and days <= 21: cadence = 'Follow up every 2–3 days until qualified.'
    elif days is not None and days <= 90: cadence = 'Follow up weekly; move qualified prospects to quotation.'
    else: cadence = 'Follow up every 2–4 weeks; re-engage 60/30/14 days before travel.'
    return {'target_role': target, 'contact_method': channel, 'opening_message': opener, 'follow_up': cadence,
            'qualification': 'Ask travel dates, passenger count, origin city, hotel nights, transfer needs and visa requirement; then quote.'}


def main():
    events = json.loads(OPP.read_text(encoding='utf-8'))
    contacts = json.loads(CONTACTS.read_text(encoding='utf-8')) if CONTACTS.exists() else []
    by_event = {}
    for c in contacts:
        by_event.setdefault(c.get('event',''), []).append(c)
    pool = []
    for e in events:
        title = e.get('title','').strip()
        if not title: continue
        matched = by_event.get(title, [])
        # Always create one organizer/official-source lead when the event has a source URL.
        seeds = matched[:] if matched else [{
            'company': e.get('source') or title,
            'country': 'Nigeria' if 'nigeria' in (e.get('city','') + ' ' + title).lower() else e.get('city') or 'International',
            'role': 'Event Contact Desk / Organizer',
            'contactPerson': '', 'contactRole': 'Public Event Contact',
            'businessEmail': '', 'businessPhone': '', 'linkedin': '',
            'source': e.get('url',''), 'note': 'Official/event source lead; contact details require public-source verification.'
        }] if e.get('url') else []
        seen = set()
        for c in seeds:
            key = (title.lower(), (c.get('company') or '').lower(), (c.get('businessEmail') or '').lower(), (c.get('businessPhone') or '').lower())
            if key in seen: continue
            seen.add(key)
            rec = {
                'id': hid(title, c.get('company'), c.get('businessEmail'), c.get('businessPhone')),
                'event': title, 'eventId': e.get('id'), 'start_date': e.get('start_date'),
                'company': c.get('company') or e.get('source') or title,
                'country': c.get('country') or e.get('city') or 'Nigeria',
                'role': c.get('role') or c.get('contactRole') or 'Organizer / Operations / Delegate',
                'contactPerson': c.get('contactPerson',''), 'contactRole': c.get('contactRole',''),
                'businessEmail': c.get('businessEmail',''), 'businessPhone': c.get('businessPhone',''),
                'linkedin': c.get('linkedin',''), 'source': c.get('source') or e.get('url',''),
                'verification': 'public_source' if (c.get('businessEmail') or c.get('businessPhone') or c.get('contactPerson')) else 'needs_contact_verification',
                'priority': priority(e.get('start_date','')),
                'products': e.get('products', []),
            }
            rec.update(strategy(e, c))
            pool.append(rec)
    OUT.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Event lead pool built: {len(pool)} leads across {len(events)} opportunities')

if __name__ == '__main__':
    main()
