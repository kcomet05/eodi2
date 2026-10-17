import pathlib, json, re, datetime
from playwright.sync_api import sync_playwright
html=pathlib.Path(str(pathlib.Path(__file__).parent.parent/'index.html')).read_text(encoding='utf8')
mock=pathlib.Path(str(pathlib.Path(__file__).parent/'mock.js')).read_text(encoding='utf8')
today=(datetime.datetime.utcnow()+datetime.timedelta(hours=9)).date()
D=lambda n:(today+datetime.timedelta(days=n)).isoformat()
COUPLES={}; ENT={}; calls=[]
def api(method,url,body):
    code=(re.search(r'code=([A-Z0-9]+)',url) or [0,''])[1]
    if '/api/sync' in url:
        c=body['code']; E=ENT.setdefault(c,{})
        for it in body['items']:
            if it['id'] not in E or E[it['id']]['u']<it['u']: E[it['id']]=it
        calls.append(('sync',len(body['items'])))
        return {'ok':True,'now':int(datetime.datetime.now().timestamp()*1000),'items':[v for v in E.values() if v['u']>body['since']]}
    if method=='POST':
        k='ABCD2345'; COUPLES[k]={'code':k,'names':body['names'],'since':body['since'],'updatedAt':'x'}; return {'ok':True,'couple':COUPLES[k]}
    if code not in COUPLES: return {'ok':False,'reason':'not_found'}
    if method=='PUT': COUPLES[code].update(names=body['names'],since=body['since']); return {'ok':True,'couple':COUPLES[code]}
    return {'ok':True,'couple':COUPLES[code]}
