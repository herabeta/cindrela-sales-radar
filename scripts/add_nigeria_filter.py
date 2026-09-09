#!/usr/bin/env python3
"""Safely add a Nigeria-only filter to Sales Opportunities.

Idempotent: makes only targeted replacements in index.html and fails closed
if the expected current UI/JS markers are missing.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "index.html"

s = PAGE.read_text(encoding="utf-8")

old_buttons = (
    '<button class="active" data-filter="all">All</button>'
    '<button data-filter="sell">🔴 Sell Now</button>'
    '<button data-filter="plan">🟠 Plan</button>'
    '<button data-filter="watch">🟢 Watch</button>'
    '<button data-filter="business">🏢 Business</button>'
    '<button data-filter="sports">⚽ Sports</button>'
    '<button data-filter="seasonal">🎯 Seasonal</button>'
)
new_buttons = (
    '<button class="active" data-filter="all">All</button>'
    '<button data-filter="nigeria">🇳🇬 Nigeria Events</button>'
    '<button data-filter="international">🌍 International</button>'
    '<button data-filter="sell">🔴 Sell Now</button>'
    '<button data-filter="plan">🟠 Plan</button>'
    '<button data-filter="watch">🟢 Watch</button>'
    '<button data-filter="business">🏢 Business</button>'
    '<button data-filter="sports">⚽ Sports</button>'
    '<button data-filter="seasonal">🎯 Seasonal</button>'
)

if 'data-filter="nigeria"' not in s:
    if old_buttons not in s:
        raise SystemExit("Expected Sales Opportunities filter toolbar was not found; refusing to modify index.html")
    s = s.replace(old_buttons, new_buttons, 1)

old_filter = "const filtered=opportunities.filter(o=>(current==='all'||o.type===current||o.group===current)&&(!q||(`${o.title} ${o.city} ${o.products} ${o.target}`).toLowerCase().includes(q))).sort((a,b)=>dateObj(a.start_date)-dateObj(b.start_date));"
new_filter = "const filtered=opportunities.filter(o=>((current==='all')||(current==='nigeria'&&isNigeriaOpportunity(o))||(current==='international'&&!isNigeriaOpportunity(o))||o.type===current||o.group===current)&&(!q||(`${o.title} ${o.city} ${o.products} ${o.target}`).toLowerCase().includes(q))).sort((a,b)=>dateObj(a.start_date)-dateObj(b.start_date));"

if "current==='nigeria'&&isNigeriaOpportunity(o)" not in s:
    if old_filter not in s:
        raise SystemExit("Expected Sales Opportunities filter logic was not found; refusing to modify index.html")
    s = s.replace(old_filter, new_filter, 1)

if "function isNigeriaOpportunity(o)" not in s:
    marker = "function isActiveOpportunity(o){"
    if marker not in s:
        raise SystemExit("Expected opportunity helper marker was not found; refusing to modify index.html")
    helper = "function isNigeriaOpportunity(o){const raw=String(o.country||o.location||o.city||'').toLowerCase();return /\\bnigeria\\b/.test(raw)||/\\b(abuj|lagos|port harcourt|ph|kano|ibadan|benin city|enugu|calabar|owerri|jos|kaduna|akure|abeokuta|ilorin|asaba|uyo|warri)\\b/.test(raw)}"
    s = s.replace(marker, helper + marker, 1)

# Fail closed: verify the intended additions exist and no duplicate helper was created.
if s.count('data-filter="nigeria"') != 1:
    raise SystemExit("Nigeria filter count is not exactly 1")
if s.count("function isNigeriaOpportunity(o)") != 1:
    raise SystemExit("Nigeria helper count is not exactly 1")
if s.count("current==='nigeria'&&isNigeriaOpportunity(o)") != 1:
    raise SystemExit("Nigeria filter logic count is not exactly 1")

PAGE.write_text(s, encoding="utf-8")
print("Nigeria-only Sales Opportunities filter applied safely.")
