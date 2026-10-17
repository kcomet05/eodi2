import pathlib, json, re
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).parent
html=ROOT.parent.joinpath('index.html').read_text(encoding='utf8'); mock=ROOT.joinpath('mock.js').read_text(encoding='utf8')
URL="http://localhost:8123/"
SEED="localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:0,since:'',code:'',dirty:false}));window.__LAB={scenario:'normal'};"
def mk(p,geo=None,h=844):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":390,"height":h})
    if geo: ctx.grant_permissions(['geolocation']); ctx.set_geolocation({'latitude':geo[0],'longitude':geo[1]})
    pg=ctx.new_page(); pg.errs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    pg.add_init_script(SEED); pg.add_init_script(mock)
    pg.route("**/*",lambda r: r.fulfill(status=200,content_type='text/html',body=html) if r.request.url==URL else r.abort())
    pg.goto(URL); pg.wait_for_timeout(500); return b,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
names=lambda pg:pg.eval_on_selector_all('#stopList .stop .fly b','e=>e.map(x=>x.textContent)')
def add(pg,n):
    for i in range(n):
        pg.click('#q'); pg.keyboard.type('성수 카페'); pg.wait_for_timeout(900); pg.click('.sgi >> nth=%d'%i); pg.wait_for_timeout(900)
