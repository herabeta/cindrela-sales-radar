#!/usr/bin/env python3
"""Apply date-range display patches safely and idempotently.

The data source owns start_date/end_date. This script may run daily, so it must
never append the same JavaScript declaration or UI enhancement more than once.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, replacements):
    p = ROOT / path
    s = p.read_text(encoding="utf-8")
    original = s
    for old, new in replacements:
        if old in s:
            s = s.replace(old, new)
    if s != original:
        p.write_text(s, encoding="utf-8")


# Sales Opportunities: replace dateLabel with a range-aware formatter.
patch("index.html", [
    (
        "function dateLabel(s){const d=dateObj(s);return isNaN(d)?s:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}",
        "function dateLabel(s,e){const d=dateObj(s),x=dateObj(e||s);if(isNaN(d))return s;if(e&&!isNaN(x)){const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return a===b?a:(d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'})+' – '+x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'}):a+' – '+b)}return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}"
    ),
    ("${esc(dateLabel(o.start_date))}", "${esc(dateLabel(o.start_date,o.end_date))}"),
    ("mPlace.textContent=`📅 ${dateLabel(selected.start_date)} • 📍 ${selected.city} • ${selected.score}/100`;", "mPlace.textContent=`📅 ${dateLabel(selected.start_date,selected.end_date)} • 📍 ${selected.city} • ${selected.score}/100`;")
])


# Safe UX improvements for Sales Opportunities. The marker makes this idempotent.
p = ROOT / "index.html"
s = p.read_text(encoding="utf-8")
original = s
marker = "sales-radar-ux-v1"
if marker not in s:
    css = """<style>/* sales-radar-ux-v1 */
