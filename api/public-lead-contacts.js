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
  if (!local || !domain || /^(example|test|domain|localhost)$/i.test(domain)) return false;
  if (!/^[A-Za-z0-9][A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]*[A-Za-z0-9]$/.test(local)) return false;
  const labels = domain.split('.');
  return labels.length >= 2 && labels.every((x) => /^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$/.test(x)) && /^[A-Za-z]{2,24}$/.test(labels.at(-1) || '');
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
  // Reject dates, event timings and coordinate-like extraction artifacts.
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
  if (!emailOk && !phoneOk) return false;
  if (!emailOk && !phoneOk && !linkedinOk) return false;
  return true;
}

function contactKey(x) {
  const email = String(x.businessEmail || '').trim().toLowerCase();
  if (validEmail(email)) return `email:${email}`;
  const phone = String(x.businessPhone || '').replace(/\D/g, '');
  if (validPhone(x.businessPhone)) return `phone:${phone}`;
  return `lead:${String(x.company || '').trim().toLowerCase()}|${String(x.event || '').trim().toLowerCase()}`;
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

    // Only expose source-backed, recently verified public business contacts.
    data = data.filter(usableLead);

    // One public email/phone = one lead card, even when the same contact
    // appears under multiple event roles such as Speakers / Sponsors.
    const seen = new Set();
    data = data.filter((x) => {
      const key = contactKey(x);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

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
