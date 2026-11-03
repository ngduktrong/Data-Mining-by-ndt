'use strict';
const $=id=>document.getElementById(id);
let heroes=[],byId={},action='pick',state={own_picks:[],enemy_picks:[],banned:[]},lastResult=null,revision=0,busy=false;
const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/đ/g,'d');
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function message(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function invalidate(){revision++;lastResult=null;$('download').hidden=true;$('recommendations').replaceChildren(el('div','Đội hình đã thay đổi. Bấm “Xem gợi ý” để cập nhật.','empty'));message('Sẵn sàng nhận gợi ý cho lựa chọn hiện tại.');}
function render(){
  $('pick').classList.toggle('active',action==='pick');$('ban').classList.toggle('active',action==='ban');
  $('pick').setAttribute('aria-pressed',action==='pick');$('ban').setAttribute('aria-pressed',action==='ban');
  $('method').textContent=action==='pick'?'COSINE':'BAN POPULARITY';
  const targets=[['own_picks','own-picks','own-count',action==='pick'?4:5],['enemy_picks','enemy-picks','enemy-count',5],['banned','banned-picks','banned-count',null]];
  targets.forEach(([key,id,count,max])=>{
    $(count).textContent=max?`${state[key].length}/${max} tướng`:`${state[key].length} tướng`;
    $(id).replaceChildren();state[key].forEach(h=>{const b=el('button',`${byId[h].hero_name} ×`,'chip');b.title='Bỏ '+byId[h].hero_name;b.onclick=()=>{state[key]=state[key].filter(x=>x!==h);invalidate();render();};$(id).append(b);});
    if(!state[key].length)$(id).append(el('span','Chưa có tướng','placeholder'));
  });
  const used=new Set(Object.values(state).flat()),query=norm($('search').value),filtered=heroes.filter(h=>norm(h.hero_name).includes(query));
  $('catalog-count').textContent=`${filtered.length} tướng`;$('catalog').replaceChildren();
  filtered.forEach(h=>{const b=el('button',undefined,'hero');b.append(el('span',h.hero_name.slice(0,2).toUpperCase(),'avatar'),el('span',h.hero_name));b.disabled=used.has(h.hero_id);b.title=used.has(h.hero_id)?'Đã chọn hoặc cấm':`Thêm ${h.hero_name}`;b.onclick=()=>{
    const key=$('destination').value,max=key==='own_picks'?(action==='pick'?4:5):key==='enemy_picks'?5:heroes.length;
    if(state[key].length>=max){message(`Danh sách này đã đủ ${max} tướng. Hãy bỏ một tướng trước.`,true);return;}
    state[key].push(h.hero_id);invalidate();render();};$('catalog').append(b);
  });
  if(!filtered.length)$('catalog').append(el('p','Không tìm thấy tướng.'));
}
function showResult(data){
  const box=$('recommendations');box.replaceChildren();
  data.recommendations.forEach(r=>{
    const card=el('article',undefined,'card'),head=el('div',undefined,'card-head');
    const score=el('div',r.score.toFixed(4),'score');score.append(el('small','điểm mô hình'));
    head.append(el('span',String(r.rank).padStart(2,'0'),'rank'),el('h3',r.hero_name),score);card.append(head);
    if(data.action==='pick'){
      card.append(el('p',`Xuất hiện trong ${r.evidence.train_lineup_count} đội hình train.`));
      const details=el('details'),list=el('ul');details.append(el('summary','Xem tương đồng với đồng đội'));
      r.evidence.allies.forEach(e=>list.append(el('li',`${byId[e.ally_hero_id]?.hero_name||e.ally_hero_id}: ${e.cosine.toFixed(4)}`)));
      if(!r.evidence.allies.length)list.append(el('li','Chưa có đồng đội: các điểm bằng 0, thứ tự theo độ phổ biến.'));
      details.append(list);card.append(details);
    }else card.append(el('p',`Bị cấm trong ${r.evidence.train_ban_count}/${r.evidence.train_games} ván train.`));
    box.append(card);
  });
  if(!data.returned_count)box.append(el('div','Không còn tướng ứng viên. Hãy kiểm tra các tướng đã chọn và cấm.','empty'));
  message(`Đã trả ${data.returned_count}/${data.requested_k} gợi ý.${data.popularity_tiebreak_for_all_zero_scores?' Tất cả điểm bằng 0; xếp theo độ phổ biến.':''}`);
  $('download').hidden=false;
}
$('pick').onclick=()=>{if(state.own_picks.length>4){message('Để gợi ý pick tiếp theo, hãy bỏ ít nhất một tướng khỏi đội đã đủ 5.',true);return;}action='pick';invalidate();render();};
$('ban').onclick=()=>{action='ban';invalidate();render();};
$('search').oninput=render;$('k').onchange=invalidate;
$('reset').onclick=()=>{state={own_picks:[],enemy_picks:[],banned:[]};$('search').value='';invalidate();render();};
$('sample').onclick=()=>{
  function ids(names){return names.map(n=>heroes.find(h=>h.hero_name===n)?.hero_id).filter(Boolean);}
  state={own_picks:ids(['Iggy','Capheny']),enemy_picks:ids(["Y'bneth",'Yena']),banned:ids(['Sinestrea'])};invalidate();render();message('Đã nạp ví dụ minh họa. Bấm “Xem gợi ý” để chạy mô hình.');
};
$('recommend').onclick=async()=>{
  if(busy)return;const current=revision;busy=true;$('recommend').disabled=true;$('recommend').textContent='Đang tính…';message('Đang chạy mô hình trên máy bạn…');
  try{
    const response=await fetch('/api/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...state,k:Number($('k').value)})});
    const data=await response.json();if(!response.ok)throw new Error(data.error||'Không thể lấy gợi ý.');
    if(current!==revision)return;lastResult=data;showResult(data);
  }catch(e){if(current===revision)message('Không lấy được kết quả: '+e.message,true);}
  finally{busy=false;$('recommend').disabled=!heroes.length;$('recommend').textContent='Xem gợi ý →';}
};
$('download').onclick=()=>{if(!lastResult)return;const url=URL.createObjectURL(new Blob([JSON.stringify(lastResult,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=`liqi_${lastResult.action}_result.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
(async()=>{try{const response=await fetch('/api/heroes');if(!response.ok)throw new Error('Không tải được danh mục');heroes=await response.json();byId=Object.fromEntries(heroes.map(h=>[h.hero_id,h]));$('connection').textContent='● Mô hình sẵn sàng · chạy cục bộ';$('recommend').disabled=false;render();}catch(e){$('connection').textContent='Không kết nối được';message('Hãy chạy python app.py rồi mở http://127.0.0.1:8000. '+e.message,true);}})();
