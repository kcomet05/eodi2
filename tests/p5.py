import pathlib, json, datetime
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).parent
html=ROOT.parent.joinpath('index.html').read_text(encoding='utf8'); mock=ROOT.joinpath('mock.js').read_text(encoding='utf8')
KST=datetime.timezone(datetime.timedelta(hours=9)); today=datetime.datetime.now(KST).date()
D=lambda n:(today+datetime.timedelta(days=n)).isoformat()
def stop(i,name,kind,lat,lng,area='성수동',cost=20000): return {'id':'s%d'%i,'name':name,'kind':kind,'area':area,'lat':lat,'lng':lng,'stay':60,'time':'%02d:00'%(11+i),'until':'%02d:00'%(12+i),'cost':cost,'note':''}
CAFE=stop(0,'성수 카페','카페',37.5446,127.0557); EXH=stop(1,'전시회','전시',37.5462,127.0612); DIN=stop(2,'파스타집','저녁',37.5470,127.0600)
def visit(date,title,st): return {'date':date,'title':title,'note':'','by':0,'tm':{'s':660,'e':1260},'stops':st}
def seed(E,code=''):
    d={'E':E,'dirty':{},'since':0}
    return "localStorage.setItem('dc_couple',JSON.stringify({names:['지우','하준'],me:0,since:'',code:'%s',dirty:false}));localStorage.setItem('dc_data',%s);"%(code,json.dumps(json.dumps(d)))
def mk(p,sd,api=None,withmock=False):
    b=p.chromium.launch(args=["--no-sandbox"]); ctx=b.new_context(viewport={"width":390,"height":844}); pg=ctx.new_page()
    pg.errs=[]; pg.reqs=[]; pg.on("pageerror",lambda e:pg.errs.append(str(e)))
    if withmock: pg.add_init_script("window.__LAB={scenario:'normal'};")
    pg.add_init_script(sd)
    if withmock: pg.add_init_script(mock)
    def route(r):
        u=r.request.url
        if api and '/api/sync' in u:
            pg.reqs.append(json.loads(r.request.post_data)); return r.fulfill(status=200,content_type='application/json',body=json.dumps(api(pg.reqs[-1],len(pg.reqs))))
        if u.startswith('http://t.local/') and '/api/' not in u: return r.fulfill(status=200,content_type='text/html',body=html)
        r.abort()
    pg.route("**/*",route); pg.goto("http://t.local/"); pg.wait_for_timeout(500); return b,pg
