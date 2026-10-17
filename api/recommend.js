// GET /api/recommend?mood=all|indoor|night|budget|food|walk&pick=0..9&start=840&end=1260  (minutes from midnight)
// Picks a trending area (weighted random, so it varies), then builds a time-fitted course from live Naver data:
// the stops follow the time of day (lunch, cafe, activity, dinner, night) and each gets an arrival time.
const N = require('./_naver');

var STAY={'카페':60,'점심':70,'저녁':90,'산책':60,'전시':80,'야경':50,'쇼핑':60,'술':70,'팝업':40};
var ACT={all:['산책','전시','쇼핑'],indoor:['전시','쇼핑','전시'],night:['산책','쇼핑','야경'],budget:['산책','쇼핑','전시'],food:['쇼핑','산책'],walk:['산책','산책','전시']};
var TIPS={
'카페':['창가 자리는 금방 차요. 도착하면 자리부터 잡아요','시그니처 메뉴를 하나씩 시켜서 나눠 먹어 보세요','사진 찍기 좋은 자리를 먼저 찾아봐요','오늘의 디저트가 있는지 물어보세요'],
'점심':['점심시간엔 대기가 생겨요. 조금 일찍 가면 여유로워요','메인 하나, 사이드 하나로 가볍게 나눠 먹어요','웨이팅이 있으면 캐치테이블·네이버 예약을 확인해 보세요'],
'저녁':['저녁 시간엔 붐벼요. 미리 예약하면 편해요','오늘의 메인 메뉴를 정하고 들어가면 고민이 줄어요','식후에 걸을 수 있는 코스가 이어지면 좋아요'],
'산책':['걷기 편한 신발이 좋아요','손잡고 천천히 걸으며 이야기 나눠요','벤치에서 잠깐 쉬어 가요'],
'전시':['관람 시간을 미리 확인해 두면 헛걸음이 없어요','마음에 드는 작품 하나씩 골라서 이야기해 봐요','마감 1시간 전에는 입장이 끝나는 곳이 많아요'],
'야경':['해 지는 시간에 맞춰 가면 노을까지 볼 수 있어요','바람이 쌀쌀하니 겉옷을 챙겨요','인증샷은 조명이 켜진 뒤가 예뻐요'],
'쇼핑':['서로에게 어울리는 소품을 골라 보세요','구경하다 보면 시간이 훅 가요. 한 곳만 정해서 가요','작은 기념품 하나 사서 오늘을 남겨요'],
'팝업':['인기 팝업은 대기가 길어요. 네이버·캐치테이블 사전예약을 확인해 보세요','굿즈는 일찍 품절돼요. 오픈 시간에 맞춰 가면 좋아요','운영 기간이 짧아요. 종료일을 꼭 확인하세요'],
'술':['마무리로 가볍게 한 잔 하기 좋아요','귀가 시간을 고려해 마지막 열차를 확인해요','안주는 나눠 먹을 수 있는 걸로 시켜요']
};
function tipFor(k,i){var a=TIPS[k]||[];return a.length?a[Math.abs(i)%a.length]:'';}
function planSlots(s,e,mood,likes){
var slots=[],t=s,lunch=false,dinner=false,last='',ai=0,cafes=0,acts=ACT[mood]||ACT.all;
var want=[];(likes||[]).forEach(function(k){var m=k==='팝업'?'쇼핑':k;if(['산책','전시','쇼핑','야경'].indexOf(m)>=0&&want.indexOf(m)<0)want.push(m);});
if(want.length){var pool=acts.filter(function(a){return want.indexOf(a)>=0;});if(mood==='all')acts=want.length>1?want:want.concat(acts.filter(function(a){return a!==want[0];}));else if(pool.length>1)acts=pool;}
var maxCafe=(likes&&likes.length&&likes.indexOf('카페')<0)?1:2;
while(slots.length<7){
var k;
if(!lunch&&t>=660&&t<840)k='점심';
else if(!dinner&&t>=1020&&t<1230)k='저녁';
else if(t>=1230)k=last==='술'?'야경':'술';
else if((last===''||last==='점심'||last==='저녁')&&cafes<maxCafe){k='카페';cafes++;}
else{k=acts[ai++%acts.length];if(k===last)k=acts[ai++%acts.length];}
var st=STAY[k]||60;
if(slots.length>=2&&t+st>e+20)break;
slots.push({kind:k,stay:st});
if(k==='점심')lunch=true;
if(k==='저녁')dinner=true;
last=k;t+=st+15;
if(t>=e&&slots.length>=2)break;
}
return slots;
}

