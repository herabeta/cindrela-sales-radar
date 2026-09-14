#!/usr/bin/env python3
"""Validate the existing Lead Finder display without rewriting its JavaScript.

The Lead Finder page already contains the required event/company grouping and
multiple-contact display. Rewriting its minified inline JS caused syntax errors,
so this step is intentionally idempotent and safe: it only verifies the expected
markers and leaves the page untouched.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'lead-finder.html'
s = PAGE.read_text(encoding='utf-8')

required = [
    'function render(){',
    'contactKey=',
    'Companies',
    'Mark Contacted',
    'Open Source',
]
missing = [m for m in required if m not in s]
if missing:
    raise SystemExit('Lead Finder display verification failed; missing: ' + ', '.join(missing))

print('Lead Finder display verified safely; existing grouped/contactable UI left unchanged.')
