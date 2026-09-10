#!/usr/bin/env python3
"""Group Lead Finder cards by event + company while preserving every contact.

The enrichment layer intentionally keeps distinct public contacts separate so no
contact is lost. The UI should not turn those contacts into repeated company cards,
so this patch makes the display one card per event/company and renders all verified
contacts inside that card.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'lead-finder.html'
s=PAGE.read_text(encoding='utf-8')

start=s.find('function render(){')
end=s.find('async function loadEvent', start)
if start<0 or end<0 or end<=start:
    raise SystemExit('Lead Finder render function markers not found; refusing to modify file.')

new_render=r'''function render(){const a=(current==='__ALL__'?leads:leads.filter(x=>x.event===current)).filter(x=>activeTitles.has(x.event)&&contactable(x)),q=$('q').value.toLowerCase().trim(),p=$('p').value,s=$('s').value,shown=a.filter(x=>(p==='all'||x.priority===p)&&(s==='all'||x.status===s)&&(!q||JSON.stringify(x).toLowerCase().includes(q)));const groups=[];const gm=new Map();shown.forEach(x=>{const k=norm(x.event)+'|'+norm(x.company);let g=gm.get(k);if(!g){g={base:x,contacts:[],ids:[]};gm.set(k,g);groups.push(g)}const ck=String(x.businessEmail||x.businessPhone||x.linkedin||x.source||'').toLowerCase().trim();if(!g.contacts.some(c=>String(c.businessEmail||c.businessPhone||c.linkedin||c.source||'').toLowerCase().trim()===ck))g.contacts.push(x);g.ids.push(x.id)});$('stats').innerHTML='<span class="stat"><b>'+a.length+'</b>Contactable Leads</span><span class="stat"><b>'+a.filter(x=>x.businessEmail||x.businessPhone).length+'</b>Email/Phone Ready</span><span class="stat"><b>'+a.filter(x=>x.linkedin).length+'</b>LinkedIn Ready</span><span class="stat"><b>'+a.filter(x=>x.priority==='HOT').length+'</b>HOT</span><span class="stat"><b>'+a.filter(x=>x.priority==='WARM').length+'</b>WARM</span><span class="stat"><b>'+a.filter(x=>x.priority==='EARLY').length+'</b>EARLY</span><span class="stat"><b>'+a.filter(x=>x.status==='Contacted').length+'</b>Contacted</span><span class="stat"><b>'+a.filter(x=>x.status==='Won').length+'</b>Won</span><span class="stat"><b>'+groups.length+'</b>Companies</span>';$('grid').innerHTML=groups.length?groups.map(g=>{const x=g.base;const contacts=g.contacts;const contactHtml=contacts.map((c,i)=>'<div style="padding:8px 0;'+(i?'border-top:1px solid #dfe7e2;':'')+'">'+(c.businessEmail?'✉️ '+esc(c.businessEmail):'')+(c.businessPhone?'<br>☎️ '+esc(c.businessPhone):'')+(c.linkedin?'<br>🔗 LinkedIn available':'')+(c.contactPerson?'<br>👤 '+esc(c.contactPerson):'')+'<div class="actions">'+(c.businessEmail?'<a href="'+mailHref(c)+'">Email</a>':'')+(c.businessPhone?'<a href="'+waHref(c)+'" target="_blank" rel="noopener">WhatsApp</a><a href="tel:'+esc(c.businessPhone)+'">Call</a>':'')+(c.linkedin?'<a href="'+esc(c.linkedin)+'" target="_blank" rel="noopener">LinkedIn ↗</a>':'')+'<a href="'+esc(c.source||'#')+'" target="_blank" rel="noopener">Open Source ↗</a><button data-s="'+c.id+'">Mark Contacted</button><button data-d="'+c.id+'">Delete</button></div></div>').join('');return '<article class="card '+x.priority.toLowerCase()+'"><div><span class="tag">'+esc(x.priority)+' • '+esc(x.status)+'</span> <span class="tag">'+esc(x.event)+'</span></div><h3>'+esc(x.company)+'</h3><div class="meta">🌍 '+esc(x.country)+'<br>🎯 '+esc(x.role)+'<br>📍 '+esc(x.stand)+'</div><div class="bar"><b>💰 What to sell</b><br>'+esc(x.product)+'</div><div class="bar contact"><b>📞 Public business contact</b>'+contactHtml+'</div></article>'}).join(''):'<div class="empty">No contactable leads found for this event/filter.</div>'}'''

s=s[:start]+new_render+s[end:]
PAGE.write_text(s,encoding='utf-8')
print('Lead Finder display grouped by event + company; all distinct public contacts preserved inside each company card.')