const AREAS = [
  { name: '성수동', q: '성수', lat: 37.5446, lng: 127.0560 },
  { name: '연남동', q: '연남', lat: 37.5622, lng: 126.9246 },
  { name: '한남동', q: '한남동', lat: 37.5340, lng: 127.0026 },
  { name: '익선동', q: '익선동', lat: 37.5744, lng: 126.9900 },
  { name: '망원동', q: '망원동', lat: 37.5560, lng: 126.9017 },
  { name: '서촌', q: '서촌', lat: 37.5805, lng: 126.9712 },
  { name: '을지로', q: '을지로', lat: 37.5661, lng: 126.9912 },
  { name: '송리단길', q: '송리단길', lat: 37.5100, lng: 127.1070 },
  { name: '북촌', q: '북촌', lat: 37.5826, lng: 126.9835 },
  { name: '홍대', q: '홍대', lat: 37.5563, lng: 126.9236 },
  { name: '합정', q: '합정', lat: 37.5495, lng: 126.9139 },
  { name: '이태원', q: '이태원', lat: 37.5345, lng: 126.9946 },
  { name: '여의도', q: '여의도', lat: 37.5219, lng: 126.9245 },
  { name: '압구정로데오', q: '압구정로데오', lat: 37.5274, lng: 127.0390 },
  { name: '가로수길', q: '가로수길', lat: 37.5203, lng: 127.0230 },
  { name: '용리단길', q: '용리단길', lat: 37.5310, lng: 126.9700 },
  { name: '삼청동', q: '삼청동', lat: 37.5850, lng: 126.9820 },
  { name: '문래동', q: '문래동', lat: 37.5180, lng: 126.8950 },
  { name: '대학로', q: '대학로', lat: 37.5820, lng: 127.0020 },
  { name: '상수동', q: '상수동', lat: 37.5480, lng: 126.9230 },
  { name: '건대', q: '건대', lat: 37.5400, lng: 127.0700 },
  { name: '청담동', q: '청담동', lat: 37.5240, lng: 127.0470 },
  { name: '신촌', q: '신촌', lat: 37.5559, lng: 126.9368 },
  { name: '성북동', q: '성북동', lat: 37.5930, lng: 126.9930 },
];

// Well-known date districts outside Seoul. Typing just the city name picks one of these, weighted by search trend.
const CITY = {
  '부산': ['광안리', '서면', '해운대', '전포카페거리', '영도', '기장'],
  '대구': ['동성로', '김광석길', '수성못', '앞산카페거리'],
  '대전': ['은행동', '둔산동', '소제동'],
  '광주': ['동명동', '양림동', '상무지구'],
  '인천': ['송도', '개항로', '월미도'],
  '울산': ['삼산동', '성남동'],
  '세종': ['나성동', '세종호수공원'],
  '수원': ['행궁동', '광교'],
  '성남': ['판교', '서현동'],
  '고양': ['일산 라페스타', '스타필드 고양'],
  '용인': ['보정동 카페거리', '기흥'],
  '전주': ['객리단길', '한옥마을'],
  '강릉': ['안목해변', '교동'],
  '속초': ['동명항', '속초 중앙시장'],
  '춘천': ['육림고개', '소양강'],
  '경주': ['황리단길', '보문단지'],
  '여수': ['여수 낭만포차', '돌산'],
  '포항': ['영일대', '구룡포'],
  '창원': ['용호동 가로수길', '창동'],
  '청주': ['성안길', '운리단길'],
  '천안': ['신부동', '불당동'],
  '제주': ['애월', '함덕', '제주시청', '협재', '성산', '서귀포 올레시장'],
  '서귀포': ['서귀포 올레시장', '중문', '성산'],
};
const CITY_SUFFIX = /(특별시|광역시|특별자치시|특별자치도|시|도)$/;

const TERMS = {
  '카페': ['카페', '디저트 카페', '베이커리 카페', '오션뷰 카페', '로스터리 카페', '신상 카페'],
  '점심': ['점심 맛집', '브런치', '파스타', '국수 맛집', '한식 맛집', '신상 맛집'],
  '저녁': ['저녁 맛집', '레스토랑', '고기 맛집', '일식', '이자카야', '신상 맛집'],
  '술': ['와인바', '칵테일바', '이자카야', '브루어리', '루프탑 바'],
  '산책': ['산책로', '공원', '가볼만한곳', '골목 산책', '포토스팟'],
  '전시': ['전시', '미술관', '갤러리', '박물관', '팝업 전시'],
  '야경': ['야경 명소', '전망대', '야경'],
  '쇼핑': ['소품샵', '편집숍', '서점', '팝업스토어', '쇼핑'],
};
const MOOD_TITLE = { all: '데이트 코스', indoor: '실내 데이트', night: '야경 데이트', budget: '가성비 데이트', food: '맛집 데이트', walk: '산책 데이트' };

