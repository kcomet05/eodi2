// GET /api/nearby?lat=35.15&lng=129.11&name=광안리해수욕장&area=광안동  - live places around the last stop, never cached.
const N = require('./_naver');
const KINDS = [
  { kind: '카페', q: '카페' },
  { kind: '저녁', q: '맛집' },
  { kind: '산책', q: '가볼만한곳' },
  { kind: '전시', q: '전시' },
  { kind: '팝업', q: '팝업스토어' },
];

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  const q = req.query || {};
  const lat = parseFloat(q.lat);
  const lng = parseFloat(q.lng);
  const area = String(q.area || '').replace(/[^0-9A-Za-z가-힣 ]/g, '').trim().slice(0, 20);
  const name = String(q.name || '').replace(/[^0-9A-Za-z가-힣 ]/g, '').trim().slice(0, 20);
  if (!N.configured()) return res.status(200).json({ source: 'error', reason: 'not_configured' });
  if (!(lat > 33 && lat < 39 && lng > 124 && lng < 132) || !(area || name)) return res.status(200).json({ source: 'error', reason: 'bad_input' });

  const here = { lat, lng };
  try {
    const jobs = [];
    KINDS.forEach((k) => {
      if (area) jobs.push({ k, query: area + ' ' + k.q });
      if (name) jobs.push({ k, query: name + ' ' + k.q });
    });
    const settled = await Promise.allSettled(jobs.map(({ k, query }) => N.local(query, 'comment').then((l) => l.map((p) => Object.assign(p, { kind: k.kind })))));
    const ok = settled.filter((s) => s.status === 'fulfilled');
    if (!ok.length) throw settled[0].reason;
    const seen = new Set();
    const rows = [];
    ok.forEach((s) => s.value.forEach((p, i) => {
      const d = N.km(here, p);
      if (d > 2.5 || d < 0.03 || seen.has(p.name)) return;
      seen.add(p.name);
      rows.push(Object.assign(p, { rank: i, distM: Math.round(d * 1000) }));
    }));
    rows.sort((a, b) => a.rank - b.rank || a.distM - b.distM);
    return res.status(200).json({ source: 'live', items: rows.slice(0, 16) });
  } catch (e) {
    return res.status(200).json({ source: 'error', reason: String((e && e.message) || e).slice(0, 120) });
  }
};
