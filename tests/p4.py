import pathlib, json, datetime
from playwright.sync_api import sync_playwright
html=pathlib.Path(__file__).parent.parent.joinpath('index.html').read_text(encoding='utf8')
KST=datetime.timezone(datetime.timedelta(hours=9))
now=datetime.datetime.now(KST); today=now.date()
ymd=today.strftime('%Y%m%d')
def at(h,m=0): return datetime.datetime(today.year,today.month,today.day,h,m,tzinfo=KST)
def visit(late=False,hours=''):
    st=[{'id':'a1','name':'성수 카페','kind':'카페','area':'성수동','lat':37.5446,'lng':127.0557,'stay':60,'time':'11:00','until':'12:00','cost':15000,'note':'','hours':hours},
        {'id':'a2','name':'전시회','kind':'전시','area':'성수동','lat':37.5462,'lng':127.0612,'stay':80,'time':'12:20','until':'13:40','cost':30000,'note':''}]
    if late: st.append({'id':'a3','name':'야식 술집','kind':'술','area':'성수동','lat':37.545,'lng':127.06,'stay':70,'time':'22:30','until':'23:40','cost':50000,'note':''})
    return {'date':today.isoformat(),'title':'성수 데이트','note':'','by':0,'tm':{'s':660,'e':1400 if late else 1260},'stops':st}
def seed(v):
    d={'E':{'v1':{'kind':'visit','u':1,'body':v}},'dirty':{},'since':0}
    return "localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:0,since:'',code:'',dirty:false}));localStorage.setItem('dc_data',%s);"%json.dumps(json.dumps(d))
