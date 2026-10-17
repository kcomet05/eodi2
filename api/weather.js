// GET /api/weather?lat=37.54&lng=127.05  - KMA 단기예보 (data.go.kr VilageFcstInfoService_2.0) hourly forecast for a point.
// Needs env KMA_SERVICE_KEY (공공데이터포털 인증키). Never echoes the key.
const BASES = [2, 5, 8, 11, 14, 17, 20, 23];

// KMA Lambert conformal conic grid (nx, ny) from WGS84.
function toGrid(lat, lng) {
  const RE = 6371.00877, GRID = 5.0, SLAT1 = 30.0, SLAT2 = 60.0, OLON = 126.0, OLAT = 38.0, XO = 43, YO = 136;
  const D = Math.PI / 180;
  const re = RE / GRID, slat1 = SLAT1 * D, slat2 = SLAT2 * D, olon = OLON * D, olat = OLAT * D;
  let sn = Math.tan(Math.PI * 0.25 + slat2 * 0.5) / Math.tan(Math.PI * 0.25 + slat1 * 0.5);
  sn = Math.log(Math.cos(slat1) / Math.cos(slat2)) / Math.log(sn);
  let sf = Math.tan(Math.PI * 0.25 + slat1 * 0.5);
  sf = (Math.pow(sf, sn) * Math.cos(slat1)) / sn;
  let ro = Math.tan(Math.PI * 0.25 + olat * 0.5);
  ro = (re * sf) / Math.pow(ro, sn);
  let ra = Math.tan(Math.PI * 0.25 + lat * D * 0.5);
  ra = (re * sf) / Math.pow(ra, sn);
  let theta = lng * D - olon;
  if (theta > Math.PI) theta -= 2 * Math.PI;
  if (theta < -Math.PI) theta += 2 * Math.PI;
  theta *= sn;
  return { nx: Math.floor(ra * Math.sin(theta) + XO + 0.5), ny: Math.floor(ro - ra * Math.cos(theta) + YO + 0.5) };
}

const pad = (n) => String(n).padStart(2, '0');
const ymd = (d) => d.getUTCFullYear() + pad(d.getUTCMonth() + 1) + pad(d.getUTCDate());

// Latest base_time already published (about 10 minutes after each base hour), in KST.
function baseTime(nowMs) {
  const k = new Date(nowMs + 9 * 3600e3 - 10 * 60e3);
  const h = k.getUTCHours();
  let b = -1;
  BASES.forEach((x) => { if (x <= h) b = x; });
  if (b < 0) {
    const y = new Date(k.getTime() - 24 * 3600e3);
    return { date: ymd(y), time: '2300' };
  }
  return { date: ymd(k), time: pad(b) + '00' };
}

function summarize(items) {
  const by = {};
  items.forEach((it) => {
    const k = it.fcstDate + it.fcstTime;
    (by[k] = by[k] || { d: it.fcstDate, t: it.fcstTime })[it.category] = it.fcstValue;
  });
  return Object.keys(by).sort().map((k) => {
    const o = by[k];
    return { d: o.d, t: o.t, tmp: o.TMP != null ? +o.TMP : null, sky: o.SKY != null ? +o.SKY : null, pty: o.PTY != null ? +o.PTY : 0, pop: o.POP != null ? +o.POP : null };
  });
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  const key = process.env.KMA_SERVICE_KEY;
  if (!key) {
    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json({ ok: false, reason: 'kma_not_configured' });
  }
  const lat = parseFloat(req.query && req.query.lat), lng = parseFloat(req.query && req.query.lng);
  if (!(lat >= 33 && lat <= 39) || !(lng >= 124 && lng <= 132)) {
    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json({ ok: false, reason: 'bad_location' });
  }
  const g = toGrid(lat, lng), b = baseTime(Date.now());
  const sk = key.indexOf('%') >= 0 ? key : encodeURIComponent(key);
  const url = 'https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey=' + sk +
    '&pageNo=1&numOfRows=1000&dataType=JSON&base_date=' + b.date + '&base_time=' + b.time + '&nx=' + g.nx + '&ny=' + g.ny;
  try {
    const r = await fetch(url, { signal: AbortSignal.timeout(9000) });
    const text = await r.text();
    let j;
    try { j = JSON.parse(text); } catch (e) {
      res.setHeader('Cache-Control', 'no-store');
      return res.status(200).json({ ok: false, reason: 'kma_bad_response', detail: text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 80) });
    }
    const h = j && j.response && j.response.header;
    if (!h || h.resultCode !== '00') {
      res.setHeader('Cache-Control', 'no-store');
      return res.status(200).json({ ok: false, reason: 'kma_error', detail: String((h && h.resultMsg) || 'unknown').slice(0, 80) });
    }
    const items = (j.response.body && j.response.body.items && j.response.body.items.item) || [];
    res.setHeader('Cache-Control', 's-maxage=600, stale-while-revalidate=1200');
    return res.status(200).json({ ok: true, grid: g, base: b, hours: summarize(items) });
  } catch (e) {
    res.setHeader('Cache-Control', 'no-store');
    return res.status(200).json({ ok: false, reason: e.name === 'TimeoutError' ? 'timeout' : 'network' });
  }
};
module.exports.toGrid = toGrid;
module.exports.baseTime = baseTime;
module.exports.summarize = summarize;
