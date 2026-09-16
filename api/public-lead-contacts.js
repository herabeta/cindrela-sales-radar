const fs = require('fs');
const path = require('path');

function read(name) {
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), 'data', name), 'utf8'));
}

module.exports = function handler(req, res) {
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

    let data = activeOnly
      ? contacts.filter((x) => activeEvents.has(String(x.event || '').trim()))
      : contacts;

    // Event filtering happens on the server so the browser never has to
    // download the complete lead database just to show one event.
    if (event) {
      const eventKey = event.toLowerCase();
      data = data.filter((x) => String(x.event || '').trim().toLowerCase() === eventKey);
    }

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
    return res.status(200).json({ data: paged, total: data.length, page, limit });
  } catch (error) {
    console.error('public-lead-contacts:', error);
    return res.status(500).json({ error: 'Unable to load public lead contacts' });
  }
};
