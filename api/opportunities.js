const fs = require('fs');
const path = require('path');
const { getDb } = require('../lib/db');

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', file), 'utf8'));
}

function isActive(x) {
  const end = x?.end_date || x?.start_date;
  if (!end) return true;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return new Date(end + 'T00:00:00') >= today;
}

function cache(res) {
  res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
}

module.exports = async function handler(req, res) {
  try {
    const activeOnly = String(req.query?.active ?? 'false').toLowerCase() === 'true';
    const sql = getDb();

    if (sql) {
      const rows = await sql`
        SELECT id, event_key, title, start_date, end_date, country, city, venue, category, source_url, raw_data
        FROM events
        ${activeOnly ? sql`WHERE COALESCE(end_date, start_date) >= CURRENT_DATE` : sql``}
        ORDER BY start_date ASC NULLS LAST, title ASC
      `;
      if (rows.length) {
        const data = rows.map((r) => ({
          ...(r.raw_data || {}),
          id: r.raw_data?.id ?? r.event_key ?? r.id,
          title: r.title,
          start_date: r.start_date ? String(r.start_date).slice(0, 10) : r.raw_data?.start_date,
          end_date: r.end_date ? String(r.end_date).slice(0, 10) : r.raw_data?.end_date,
          country: r.country ?? r.raw_data?.country,
          city: r.city ?? r.raw_data?.city,
          venue: r.venue ?? r.raw_data?.venue,
          group: r.category ?? r.raw_data?.group,
          url: r.source_url ?? r.raw_data?.url
        }));
        cache(res);
        return res.status(200).json({ data, total: data.length, source: 'database' });
      }
    }

    const data = readJson('opportunities.json');
    const opportunities = activeOnly ? data.filter(isActive) : data;
    cache(res);
    return res.status(200).json({ data: opportunities, total: opportunities.length, source: 'json-fallback' });
  } catch (error) {
    console.error('opportunities API', error);
    return res.status(500).json({ error: 'Unable to load opportunities' });
  }
};
