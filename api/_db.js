// Minimal Neon client over HTTPS (no npm packages). Needs the DATABASE_URL env var.
function conf() {
  const url = process.env.DATABASE_URL || '';
  const m = url.match(/^postgres(?:ql)?:\/\/[^@]+@([^/?]+)/);
  return m ? { url, host: m[1] } : null;
}
function configured() { return !!conf(); }
async function query(text, params) {
  const c = conf();
  if (!c) throw new Error('db_not_configured');
  const r = await fetch('https://' + c.host + '/sql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Neon-Connection-String': c.url },
    body: JSON.stringify({ query: text, params: params || [] }),
    signal: AbortSignal.timeout(8000),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error('db ' + r.status + ' ' + String(j.message || '').slice(0, 100));
  return j.rows || [];
}
const arr = (a) => '{' + a.map((s) => '"' + String(s).replace(/(["\\])/g, '\\$1') + '"').join(',') + '}';
module.exports = { configured, query, arr };