ok=lambda c,m:print(('PASS ' if c else 'FAIL ')+m)
def store(pg): return json.loads(pg.evaluate("localStorage.getItem('dc_data')"))
PAST={'v1':{'kind':'visit','u':1,'body':visit(D(-10),'첫 성수',[CAFE,EXH])},'v2':{'kind':'visit','u':1,'body':visit(D(-3),'다시 성수',[CAFE,DIN])},'v3':{'kind':'visit','u':1,'body':visit(D(5),'다음 데이트',[stop(0,'미래 장소','산책',37.5,127.0)])}}
with sync_playwright() as p:
    # ---- favorites / blocked ----
    b,pg=mk(p,seed(PAST)); pg.click('#tabs [data-go="cal"]'); pg.click('[data-day="%s"]'%D(-10)); pg.wait_for_timeout(300)
    ok(pg.locator('.mk').count()==4,'fav/block buttons on both stops')
    pg.click('.mk[aria-label="성수 카페 즐겨찾기"]'); pg.wait_for_timeout(200)
    pl=[v for v in store(pg)['E'].values() if v['kind']=='place']
    ok(len(pl)==1 and pl[0]['body']['mark']=='fav' and pl[0]['body']['name']=='성수 카페','favorite stored as place item')
    ok(pg.get_attribute('.mk[aria-label="성수 카페 즐겨찾기"]','aria-pressed')=='true','★ shows pressed')
    pg.click('.mk[aria-label="전시회 다시 안 가기"]'); pg.wait_for_timeout(200)
    marks=sorted(v['body']['mark'] for v in store(pg)['E'].values() if v['kind']=='place'); ok(marks==['block','fav'],'block stored: %s'%marks)
    pg.click('.mk[aria-label="전시회 다시 안 가기"]'); pg.wait_for_timeout(200)
    pl2=[v for v in store(pg)['E'].values() if v['kind']=='place' and not v['body'].get('deleted')]; ok(len(pl2)==1,'tap again removes block (tombstone)')
    ok('성수 카페' in pg.inner_text('.vstops') and '★' in pg.inner_text('.vstops'),'badge shown on favorited stop')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # ---- route screen ----
    E=dict(PAST); b,pg=mk(p,seed(E)); pg.click('#tabs [data-go="route"]'); pg.wait_for_timeout(300)
    st=pg.inner_text('#rtStats'); ok('2\n함께한 데이트' in st and '3\n다녀간 곳' in st,'stats count only past visits, unique places: '+st.replace('\n',' | ')[:90])
    ok('80,000원' in st,'spend total is 80,000원 (4 stops x 20,000)')
    ok(pg.locator('#rtLine .c.x').count()==2,'repeat visit (성수 카페) drawn as 환승역 twice: %d'%pg.locator('#rtLine .c.x').count())
    ok('미래 장소' not in pg.inner_text('#rtLine'),'future visit not on the line')
    ok('성수동 4번' in st,'top area: '+st.split('자주')[-1][:20])
    pg.screenshot(path='/tmp/p5_route.png',full_page=True); ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # ---- photos ----
    b,pg=mk(p,seed(PAST)); pg.click('#tabs [data-go="cal"]'); pg.click('[data-day="%s"]'%D(-10)); pg.wait_for_timeout(300)
    pg.evaluate("""()=>{const c=document.createElement('canvas');c.width=1600;c.height=1200;const x=c.getContext('2d');const im=x.createImageData(1600,1200);for(let i=0;i<im.data.length;i++)im.data[i]=(i%4==3)?255:Math.random()*255;x.putImageData(im,0,0);
      return new Promise(r=>c.toBlob(bl=>{const f=new File([bl],'a.jpg',{type:'image/jpeg'});const dt=new DataTransfer();dt.items.add(f);const i=document.getElementById('photoIn');i.setAttribute('data-v','v1');i.files=dt.files;i.dispatchEvent(new Event('change',{bubbles:true}));r(bl.size)},'image/jpeg',.95));}""")
    pg.wait_for_timeout(1200)
    ph=[v for v in store(pg)['E'].values() if v['kind']=='photo']
    ok(len(ph)==1 and ph[0]['body']['v']=='v1' and ph[0]['body']['t'].startswith('data:image/jpeg;base64,') and len(ph[0]['body']['t'])<24000,'noisy 1600px photo compressed to %d chars'%(len(ph[0]['body']['t']) if ph else -1))
    ok(len(json.dumps(ph[0]['body']))<30000,'photo item fits the 30KB sync limit')
    ok(pg.locator('.pth img').count()==1 and '1/12' in pg.inner_text('#dayPanel'),'thumbnail strip + counter')
    pg.click('.pth'); pg.wait_for_timeout(200); ok(pg.evaluate("document.getElementById('photoSheet').open"),'viewer opens')
    pg.click('#phDel'); ok('정말' in pg.inner_text('#phDel'),'delete is armed first'); pg.click('#phDel'); pg.wait_for_timeout(300)
    ok(pg.locator('.pth').count()==0 and any(v['kind']=='photo' and v['body'].get('deleted') for v in store(pg)['E'].values()),'deleted as tombstone')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    evil=dict(PAST); evil['phx']={'kind':'photo','u':2,'body':{'v':'v1','t':'data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=','at':1}}; evil['phy']={'kind':'photo','u':2,'body':{'v':'v1','t':'javascript:alert(1)','at':2}}
    b,pg=mk(p,seed(evil)); pg.click('#tabs [data-go="cal"]'); pg.click('[data-day="%s"]'%D(-10)); pg.wait_for_timeout(300)
    ok(pg.locator('.pth').count()==0,'non-JPEG data URLs from sync are never rendered'); b.close()
    # ---- anniversary suggestion from favorites ----
    F={'pa':{'kind':'place','u':1,'body':{'name':'성수 카페','kind':'카페','area':'성수동','lat':37.5446,'lng':127.0557,'mark':'fav'}},
       'pb':{'kind':'place','u':1,'body':{'name':'파스타집','kind':'저녁','area':'성수동','lat':37.5470,'lng':127.0600,'mark':'fav'}},
       'pc':{'kind':'place','u':1,'body':{'name':'멀리 있는 곳','kind':'산책','area':'부산','lat':35.15,'lng':129.06,'mark':'fav'}},
       'sp':{'kind':'special','u':1,'body':{'date':D(10),'title':'우리 기념일','yearly':False}}}
    b,pg=mk(p,seed(F)); ok(pg.is_visible('#annSug') and '우리 기념일' in pg.inner_text('#annSug') and 'D-10' in pg.inner_text('#annSug'),'suggestion card for upcoming special')
    txt=pg.inner_text('#annSug'); ok('성수 카페 → 파스타집' in txt and '멀리' not in txt,'nearby favorites only, in meal order')
    pg.click('[data-annuse]'); pg.wait_for_timeout(600)
    ok(pg.locator('#stopList .stop').count()==2 and '우리 기념일 데이트' in pg.inner_text('#planTitle'),'opens planner with the 2 stops')
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    F1={k:v for k,v in F.items() if k!='pb'}; b,pg=mk(p,seed(F1)); ok(not pg.is_visible('#annSug'),'no suggestion with fewer than 2 nearby favorites'); b.close()
    F2=dict(F); F2['sp2']={'kind':'visit','u':1,'body':visit(D(10),'이미 계획',[CAFE])}; b,pg=mk(p,seed(F2)); ok(not pg.is_visible('#annSug'),'no suggestion when that day already has a date'); b.close()
    # ---- blocked places leave nearby recommendations ----
    b,pg=mk(p,seed({}),withmock=True); pg.click('#home [data-go="plan"]'); pg.wait_for_timeout(300)
    pg.click('#q'); pg.keyboard.type('성수 카페'); pg.wait_for_timeout(900); pg.click('.sgi >> nth=0'); pg.wait_for_timeout(1500)
    n1=pg.eval_on_selector_all('.nbi b','e=>e.map(x=>x.textContent)'); ok(len(n1)>=2,'nearby list present: %s'%n1[:3])
    pg.click('[data-addnear] >> nth=0'); pg.wait_for_timeout(1200)
    names=pg.eval_on_selector_all('#stopList .stop .fly b','e=>e.map(x=>x.textContent)'); added=names[1]
    pg.click('#stopList .stop >> nth=1 >> .mk >> nth=1'); pg.wait_for_timeout(200)
    ok(any(v['kind']=='place' and v['body']['mark']=='block' for v in store(pg)['E'].values()),'blocked from the planner list')
    pg.click('[data-del] >> nth=1'); pg.wait_for_timeout(1200)
    n2=pg.eval_on_selector_all('.nbi b','e=>e.map(x=>x.textContent)')
    ok(added not in ' '.join(n2) and len(n2)>=1,'blocked place "%s" no longer suggested nearby'%added)
    ok(not pg.errs,'no errors %s'%pg.errs); b.close()
    # ---- paged sync pulls everything ----
    def api(req,n):
        if n==1: return {'ok':True,'now':2000000,'more':True,'last':1000,'items':[{'id':'pla','kind':'place','u':900,'body':{'name':'A','kind':'카페','area':'','lat':37.5,'lng':127.0,'mark':'fav'}}]}
        return {'ok':True,'now':2000000,'items':[{'id':'plb','kind':'place','u':1100,'body':{'name':'B','kind':'카페','area':'','lat':37.6,'lng':127.1,'mark':'fav'}}]}
    b,pg=mk(p,seed({},'ABCD2345'),api=api); pg.wait_for_timeout(1500)
    ok(len(pg.reqs)>=2 and pg.reqs[1]['since']>=999,'second request continues from last: since=%s'%[r['since'] for r in pg.reqs])
    E=store(pg)['E']; ok('pla' in E and 'plb' in E,'both pages merged locally')
    ok(store(pg)['since']==2000000-600000,'cursor settles at now-10min after last page: %s'%store(pg)['since']); b.close()