def first_arr(pg): return pg.inner_text('#stopList .stop >> nth=0 >> .fly small').split(' ')[0]
with sync_playwright() as p:
    # ---- reorder ----
    b,pg=mk(p,h=2400); pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300); add(pg,3)
    n0=names(pg); ok(len(n0)==3,'three stops: %s'%n0)
    ok(pg.locator('[data-mv$="|-1"]').first.is_disabled() and pg.locator('[data-mv$="|1"]').last.is_disabled(),'first ↑ and last ↓ disabled')
    pg.screenshot(path='/tmp/p6_plan.png',full_page=True)
    pg.click('[data-mv$="|1"] >> nth=0'); pg.wait_for_timeout(300)
    n1=names(pg); ok(n1==[n0[1],n0[0],n0[2]],'↓ on first swaps with second: %s'%n1)
    ok(pg.evaluate("document.activeElement.getAttribute('data-mv')||''").endswith('|1'),'focus stays on the moved stop button')
    pg.click('[data-mv$="|-1"] >> nth=2'); pg.wait_for_timeout(300)
    ok(names(pg)==[n0[1],n0[2],n0[0]],'↑ on last moves it up: %s'%names(pg))
    ok(pg.inner_text('#announce')!='' and '번째로 옮겼어요' in pg.inner_text('#announce'),'screen-reader announcement: '+pg.inner_text('#announce'))
    # mouse drag first stop below the last one
    cur=names(pg); g=pg.locator('[data-grip] >> nth=0').bounding_box(); last=pg.locator('#stopList .stop >> nth=2').bounding_box()
    pg.mouse.move(g['x']+g['width']/2,g['y']+g['height']/2); pg.mouse.down()
    ty=last['y']+last['height']-4
    for k in range(1,9): pg.mouse.move(g['x']+g['width']/2,g['y']+g['height']/2+(ty-g['y']-g['height']/2)*k/8); pg.wait_for_timeout(30)
    ok(pg.locator('.stop.dragging').count()==1,'dragged row marked while held')
    pg.mouse.up(); pg.wait_for_timeout(400)
    ok(names(pg)==[cur[1],cur[2],cur[0]],'drag first to bottom: %s'%names(pg))
    ok(pg.locator('.stop.dragging').count()==0 and pg.evaluate("[...document.querySelectorAll('#stopList .stop')].every(e=>!e.style.transform)"),'drag styles cleaned up')
    # drag last to top
    cur=names(pg); g=pg.locator('[data-grip] >> nth=2').bounding_box(); first=pg.locator('#stopList .stop >> nth=0').bounding_box()
    pg.mouse.move(g['x']+g['width']/2,g['y']+g['height']/2); pg.mouse.down()
    for k in range(1,9): pg.mouse.move(g['x']+g['width']/2,g['y']+g['height']/2+(first['y']+4-g['y']-g['height']/2)*k/8); pg.wait_for_timeout(30)
    pg.mouse.up(); pg.wait_for_timeout(400)
    ok(names(pg)==[cur[2],cur[0],cur[1]],'drag last to top: %s'%names(pg))
    # tiny drag = no change; cancel keeps order
    cur=names(pg); g=pg.locator('[data-grip] >> nth=1').bounding_box()
    pg.mouse.move(g['x']+20,g['y']+20); pg.mouse.down(); pg.mouse.move(g['x']+20,g['y']+26); pg.mouse.up(); pg.wait_for_timeout(300)
    ok(names(pg)==cur,'small wiggle does not reorder')
    # keyboard on the grip
    pg.focus('[data-grip] >> nth=0'); pg.keyboard.press('ArrowDown'); pg.wait_for_timeout(300)
    ok(names(pg)==[cur[1],cur[0],cur[2]],'ArrowDown on grip moves stop: %s'%names(pg))
    ok(pg.evaluate("document.activeElement.hasAttribute('data-grip')"),'focus returns to the grip')
    # times recompute after reorder (first stop starts at 14:00)
    ok(first_arr(pg)=='14:00','first stop arrives at start time after reorder: '+first_arr(pg))
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # touch drag (phone): real touch events through CDP
    b,pg=mk(p,h=2400); pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300); add(pg,3)
    ctx=pg.context; cdp=ctx.new_cdp_session(pg); cur=names(pg)
    g=pg.locator('[data-grip] >> nth=0').bounding_box(); last=pg.locator('#stopList .stop >> nth=2').bounding_box()
    x=g['x']+g['width']/2; y=g['y']+g['height']/2; ty=last['y']+last['height']-4
    cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    for k in range(1,9): cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+(ty-y)*k/8}]}); pg.wait_for_timeout(30)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]}); pg.wait_for_timeout(400)
    ok(names(pg)==[cur[1],cur[2],cur[0]],'touch drag first to bottom: %s'%names(pg))
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # ---- geolocation start ----
    b,pg=mk(p,geo=(37.5665,126.9780)); pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300)
    pg.click('#geoBtn'); pg.wait_for_timeout(800)
    ok(pg.is_visible('.startrow') and '현재 위치에서 출발' in pg.inner_text('.startrow'),'start row shown')
    ok(pg.locator('#stopList .stop').count()==0,'start is not a stop')
    ok(pg.is_visible('#nearby') and '현재 위치' in pg.inner_text('#nearby h3'),'nearby suggestions anchored on current location: '+pg.inner_text('#nearby h3'))
    add(pg,1)
    a=first_arr(pg); ok(a!='14:00' and a>'14:00','first arrival shifted by travel from start: '+a)
    ok('첫 장소까지' in pg.inner_text('.startrow'),'start row shows leg to first stop: '+pg.inner_text('.startrow')[:30])
    # save, reload edit -> start preserved
    pg.click('#saveBtn'); pg.wait_for_timeout(200); pg.click('#saveForm button[type=submit]'); pg.wait_for_timeout(400)
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')")); v=[x for x in dc['E'].values() if x['kind']=='visit'][0]['body']
    ok(v['start'] and abs(v['start']['lat']-37.5665)<1e-4 and v['stops'][0]['time']==a,'visit stores start + shifted time %s'%v['stops'][0]['time'])
    pg.click('[data-editv]'); pg.wait_for_timeout(500)
    ok(pg.is_visible('.startrow'),'edit restores start point')
    pg.click('#startX'); pg.wait_for_timeout(300)
    ok(pg.locator('.startrow').count()==0 and first_arr(pg)=='14:00','removing start restores times')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # outside Korea / denied
    b,pg=mk(p,geo=(48.85,2.35)); pg.click('#home [data-go="plan"]'); pg.click('#geoBtn'); pg.wait_for_timeout(600)
    ok('한국' in pg.inner_text('#toast') and pg.locator('.startrow').count()==0,'location outside Korea refused: '+pg.inner_text('#toast')); b.close()
    b,pg=mk(p); pg.click('#home [data-go="plan"]'); pg.click('#geoBtn'); pg.wait_for_timeout(800)
    ok('위치' in pg.inner_text('#toast') and pg.locator('.startrow').count()==0,'denied permission shows message: '+pg.inner_text('#toast')); b.close()
    # ---- recommend area from location ----
    b,pg=mk(p,geo=(37.5450,127.0570)); pg.click('#home [data-go="rec"]'); pg.wait_for_timeout(400)
    pg.click('#geoRec'); pg.wait_for_timeout(800)
    ok(pg.get_attribute('[data-area="성수동"]','aria-pressed')=='true','nearest area chip selected: 성수동')
    b.close()
    b,pg=mk(p,geo=(35.1587,129.1604)); pg.click('#home [data-go="rec"]'); pg.wait_for_timeout(300); pg.click('#geoRec'); pg.wait_for_timeout(600)
    ok('못 찾았어요' in pg.inner_text('#toast'),'far from supported neighbourhoods: '+pg.inner_text('#toast')); b.close()
