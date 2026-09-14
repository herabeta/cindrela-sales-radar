#!/usr/bin/env python3
"""Group Lead Finder by event + company and prioritize sales-ready contacts.

Preserves every distinct public contact while making the UI easier to sell from:
- one card per event/company
- transparent 0-100 sales-fit score
- Sales-ready filter (>=65)
- score-first ordering
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAGE=ROOT/'lead-finder.html'
s=PAGE.read_text(encoding='utf-8')

start=s.find('function render(){')
end=s.find('async function loadEvent', start)
if start<0 or end<0 or end<=start:
    raise SystemExit('Lead Finder render function markers not found; refusing to modify file.')

marker="},phoneForWhatsApp="
if marker in s and 'salesFitScore=' not in s:
    score_js="},salesFitScore=x=>{const stored=Number(x?.salesFitScore);if(stored>0)return Math.min(100,stored);let n=20;if(x?.businessEmail)n+=30;if(x?.businessPhone)n+=30;if(x?.linkedin)n+=10;if(x?.contactPerson)n+=15;const t=String(x?.role||'')+' '+String(x?.contactRole||'')+' '+String(x?.company||'');if(/procurement|purchase|purchasing|admin|hr|human resources|travel desk|operations|events|event|manager|director|founder|owner|sales|marketing/i.test(t))n+=15;if(/exhibitor|sponsor|partner|delegate|speaker|buyer|supplier/i.test(t))n+=10;return Math.min(100,n)},salesReady=x=>salesFitScore(x)>=65,salesTier=x=>salesFitScore(x)>=80?'TOP':salesReady(x)?'READY':'EARLY',phoneForWhatsApp="
    s=s.replace(marker,score_js,1)

status_select='<select id="s"><option value="all">All statuses</option><option>New</option><option>Contacted</option><option>Interested</option><option>Quoted</option><option>Won</option><option>Lost</option></select>'
if 'id="r"' not in s and status_select in s:
    replacement=status_select+'<select id="r"><option value="all">All sales leads</option><option value="ready">Sales-ready (65+)</option><option value="top">Top leads (80+)</option></select>'
    s=s.replace(status_select,replacement,1)

if '.sales-score' not in s:
    s=s.replace('</style>','.sales-score{font-size:11px;background:#ecfdf3;color:#067647;padding:5px 8px;border-radius:15px;font-weight:800}.sales-top{background:#fff1f3;color:#c01048}.sales-early{background:#f2f4f7;color:#475467}.score-note{font-size:11px;color:#667085;margin-top:5px}</style>',1)

new_render=r'''function render(){const a=(current==='__ALL__'?leads:leads.filter(x=>x.event===current)).filter(x=>activeTitles.has(x.event)&&contactable(x)),q=$('q').value.toLowerCase().trim(),p=$('p').value,s=$('s').value,r=$('r')?.value||'all',shown=a.filter(x=>(p==='all'||x.priority===p)&&(s==='all'||x.status===s)&&(r==='all'||(r==='ready'&&salesReady(x))||(r==='top'&&salesFitScore(x)>=80))&&(!q||JSON.stringify(x).toLowerCase().includes(q))).sort((a,b)=>salesFitScore(b)-salesFitScore(a));const groups=[];const gm=new Map();shown.forEach(x=>{const k=norm(x.event)+'|'+norm(x.company);let g=gm.get(k);if(!g){g={base:x,contacts:[],ids:[]};gm.set(k,g);groups.push(g)}const ck=String(x.businessEmail||x.businessPhone||x.linkedin||x.source||'').toLowerCase().trim();if(!g.contacts.some(c=>String(c.businessEmail||c.businessPhone||c.linkedin||c.source||'').toLowerCase().trim()===ck))g.contacts.push(x);g.ids.push(x.id)});$('stats').innerHTML='<span class="stat"><b>'+a.length+'</b>Contactable Leads</span><span class="stat"><b>'+a.filter(x=>x.businessEmail||x.businessPhone).length+'</b>Email/Phone Ready</span><span class="stat"><b>'+a.filter(x=>x.linkedin).length+'</b>LinkedIn Ready</span><span class="stat"><b>'+a.filter(x=>salesReady(x)).length+'</b>Sales-ready</span><span class="stat"><b>'+a.filter(x=>salesFitScore(x)>=80).length+'</b>Top Leads</span><span class="stat"><b>'+a.filter(x=>x.priority==='HOT').length+'</b>HOT</span><span class="stat"><b>'+groups.length+'</b>Companies</span>';$('grid').innerHTML=groups.length?groups.map(g=>{const x=g.base;const sx=salesFitScore(x),tier=salesTier(x),contacts=g.contacts;const contactHtml=contacts.map((c,i)=>'<div style="padding:8px 0;'+(i?'border-top:1px solid #dfe7e2;':'')+'">'+(c.businessEmail?'✉️ '+esc(c.businessEmail):'')+(c.businessPhone?'<br>☎️ '+esc(c.businessPhone):'')+(c.linkedin?'<br>🔗 LinkedIn available':'')+(c.contactPerson?'<br>👤 '+esc(c.contactPerson):'')+'<div class="actions">'+(c.businessEmail?'<a href="'+mailHref(c)+'">Email</a>':'')+(c.businessPhone?'<a href="'+waHref(c)+'" target="_blank" rel="noopener">WhatsApp</a><a href="tel:'+esc(c.businessPhone)+'">Call</a>':'')+(c.linkedin?'<a href="'+esc(c.linkedin)+'" target="_blank" rel="noopener">LinkedIn ↗</a>':'')+'<a href="'+esc(c.source||'#')+'" target="_blank" rel="noopener">Open Source ↗</a><button data-s="'+c.id+'">Mark Contacted</button><button data-d="'+c.id+'">Delete</button></div></div>').join('');return '<article class="card '+x.priority.toLowerCase()+'"><div><span class="tag">'+esc(x.priority)+' • '+esc(x.status)+'</span> <span class="tag">'+esc(x.event)+'</span> <span class="sales-score '+(tier==='TOP'?'sales-top':tier==='EARLY'?'sales-early':'')+'">'+sx+'/100 '+tier+'</span></div><h3>'+esc(x.company)+'</h3><div class="meta">🌍 '+esc(x.country)+'<br>🎯 '+esc(x.role)+'<br>📍 '+esc(x.stand)+'</div><div class="score-note">Sales fit: '+sx+'/100 • ranked for practical outreach</div><div class="bar"><b>💰 What to sell</b><br>'+esc(x.product)+'</div><div class="bar contact"><b>📞 Public business contact</b>'+contactHtml+'</div></article>'}).join(''):'<div class="empty">No contactable leads found for this event/filter.</div>';}'''

s=s[:start]+new_render+s[end:]
PAGE.write_text(s,encoding='utf-8')
print('Lead Finder upgraded: company grouping preserved, sales-fit scoring/filtering added, and cards ranked by outreach readiness.')