.stat[data-clickable="1"]{cursor:pointer;transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}.stat[data-clickable="1"]:hover{transform:translateY(-2px);box-shadow:0 7px 18px #10182812;border-color:#cfd6e2}.stat[data-clickable="1"].stat-active{border-color:#101828;box-shadow:0 0 0 2px #10182812}.opportunity-tools{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:0 0 12px}.result-count{font-size:12px;color:#667085;font-weight:700}.clear-search{display:none;border:1px solid #e4e7ec;background:#fff;color:#344054;padding:7px 10px;border-radius:8px;font-weight:800;cursor:pointer}.clear-search.show{display:inline-block}.next-opportunity{margin:0 0 16px;padding:12px 14px;border:1px solid #d9e2f1;background:#f8fbff;border-radius:11px;font-size:12.5px;color:#344054}.next-opportunity b{color:#101828}.next-opportunity button{border:0;background:#101828;color:#fff;padding:7px 10px;border-radius:7px;font-weight:800;cursor:pointer;margin-left:8px}</style>"""
    if "</style>" in s:
        s = s.replace("</style>", css + "</style>", 1)

    js = """<script>/* sales-radar-ux-v1 */
(function(){
  const search=document.getElementById('search');
  const toolbar=document.querySelector('.toolbar');
  const cards=document.getElementById('cards');
  if(!search||!toolbar||!cards)return;
  const tools=document.createElement('div');
  tools.className='opportunity-tools';
  tools.innerHTML='<span class="result-count" id="resultCount">Preparing opportunities…</span><button class="clear-search" id="clearSearch" type="button">Clear search</button>';
  toolbar.insertAdjacentElement('afterend',tools);
  const clear=document.getElementById('clearSearch');
  function syncCount(){
    const visible=cards.querySelectorAll('.card').length;
    const empty=cards.textContent.includes('No matching opportunity found');
    document.getElementById('resultCount').textContent=empty?'No matching opportunities':(visible+' opportunity'+(visible===1?'':'ies').replace('opportunit ies','opportunities')+' shown');
    clear.classList.toggle('show',!!search.value.trim());
  }
  clear.addEventListener('click',function(){search.value='';search.dispatchEvent(new Event('input'));search.focus()});
  search.addEventListener('input',()=>setTimeout(syncCount,0));
  const originalRender=window.render;
  if(typeof originalRender==='function')window.render=function(){originalRender();syncCount()};
  const map={sellCount:'sell',planCount:'plan',watchCount:'watch',totalCount:'all'};
  Object.keys(map).forEach(id=>{
    const el=document.getElementById(id);const box=el&&el.closest('.stat');if(!box)return;
    box.dataset.clickable='1';box.title='Click to filter opportunities';
    box.addEventListener('click',function(){
      const button=document.querySelector('.filters button[data-filter="'+map[id]+'"]');
      if(button)button.click();
      document.querySelectorAll('.stat[data-clickable="1"]').forEach(x=>x.classList.remove('stat-active'));
      box.classList.add('stat-active');
      window.scrollTo({top:Math.max(0,toolbar.getBoundingClientRect().top+window.scrollY-95),behavior:'smooth'});
    });
  });
  document.querySelector('.filters button[data-filter="all"]')?.addEventListener('click',function(){document.querySelectorAll('.stat[data-clickable="1"]').forEach(x=>x.classList.remove('stat-active'))});
  const next=document.createElement('div');
  next.className='next-opportunity';
  next.id='nextOpportunity';
  next.innerHTML='<b>⏭️ Next opportunity:</b> loading…';
  cards.parentNode.insertBefore(next,cards);
  const refreshNext=()=>{
    if(!Array.isArray(window.opportunities)||!window.opportunities.length)return;
    const now=new Date();now.setHours(0,0,0,0);
    const nextEvent=window.opportunities.slice().sort((a,b)=>new Date(a.start_date)-new Date(b.start_date)).find(o=>new Date(o.start_date+'T00:00:00')>=now);
    if(nextEvent){
      const d=dateObj(nextEvent.start_date);
      const label=isNaN(d)?nextEvent.start_date:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});
      next.innerHTML='<b>⏭️ Next opportunity:</b> '+esc(nextEvent.title)+' • '+esc(label)+' • '+esc(nextEvent.city||'')+' <button type="button" onclick="openModal('+nextEvent.id+')">Open sales play</button>';
    }else next.innerHTML='<b>⏭️ Next opportunity:</b> No future event currently loaded.';
  };
  const watch=()=>{syncCount();refreshNext()};
  setTimeout(watch,1200);
  setInterval(watch,3000);
})();</script>"""
    if "</script></body>" in s:
        s = s.replace("</script></body>", js + "</script></body>", 1)
    if s != original:
        p.write_text(s, encoding="utf-8")


# Event Explorer: update the card, but add the formatter only when it is absent.
p = ROOT / "event-calendar-full.html"
s = p.read_text(encoding="utf-8")
original = s
s = s.replace("<b>📅 ${esc(e.start_date)}</b>", "<b>📅 ${esc(dateLabel(e.start_date,e.end_date))}</b>")
if "const dateLabel=" not in s:
    anchor = "const monthKey=e=>String(e.start_date||'').slice(0,7);"
    declaration = "const dateLabel=(s,e)=>{const d=new Date((s||'')+'T00:00:00'),x=new Date((e||s||'')+'T00:00:00');if(isNaN(d))return s||'';if(!e||isNaN(x)||d.getTime()===x.getTime())return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?a+' – '+b:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})+' – '+b};"
    if anchor in s:
        s = s.replace(anchor, anchor + declaration, 1)
if s != original:
    p.write_text(s, encoding="utf-8")


# Lead Finder: add its formatter only when absent, then update date usages.
p = ROOT / "lead-finder.html"
s = p.read_text(encoding="utf-8")
original = s
if "const dateLabel=" not in s:
    anchor = "const productsFor=e=>Array.isArray(e.products)?e.products.join(' + '):(e?.products||'Flight + Hotel + Transfers')"
    declaration = "const dateLabel=(s,e)=>{const d=new Date((s||'')+'T00:00:00'),x=new Date((e||s||'')+'T00:00:00');if(isNaN(d))return s||'';if(!e||isNaN(x)||d.getTime()===x.getTime())return d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});const a=d.toLocaleDateString('en-GB',{day:'2-digit',month:'short'}),b=x.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return d.getFullYear()===x.getFullYear()&&d.getMonth()===x.getMonth()?a+' – '+b:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})+' – '+b};"
    if anchor in s:
        s = s.replace(anchor, declaration + anchor, 1)
s = s.replace("esc(e.start_date)+' • '+esc(e.title)", "esc(dateLabel(e.start_date,e.end_date))+' • '+esc(e.title)")
s = s.replace("$('eventInfo').textContent=e.start_date+' • '+e.city+' • Target:", "$('eventInfo').textContent=dateLabel(e.start_date,e.end_date)+' • '+e.city+' • Target:")
if s != original:
    p.write_text(s, encoding="utf-8")

print("Date range patches and Sales Opportunities UX enhancements applied safely (idempotent).")
