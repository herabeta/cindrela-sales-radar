const fs = require('fs');
const path = require('path');

function read(name) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', name), 'utf8'));
}

const genericCompany = /^(media partners?|speakers?|why sponsor|sponsors?|exhibitors?|delegates?|visitors?|attendees?|organisers?|organizers?|partners?|contact us|about us|registration|sales|marketing|head office|general enquiries?|general inquiries?|event organiser listings|event organizer listings|public business contact|event contact desk)$/i;

function validEmail(value) {
  const email = String(value || '').trim();
  if (!email || /[<>]/.test(email)) return false;
  const parts = email.split('@');
  if (parts.length !== 2) return false;
  const [local, domain] = parts;
  if (!local || !domain || local.length < 3 || /^(example|test|domain|localhost)$/i.test(domain)) return false;
  if (!/^[A-Za-z0-9][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*[A-Za-z0-9]$/.test(local)) return false;
  const labels = domain.split('.');
  if (labels.length < 2 || labels.some((x) => x.length < 2)) return false;
  return labels.every((x) => /^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$/.test(x)) && /^[A-Za-z]{2,24}$/.test(labels.at(-1) || '');
}

function validPhone(value) {
  const phone = String(value || '').trim();
  const digits = phone.replace(/\D/g, '');
  if (digits.length < 8 || digits.length > 15) return false;
  if (/^([0-9])\1{6,}$/.test(digits)) return false;
  if (/(?:\d+\.\d+\s+){2,}\d+\.\d+/.test(phone)) return false;
  if (/^\d{1,3}\s+\d{1,3}\s+0{5,}\d+$/.test(phone)) return false;
  if (/(19|20)\d{2}[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])/.test(phone)) return false;
  if (/(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}/.test(phone)) return false;
  if (/\b(19|20)\d{2}\b/.test(phone)) return false;
  if (/\b\d{1,2}:\d{2}\b/.test(phone)) return false;
  if (/\b\d{1,2}\s*[-–]\s*\d{1,2}\b/.test(phone) && digits.length < 9) return false;
  return true;
}

function validLinkedIn(value) {
  return /^https?:\/\/(?:www\.)?linkedin\.com\/(?:company|in)\/[A-Za-z0-9_./%-]+/i.test(String(value || '').trim());
}

function usableLead(x) {
  const company = String(x.company || '').trim();
  const emailOk = validEmail(x.businessEmail);
  const phoneOk = validPhone(x.businessPhone);
  const linkedinOk = validLinkedIn(x.linkedin);
  const sourceOk = /^https?:\/\//i.test(String(x.source || '').trim());
  const verifiedOk = /^\d{4}-\d{2}-\d{2}$/.test(String(x.lastVerified || '').trim());

  if (!company || genericCompany.test(company)) return false;
  if (!sourceOk || !verifiedOk) return false;
  if (x.salesReady === false) return false;
  // Event-specific public intent signals are allowed without contact details.
  // They are clearly marked as VERIFY and are never presented as verified contacts.
  if (x.intentSignal === true) return true;
  if (!emailOk && !phoneOk) return false;
  if (!emailOk && !phoneOk && !linkedinOk) return false;
  return true;
}

function contactKey(x) {
  const email = String(x.businessEmail || '').trim().toLowerCase();
  if (validEmail(email)) return `email:${email}`;
  const phone = String(x.businessPhone || '').replace(/\D/g, '');
  if (validPhone(x.businessPhone)) return `phone:${phone}`;
  if (x.intentSignal) return `intent:${String(x.source || '').toLowerCase()}|${String(x.role || '').toLowerCase()}|${String(x.event || '').toLowerCase()}`;
  return `lead:${String(x.company || '').trim().toLowerCase()}|${String(x.event || '').trim().toLowerCase()}`;
}

function eventKey(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function decode(s='') {
  return s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'").replace(/&quot;/g, '"');
}

function xmlTag(block, name) {
  const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, 'i'));
  return m ? decode(m[1]).trim() : '';
}

