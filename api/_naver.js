// Shared Naver API access. Files starting with "_" are not exposed as routes on Vercel.
// Each API (local, blog) remembers which gateway worked; a failure in one never switches the other.
const HUB = 'https://naverapihub.apigw.ntruss.com';
const gw = { local: null, blog: null };

function configured() {
  return !!(process.env.NAVER_API_KEY_ID && process.env.NAVER_API_KEY_SECRET);
}
function hubHeaders() {
  return { 'X-NCP-APIGW-API-KEY-ID': process.env.NAVER_API_KEY_ID, 'X-NCP-APIGW-API-KEY': process.env.NAVER_API_KEY_SECRET };
}
function classicHeaders() {
  return { 'X-Naver-Client-Id': process.env.NAVER_API_KEY_ID, 'X-Naver-Client-Secret': process.env.NAVER_API_KEY_SECRET };
}
function clean(t) {
  return String(t || '')
    .replace(/<[^>]*>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .trim();
}
function km(a, b) {
  const t = (d) => (d * Math.PI) / 180;
  const x = Math.sin(t(b.lat - a.lat) / 2) ** 2 + Math.cos(t(a.lat)) * Math.cos(t(b.lat)) * Math.sin(t(b.lng - a.lng) / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(x));
}
function kstDate(offsetDays) {
  return new Date(Date.now() + 9 * 3600e3 + offsetDays * 86400e3).toISOString().slice(0, 10);
}

async function tryGateway(which, kind, qs) {
  const url = which === 'hub' ? HUB + '/search/v1/' + kind : 'https://openapi.naver.com/v1/search/' + kind + '.json';
  const r = await fetch(url + '?' + qs, { headers: which === 'hub' ? hubHeaders() : classicHeaders(), signal: AbortSignal.timeout(5000) });
  if (r.ok) return { ok: true, json: await r.json() };
  let body = '';
  try { body = (await r.text()).replace(/\s+/g, ' ').slice(0, 80); } catch (e) {}
  return { ok: false, status: r.status, body };
}

// GET a Naver search API (kind: 'local' or 'blog'). Tries the remembered gateway first, then the other one on auth/not-found errors.
async function search(kind, params) {
  const qs = new URLSearchParams(params).toString();
  const order = gw[kind] === 'classic' ? ['classic', 'hub'] : ['hub', 'classic'];
  let last = '';
  for (const which of order) {
    let res;
    try { res = await tryGateway(which, kind, qs); }
    catch (e) { last = kind + ' ' + which + ' ' + (e.name === 'TimeoutError' ? 'timeout' : 'network'); continue; }
    if (res.ok) { gw[kind] = which; return res.json; }
    last = kind + ' ' + which + ' ' + res.status + (res.body ? ' ' + res.body : '');
    if (!(res.status >= 401 && res.status <= 404)) break;
  }
  throw new Error(last);
}

async function local(query, sort) {
  const j = await search('local', { query, display: '5', start: '1', sort: sort || 'comment' });
  return (j.items || []).map((it) => {
    let lng = parseFloat(it.mapx);
    let lat = parseFloat(it.mapy);
    if (Math.abs(lng) > 1000) { lng /= 1e7; lat /= 1e7; }
    return { name: clean(it.title), category: clean(it.category), address: clean(it.roadAddress || it.address), lat, lng, link: it.link || '' };
  }).filter((p) => p.name && isFinite(p.lat) && isFinite(p.lng) && p.lat > 33 && p.lat < 39 && p.lng > 124 && p.lng < 132);
}

async function blog(query, display) {
  const j = await search('blog', { query, display: String(display || 30), start: '1', sort: 'date' });
  return j.items || [];
}

// Search trend (DataLab) exists only on API Hub.
async function trend(groups, startDate, endDate) {
  const r = await fetch(HUB + '/search-trend/v1/search', {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, hubHeaders()),
    body: JSON.stringify({ startDate, endDate, timeUnit: 'date', keywordGroups: groups }),
    signal: AbortSignal.timeout(5000),
  });
  if (!r.ok) {
    let body = '';
    try { body = (await r.text()).replace(/\s+/g, ' ').slice(0, 80); } catch (e) {}
    throw new Error('trend ' + r.status + (body ? ' ' + body : ''));
  }
  return (await r.json()).results || [];
}

module.exports = { configured, clean, km, kstDate, local, blog, trend, tryGateway, HUB, hubHeaders };
