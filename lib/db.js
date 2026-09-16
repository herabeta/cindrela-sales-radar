const { neon } = require('@neondatabase/serverless');

let sql;

function getDb() {
  if (!process.env.DATABASE_URL) return null;
  if (!sql) sql = neon(process.env.DATABASE_URL);
  return sql;
}

module.exports = { getDb };
