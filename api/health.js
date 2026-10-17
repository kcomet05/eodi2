// GET /api/health  - checks each Naver API with the configured key and reports status codes (never the keys).
const N = require('./_naver');

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  const env = { keyId: !!process.env.NAVER_API_KEY_ID, keySecret: !!process.env.NAVER_API_KEY_SECRET };
  if (!N.configured()) return res.status(200).json({ env, checks: [] });
  const qs = new URLSearchParams({ query: '부산 광안리 카페', display: '1', start: '1' }).toString();
  const probe = async (label, fn) => {
    try {
      const r = await fn();
      return { api: label, ok: r.ok, status: r.ok ? 200 : r.status, detail: r.ok ? '' : r.body || '' };
    } catch (e) {
      return { api: label, ok: false, status: 0, detail: e.name === 'TimeoutError' ? 'timeout' : String(e.message || e).slice(0, 80) };
    }
  };
  const checks = await Promise.all([
    probe('장소 검색 (API Hub)', () => N.tryGateway('hub', 'local', qs)),
    probe('장소 검색 (네이버 개발자센터)', () => N.tryGateway('classic', 'local', qs)),
    probe('블로그 검색 (API Hub)', () => N.tryGateway('hub', 'blog', qs)),
    probe('블로그 검색 (네이버 개발자센터)', () => N.tryGateway('classic', 'blog', qs)),
    probe('검색어 트렌드 (API Hub)', async () => {
      try {
        await N.trend([{ groupName: 'a', keywords: ['성수 데이트'] }], N.kstDate(-8), N.kstDate(-1));
        return { ok: true };
      } catch (e) {
        const m = String(e.message).match(/trend (\d+) ?(.*)/);
        return { ok: false, status: m ? +m[1] : 0, body: m ? m[2] : String(e.message) };
      }
    }),
  ]);
  return res.status(200).json({ env, checks, at: new Date().toISOString() });
};
