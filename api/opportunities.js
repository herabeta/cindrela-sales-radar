const fs = require('fs');
const path = require('path');

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', file), 'utf8'));
}

module.exports = function handler(req, res) {
  try {
    const data = readJson('opportunities.json');
    const activeOnly = String(req.query?.active ?? 'false').toLowerCase() === 'true';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const opportunities = activeOnly
      ? data.filter((x) => new Date((x.end_date || x.start_date) + 'T00:00:00') >= today)
      : data;

    res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    return res.status(200).json({ data: opportunities, total: opportunities.length });
  } catch (error) {
    return res.status(500).json({ error: 'Unable to load opportunities' });
  }
};
