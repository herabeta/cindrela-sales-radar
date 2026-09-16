const fs = require('fs');
const path = require('path');

module.exports = function handler(req, res) {
  try {
    const file = path.join(process.cwd(), 'data', 'daily-intelligence.json');
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));

    res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=86400');
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    return res.status(200).json(data);
  } catch (error) {
    return res.status(500).json({ error: 'Unable to load intelligence data' });
  }
};