WX={'ok':True,'hours':[{'d':ymd,'t':'%02d00'%h,'tmp':18+h%5,'sky':1,'pty':0,'pop':10} for h in range(10,20)]}
RAIN={'ok':True,'hours':[{'d':ymd,'t':'%02d00'%h,'tmp':15,'sky':4,'pty':1 if h==13 else 0,'pop':80 if h==13 else 20} for h in range(10,20)]}
calls=[]
def mk(p,v,when,wx):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":390,"height":844}); ctx.clock.set_fixed_time(when); pg=ctx.new_page()
    pg.errs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    pg.add_init_script(seed(v))
    def route(r):
        u=r.request.url
        if '/api/weather' in u: calls.append(u); return r.fulfill(status=200,content_type='application/json',body=json.dumps(wx))
        if u.startswith('http://t.local/'): return r.fulfill(status=200,content_type='text/html',body=html)
        r.abort()
    pg.route("**/*",route); pg.goto("http://t.local/"); pg.wait_for_timeout(500); return b,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    b,pg=mk(p,visit(),at(11,30),WX)
    ok(pg.is_visible('#liveCard') and '오늘 데이트' in pg.inner_text('#liveCard'),'home shows live card')
    pg.click('#liveCard [data-golive]'); pg.wait_for_timeout(600)
    ok(pg.is_visible('#live'),'live view opens')
    st=pg.inner_text('#liveStatus'); ok('지금 성수 카페' in st and '다음 전시회 12:20' in st,'11:30 -> at cafe, next exhibit: '+st.replace('\n',' | '))
    ok(pg.locator('#liveList li[data-st="now"]').count()==1 and pg.locator('#liveList li[data-st="next"]').count()==1,'one now, one upcoming')
    ok(len(calls)==1 and 'lat=37.5446' in calls[0],'weather fetched once for first stop')
    wx=pg.inner_text('#liveWx'); ok('기상청' in wx and pg.locator('.wxc').count()>=3 and '맑음' in wx and '우산 걱정은 크지' in wx,'weather strip: '+wx.replace('\n',' ')[:80])
    ok('막차 걱정은 크지 않' in pg.inner_text('#liveTrain'),'early finish: no last-train worry')
    ok(pg.get_attribute('#liveList a','href').startswith('https://map.naver.com/p/search/') and pg.get_attribute('#liveList a','rel')=='noopener noreferrer','map link safe')
    pg.screenshot(path='/tmp/p4_live.png',full_page=True)
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # other times of day
    for h,m,exp in [(10,20,'시작 전 · 성수 카페 40분 뒤 도착'),(12,10,'이동 중 · 전시회 10분 뒤 도착'),(15,0,'오늘 데이트가 끝났어요')]:
        b,pg=mk(p,visit(),at(h,m),WX); pg.click('#liveCard [data-golive]'); pg.wait_for_timeout(300)
        ok(exp in pg.inner_text('#liveStatus'),'%02d:%02d -> %s'%(h,m,exp)); b.close()
    # rain advisory + late-night train note + midnight wrap
    b,pg=mk(p,visit(True),at(13,5),RAIN); pg.click('#liveCard [data-golive]'); pg.wait_for_timeout(600)
    ok('비 소식' in pg.inner_text('#liveWx'),'rain advisory shown')
    ok('막차' in pg.inner_text('#liveTrain') and '23:40' in pg.inner_text('#liveTrain') and '확인' in pg.inner_text('#liveTrain'),'late finish -> last-train warning: '+pg.inner_text('#liveTrain')[:60]); b.close()
    # KMA key missing / error
    b,pg=mk(p,visit(),at(11,30),{'ok':False,'reason':'kma_not_configured'}); pg.click('#liveCard [data-golive]'); pg.wait_for_timeout(500)
    ok('KMA_SERVICE_KEY' in pg.inner_text('#liveWx') and '지금 성수 카페' in pg.inner_text('#liveStatus'),'no key: friendly note, rest of live mode still works'); b.close()
    b,pg=mk(p,visit(),at(11,30),{'ok':False,'reason':'kma_error'}); pg.click('#liveCard [data-golive]'); pg.wait_for_timeout(500)
    ok('불러오지 못했어요' in pg.inner_text('#liveWx'),'weather error message'); b.close()
    # opening hours: input, validation, warning, persistence
    b,pg=mk(p,visit(),at(11,30),WX); pg.click('#tabs [data-go="cal"]'); pg.wait_for_timeout(400)
    ok(pg.locator('[data-shours]').count()==2,'hours input per stop')
    pg.fill('[data-shours="v1|0"]','12:00-21:00'); pg.keyboard.press('Tab'); pg.wait_for_timeout(300)
    ok('영업시간(12:00~21:00) 밖' in pg.inner_text('.vstops'),'warns: 11:00 arrival before opening')
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')")); ok(dc['E']['v1']['body']['stops'][0]['hours']=='12:00-21:00' and 'v1' in dc['dirty'],'hours stored + dirty')
    pg.fill('[data-shours="v1|0"]','열심히'); pg.keyboard.press('Tab'); pg.wait_for_timeout(300)
    ok('10:00-21:00' in pg.inner_text('#toast') and pg.input_value('[data-shours="v1|0"]')=='12:00-21:00','bad format rejected, value restored')
    pg.fill('[data-shours="v1|0"]','10:00-21:00'); pg.keyboard.press('Tab'); pg.wait_for_timeout(300)
    ok('밖' not in pg.inner_text('.vstops'),'no warning when open')
    pg.fill('[data-shours="v1|1"]','9:00~12:00'); pg.keyboard.press('Tab'); pg.wait_for_timeout(300)
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')")); ok(dc['E']['v1']['body']['stops'][1]['hours']=='09:00-12:00','normalised 9:00~12:00 -> 09:00-12:00')
    ok('영업시간(09:00~12:00) 밖' in pg.inner_text('.vstops'),'exhibit 12:20 after close warns')
    pg.click('[data-editv="v1"]'); pg.wait_for_timeout(400); pg.click('#saveBtn'); pg.wait_for_timeout(200); pg.click('#saveForm button[type=submit]'); pg.wait_for_timeout(300)
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')")); ok(dc['E']['v1']['body']['stops'][1]['hours']=='09:00-12:00','hours survive course edit')
    pg.click('#dayPanel [data-golive]'); pg.wait_for_timeout(500)
    ok('영업시간 10:00-21:00' in pg.inner_text('#liveList'),'hours shown in live list')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