const sum = (a) => a.reduce((x, y) => x + y, 0);
const fmt = (m) => String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');

// Small seeded random generator, so each page load gives a different (but reproducible) course.
function rng(seed) {
  let a = (seed >>> 0) || 1;
  return () => {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function weightedPick(items, weight, rand) {
  const w = items.map(weight);
  let r = rand() * sum(w);
  for (let i = 0; i < items.length; i++) { r -= w[i]; if (r <= 0) return items[i]; }
  return items[items.length - 1];
}

// Ranks areas by the last week's search volume, boosted by growth versus the 3 weeks before (Naver DataLab).
async function rankAreas(list) {
  const startDate = N.kstDate(-30);
  const endDate = N.kstDate(-1);
  const anchor = list[0];
  const rest = list.slice(1);
  const chunks = [];
  for (let i = 0; i < rest.length; i += 4) chunks.push(rest.slice(i, i + 4));
  if (!chunks.length) chunks.push([]);
  const groups = (c) => [anchor].concat(c).map((a) => ({ groupName: a.name, keywords: [a.q + ' 데이트', a.q + ' 핫플'] }));
  const responses = await Promise.all(chunks.map((c) => N.trend(groups(c), startDate, endDate)));
  const series = {};
  let refSum = null;
  responses.forEach((results) => {
    const a = results.find((x) => x.title === anchor.name);
    const aSum = a ? sum(a.data.map((d) => d.ratio)) : 0;
    if (!aSum) return;
    if (refSum === null) refSum = aSum;
    const f = refSum / aSum;
    results.forEach((x) => { series[x.title] = x.data.map((d) => d.ratio * f); });
  });
  const scored = list.filter((a) => series[a.name] && series[a.name].length >= 14).map((a) => {
    const s = series[a.name];
    const recentDays = s.slice(-7);
    const earlier = s.slice(0, -7);
    const recent = sum(recentDays) / recentDays.length;
    const before = sum(earlier) / Math.max(earlier.length, 1);
    const growth = (recent - before) / Math.max(before, 0.5);
    const g = Math.max(-0.3, Math.min(0.7, growth));
    return { area: a, growth, score: recent * (1 + g) };
  }).sort((x, y) => y.score - x.score);
  if (!scored.length) throw new Error('no trend data');
  const top = scored[0].score || 1;
  scored.forEach((s) => {
    s.heat = Math.max(1, Math.round((s.score / top) * 100));
    s.trend = s.growth > 0.15 ? 'rising' : 'steady';
  });
  return scored;
}

// Hot areas are drawn at random, weighted by trend, so the top area doesn't win every time; areas shown recently are skipped.
function chooseArea(ranking, list, avoid, rand, size) {
  const pool = ranking ? ranking.slice(0, size) : list.map((a) => ({ area: a, heat: null, trend: 'steady' }));
  const fresh = pool.filter((r) => avoid.indexOf(r.area.name) < 0);
  const use = fresh.length >= 2 ? fresh : pool;
  return weightedPick(use, (r) => (r.heat == null ? 50 : r.heat) + 30 + (r.trend === 'rising' ? 25 : 0), rand);
}

// How much people blogged about a place in the last 30 days: the popularity signal used to rank places.
async function blogBuzz(name, areaQ) {
  const items = await N.blog(areaQ + ' ' + name, 30);
  const cutoff = N.kstDate(-30).replace(/-/g, '');
  return { recent: items.filter((it) => String(it.postdate || '') >= cutoff).length, latest: items[0] ? String(items[0].postdate || '') : '' };
}

// Turns typed text into coordinates with place search. API errors are reported as they are, not as "not found".
async function geocode(text) {
  let l = await N.local(text, 'random');
  if (!l.length) l = await N.local(text + ' 가볼만한곳', 'random');
  if (!l.length) throw new Error('place_not_found');
  return { lat: l[0].lat, lng: l[0].lng };
}

// A bare city name picks a trending district of that city; anything else is searched as typed.
async function resolvePlace(text, rand, avoid) {
  const bare = text.replace(/\s+/g, '');
  const key = CITY[bare] ? bare : (CITY[bare.replace(CITY_SUFFIX, '')] ? bare.replace(CITY_SUFFIX, '') : null);
  if (key) {
    const list = CITY[key].map((d) => ({ name: d, q: (d.indexOf(key) === 0 ? d : key + ' ' + d) }));
    let ranking = null;
    try { ranking = await rankAreas(list); } catch (e) { ranking = null; }
    const pickd = chooseArea(ranking, list, avoid.map((a) => a.replace(key + ' ', '')), rand, list.length);
    const c = await geocode(pickd.area.q);
    const chosen = Object.assign({}, pickd, { area: Object.assign({}, pickd.area, c, { name: key + ' ' + pickd.area.name }) });
    return { chosen, ranking, city: key };
  }
  const c = await geocode(text);
  return { chosen: { area: { name: text, q: text, lat: c.lat, lng: c.lng }, heat: null, trend: 'steady' }, ranking: null, city: null };
}

async function buildCourse(area, mood, start, end, rand, baseR, likes, cheap) {
  const slots = planSlots(start, end, mood, likes);
  const off = Math.floor(rand() * 60);
  // Two different searches per slot (sorted by review count) give enough candidates even in spread-out places like Jeju.
  const settled = await Promise.allSettled(slots.map((sl, i) => {
    const terms = TERMS[sl.kind];
    const pre = cheap && (sl.kind === '점심' || sl.kind === '저녁') ? '가성비 ' : '';
    return Promise.allSettled([0, 1].map((k) => N.local(area.q + ' ' + pre + terms[(off + i + k * 3) % terms.length], 'comment')))
      .then((rs) => {
        if (rs.every((r) => r.status === 'rejected')) throw rs[0].reason;
        const seen = new Set();
        const out = [];
        for (let r = 0; r < 5; r++) rs.forEach((x) => { const p = x.status === 'fulfilled' && x.value[r]; if (p && !seen.has(p.name)) { seen.add(p.name); out.push(p); } });
        return out;
      });
  }));
  if (settled.every((s) => s.status === 'rejected')) throw settled[0].reason;
  const lists = settled.map((s) => (s.status === 'fulfilled' ? s.value : []));
  // Keep stops close to the area, widening the circle only when a slot has nothing nearby.
  const radii = [baseR, baseR * 2, baseR * 4];
  const cands = lists.map((list) => {
    for (const r of radii) {
      const c = list.filter((x) => N.km(x, area) < r);
      if (c.length) return c.slice(0, 4).map((p, idx) => Object.assign(p, { rank: idx }));
    }
    return [];
  });
  const names = [];
  const byName = {};
  cands.forEach((c) => c.forEach((p) => { if (!byName[p.name]) { byName[p.name] = p; names.push(p.name); } }));
  const buzzList = await Promise.all(names.slice(0, 24).map((n) => blogBuzz(n, area.q).catch(() => null)));
  names.slice(0, 24).forEach((n, i) => { byName[n].buzz = buzzList[i]; });

  const used = new Set();
  const stops = [];
  cands.forEach((c, i) => {
    const sl = slots[i];
    const avail = c.filter((p) => !used.has(p.name));
    if (!avail.length) return;
    // Popularity score: recent blog posts weigh most, review-count order adds a little; then a weighted random pick for variety.
    const p = weightedPick(avail, (x) => 1 + (x.buzz ? Math.min(x.buzz.recent, 30) * 2 : 0) + (4 - x.rank) * 2, rand);
    used.add(p.name);
    stops.push({ kind: sl.kind, stay: sl.stay, name: p.name, category: p.category, address: p.address, lat: p.lat, lng: p.lng, link: p.link, tip: tipFor(sl.kind, i + off), hot: p.rank === 0, buzz: p.buzz || null });
  });
  if (stops.length < 2) throw new Error('too_few_places');
  let t = start;
  stops.forEach((s, i) => {
    if (i) {
      const d = N.km(stops[i - 1], s) * 1.3;
      const w = Math.max(1, Math.round((d / 4.5) * 60));
      s.travelMode = w <= 20 ? 'walk' : 'transit';
      s.travelMin = w <= 20 ? w : Math.round(8 + (d / 20) * 60);
      t += s.travelMin;
    }
    s.arr = t;
    t += s.stay;
    s.dep = t;
  });
  while (stops.length > 2 && stops[stops.length - 1].dep > end + 20) stops.pop();
  stops.forEach((s) => { s.time = fmt(s.arr); s.until = fmt(s.dep); delete s.arr; delete s.dep; });
  const trending = names.map((n) => byName[n]).filter((p) => !used.has(p.name) && p.buzz && p.buzz.recent > 0)
    .sort((a, b) => b.buzz.recent - a.buzz.recent).slice(0, 6);
  return { stops, trending };
}

const clampInt = (v, lo, hi, d) => { const n = parseInt(v, 10); return isFinite(n) ? Math.max(lo, Math.min(hi, n)) : d; };

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  const query = req.query || {};
  const mood = MOOD_TITLE[query.mood] ? query.mood : 'all';
  const start = clampInt(query.start, 0, 1380, 840);
  let end = clampInt(query.end, 0, 1439, start + 360);
  if (end < start + 60) end = Math.min(1439, start + 240);
  const place = String(query.place || '').replace(/[^0-9A-Za-z가-힣 ]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 30);
  const seed = clampInt(query.seed, 1, 2147483646, Date.now() % 2147483646);
  const avoid = String(query.avoid || '').split(',').map((x) => x.trim()).filter(Boolean).slice(0, 6);
  const rand = rng(seed);
  const LIKE_OK = ['카페', '맛집', '산책', '전시', '쇼핑', '팝업', '술', '야경'];
  const likes = String(query.likes || '').split(',').map((x) => x.trim()).filter((x) => LIKE_OK.indexOf(x) >= 0).slice(0, 8);
  const budgetWon = clampInt(query.budget, 0, 10000000, 0);
  const cheap = mood === 'budget' || (budgetWon > 0 && budgetWon <= 60000);

  if (!N.configured()) return res.status(200).json({ source: 'error', reason: 'not_configured' });

  try {
    const fixed = place ? null : AREAS.find((a) => a.name === String(query.area || ''));
    let ranking = null;
    let chosen;
    let mode;
    let trendOk = true;
    if (place) {
      const r = await resolvePlace(place, rand, avoid);
      chosen = r.chosen; ranking = r.ranking; mode = r.city ? 'city' : 'place';
      trendOk = !r.city || !!r.ranking;
    } else {
      try { ranking = await rankAreas(AREAS); } catch (e) { ranking = null; trendOk = false; }
      if (fixed) {
        chosen = (ranking && ranking.find((r) => r.area.name === fixed.name)) || { area: fixed, heat: null, trend: 'steady' };
        mode = 'area';
      } else {
        chosen = chooseArea(ranking, AREAS, avoid, rand, 12);
        mode = 'hot';
      }
    }
    const baseR = place ? 3 : 2;
    const { stops, trending } = await buildCourse(chosen.area, mood, start, end, rand, baseR, likes, cheap);

    const why = !trendOk && (mode === 'hot' || mode === 'city') ? '검색 추이를 불러오지 못해 대표 동네 중에서 골랐어요'
      : mode === 'hot' ? (chosen.trend === 'rising' ? '요즘 검색량이 오르는 동네예요' : '검색량 상위권 동네예요')
      : mode === 'city' ? '이 도시에서 요즘 검색이 많은 동네예요'
      : mode === 'area' ? '고른 동네' + (chosen.heat == null ? '' : chosen.trend === 'rising' ? ' · 검색량이 오르는 중' : ' · 꾸준한 인기')
      : '입력한 지역 주변이에요';

    return res.status(200).json({
      source: 'live',
      mood,
      mode,
      place,
      title: chosen.area.name + ' ' + MOOD_TITLE[mood],
      blurb: fmt(start) + '~' + fmt(end) + ' · ' + stops.length + '곳 · ' + why + '. 리뷰 수와 최근 블로그 후기로 인기를 따져 골랐어요.',
      window: { s: start, e: end },
      area: { name: chosen.area.name, heat: chosen.heat, trend: chosen.trend },
      stops,
      trending: trending.map((p) => ({ kind: kindOf(p.category), name: p.name, category: p.category, address: p.address, lat: p.lat, lng: p.lng, buzz: p.buzz })),
      ranking: (ranking || []).slice(0, 5).map((r) => ({ name: r.area.name, heat: r.heat, trend: r.trend })),
      generatedAt: new Date().toISOString(),
    });
  } catch (e) {
    return res.status(200).json({ source: 'error', reason: String((e && e.message) || e).slice(0, 120) });
  }
};

function kindOf(category) {
  const c = category || '';
  if (/카페|디저트|베이커리|제과/.test(c)) return '카페';
  if (/음식|한식|양식|일식|중식|레스토랑|고기|육류|분식|술집|주점|바$|요리/.test(c)) return '저녁';
  if (/전시|미술관|갤러리|박물관/.test(c)) return '전시';
  if (/공원|산책|해수욕장|해변|명소|관광/.test(c)) return '산책';
  if (/팝업/.test(c)) return '팝업';
  return '쇼핑';
}
