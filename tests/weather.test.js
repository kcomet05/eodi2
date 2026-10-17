// node tests/weather.test.js  - api/weather.js with a mocked KMA response (no network, no key needed)
const assert = require('assert');
const w = require('../api/weather.js');
const call = async (q) => { let out; const res = { setHeader() {}, status(c) { this.c = c; return this; }, json(b) { out = b; return this; } }; await w({ query: q }, res); return out; };
(async () => {
  delete process.env.KMA_SERVICE_KEY;
  assert.deepStrictEqual(await call({ lat: '37.5', lng: '127' }), { ok: false, reason: 'kma_not_configured' });
  process.env.KMA_SERVICE_KEY = 'SECRET+KEY/==';
  assert.strictEqual((await call({ lat: '10', lng: '127' })).reason, 'bad_location');
  assert.strictEqual((await call({ lat: 'x', lng: 'y' })).reason, 'bad_location');
  let seen;
  const item = (t, c, v) => ({ fcstDate: '20261017', fcstTime: t, category: c, fcstValue: v });
  global.fetch = async (u) => { seen = u; return { text: async () => JSON.stringify({ response: { header: { resultCode: '00' }, body: { items: { item: [item('1200', 'TMP', '21'), item('1200', 'SKY', '3'), item('1200', 'PTY', '0'), item('1200', 'POP', '30'), item('1300', 'TMP', '20'), item('1300', 'PTY', '1'), item('1300', 'POP', '80')] } } } }) }; };
  const r = await call({ lat: '37.5446', lng: '127.0557' });
  assert.ok(r.ok && r.grid.nx === 61 && r.grid.ny === 126, 'grid');
  assert.deepStrictEqual(r.hours[0], { d: '20261017', t: '1200', tmp: 21, sky: 3, pty: 0, pop: 30 });
  assert.strictEqual(r.hours[1].pty, 1); assert.strictEqual(r.hours.length, 2);
  assert.ok(seen.includes('serviceKey=SECRET%2BKEY%2F%3D%3D') && seen.includes('nx=61&ny=126'), 'key url-encoded once');
  assert.ok(!JSON.stringify(r).includes('SECRET'), 'key never echoed');
  process.env.KMA_SERVICE_KEY = 'ab%2Bcd'; await call({ lat: '37.5', lng: '127' });
  assert.ok(seen.includes('serviceKey=ab%2Bcd&'), 'already-encoded key kept as is');
  global.fetch = async () => ({ text: async () => '<OpenAPI_ServiceResponse><cmmMsgHeader><returnAuthMsg>SERVICE KEY IS NOT REGISTERED ERROR.</returnAuthMsg></cmmMsgHeader></OpenAPI_ServiceResponse>' });
  const x = await call({ lat: '37.5', lng: '127' }); assert.strictEqual(x.reason, 'kma_bad_response'); assert.ok(/NOT REGISTERED/.test(x.detail) && !/</.test(x.detail));
  global.fetch = async () => ({ text: async () => JSON.stringify({ response: { header: { resultCode: '03', resultMsg: 'NO_DATA' } } }) });
  assert.strictEqual((await call({ lat: '37.5', lng: '127' })).reason, 'kma_error');
  global.fetch = async () => { const e = new Error('t'); e.name = 'TimeoutError'; throw e; };
  assert.strictEqual((await call({ lat: '37.5', lng: '127' })).reason, 'timeout');
  console.log('PASS weather api: 9 checks');
})().catch((e) => { console.log('FAIL ' + e.message); process.exit(1); });
