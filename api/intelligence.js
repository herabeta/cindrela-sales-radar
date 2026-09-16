const fs = require('fs');
const path = require('path');

module.exports = function handler(req, res) {
  try {
    const file = path.join(process.cwd(), 'data', 'daily-intelligence.json');
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    const limit = Math.min(Math.max(Number(req.query?.limit) || 50, 1), 200);
    const page = Math.max(Number(req.query?.page) || 1, 1);
    const start = (page - 1) * limit;
    const items = Array.isArray(data) ? data.slice(start, start + limit) : data;

    res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    return res.status(200).json({ data: items, total: Array.isArray(data) ? data.length : 1, page, limit });
  } catch (error) {
    return res.status(500).json({ error: 'Unable to load intelligence data' });
  }
};
