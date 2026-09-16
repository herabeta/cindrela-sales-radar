const fs = require('fs');
const path = require('path');
const { neon } = require('@neondatabase/serverless');

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', file), 'utf8'));
}

function key(prefix, value, index) {
  const text = typeof value === 'string' ? value : JSON.stringify(value);
  return `${prefix}_${Buffer.from(`${text || ''}_${index}`).toString('base64url')}`.slice(0, 240);
}

function dateOrNull(value) {
  if (!value) return null;
  const d = new Date(`${String(value).slice(0, 10)}T00:00:00Z`);
  return Number.isNaN(d.getTime()) ? null : String(value).slice(0, 10);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'POST required' });
  if (!process.env.DATABASE_URL) return res.status(503).json({ ok: false, error: 'DATABASE_URL not configured' });
  if (!process.env.MIGRATION_SECRET || req.headers['x-migration-secret'] !== process.env.MIGRATION_SECRET) {
    return res.status(401).json({ ok: false, error: 'Unauthorized' });
  }

  try {
    const sql = neon(process.env.DATABASE_URL);
    const schema = fs.readFileSync(path.join(process.cwd(), 'db', 'schema.sql'), 'utf8');
    for (const statement of schema.split(';').map((x) => x.trim()).filter(Boolean)) await sql.query(statement);

    const opportunities = readJson('opportunities.json');
    const contacts = readJson('public-lead-contacts.json');
    const intelligence = readJson('daily-intelligence.json');
    const enrichment = readJson('lead-enrichment.json');
    const candidates = readJson('event-candidates.json');

    for (let i = 0; i < opportunities.length; i++) {
      const x = opportunities[i] || {};
      await sql`insert into events (event_key,title,start_date,end_date,country,city,venue,category,source_url,raw_data)
        values (${key('event', x.title || x.name || x.event, i)},${String(x.title || x.name || x.event || 'Untitled event')},${dateOrNull(x.start_date)},${dateOrNull(x.end_date)},${x.country || null},${x.city || null},${x.venue || null},${x.category || x.type || null},${x.source_url || x.url || null},${x})
        on conflict (event_key) do update set title=excluded.title,start_date=excluded.start_date,end_date=excluded.end_date,country=excluded.country,city=excluded.city,venue=excluded.venue,category=excluded.category,source_url=excluded.source_url,raw_data=excluded.raw_data,updated_at=now()`;
    }

    for (let i = 0; i < contacts.length; i++) {
      const x = contacts[i] || {};
      await sql`insert into public_lead_contacts (lead_key,event,company,country,role,contact_person,business_email,business_phone,linkedin,raw_data)
        values (${key('lead', `${x.event}|${x.company}|${x.contactPerson}|${x.businessEmail}|${x.businessPhone}`, i)},${x.event || null},${x.company || null},${x.country || null},${x.role || null},${x.contactPerson || null},${x.businessEmail || null},${x.businessPhone || null},${x.linkedin || null},${x})
        on conflict (lead_key) do update set event=excluded.event,company=excluded.company,country=excluded.country,role=excluded.role,contact_person=excluded.contact_person,business_email=excluded.business_email,business_phone=excluded.business_phone,linkedin=excluded.linkedin,raw_data=excluded.raw_data,updated_at=now()`;
    }

    for (let i = 0; i < intelligence.length; i++) {
      const x = intelligence[i] || {};
      await sql`insert into daily_intelligence (item_key,item_date,title,category,raw_data)
        values (${key('intel', `${x.date || x.item_date}|${x.title || x.headline || x.id}`, i)},${dateOrNull(x.date || x.item_date)},${x.title || x.headline || null},${x.category || x.type || null},${x})
        on conflict (item_key) do update set item_date=excluded.item_date,title=excluded.title,category=excluded.category,raw_data=excluded.raw_data,updated_at=now()`;
    }

    for (let i = 0; i < enrichment.length; i++) {
      const x = enrichment[i] || {};
      await sql`insert into lead_enrichment (lead_key,raw_data) values (${key('enrich', x.lead_key || x.id || x.company || x.email, i)},${x})
        on conflict (lead_key) do update set raw_data=excluded.raw_data,updated_at=now()`;
    }

    for (let i = 0; i < candidates.length; i++) {
      const x = candidates[i] || {};
      await sql`insert into event_candidates (candidate_key,event,raw_data) values (${key('candidate', `${x.event}|${x.company}|${x.name}|${x.id}`, i)},${x.event || x.event_name || null},${x})
        on conflict (candidate_key) do update set event=excluded.event,raw_data=excluded.raw_data,updated_at=now()`;
    }

    const counts = await sql`select (select count(*) from events) events,(select count(*) from public_lead_contacts) leads,(select count(*) from daily_intelligence) intelligence,(select count(*) from lead_enrichment) enrichment,(select count(*) from event_candidates) candidates`;
    return res.status(200).json({ ok: true, migrated: counts[0] });
  } catch (error) {
    console.error('Neon migration failed:', error);
    return res.status(500).json({ ok: false, error: 'Migration failed' });
  }
};
