// node tests/sync.test.js  - /api/sync reply paging and kind whitelist with a stubbed database
const assert = require('assert'), path = require('path');
const dbPath = require.resolve('../api/_db.js');
let rows = [], inserted = null;
require.cache[dbPath] = { id: dbPath, filename: dbPath, loaded: true, exports: {
  configured: () => true,
  query: async (sql, args) => { if (/select 1 from couples/.test(sql)) return [{ '?column?': 1 }]; if (/insert into entries/.test(sql)) { inserted = JSON.parse(args[1]); return []; } return rows; } } };
const h = require('../api/sync.js');
const call = async (body) => { let out; await h({ method: 'POST', body }, { setHeader() {}, status() { return this; }, json(b) { out = b; return this; } }); return out; };
(async () => {
  const big = (n) => ({ id: 'ph' + n, kind: 'photo', u: 100 + n, body: { t: 'x'.repeat(1200000) } });
  rows = [big(1), big(2), big(3)];
  let r = await call({ code: 'ABCD2345', since: 0, items: [] });
  assert.ok(r.ok && r.more === true && r.items.length === 2 && r.last === 102, 'pages at ~3MB: ' + r.items.length);
  rows = [big(1)]; rows[0].body.t = 'x'.repeat(4000000);
  r = await call({ code: 'ABCD2345', since: 0, items: [] });
  assert.ok(r.items.length === 1 && !r.more, 'a single oversized row still returned');
  rows = [{ id: 'a', kind: 'visit', u: 5, body: { x: 1 } }, { id: 'b', kind: 'place', u: 6, body: { x: 1 } }];
  r = await call({ code: 'ABCD2345', since: 0, items: [] });
  assert.ok(!r.more && r.last === undefined && r.items.length === 2, 'small reply not paged');
  await call({ code: 'ABCD2345', since: 0, items: [
    { id: 'p1', kind: 'place', u: 1, body: { mark: 'fav' } }, { id: 'p2', kind: 'photo', u: 2, body: { t: 'd' } },
    { id: 'p3', kind: 'evil', u: 3, body: { a: 1 } }, { id: 'p4', kind: 'photo', u: 4, body: { t: 'x'.repeat(31000) } }] });
  assert.deepStrictEqual(inserted.map((i) => i.id), ['p1', 'p2'], 'place+photo accepted; unknown kind and >30KB body dropped');
  console.log('PASS sync api: 4 checks');
})().catch((e) => { console.log('FAIL ' + e.message); process.exit(1); });
