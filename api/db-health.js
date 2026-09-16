const { getDb } = require('../lib/db');

module.exports = async function handler(req, res) {
  try {
    const sql = getDb();
    if (!sql) {
      return res.status(503).json({ ok: false, database: 'not_configured' });
    }

    const result = await sql`select now() as now`;
    return res.status(200).json({ ok: true, database: 'neon', now: result[0]?.now || null });
  } catch (error) {
    console.error('Neon health check failed:', error);
    return res.status(500).json({ ok: false, database: 'neon', error: 'connection_failed' });
  }
};
