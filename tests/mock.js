(function(){
var L=window.__LAB||{scenario:'normal'},S=L.scenario;
window.addEventListener('error',function(e){try{parent.postMessage({lab:'err',msg:String(e.message)},'*');}catch(x){}});
var realFetch=window.fetch?window.fetch.bind(window):null;
var seed=1;function rnd(){seed=(seed*16807)%2147483647;return (seed-1)/2147483646;}
function pick(a){return a[Math.floor(rnd()*a.length)];}
var SEOUL={'성수동':[37.5446,127.056],'연남동':[37.5622,126.9246],'한남동':[37.534,127.0026],'익선동':[37.5744,126.99],'망원동':[37.556,126.9017],'서촌':[37.5805,126.9712],'을지로':[37.5661,126.9912],'송리단길':[37.51,127.107],'북촌':[37.5826,126.9835],'홍대':[37.5563,126.9236],'합정':[37.5495,126.9139],'이태원':[37.5345,126.9946],'여의도':[37.5219,126.9245],'압구정로데오':[37.5274,127.039],'가로수길':[37.5203,127.023],'용리단길':[37.531,126.97],'삼청동':[37.585,126.982],'문래동':[37.518,126.895],'대학로':[37.582,127.002],'상수동':[37.548,126.923],'건대':[37.54,127.07],'청담동':[37.524,127.047],'신촌':[37.5559,126.9368],'성북동':[37.593,126.993]};
var CITY={'부산':['광안리',35.1532,129.1186],'대구':['동성로',35.869,128.594],'대전':['은행동',36.3285,127.4277],'광주':['동명동',35.1468,126.9206],'인천':['송도',37.3943,126.639],'수원':['행궁동',37.2819,127.0137],'전주':['객리단길',35.815,127.153],'강릉':['안목해변',37.7722,128.9475],'경주':['황리단길',35.8383,129.2105],'여수':['낭만포차',34.7395,127.7454],'제주':['애월',33.4628,126.3104]};
var NAMES={
'카페':['{a} 로스터리','온기 커피 {a}점','{a} 디저트 하우스','창가 베이커리','{a} 티 하우스'],
'점심':['{a} 브런치 키친','국수당 {a}','작은 파스타집','{a} 한식 밥상'],
'저녁':['{a} 화로구이','오늘의 비스트로','{a} 이자카야','골목 파스타'],
'술':['{a} 와인바','루프탑 바 별','{a} 하이볼집'],
'산책':['{a} 골목길','{a} 공원','물길 산책로','{a} 전망 언덕'],
'전시':['{a} 갤러리','작은 미술관 {a}','{a} 팝업 전시관'],
'야경':['{a} 전망대','다리 위 야경 포인트'],
'쇼핑':['{a} 소품샵','{a} 편집숍','동네 책방 {a}','{a} 팝업스토어']};
var CAT={'카페':'카페,디저트>카페','점심':'음식점>한식','저녁':'음식점>양식','술':'술집>와인바','산책':'여행,명소>공원','전시':'문화,예술>갤러리','야경':'여행,명소>전망대','쇼핑':'생활,편의>소품'};
var LONG='오래된 한옥을 개조한 감성 가득한 와인 비스트로 본점';
var STAY={'카페':60,'점심':70,'저녁':90,'산책':60,'전시':80,'야경':50,'쇼핑':60,'술':70};
var ACT={all:['산책','전시','쇼핑'],indoor:['전시','쇼핑','전시'],night:['산책','쇼핑','야경'],budget:['산책','쇼핑','전시'],food:['쇼핑','산책'],walk:['산책','산책','전시']};
var TITLE={all:'데이트 코스',indoor:'실내 데이트',night:'야경 데이트',budget:'가성비 데이트',food:'맛집 데이트',walk:'산책 데이트'};
function slots(s,e,mood){var out=[],t=s,lunch=0,dinner=0,last='',ai=0,cafes=0,acts=ACT[mood]||ACT.all;while(out.length<7){var k;if(!lunch&&t>=660&&t<840)k='점심';else if(!dinner&&t>=1020&&t<1230)k='저녁';else if(t>=1230)k=last==='술'?'야경':'술';else if((last===''||last==='점심'||last==='저녁')&&cafes<2){k='카페';cafes++;}else{k=acts[ai++%acts.length];if(k===last)k=acts[ai++%acts.length];}var st=STAY[k]||60;if(out.length>=2&&t+st>e+20)break;out.push({kind:k,stay:st});if(k==='점심')lunch=1;if(k==='저녁')dinner=1;last=k;t+=st+15;if(t>=e&&out.length>=2)break;}return out;}
function km(a,b){var r=Math.PI/180,x=Math.sin((b.lat-a.lat)*r/2)*Math.sin((b.lat-a.lat)*r/2)+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin((b.lng-a.lng)*r/2)*Math.sin((b.lng-a.lng)*r/2);return 12742*Math.asin(Math.sqrt(x));}
function fmt(m){return ('0'+Math.floor(m/60)%24).slice(-2)+':'+('0'+m%60).slice(-2);}
function short(a){return a.replace(/(동|길)$/,'').replace(/로데오$/,'');}
function err(reason){return {source:'error',reason:reason};}
function place(name,kind,c,spread,i){var d=spread?0.03+rnd()*0.02:0.002+rnd()*0.006,ang=rnd()*6.28;var nm=S==='long'&&i%2===0?short(name)+' '+LONG:pick(NAMES[kind]||NAMES['쇼핑']).replace('{a}',short(name));return {name:nm,category:CAT[kind]||'',address:'테스트 주소',lat:c[0]+Math.sin(ang)*d,lng:c[1]+Math.cos(ang)*d,link:''};}
function recommend(p){
if(S==='notfound'&&p.get('place'))return err('place_not_found');
seed=(+p.get('seed')||7)%2147483646||7;
var plc=p.get('place')||'',area=p.get('area')||'any',mood=p.get('mood')||'all',avoid=(p.get('avoid')||'').split(','),name,c,mode;
if(plc){var city=CITY[plc.replace(/\s+/g,'')];if(city){name=plc+' '+city[0];c=[city[1],city[2]];mode='city';}else{name=plc;c=[37.55,126.99];mode='place';}}
else if(SEOUL[area]){name=area;c=SEOUL[area];mode='area';}
else{var pool=Object.keys(SEOUL).slice(0,12).filter(function(a){return avoid.indexOf(a)<0;});name=pick(pool);c=SEOUL[name];mode='hot';}
var spread=S==='spread';
var s=+p.get('start')||840,e=+p.get('end')||1260,t=s;
var stops=slots(s,e,mood).map(function(sl,i){var pl=place(name,sl.kind,c,spread,i);pl.kind=sl.kind;pl.stay=sl.stay;pl.tip='';pl.hot=rnd()<.35;pl.buzz={recent:Math.floor(rnd()*28),latest:'2026101'+Math.floor(rnd()*6)};return pl;});
stops.forEach(function(x,i){if(i){var d=km(stops[i-1],x)*1.3,w=Math.max(1,Math.round(d/4.5*60));x.travelMode=w<=20?'walk':'transit';x.travelMin=w<=20?w:Math.round(8+d/20*60);t+=x.travelMin;}x.time=fmt(t);t+=x.stay;x.until=fmt(t);});
var trending=[0,1,2].map(function(i){var k=pick(['카페','저녁','쇼핑']);var pl=place(name,k,c,spread,i+10);pl.kind=k;pl.buzz={recent:30-i*6,latest:'20261016'};return pl;});
var keys=Object.keys(SEOUL);
return {source:'live',mood:mood,mode:mode,place:plc,title:name+' '+(TITLE[mood]||'데이트 코스'),blurb:fmt(s)+'~'+fmt(e)+' · '+stops.length+'곳 · '+(mode==='hot'?'요즘 검색량이 오르는 동네예요':mode==='area'?'고른 동네':'입력한 지역 주변이에요')+'. 리뷰 수와 최근 블로그 후기로 인기를 따져 골랐어요.',
 window:{s:s,e:e},area:{name:name,heat:mode==='place'?null:Math.round(55+rnd()*45),trend:rnd()<.5?'rising':'steady'},stops:stops,trending:trending,
 ranking:mode==='place'?[]:[0,1,2,3,4].map(function(i){return {name:mode==='city'?name.split(' ')[0]+' '+['광안리','서면','해운대','전포카페거리','영도'][i]:keys[(i*5)%keys.length],heat:100-i*14,trend:i%2?'steady':'rising'};}),generatedAt:new Date().toISOString()};
}
function search(p){
var q=(p.get('q')||'').trim();if(!q)return {source:'live',items:[]};
seed=q.length*97+3;var c=[37.556,126.92];Object.keys(CITY).forEach(function(k){if(q.indexOf(k)>=0)c=[CITY[k][1],CITY[k][2]];});Object.keys(SEOUL).forEach(function(k){if(q.indexOf(short(k))>=0)c=SEOUL[k];});
var kinds=['카페','저녁','산책','전시','쇼핑','카페'];
return {source:'live',items:kinds.map(function(k,i){var pl=place(q.split(' ')[0],k,c,S==='spread',i);if(i===0&&S!=='long')pl.name=q+' 본점';return pl;})};
}
function nearby(p){
var c=[+p.get('lat'),+p.get('lng')],nm=p.get('area')||p.get('name')||'근처';seed=Math.round(c[0]*1000);
var kinds=['카페','저녁','산책','전시','쇼핑','카페','저녁','산책'];
return {source:'live',items:kinds.map(function(k,i){var pl=place(nm,k,c,false,i+3);pl.kind=k;return pl;})};
}
function health(){
var bad=S==='naver401';
return {env:{keyId:true,keySecret:true},checks:['장소 검색 (API Hub)','장소 검색 (네이버 개발자센터)','블로그 검색 (API Hub)','블로그 검색 (네이버 개발자센터)','검색어 트렌드 (API Hub)'].map(function(a){return {api:a,ok:!bad,status:bad?401:200,detail:bad?'Authentication failed':''};})};
}
function route(u){
var p=u.searchParams,path=u.pathname;
if(path==='/api/health')return health();
if(S==='naver401')return err(path==='/api/recommend'?'local hub 401 {"errorMessage":"Authentication failed"}':'local classic 401 Not Exist Client ID');
if(path==='/api/recommend')return recommend(p);
if(path==='/api/search')return search(p);
if(path==='/api/nearby')return nearby(p);
return err('unknown_route');
}
window.fetch=function(input,opt){
var u;try{u=new URL(String(input),'https://lab.test/');}catch(e){u=null;}
if(!u||u.pathname.indexOf('/api/')!==0)return realFetch?realFetch(input,opt):Promise.reject(new Error('blocked'));
var body=route(u),wait=S==='slow'?3500:180+Math.random()*220;
return new Promise(function(res){setTimeout(function(){res(new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}}));},wait);});
};
})();
