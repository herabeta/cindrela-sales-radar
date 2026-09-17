const INTENT_TERMS = [
  'business travel Nigeria conference exhibition visa hotel flight',
  'Nigeria company delegation conference travel hotel visa',
  'Nigeria exhibitors international exhibition travel visa hotel',
  'Nigeria business trip conference flight hotel',
  'Nigeria event delegates travel accommodation visa'
];

const KEYWORDS = [
  ['visa', 24], ['business travel', 24], ['conference', 20], ['exhibition', 20],
  ['delegation', 18], ['delegate', 16], ['exhibitor', 16], ['hotel', 12],
  ['flight', 12], ['airfare', 12], ['business trip', 18], ['attend', 10],
  ['travel', 8], ['accommodation', 8], ['event', 6]
];

function decode(s='') { return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,'$1').replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&#39;/g,"'").replace(/&quot;/g,'"'); }
function tag(block, name) { const m=block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`,'i')); return m ? decode(m[1]).trim() : ''; }
function strip(s='') { return s.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim(); }
function score(title, desc) {
  const text=(title+' '+desc).toLowerCase();
  return KEYWORDS.reduce((n,[k,v])=>n+(text.includes(k)?v:0),0);
}
function entity(title) {
  const cleaned=title.replace(/\s+/g,' ').trim();
  const patterns=[
    /^(.+?)\s+(?:to attend|will attend|attends|joins|participate|participates|hosts|announces|plans to|set to)\b/i,
    /^(.+?)\s+(?:seeks|seeking|looking for|needs|requires)\b/i
  ];
  for (const p of patterns) { const m=cleaned.match(p); if (m && m[1].length>=3 && m[1].length<=100) return m[1].replace(/^[-–—: ]+|[-–—: ]+$/g,''); }
  return '';
}
async function feed(q) {
  const url='https://news.google.com/rss/search?q='+encodeURIComponent(q)+'&hl=en-NG&gl=NG&ceid=NG:en';
  const r=await fetch(url,{headers:{'user-agent':'Cindrela-Sales-Radar/1.0'}});
  if(!r.ok) throw new Error('Search source returned '+r.status);
  return r.text();
}

module.exports=async function handler(req,res){
  try {
    if(req.method!=='GET') return res.status(405).json({error:'GET only'});
    const custom=String(req.query?.q||'').trim();
    const terms=custom?[custom]:INTENT_TERMS;
    const results=[]; const seen=new Set();
    for(const q of terms.slice(0,5)){
      let xml='';
      try{xml=await feed(q)}catch(e){continue}
      for(const block of xml.match(/<item>[\s\S]*?<\/item>/gi)||[]){
        const title=tag(block,'title'), link=tag(block,'link'), pubDate=tag(block,'pubDate'), source=tag(block,'source'), desc=strip(tag(block,'description'));
        if(!title||!link) continue;
        const s=score(title,desc); if(s<24) continue;
        const key=link.split('?')[0]; if(seen.has(key)) continue; seen.add(key);
        results.push({
          id:'intent_'+Buffer.from(key).toString('base64url').slice(0,20),
          entity:entity(title), title, source, url:link, publishedAt:pubDate,
          intentScore:Math.min(100,s), intentLevel:s>=55?'HIGH':s>=35?'MEDIUM':'WATCH',
          intentSignals:KEYWORDS.filter(([k])=>(title+' '+desc).toLowerCase().includes(k)).map(([k])=>k),
          requirement:'Public web signal suggests travel/event/visa/hotel/flight intent',
          needsVerification:true
        });
      }
    }
    results.sort((a,b)=>new Date(b.publishedAt||0)-new Date(a.publishedAt||0) || b.intentScore-a.intentScore);
    res.setHeader('Cache-Control','public, s-maxage=900, stale-while-revalidate=3600');
    return res.status(200).json({ok:true,generatedAt:new Date().toISOString(),source:'Google News public RSS search results',count:results.length,data:results.slice(0,100)});
  } catch(e){ console.error('intent-radar',e); return res.status(500).json({error:'Unable to scan public intent signals right now'}); }
};
