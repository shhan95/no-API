async function loadJSON(path){
  const r = await fetch(path, { cache: "no-store" });
  if(!r.ok) throw new Error("Failed to load " + path);
  return await r.json();
}
function esc(s){ return (s||"").replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])); }

function renderBanners(items, query){
  const box = document.getElementById("banners");
  box.innerHTML = "";
  const q = (query||"").trim().toLowerCase();
  const map = new Map();
  for(const it of items){
    const code = it.code || "";
    if(!code) continue;
    if(q && !(code.toLowerCase().includes(q) || (it.title||"").toLowerCase().includes(q))) continue;
    if(!map.has(code)) map.set(code, it);
  }
  const arr = Array.from(map.values()).sort((a,b)=> (a.code||"").localeCompare(b.code||""));
  if(arr.length === 0){
    box.innerHTML = "<div class='hint'>표시할 배너가 없습니다(아직 수집이 안 되었거나, 필터 조건에 없음)</div>";
    return;
  }
  for(const it of arr){
    const a = document.createElement("a");
    a.className = "banner";
    a.href = it.url || "#";
    a.target = "_blank";
    a.innerHTML = `<span class="badge">${esc(it.code)}</span><span>${esc(it.title)}</span>`;
    box.appendChild(a);
  }
}

function renderLogs(records, query){
  const box = document.getElementById("logs");
  box.innerHTML = "";
  const q = (query||"").trim().toLowerCase();
  for(const r of records){
    const text = JSON.stringify(r).toLowerCase();
    if(q && !text.includes(q)) continue;
    const div = document.createElement("div");
    div.className = "log";
    const pill = r.result === "변경 없음" ? "변경 없음" : "변경 있음";
    const rep = r.report ? `<a href="${esc(r.report)}" target="_blank">리포트</a>` : "";
    div.innerHTML = `
      <div class="top">
        <div><b>${esc(r.date)}</b> <span class="pill">${esc(pill)}</span> — ${esc(r.summary||"")}</div>
        <div class="noprint">${rep}</div>
      </div>
      <div style="margin-top:8px;color:#a9b7df;font-size:13px">
        추가 ${r.added?.length||0} / 제외 ${r.removed?.length||0}
      </div>
    `;
    box.appendChild(div);
  }
}

(async function init(){
  document.getElementById("btnPrint").addEventListener("click", ()=>window.print());
  const qInput = document.getElementById("q");
  let data;
  try{
    data = await loadJSON("data.json");
  }catch(e){
    document.getElementById("logs").innerHTML = `<div class="hint">data.json을 불러오지 못했습니다. (아직 첫 실행 전일 수 있음)</div>`;
    return;
  }
  const snapshot = await loadJSON("snapshot.json").catch(()=>({items:[]}));
  const rerender = ()=>{
    const q = qInput.value || "";
    renderBanners(snapshot.items || [], q);
    renderLogs(data.records || [], q);
  };
  qInput.addEventListener("input", rerender);
  rerender();
})();
