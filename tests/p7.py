# Redesign checks: tab bar navigation, resume card, favorites quick-add, chip rails, no sideways scroll on any screen.
import pathlib, json, datetime
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).parent
html=ROOT.parent.joinpath('index.html').read_text(encoding='utf8'); mock=ROOT.joinpath('mock.js').read_text(encoding='utf8')
URL="http://localhost:8123/"
KST=datetime.timezone(datetime.timedelta(hours=9)); today=datetime.datetime.now(KST).date()
D=lambda n:(today+datetime.timedelta(days=n)).isoformat()
E={'v1':{'kind':'visit','u':1,'body':{'date':D(-3),'title':'성수','note':'','by':0,'tm':{'s':720,'e':1260},'stops':[{'id':'a','name':'어니언 성수','kind':'카페','area':'성수동','lat':37.5446,'lng':127.0557,'stay':60,'time':'12:00','until':'13:00','cost':15000,'note':''}]}},
   'pla':{'kind':'place','u':1,'body':{'name':'어니언 성수','kind':'카페','area':'성수동','lat':37.5446,'lng':127.0557,'mark':'fav'}},
   'plb':{'kind':'place','u':1,'body':{'name':'성수 파스타','kind':'저녁','area':'성수동','lat':37.5470,'lng':127.0600,'mark':'fav'}},
   'plc':{'kind':'place','u':1,'body':{'name':'시끄러운 술집','kind':'술','area':'성수동','lat':37.545,'lng':127.059,'mark':'block'}}}
SEED="localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:0,since:'%s',code:'',dirty:false}));localStorage.setItem('dc_data',%s);window.__LAB={scenario:'normal'};"%(D(-50),json.dumps(json.dumps({'E':E,'dirty':{},'since':0})))
def mk(p,w=390,seed=SEED,geo=None):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":w,"height":800})
    if geo: ctx.grant_permissions(['geolocation']); ctx.set_geolocation({'latitude':geo[0],'longitude':geo[1]})
    pg=ctx.new_page(); pg.errs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    pg.add_init_script(seed); pg.add_init_script(mock)
    pg.route("**/*",lambda r: r.fulfill(status=200,content_type='text/html',body=html) if r.request.url==URL else r.abort())
    pg.goto(URL); pg.wait_for_timeout(500); return b,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
cur=lambda pg:pg.evaluate("(document.querySelector('#tabs [aria-current=page]')||{}).getAttribute&&document.querySelector('#tabs [aria-current=page]').getAttribute('data-go')")
with sync_playwright() as p:
    b,pg=mk(p)
    ok(pg.is_visible('#tabs') and cur(pg)=='home','tab bar visible, 홈 current')
    for v in ['plan','rec','cal','route','home']:
        pg.click('#tabs [data-go="%s"]'%v); pg.wait_for_timeout(250)
        ok(pg.is_visible('#'+v) and cur(pg)==v,'tab → %s'%v)
    # favorites quick-add in the empty planner (blocked places are not offered)
    pg.click('#tabs [data-go="plan"]'); pg.wait_for_timeout(300)
    chips=pg.eval_on_selector_all('[data-addfav]','e=>e.map(x=>x.textContent)')
    ok(chips==['어니언 성수','성수 파스타'],'empty planner offers favorites: %s'%chips)
    ok(not pg.is_visible('#planActions'),'save/clear hidden while the course is empty')
    pg.click('[data-addfav] >> nth=1'); pg.wait_for_timeout(500)
    ok(pg.locator('#stopList .stop').count()==1 and '성수 파스타' in pg.inner_text('#stopList') and pg.is_visible('#planActions'),'favorite added as a stop; save bar appears')
    # leaving via the tab bar keeps the course; home shows a resume card
    pg.click('#tabs [data-go="home"]'); pg.wait_for_timeout(250)
    ok(pg.is_visible('#resumeCard') and '만들던 코스 · 1곳' in pg.inner_text('#resumeCard'),'home resume card: '+pg.inner_text('#resumeCard').replace('\n',' '))
    pg.click('[data-resume]'); pg.wait_for_timeout(300)
    ok(pg.is_visible('#plan') and pg.locator('#stopList .stop').count()==1,'resume returns to the same course')
    pg.click('#tabs [data-go="cal"]'); pg.wait_for_timeout(200); pg.click('#tabs [data-go="plan"]'); pg.wait_for_timeout(200)
    ok(pg.locator('#stopList .stop').count()==1,'tab round-trip keeps the course')
    pg.click('#tabs [data-go="home"]'); pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300)
    ok(pg.locator('#stopList .stop').count()==0,'home CTA still starts a fresh course')
    pg.click('#tabs [data-go="home"]'); pg.wait_for_timeout(200); ok(not pg.is_visible('#resumeCard'),'no resume card when nothing is in progress')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # onboarding hides the tab bar
    b,pg=mk(p,seed="window.__LAB={scenario:'normal'};"); ok(pg.is_visible('#setup') and not pg.is_visible('#tabs'),'no tab bar during onboarding')
    pg.fill('#n0','지우'); pg.fill('#n1','하준'); pg.click('#setA button[type=submit]'); pg.wait_for_timeout(200); pg.click('#setB button[type=submit]'); pg.wait_for_timeout(200)
    pg.click('#pALikes [data-like="카페"]'); pg.click('#pAPresets [data-bud="100000"]'); pg.click('#setP button[type=submit]'); pg.wait_for_timeout(1500)
    ok(pg.is_visible('#home') and pg.is_visible('#tabs'),'tab bar appears after onboarding'); b.close()
    # selected chip scrolled into view in a one-line rail
    b,pg=mk(p,geo=(37.5622,126.9246)); pg.click('#tabs [data-go="rec"]'); pg.wait_for_timeout(300); pg.click('#geoRec'); pg.wait_for_timeout(800)
    vis=pg.evaluate("(()=>{const b=document.querySelector('#areaChips [aria-pressed=true]'),r=document.getElementById('areaChips').getBoundingClientRect(),c=b.getBoundingClientRect();return [b.dataset.area,c.left>=r.left-1&&c.right<=r.right+1]})()")
    ok(vis[0]=='연남동' and vis[1],'location-picked chip is inside the visible rail: %s'%vis)
    ok(pg.evaluate("getComputedStyle(document.getElementById('areaChips')).flexWrap")=='nowrap','area chips are one scrolling line'); b.close()
    # no sideways scrolling on any screen at 360px; touch targets
    b,pg=mk(p,w=360)
    for v in ['home','plan','rec','cal','route']:
        pg.click('#tabs [data-go="%s"]'%v); pg.wait_for_timeout(400)
        ok(not pg.evaluate("document.documentElement.scrollWidth>innerWidth"),'no horizontal overflow at 360: %s'%v)
    pg.click('#tabs [data-go="cal"]'); pg.click('[data-day="%s"]'%D(-3)); pg.wait_for_timeout(300)
    small=pg.evaluate("[...document.querySelectorAll('#cal button:not([hidden]),#tabs button')].filter(e=>e.offsetParent).map(e=>e.getBoundingClientRect()).filter(r=>r.width<43.5||r.height<43.5).length")
    ok(small==0,'every calendar/tab button is at least 44px: %d smaller'%small)
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
