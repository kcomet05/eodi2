// /api/couple  POST create | GET ?code= read | PUT ?code= update. Invite code = the only key (no login).
const D = require('./_db');
const ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const newCode = () => { let s = ''; const b = require('crypto').randomBytes(8); for (let i = 0; i < 8; i++) s += ALPHA[b[i] % 32]; return s; };
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);

function clean(body) {
  const b = body && typeof body === 'object' ? body : {};
  const names = Array.isArray(b.names) ? b.names.map((n) => String(n || '').replace(/\s+/g, ' ').trim()) : [];
  if (names.length !== 2 || names.some((n) => !n || [...n].length > 10)) return { error: 'bad_names' };
  let since = null;
  if (b.since) {
    since = String(b.since);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(since) || isNaN(Date.parse(since)) || since > kst() || since < '1950-01-01') return { error: 'bad_since' };
  }
  return { names, since };
}
const out = (r) => ({ code: r.code, names: r.names, since: r.since ? String(r.since).slice(0, 10) : null, updatedAt: r.updated_at });
const COLS = "code, names, to_char(since,'YYYY-MM-DD') as since, updated_at";
const SEL = 'select ' + COLS + ' from couples ';

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  if (!D.configured()) return res.status(200).json({ ok: false, reason: 'db_not_configured' });
  const code = String((req.query && req.query.code) || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8);
  try {
    if (req.method === 'POST') {
      const c = clean(req.body);
      if (c.error) return res.status(200).json({ ok: false, reason: c.error });
      for (let i = 0; i < 4; i++) {
        const k = newCode();
        const r = await D.query('insert into couples(code,names,since) values($1,$2::text[],$3::date) on conflict do nothing returning ' + COLS, [k, D.arr(c.names), c.since]);
        if (r.length) return res.status(200).json({ ok: true, couple: out(r[0]) });
      }
      return res.status(200).json({ ok: false, reason: 'code_busy' });
    }
    if (code.length !== 8) return res.status(200).json({ ok: false, reason: 'bad_code' });
    if (req.method === 'GET') {
      const r = await D.query(SEL + 'where code=$1', [code]);
      return res.status(200).json(r.length ? { ok: true, couple: out(r[0]) } : { ok: false, reason: 'not_found' });
    }
    if (req.method === 'PUT') {
      const c = clean(req.body);
      if (c.error) return res.status(200).json({ ok: false, reason: c.error });
      const r = await D.query("update couples set names=$2::text[], since=$3::date, updated_at=now() where code=$1 returning " + COLS, [code, D.arr(c.names), c.since]);
      return res.status(200).json(r.length ? { ok: true, couple: out(r[0]) } : { ok: false, reason: 'not_found' });
    }
    return res.status(405).json({ ok: false, reason: 'method' });
  } catch (e) {
    return res.status(200).json({ ok: false, reason: String((e && e.message) || e).slice(0, 120) });
  }
};
