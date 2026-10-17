// GET /api/search?q=부산 광안리 카페  - live Naver place search, never cached.
const N = require('./_naver');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  const q = String((req.query && req.query.q) || '').trim().slice(0, 40);
  if (!N.configured()) return res.status(200).json({ source: 'error', reason: 'not_configured' });
  if (!q) return res.status(200).json({ source: 'live', items: [] });
  try {
    const [a, b] = await Promise.allSettled([N.local(q, 'random'), N.local(q, 'comment')]);
    if (a.status === 'rejected' && b.status === 'rejected') throw a.reason;
    const seen = new Set();
    const items = [].concat(a.value || [], b.value || []).filter((p) => {
      const k = p.name + '|' + p.address;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
    return res.status(200).json({ source: 'live', items });
  } catch (e) {
    return res.status(200).json({ source: 'error', reason: String((e && e.message) || e).slice(0, 120) });
  }
};
