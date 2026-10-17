import pathlib, json, datetime, base64
from playwright.sync_api import sync_playwright
html=pathlib.Path(__file__).parent.parent.joinpath('index.html').read_text(encoding='utf8')
today=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=9)).date().isoformat()
VISIT={'date':today,'title':'성수 데이트','note':'','by':0,'tm':{'s':660,'e':1260},'stops':[
 {'id':'a1','name':'성수 카페','kind':'카페','area':'성수동','lat':37.5446,'lng':127.0557,'stay':60,'time':'11:00','until':'12:00','cost':15000,'note':''},
 {'id':'a2','name':'전시회','kind':'전시','area':'성수동','lat':37.5462,'lng':127.0612,'stay':80,'time':'12:20','until':'13:40','cost':30000,'note':''}]}
def seed(me,data=None):
    d=data or {'E':{'v1':{'kind':'visit','u':1,'body':VISIT}},'dirty':{},'since':0}
    return "localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:%d,since:'',code:'',dirty:false}));localStorage.setItem('dc_data',%s);"%(me,json.dumps(json.dumps(d)))
def mk(p,sd,url="http://t.local/"):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":390,"height":844}); ctx.grant_permissions([]); pg=ctx.new_page()
    pg.errs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    pg.add_init_script("window.__shared=null;")
    if sd: pg.add_init_script(sd)
    def route(r):
        u=r.request.url
        if u.startswith('http://t.local/'): return r.fulfill(status=200,content_type='text/html',body=html)
        r.abort()
    pg.route("**/*",route); pg.goto(url); pg.wait_for_timeout(500); return b,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
with sync_playwright() as p:
    # ---- voting ----
    b,pg=mk(p,seed(0)); pg.click('#tabs [data-go="cal"]'); pg.wait_for_timeout(400)
    ok(pg.locator('.vbtn').count()==4,'two vote buttons per stop: %d'%pg.locator('.vbtn').count())
    pg.click('[data-vote="v1|0|1"]'); pg.wait_for_timeout(200)
    ok(pg.get_attribute('[data-vote="v1|0|1"]','aria-pressed')=='true','♥ pressed')
    pg.click('[data-vote="v1|0|-1"]'); pg.wait_for_timeout(200)
    ok(pg.get_attribute('[data-vote="v1|0|1"]','aria-pressed')=='false' and pg.get_attribute('[data-vote="v1|0|-1"]','aria-pressed')=='true','switch to ✕')
    pg.click('[data-vote="v1|0|-1"]'); pg.wait_for_timeout(200)
    ok(pg.get_attribute('[data-vote="v1|0|-1"]','aria-pressed')=='false','tap again clears')
    pg.click('[data-vote="v1|1|1"]'); pg.wait_for_timeout(200)
    dc=json.loads(pg.evaluate("localStorage.getItem('dc_data')"))
    ok(dc['E']['v1']['body']['stops'][1]['votes']=={'0':1} and not dc['E']['v1']['body']['stops'][0]['votes'],'votes stored per person per stop: %s'%dc['E']['v1']['body']['stops'][1].get('votes'))
    ok(dc['E']['v1']['u']>1 and 'v1' in dc['dirty'],'vote marks visit dirty for sync')
    ok(pg.evaluate("document.activeElement.getAttribute('data-vote')")=='v1|1|1','focus kept on vote button')
    # edit keeps votes
    pg.click('[data-editv="v1"]'); pg.wait_for_timeout(400); pg.click('#saveBtn'); pg.wait_for_timeout(200); pg.click('#saveForm button[type=submit]'); pg.wait_for_timeout(300)
    dc2=json.loads(pg.evaluate("localStorage.getItem('dc_data')"))
    ok(dc2['E']['v1']['body']['stops'][1]['votes']=={'0':1},'votes survive course edit + re-save')
    ok(not pg.errs,'no page errors %s'%pg.errs); b.close()
    # partner (me=1) sees the other vote and votes independently
    b,pg=mk(p,seed(1,dc2)); pg.click('#tabs [data-go="cal"]'); pg.wait_for_timeout(400)
    ok('지우 ♥' in pg.inner_text('.vstops'),'partner sees 지우 ♥')
    pg.click('[data-vote="v1|1|-1"]'); pg.wait_for_timeout(200); pg.screenshot(path='/tmp/p3_votes.png',full_page=True)
    dc3=json.loads(pg.evaluate("localStorage.getItem('dc_data')"))
    ok(dc3['E']['v1']['body']['stops'][1]['votes']=={'0':1,'1':-1},'both votes kept: %s'%dc3['E']['v1']['body']['stops'][1]['votes'])
    # ---- share link ----
    pg.evaluate("window.prompt=function(m,v){window.__shared=v;return null;}")
    pg.click('[data-sharev="v1"]'); pg.wait_for_timeout(300)
    link=pg.evaluate("window.__shared")
    ok(link and '/#c=' in link,'share link built: %s'%(link or '')[:60])
    ok('ABCD' not in link and 'v1' not in link,'link carries no couple code or visit id')
    b.close()
    h=link.split('t.local/')[1]
    b,pg=mk(p,None,"http://t.local/"+h)
    pg.wait_for_timeout(300)
    ok(pg.evaluate("document.getElementById('shareSheet').open"),'shared sheet opens for a stranger')
    ok(pg.inner_text('#shT')=='성수 데이트' and pg.locator('#shList li').count()==2,'shows title + 2 stops')
    ok(pg.evaluate("location.hash")=='','hash cleared after reading')
    ok('지우' not in pg.inner_text('#shareSheet') and 'v1' not in pg.inner_text('#shareSheet'),'no couple data in shared view')
    b.close()
    b,pg=mk(p,seed(0,{'E':{},'dirty':{},'since':0}),"http://t.local/"+h)
    pg.click('#shUse'); pg.wait_for_timeout(500)
    ok(pg.locator('#stopList .stop').count()==2 and '성수 데이트' in pg.inner_text('#planTitle'),'import loads 2 stops into planner')
    ok(not pg.errs,'no page errors %s'%pg.errs); b.close()
    # malicious / broken links
    def enc(o): return base64.urlsafe_b64encode(json.dumps(o,ensure_ascii=False).encode()).decode().rstrip('=')
    bad=[enc({'t':'x','s':[['<img src=x onerror=alert(1)>','카페','',37.5,127.0,60,0]]}),
         enc({'t':'x','s':[['장소','해킹',"",37.5,127.0,60,0]]}),
         enc({'t':'x','s':[['장소','카페','',10,10,60,0]]}),'!!!notbase64','e30']
    for i,x in enumerate(bad):
        b,pg=mk(p,seed(0),"http://t.local/#c="+x); pg.wait_for_timeout(300)
        opened=pg.evaluate("document.getElementById('shareSheet').open")
        if i==0:
            ok(opened and pg.locator('#shList img').count()==0 and '<img' in pg.inner_text('#shList'),'html in names is escaped')
        else: ok(not opened,'invalid link %d ignored'%i)
        ok(not pg.errs,'no errors on bad link %d'%i); b.close()