function stripHtml(s='') {
  return s.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const INTENT_WORDS = [
  'travel', 'flight', 'hotel', 'accommodation', 'visa', 'tickets', 'hospitality',
  'package', 'trip', 'tour', 'attend', 'attendees', 'delegation', 'business travel',
  'conference', 'exhibition', 'grand prix', 'motogp', 'formula 1', 'event'
];

function intentScore(title, description) {
  const text = `${title} ${description}`.toLowerCase();
  return INTENT_WORDS.reduce((score, word) => score + (text.includes(word) ? 1 : 0), 0);
}

async function publicIntentSignals(event) {
  if (!event) return [];
  const queries = [`"${event}" travel`,`"${event}" hotel`,`"${event}" flight`,`"${event}" visa`,`"${event}" accommodation`,`"${event}" attendees`,`"${event}" delegates`,`"${event}" exhibitors`,`"${event}" visitors`,`"${event}" tourism`,`"${event}" Nigeria travel`,`"${event}" Nigeria hotel`,`"${event}" Nigeria flight`,`"${event}" Nigeria visa`,`"${event}" Nigeria exhibitors`,`"${event}" Nigeria delegation`,`"${event}" "travel agency" Nigeria`,`"${event}" "business travel" Nigeria`];
  const results = [];
  const seen = new Set();

  for (const query of queries) {
    try {
      const url = 'https://news.google.com/rss/search?q=' + encodeURIComponent(query) + '&hl=en-NG&gl=NG&ceid=NG:en';
      const response = await fetch(url, { headers: { 'user-agent': 'Cindrela-Sales-Radar/1.0' } });
      if (!response.ok) continue;
      const xml = await response.text();
      for (const block of xml.match(/<item>[\s\S]*?<\/item>/gi) || []) {
        const title = xmlTag(block, 'title');
        const link = xmlTag(block, 'link');
        const source = xmlTag(block, 'source') || 'Public Web';
        const pubDate = xmlTag(block, 'pubDate');
        const description = stripHtml(xmlTag(block, 'description'));
        if (!title || !link) continue;
        const key = link.split('?')[0];
        if (seen.has(key)) continue;
        seen.add(key);
        const score = intentScore(title, description);
        if (score < 2) continue;
        results.push({
          company: source,
          role: `PUBLIC INTENT • ${title.slice(0, 85)}`,
          contactPerson: '',
          businessEmail: '',
          businessPhone: '',
          linkedin: '',
          country: 'Nigeria / Public Web',
          event,
          source: link,
          lastVerified: new Date().toISOString().slice(0, 10),
          salesReady: true,
          intentSignal: true,
          intentScore: Math.min(100, score * 12),
          intentPublishedAt: pubDate,
          intentReason: 'Public web content related to this event and travel demand. Verify the business/person before outreach.'
        });
      }
    } catch (error) {
      console.error('public intent query failed:', error.message);
    }
  }

  return results.sort((a, b) => (b.intentScore || 0) - (a.intentScore || 0)).slice(0, 20);
}

module.exports = async function handler(req, res) {
  try {
    const contacts = read('public-lead-contacts.json');
    const opportunities = read('opportunities.json');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const activeEvents = new Set(
      opportunities
        .filter((x) => new Date((x.end_date || x.start_date) + 'T00:00:00') >= today)
        .map((x) => String(x.title || '').trim())
    );

    const activeOnly = String(req.query?.active ?? 'true').toLowerCase() !== 'false';
    const event = String(req.query?.event || '').trim();
    const q = String(req.query?.q || '').trim().toLowerCase();

    let data = event
      ? contacts.filter((x) => eventKey(x.event) === eventKey(event))
      : (activeOnly ? contacts.filter((x) => activeEvents.has(String(x.event || '').trim())) : contacts);

    data = data.filter(usableLead);

    // The event-specific intent scan happens only when a user clicks Find Leads
    // for a particular card. It is never run for every card during page load.
    let intent = [];
    if (event) intent = await publicIntentSignals(event);
    data = [...data, ...intent];

    const seen = new Set();
    data = data.filter((x) => {
      const key = contactKey(x);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    if (q) {
      data = data.filter((x) => [
        x.event, x.company, x.country, x.role, x.contactPerson,
        x.businessEmail, x.businessPhone, x.linkedin
      ].some((v) => String(v || '').toLowerCase().includes(q)));
    }

    const limit = Math.min(Math.max(Number(req.query?.limit) || 100, 1), 500);
    const page = Math.max(Number(req.query?.page) || 1, 1);
    const start = (page - 1) * limit;
    const paged = data.slice(start, start + limit);

    res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    return res.status(200).json({
      data: paged,
      total: data.length,
      page,
      limit,
      intentScanned: Boolean(event),
      intentCount: intent.length
    });
  } catch (error) {
    console.error('public-lead-contacts:', error);
    return res.status(500).json({ error: 'Unable to load public lead contacts' });
  }
};
