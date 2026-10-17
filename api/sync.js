// /api/sync  POST {code, since, items:[{id,kind,u,body}]} -> upserts newer items, returns every item changed after `since`.
// Last write wins per item (u = client timestamp in ms). Deleted items are kept as {deleted:true} so the partner's phone learns about it.
const D = require('./_db');
const KINDS = ['visit', 'special', 'prefs', 'place', 'photo'];
const MAX_REPLY = 3000000; // Vercel caps a function response at 4.5MB; photos are ~25KB each, so page the reply

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  if (!D.configured()) return res.status(200).json({ ok: false, reason: 'db_not_configured' });
  if (req.method !== 'POST') return res.status(405).json({ ok: false, reason: 'method' });
  const b = req.body && typeof req.body === 'object' ? req.body : {};
  const code = String(b.code || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (code.length !== 8) return res.status(200).json({ ok: false, reason: 'bad_code' });
  const since = Number.isFinite(+b.since) ? Math.max(0, Math.floor(+b.since)) : 0;
  const now = Date.now();
  const items = (Array.isArray(b.items) ? b.items : []).slice(0, 100).filter((it) =>
    it && /^[A-Za-z0-9_-]{1,40}$/.test(String(it.id)) && KINDS.indexOf(it.kind) >= 0 &&
    Number.isFinite(+it.u) && +it.u > 0 && it.body && typeof it.body === 'object' &&
    JSON.stringify(it.body).length < 30000
  ).map((it) => ({ id: String(it.id), kind: it.kind, u: Math.min(Math.floor(+it.u), now + 60000), body: it.body }));
  try {
    const ok = await D.query('select 1 from couples where code=$1', [code]);
    if (!ok.length) return res.status(200).json({ ok: false, reason: 'not_found' });
    if (items.length) {
      await D.query(
        'insert into entries(couple_code,id,kind,u,body) select $1, x.id, x.kind, x.u, x.body from jsonb_to_recordset($2::jsonb) as x(id text, kind text, u bigint, body jsonb) ' +
        'on conflict (couple_code,id) do update set kind=excluded.kind, u=excluded.u, body=excluded.body where entries.u < excluded.u',
        [code, JSON.stringify(items)]
      );
    }
    const rows = await D.query('select id, kind, u, body from entries where couple_code=$1 and u>$2 order by u limit 500', [code, since]);
    let size = 0, cut = rows.length;
    for (let i = 0; i < rows.length; i++) {
      size += JSON.stringify(rows[i].body).length + 80;
      if (size > MAX_REPLY && i > 0) { cut = i; break; }
    }
    const page = rows.slice(0, cut);
    const out = { ok: true, now, items: page.map((r) => ({ id: r.id, kind: r.kind, u: Number(r.u), body: r.body })) };
    if (cut < rows.length) { out.more = true; out.last = Number(page[page.length - 1].u); }
    return res.status(200).json(out);
  } catch (e) {
    return res.status(200).json({ ok: false, reason: String((e && e.message) || e).slice(0, 120) });
  }
};
