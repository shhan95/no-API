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
async function loadJson(path, fallback) {
  try {
    const r = await fetch(path, { cache: "no-store" });
    if (!r.ok) throw new Error(`${path} ${r.status}`);
    return await r.json();
  } catch (e) {
    console.warn("loadJson fail:", path, e);
    return fallback;
  }
}

function lawgoSearchUrl(q) {
  // API 없이도 “법제처 웹 검색”으로 연결하는 안전한 링크
  const base = "https://www.law.go.kr/LSO/openApi/ocuAskUpdateSubmit.do"; // (이건 신청페이지라서)
  // 실제 검색은 아래가 더 낫습니다(국가법령정보센터 검색):
  return `https://www.law.go.kr/LSW/admRulLsInfoP.do?searchType=0&searchText=${encodeURIComponent(q)}`;
}

function normalizeItems(stdJson, type) {
  const items = (stdJson && stdJson.items) ? stdJson.items : [];
  return items.map(it => {
    const code = (it.code || "").trim();
    const title = (it.title || "").trim();
    // 파일에 url이 있으면 그대로, 없으면 법제처 검색으로 대체
    const url = (it.url && String(it.url).trim()) ? it.url : lawgoSearchUrl(`${code} ${title}`);
    return { type, code, title, url };
  }).filter(x => x.code);
}

function renderBanners(all, filterType, q) {
  const grid = document.getElementById("bannerGrid");
  if (!grid) return;

  const keyword = (q || "").trim().toLowerCase();

  const rows = all.filter(x => {
    if (filterType !== "ALL" && x.type !== filterType) return false;
    if (!keyword) return true;
    return (
      (x.code || "").toLowerCase().includes(keyword) ||
      (x.title || "").toLowerCase().includes(keyword)
    );
  });

  grid.innerHTML = rows.map(x => `
    <div class="banner-card">
      <div class="banner-top">
        <div>
          <div class="banner-code">${x.code}</div>
          <div class="banner-title">${x.title || ""}</div>
        </div>
        <div class="badge">${x.type}</div>
      </div>
      <div class="banner-actions">
        <a href="${x.url}" target="_blank" rel="noopener">법제처 원문/검색</a>
        <a href="#"
           onclick="navigator.clipboard.writeText('${x.url.replace(/'/g, "\\'")}'); alert('링크 복사됨'); return false;">
           링크복사
        </a>
      </div>
    </div>
  `).join("");

  if (rows.length === 0) {
    grid.innerHTML = `<div style="opacity:.8; padding:16px;">검색 결과가 없습니다.</div>`;
  }
}

async function initBannerSection() {
  const nfpc = await loadJson("standards_nfpc.json", { items: [] });
  const nftc = await loadJson("standards_nftc.json", { items: [] });

  const all = [
    ...normalizeItems(nfpc, "NFPC"),
    ...normalizeItems(nftc, "NFTC")
  ];

  let filterType = "ALL";

  const qEl = document.getElementById("bannerQ");
  const btnAll = document.getElementById("btnAll");
  const btnNFPC = document.getElementById("btnNFPC");
  const btnNFTC = document.getElementById("btnNFTC");

  function setActive(btn) {
    [btnAll, btnNFPC, btnNFTC].forEach(b => b && b.classList.remove("active"));
    btn && btn.classList.add("active");
  }

  btnAll?.addEventListener("click", () => {
    filterType = "ALL"; setActive(btnAll);
    renderBanners(all, filterType, qEl?.value);
  });
  btnNFPC?.addEventListener("click", () => {
    filterType = "NFPC"; setActive(btnNFPC);
    renderBanners(all, filterType, qEl?.value);
  });
  btnNFTC?.addEventListener("click", () => {
    filterType = "NFTC"; setActive(btnNFTC);
    renderBanners(all, filterType, qEl?.value);
  });

  qEl?.addEventListener("input", () => {
    renderBanners(all, filterType, qEl.value);
  });

  renderBanners(all, filterType, qEl?.value);
}

document.addEventListener("DOMContentLoaded", () => {
  initBannerSection();
});
