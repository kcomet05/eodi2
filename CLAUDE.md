# 우리 오늘 어디가 (Eodi) — project notes for Claude

Couples' date-planning web app. Korean UI, mobile-first. Live at https://date-course-kcomet.vercel.app
(Vercel project `date-course`, team `kcomet`). Production runs the latest `main`;
every push to `main` auto-deploys to production via the GitHub integration (repo `kcomet05/eodi2`).

## Stack
- `index.html` — the whole client: one file, one IIFE, no build step. Naver Maps v3 (client id `2qvv05vrkk`, public,
  domain-restricted) with a canvas fallback map.
- `api/*.js` — Vercel Node serverless functions, no npm dependencies.
  - `_naver.js` shared Naver Search / DataLab access (API Hub first, developers.naver.com fallback)
  - `search.js`, `nearby.js`, `recommend.js` (course algorithm), `health.js` (key diagnostics)
  - `_db.js` dependency-free Neon client over HTTPS (`POST https://<host>/sql`, header `Neon-Connection-String`)
  - `weather.js` (KMA getVilageFcst by lat/lng → Lambert grid; 10 min s-maxage; returns `kma_not_configured` without the key)
  - `couple.js` (couple create/read/update by 8-char invite code), `sync.js` (shared item store)
- `vercel.json` — function maxDuration only.

## Env vars (set in Vercel dashboard only — never ask for or print values)
`NAVER_API_KEY_ID`, `NAVER_API_KEY_SECRET`, `DATABASE_URL` (Neon), `KMA_SERVICE_KEY` (공공데이터포털 인증키 for 기상청 단기예보 — 활용신청 필요). Without `DATABASE_URL` the APIs return
`db_not_configured` and the app still works on one phone (shows "공유 저장소가 아직 연결되지 않았어요").

## Neon tables (already created)
- `couples(code text pk, names text[], since date, created_at, updated_at)`
- `entries(couple_code text, id text, kind text, u bigint, body jsonb, pk(couple_code,id))`