def mk(p,w=390,h=844,dark=False,seed=None):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":w,"height":h},device_scale_factor=2,color_scheme='dark' if dark else 'light'); pg=ctx.new_page()
    pg.errs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    pg.add_init_script("window.__nf=window.fetch.bind(window);window.__urls=[];")
    if seed: pg.add_init_script(seed)
    pg.add_init_script("window.__LAB={scenario:'normal'};")
    pg.add_init_script(mock)
    pg.add_init_script("(function(){var mf=window.fetch;window.fetch=function(i,o){var s=String(i);window.__urls.push(s);if(/\\/api\\/(couple|sync)/.test(s))return window.__nf(i,o);return mf(i,o);};})();")
    def route(r):
        u=r.request.url
        if u=='http://t.local/' or u.startswith('http://t.local/?'): return r.fulfill(status=200,content_type='text/html',body=html)
        if '/api/couple' in u or '/api/sync' in u:
            body=json.loads(r.request.post_data) if r.request.post_data else None
            return r.fulfill(status=200,content_type='application/json',body=json.dumps(api(r.request.method,u,body)))
        r.abort()
    pg.route("**/*",route); return b,ctx,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    # ---------- A. onboarding with preferences ----------
    b,ctx,pg=mk(p); pg.goto("http://t.local/"); pg.wait_for_timeout(400)
    pg.fill('#n0','지우'); pg.fill('#n1','하준'); pg.click('#setA button[type=submit]'); pg.wait_for_timeout(150)
    ok(pg.inner_text('#stepLbl')=='2 / 3','step 2 of 3')
    pg.fill('#since',D(-94)); pg.click('#setB button[type=submit]'); pg.wait_for_timeout(200)
    ok(pg.is_visible('#setP') and pg.inner_text('#stepLbl')=='3 / 3','preferences step shown')
    pg.screenshot(path='/tmp/p2_a_prefs.png',full_page=True)
    pg.click('#setP button[type=submit]'); ok('좋아하는' in pg.inner_text('#errP'),'needs a like: '+pg.inner_text('#errP'))
    pg.click('#pALikes [data-like="카페"]'); pg.click('#pALikes [data-like="전시"]')
    pg.click('#setP button[type=submit]'); ok('예산' in pg.inner_text('#errP'),'needs a budget: '+pg.inner_text('#errP'))
    pg.click('#pAPresets [data-bud="100000"]'); ok(pg.input_value('#pABud')=='100000','preset fills budget')
    ok(pg.get_attribute('#pAPresets [data-bud="100000"]','aria-pressed')=='true','preset shows pressed')
    pg.click('#setP button[type=submit]'); pg.wait_for_timeout(2500)
    ok(pg.is_visible('#home'),'home after 3 steps')
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')")); ok(dc['E']['prefs']['body']['likes']==['카페','전시'] and dc['E']['prefs']['body']['budget']==100000,'prefs stored locally')
    ok('prefs' in ENT.get('ABCD2345',{}),'prefs synced to server')
    ok('100일' in pg.inner_text('#nextSp') and 'D-5' in pg.inner_text('#nextSp'),'next special on home: '+pg.inner_text('#nextSp').replace('\n',' '))
    ok(not pg.is_visible('#prefNudge'),'no nudge once prefs exist')
    pg.screenshot(path='/tmp/p2_home.png',full_page=True)
    # ---------- B. plan: add, insert between, cost, save ----------
    pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300)
    for i in (0,1):
        pg.click('#q'); pg.keyboard.type('성수 카페'); pg.wait_for_timeout(900); pg.click('.sgi >> nth=%d'%i); pg.wait_for_timeout(1000)
    ok(pg.locator('#stopList .stop').count()==2,'two stops')
    names=pg.eval_on_selector_all('#stopList .stop .fly b','e=>e.map(x=>x.textContent)')
    ok(pg.locator('.insbtn').count()==1,'one between-button for two stops')
    pg.click('.insbtn'); pg.wait_for_timeout(900)
    ok(pg.is_visible('#suggest') and '사이' in pg.inner_text('#suggest .sg-head'),'insert search opened: '+pg.inner_text('#suggest .sg-head'))
    nsg=pg.locator('.sgi').count(); ok(nsg>=1,'between candidates: %d'%nsg)
    cand=pg.inner_text('.sgi >> nth=0 >> b'); pg.click('.sgi >> nth=0'); pg.wait_for_timeout(1100)
    n2=pg.eval_on_selector_all('#stopList .stop .fly b','e=>e.map(x=>x.textContent)')
    ok(len(n2)==3 and n2[1]==cand and n2[0]==names[0] and n2[2]==names[1],'inserted between: %s'%n2)
    ok(pg.locator('.insbtn').count()==2,'two between-buttons for three stops')
    ok('예산' in pg.inner_text('#budgetBox') and '100,000원' in pg.inner_text('#budgetBox'),'budget box: '+pg.inner_text('#budgetBox').replace('\n',' '))
    pg.fill('#stopList .costin >> nth=0','x') if False else None
    pg.fill('[data-cost] >> nth=0','90000'); pg.keyboard.press('Tab'); pg.wait_for_timeout(200)
    ok('넘어요' in pg.inner_text('#budgetBox'),'over-budget warning: '+pg.inner_text('#budgetBox').replace('\n',' '))
    pg.screenshot(path='/tmp/p2_plan.png',full_page=True)
    pg.click('#saveBtn'); pg.wait_for_timeout(250); ok(pg.is_visible('#saveSheet'),'save dialog')
    pg.fill('#sdate',D(-3)); pg.fill('#stitle','성수 데이트'); pg.fill('#smemo','첫 전시 보러 감')
    pg.screenshot(path='/tmp/p2_save.png')
    pg.click('#saveForm button[type=submit]'); pg.wait_for_timeout(500)
    ok(pg.is_visible('#cal') and not pg.is_visible('#plan'),'goes to calendar after save')
    ok(pg.locator('#dayPanel .vcard').count()==1 and '성수 데이트' in pg.inner_text('#dayPanel'),'visit on selected day')
    ok(pg.locator('[data-day="%s"] .mk-v'%D(-3)).count()==1,'calendar cell marked')
    # ---------- C. notes ----------
    pg.fill('[data-snote] >> nth=0','파스타 맛있음'); pg.keyboard.press('Tab'); pg.wait_for_timeout(200)
    pg.fill('[data-vnote]','우리 첫 전시!'); pg.keyboard.press('Tab'); pg.wait_for_timeout(2500)
    vid=[k for k,v in json.loads(pg.evaluate("localStorage.getItem('dc_data')"))['E'].items() if v['kind']=='visit'][0]
    body=ENT['ABCD2345'][vid]['body']
    ok(body['note']=='우리 첫 전시!' and body['stops'][0]['note']=='파스타 맛있음','notes saved + synced: %s'%[body['note'],body['stops'][0]['note']])
    ok(body['stops'][0]['cost']==90000 and len(body['stops'])==3,'cost + stops stored')
    pg.screenshot(path='/tmp/p2_cal.png',full_page=True)
    # ---------- D. special dates ----------
    pg.click('[data-spgo] >> nth=0'); pg.wait_for_timeout(200)
    ok('100일' in pg.inner_text('#dayPanel') and '자동' in pg.inner_text('#dayPanel'),'auto 100일 on its day: '+pg.inner_text('#dayPanel h3'))
    pg.click('#upcoming [data-addsp]'); pg.wait_for_timeout(250)
    pg.fill('#spTitle','지우 생일'); pg.fill('#spDate','1999-%s'%D(20)[5:]); pg.check('#spYearly'); pg.click('#spForm button[type=submit]'); pg.wait_for_timeout(500)
    ok('지우 생일' in pg.inner_text('#dayPanel'),'custom yearly special added')
    ok('지우 생일' in pg.inner_text('#upcoming'),'listed in upcoming')
    pg.click('#calNext'); pg.click('#calPrev'); pg.click('#calToday'); pg.wait_for_timeout(200)
    ok(pg.get_attribute('[data-day="%s"]'%D(0),'aria-pressed')=='true','today button selects today')
    # first-year anniversary computed
    pg.evaluate("document.querySelector('#calToday').click()")
    # ---------- E. partner phone ----------
    b2,ctx2,pg2=mk(p); pg2.goto("http://t.local/?join=ABCD2345"); pg2.wait_for_timeout(900)
    ok(pg2.is_visible('#setW'),'partner sees who-are-you after join link')
    pg2.click('#whoW .chip >> nth=1'); pg2.wait_for_timeout(1500)
    ok(pg2.is_visible('#home') and '100일' in pg2.inner_text('#nextSp'),'partner home has shared specials')
    ok(not pg2.is_visible('#prefNudge'),'partner got prefs from shared data')
    pg2.click('#tabs [data-go=cal]'); pg2.wait_for_timeout(300)
    pg2.click('[data-day="%s"]'%D(-3)); pg2.wait_for_timeout(200)
    ok('성수 데이트' in pg2.inner_text('#dayPanel') and pg2.input_value('[data-vnote]')=='우리 첫 전시!','partner sees the same visit + note')
    pg2.fill('[data-vnote]','하준: 나도 좋았어'); pg2.keyboard.press('Tab'); pg2.wait_for_timeout(2500)
    pg.click('[data-day="%s"]'%D(-3))
    pg.evaluate("Object.defineProperty(document,'hidden',{value:false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(1500)
    ok(pg.input_value('[data-vnote]')=='하준: 나도 좋았어','first phone receives partner note after refocus: '+pg.input_value('[data-vnote]'))
    # ---------- F. edit saved visit, add between, resave same id ----------
    pg.click('[data-editv]'); pg.wait_for_timeout(700)
    ok(pg.is_visible('#plan') and pg.locator('#stopList .stop').count()==3 and '고치기' in pg.inner_text('#planTitle'),'edit opens plan with 3 stops')
    pg.click('.insbtn >> nth=1'); pg.wait_for_timeout(900); pg.click('.sgi >> nth=0'); pg.wait_for_timeout(1100)
    ok(pg.locator('#stopList .stop').count()==4,'added a 4th between')
    pg.click('#saveBtn'); pg.wait_for_timeout(250); ok('다시' in pg.inner_text('#saveT'),'save dialog says re-save'); pg.click('#saveForm button[type=submit]'); pg.wait_for_timeout(500)
    ok(pg.locator('#dayPanel .vcard').count()==1 and pg.locator('#dayPanel .vstop').count()==4,'same visit updated to 4 stops (not duplicated)')
    ok(pg.input_value('[data-snote] >> nth=0')=='파스타 맛있음','stop note survived edit')
    # ---------- G. delete ----------
    pg.click('[data-delv]'); ok(pg.locator('#dayPanel .vcard').count()==1 and '정말' in pg.inner_text('[data-delv]'),'first tap arms delete')
    pg.click('[data-delv]'); pg.wait_for_timeout(300)
    ok(pg.locator('#dayPanel .vcard').count()==0,'second tap deletes')
    pg.wait_for_timeout(2000); ok(ENT['ABCD2345'][vid]['body'].get('deleted') is True,'tombstone synced')
    pg2.evaluate("Object.defineProperty(document,'hidden',{value:false,configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); pg2.wait_for_timeout(1500)
    pg2.click('[data-day="%s"]'%D(-3)); ok(pg2.locator('#dayPanel .vcard').count()==0,'partner sees deletion')
    # ---------- H. recommendations use prefs ----------
    pg.click('#cal [data-go=home]'); pg.click('#home [data-go=rec]'); pg.wait_for_timeout(1000)
    urls=pg.evaluate("window.__urls.filter(function(u){return u.indexOf('/api/recommend')>=0})")
    ok(urls and 'likes=%EC%B9%B4%ED%8E%98%2C%EC%A0%84%EC%8B%9C' in urls[-1] and 'budget=100000' in urls[-1],'recommend request carries likes+budget')
    ok(not pg.errs and not pg2.errs,'no page errors %s %s'%(pg.errs,pg2.errs))
    b.close(); b2.close()
    # ---------- I. existing user without prefs ----------
    ENT.clear(); COUPLES.clear()
    seed="localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:0,since:'%s',code:'',dirty:false}));"%D(-30)
    b3,ctx3,pg3=mk(p,seed=seed); pg3.goto("http://t.local/"); pg3.wait_for_timeout(600)
    ok(pg3.is_visible('#prefNudge'),'existing couple sees the prefs nudge')
    pg3.click('[data-openprefs]'); pg3.wait_for_timeout(300); ok(pg3.is_visible('#sheet') and pg3.is_visible('#pSLikes'),'nudge opens settings with prefs')
    pg3.click('#setS button[type=submit]'); ok('좋아하는' in pg3.inner_text('#errS'),'sheet validates prefs')
    pg3.click('#pSLikes [data-like="산책"]'); pg3.fill('#pSBud','50000'); pg3.click('#setS button[type=submit]'); pg3.wait_for_timeout(400)
    ok(not pg3.is_visible('#sheet') and not pg3.is_visible('#prefNudge'),'prefs saved from sheet, nudge gone')
    ok(not pg3.errs,'no errors %s'%pg3.errs); b3.close()
    # ---------- J. dark 360 screenshots ----------
    b4,ctx4,pg4=mk(p,w=360,h=780,dark=True,seed=seed+"localStorage.setItem('dc_data',JSON.stringify({E:{prefs:{kind:'prefs',u:1,body:{likes:['카페'],budget:80000}},v1:{kind:'visit',u:2,body:{date:'%s',title:'성수 데이트',note:'좋았다',by:0,tm:{s:840,e:1260},stops:[{id:'a',name:'카페 하나',kind:'카페',area:'성수동',lat:37.544,lng:127.056,stay:60,time:'14:00',until:'15:00',cost:15000,note:'라떼'},{id:'b',name:'전시 둘',kind:'전시',area:'성수동',lat:37.546,lng:127.058,stay:80,time:'15:20',until:'16:40',cost:30000,note:''}]}}},dirty:{},since:0}));"%D(-2))
    pg4.goto("http://t.local/"); pg4.wait_for_timeout(500); pg4.screenshot(path='/tmp/p2_dark_home.png',full_page=True)
    pg4.click('#tabs [data-go=cal]'); pg4.wait_for_timeout(300); pg4.click('[data-day="%s"]'%D(-2)); pg4.wait_for_timeout(200); pg4.screenshot(path='/tmp/p2_dark_cal.png',full_page=True)
    ok(pg4.evaluate("document.documentElement.scrollWidth<=360"),'no horizontal scroll at 360')
    ok(not pg4.errs,'no errors %s'%pg4.errs); b4.close()
