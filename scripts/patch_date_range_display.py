#!/usr/bin/env python3
"""Patch the three user-facing pages to display verified event date ranges.

The data source owns start_date/end_date. Pages fall back to the existing single
start date when an end date is not available.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def patch(path, replacements):
    p=ROOT/path
    s=p.read_text(encoding='utf-8')
    original=s
    for old,new in replacements:
        if old in s:
            s=s.replace(old,new)
    if s!=original:p.write_text(s,encoding='utf-8')

# Sales Opportunities: replace dateLabel with a range-aware formatter.
patch('index.html', [
("function dateLabel(s){const d=dateObj(s);return isNaN(d)?s:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}",
"function dateLabel(s,e){const d=dateObj(s),x=dateObj(e||s);if(isNaN(d))return s;if(e&&!isNaN(x)){const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return a===b?a:(d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'})+' – '+x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):a+' – '+b)}return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}"),
("${esc(dateLabel(o.start_date))}","${esc(dateLabel(o.start_date,o.end_date))}"),
("mPlace.textContent=`📅 ${dateLabel(selected.start_date)} • 📍 ${selected.city} • ${selected.score}/100`;","mPlace.textContent=`📅 ${dateLabel(selected.start_date,selected.end_date)} • 📍 ${selected.city} • ${selected.score}/100`;")
])

# Event Explorer: its card currently prints only start_date.
patch('event-calendar-full.html', [
("<b>📅 ${esc(e.start_date)}</b>","<b>📅 ${esc(dateLabel(e.start_date,e.end_date))}</b>"),
("const monthKey=e=>String(e.start_date||'').slice(0,7);","const monthKey=e=>String(e.start_date||'').slice(0,7);const dateLabel=(s,e)=>{const d=new Date((s||'')+'T00:00:00'),x=new Date((e||s||'')+'T00:00:00');if(isNaN(d))return s||'';if(!e||isNaN(x)||d.getTime()===x.getTime())return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?a+' – '+b:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})+' – '+b};")
])

# Lead Finder: show the range in the event selector and event info.
patch('lead-finder.html', [
("const productsFor=e=>Array.isArray(e.products)?e.products.join(' + '):(e?.products||'Flight + Hotel + Transfers')", "const dateLabel=(s,e)=>{const d=new Date((s||'')+'T00:00:00'),x=new Date((e||s||'')+'T00:00:00');if(isNaN(d))return s||'';if(!e||isNaN(x)||d.getTime()===x.getTime())return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?a+' – '+b:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})+' – '+b};const productsFor=e=>Array.isArray(e.products)?e.products.join(' + '):(e?.products||'Flight + Hotel + Transfers')"),
("esc(e.start_date)+' • '+esc(e.title)","esc(dateLabel(e.start_date,e.end_date))+' • '+esc(e.title)"),
("$('eventInfo').textContent=e.start_date+' • '+e.city+' • Target:","$('eventInfo').textContent=dateLabel(e.start_date,e.end_date)+' • '+e.city+' • Target:")
])