## Data model (client)
localStorage: `dc_couple`, `dc_data` = `{E:{id:{kind,u,body}}, dirty:{id:1}, since}`, `dc_tm`, `dc_area`, `dc_recent`.
Items kind = `visit` | `special` | `prefs` | `place` | `photo`; last-write-wins by `u` (client ms); deletes are tombstones `{deleted:true}`.
`/api/sync` POST `{code, since, items}` (≤100 items, body <30KB) → returns items with `u>since` + `now`. Replies are paged at ~3MB (Vercel's limit is 4.5MB): `more:true,last:<u>` → client advances `since` to `last-1` and syncs again.
Auto special dates from `since` (day 1 = since): 100…1000 days, 1500/2000/2500/3000 days, 1–40주년, plus seasonal
(1/1, 2/14, 3/14, 5/14, 11/11, 12/24, 12/25). Custom specials can repeat yearly.

## Design rules ("노선도 for two" — full system in DESIGN.md; follow it for any UI change)
Red route line + ringed station dots only where there is a sequence; Do Hyeon (display) + IBM Plex Sans KR (body); lilac-gray paper + plum ink.
Tokens on :root (colour, type scale, 4-pt spacing, radii 8/12/16/pill, control heights 44/52/56) with dark values via prefers-color-scheme and [data-theme].
Flat cards (surface + 1px `--hair`), shadows only on floating layers. One accent (line red); `--sun` yellow only for anniversaries/hot badges.
Icons: one inline SVG sprite (`#i-*`, JS helper `ico(name)`), no emoji in UI chrome. Bottom tab bar `#tabs` (home/plan/rec/cal/route; hidden in onboarding, synced in `show()` via `syncTabs`).
Tabs resume the current course; only the home CTA starts a fresh one (home shows a "만들던 코스" resume card when stops exist).
390px mobile-first, 44px min touch targets, visible focus, prefers-reduced-motion. ≥960px: planner is two columns (sticky map). Screens stay a 440px column.
API keys only in Vercel env vars. Ask the owner before adding paid services.

## Tests
`cd tests && python3 p2.py && python3 p1_reg.py && python3 p3.py && python3 p4.py && python3 p5.py && python3 p6.py && python3 p7.py && node weather.test.js && node sync.test.js` (Playwright; mocks all /api routes via `mock.js` + in-memory
couple/sync). All checks currently pass.

## Roadmap
- Phase 1 couple setup + Neon — done. Calendar / save course / notes / insert-between / prefs / budget / special dates — done, NOT yet deployed.
- Phase 2 — done. ♥/✕ vote per stop per person (`stops[i].votes={0|1:1|-1}` inside the visit, synced like notes; shown in the calendar day panel).
  Share link `/#c=<base64url JSON>` encodes title + stops only (no couple code, notes, or votes); recipient sees a sheet and can load it into the planner.
  Hash input is untrusted: validated (kind whitelist, Korea lat/lng box, ≤12 stops, escaped on render). Native share sheet / copy fallback.
  KakaoTalk share intentionally dropped by the owner — no Kakao JS key needed.
- Phase 3 — done (KMA chosen by owner). Live-date mode (`#live`): home card + day-panel button for today's visit; shows now/next stop from stored stop times (KST, midnight-wrap aware), KMA hourly strip for the course window + rain advisory, per-stop opening hours, last-train note.
  Opening hours are owner-entered per stop (`stops[i].hours` = `HH:MM-HH:MM`), NOT fetched — Naver search has no hours. Warning if arrival/leave falls outside. Last-train note is a generic heuristic (finish ≥ 23:00 → "check your subway app"); no real timetable data.
  Weather needs `KMA_SERVICE_KEY` in Vercel; without it live mode still works and says weather isn't connected.
- Phase 4 — done.
  `place` items (id `pl`+hash(name+lat/lng 3dp)): body `{name,kind,area,lat,lng,mark:'fav'|'block'}`; ★/🚫 buttons in plan list and calendar day panel. Blocked places are hidden from nearby/insert suggestions (search results still show them, labelled "제외한 곳"); the server `/api/recommend` does not know about blocks.
  `photo` items: ONE JPEG thumbnail (≤360px, data URL <24KB so the item stays <30KB) per item `{v:visitId,t,at,by}`, max 12 per visit / 150 total, stored in Neon like any item (free tier). Originals are NOT kept anywhere — chosen to avoid a paid blob store; if full-size photos are wanted, ask the owner about Vercel Blob. Only `data:image/jpeg;base64,` strings are ever rendered.
  `#route` "우리의 노선도": stats, metro-style line of past visits (places visited 2+ times drawn as 환승역), photos, favorites/blocked lists.
  Anniversary suggestion (`#annSug` on home): next special within 60 days with no date planned → course from ≥2 favorites within 3km, ordered 점심→카페→전시→산책→야경→저녁→술, one tap opens it in the planner.
- Phase 5 — done.
  Reorder: per-stop ☰ grip (pointer events, works for mouse + touch; `touch-action:none`), ↑/↓ buttons and ArrowUp/Down on the grip for keyboard/screen readers; `moveStop()` re-times everything via `schedule()`.
  Current-location start: `PLAN.start={lat,lng}` (saved as `visit.start`, restored on edit). It is NOT a stop; it adds the travel leg to the first stop's arrival time and anchors nearby suggestions when the plan is empty (needs a supported neighbourhood within 6km via `nearestArea`, else nearby is hidden). Geolocation is only requested on button tap; denied/out-of-Korea/timeouts show a toast. Rec screen: "📍 내 위치 주변 동네로 추천받기" picks the nearest AREAS entry within 6km.
  Testing geolocation needs a secure origin: tests use `http://localhost:8123/` (not `t.local`).
- All 5 phases done. Ideas not started: server-side `/api/recommend` honouring blocked places, full-size photo storage (would need a paid blob store — ask owner), real opening-hours/last-train data.
Finish, test and report each phase before starting the next.
