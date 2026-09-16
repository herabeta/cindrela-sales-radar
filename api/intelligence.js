const fs = require('fs');
const path = require('path');
const { getDb } = require('../lib/db');

function readJson() {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', 'daily-intelligence.json'), 'utf8'));
}

function cache(res) {
  res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
}

module.exports = async function handler(req, res) {
  try {
    const sql = getDb();
    if (sql) {
      const rows = await sql`
        SELECT item_date, raw_data
        FROM daily_intelligence
        WHERE item_date BETWEEN CURRENT_DATE - INTERVAL '1 day' AND CURRENT_DATE + INTERVAL '7 days'
        ORDER BY item_date DESC, id DESC
        LIMIT 500
      `;
      if (rows.length) {
        const fallback = readJson();
        const items = rows.map((r) => ({ ...(r.raw_data || {}), published: r.raw_data?.published || String(r.item_date).slice(0, 10) }));
        cache(res);
        return res.status(200).json({
          ...fallback,
          items,
          generated_at: fallback.generated_at || new Date().toISOString(),
          status: fallback.status || 'live',
          source: 'database'
        });
      }
    }

    const data = readJson();
    cache(res);
    return res.status(200).json({ ...data, source: 'json-fallback' });
  } catch (error) {
    console.error('intelligence API', error);
    return res.status(500).json({ error: 'Unable to load intelligence data' });
  }
};
