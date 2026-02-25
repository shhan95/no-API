import os, json, re, hashlib, time
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

UA = "Mozilla/5.0 (compatible; nfpc-nftc-checker/1.0; +github-actions)"

def load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def sha(t: str) -> str:
    return hashlib.sha256((t or "").encode("utf-8")).hexdigest()

def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip())

def ymd_dot(s):
    s = re.sub(r"[^\d]", "", s or "")
    return f"{s[0:4]}.{s[4:6]}.{s[6:8]}" if len(s) == 8 else (s or "")

LAWGO_LIST_URL = "https://www.law.go.kr/DRF/NwAdmRulLnkListR.do"
LAWGO_PARAMS = {
    "searchType": "admRulNm",
    "admRulNm": "",
    "cptOfi": "1661000",  # 소방청
    "lsKnd": "",
    "frmPrmlYd": "",
    "toPrmlYd": "",
    "sortIdx": "0",
    "chrIdx": "14"
}

NFA_LIST_URL = "https://www.nfa.go.kr/nfa/publicrelations/legalinformation/instruction"

def looks_like_nfpc_nftc(title: str) -> bool:
    t = (title or "").upper()
    return ("화재안전성능기준" in title) or ("화재안전기술기준" in title) or ("NFPC" in t) or ("NFTC" in t)

def extract_code(title: str) -> str:
    m = re.search(r"\b(NFPC|NFTC)\s*[-]?\s*(\d{2,4})\b", (title or "").upper())
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return ""

def safe_get(url, params=None):
    return requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)

def parse_lawgo_list():
    items = []
    try:
        r = safe_get(LAWGO_LIST_URL, LAWGO_PARAMS)
        soup = BeautifulSoup(r.text, "lxml")

        rows = soup.select("table tbody tr")
        if not rows:
            rows = soup.select("tr")

        for tr in rows:
            tds = [norm(td.get_text(" ", strip=True)) for td in tr.select("td")]
            if len(tds) < 2:
                continue

            name = tds[1] if len(tds) > 1 else tds[0]
            if not looks_like_nfpc_nftc(name):
                continue

            notice = tds[4] if len(tds) > 4 else ""
            date = tds[5] if len(tds) > 5 else ""

            a = tr.select_one("a")
            href = a.get("href") if a else ""
            if href and href.startswith("/"):
                href = "https://www.law.go.kr" + href
            if not href:
                q = requests.utils.quote(name)
                href = f"https://www.law.go.kr/admRulSc.do?menuId=5&query={q}"

            items.append({
                "source": "LAWGO",
                "title": name,
                "code": extract_code(name),
                "noticeNo": notice,
                "announceDate": ymd_dot(date),
                "url": href
            })

        return items, None

    except Exception as e:
        return [], f"LAWGO parse error: {repr(e)}"

def parse_nfa_list():
    items = []
    try:
        r = safe_get(NFA_LIST_URL)
        soup = BeautifulSoup(r.text, "lxml")

        rows = soup.select("table tbody tr")
        if not rows:
            rows = soup.select("tr")

        for tr in rows:
            tds = [norm(td.get_text(" ", strip=True)) for td in tr.select("td")]
            if len(tds) < 2:
                continue

            name = tds[0]
            if not looks_like_nfpc_nftc(name):
                continue

            date = tds[4] if len(tds) > 4 else ""

            a = tr.select_one("a")
            href = a.get("href") if a else ""
            if href and href.startswith("/"):
                href = "https://www.nfa.go.kr" + href
            if not href:
                href = NFA_LIST_URL

            items.append({
                "source": "NFA",
                "title": name,
                "code": extract_code(name),
                "noticeNo": "",
                "announceDate": ymd_dot(date),
                "url": href
            })

        return items, None
    except Exception as e:
        return [], f"NFA parse error: {repr(e)}"

def key_of(it):
    return sha("|".join([
        it.get("source",""),
        it.get("title",""),
        it.get("noticeNo",""),
        it.get("announceDate",""),
        it.get("url",""),
    ]))

def write_report(path, result, summary, added, removed, lawgo_err, nfa_err):
    html = []
    html.append(f"<html><head><meta charset='utf-8'><title>NFPC/NFTC 주간 점검 {TODAY}</title>")
    html.append("<style>body{font-family:system-ui,Segoe UI,Apple SD Gothic Neo,Malgun Gothic,sans-serif;padding:24px} ")
    html.append("table{border-collapse:collapse;width:100%;margin:12px 0} th,td{border:1px solid #ddd;padding:8px;font-size:14px} th{background:#f5f5f5} ")
    html.append(".badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#111;color:#fff;font-size:12px} ")
    html.append("@media print{button{display:none} body{padding:0}} </style></head><body>")
    html.append(f"<h1>NFPC/NFTC 주간 점검</h1><div>기준일: <b>{TODAY}</b> / 결과: <span class='badge'>{result}</span> / {summary}</div>")
    html.append("<button onclick='window.print()' style='margin-top:10px;padding:8px 12px;'>프린트</button>")

    def render_list(title, items):
        html.append(f"<h2>{title} ({len(items)}건)</h2>")
        if not items:
            html.append("<div>없음</div>")
            return
        html.append("<table><thead><tr><th>출처</th><th>코드</th><th>명칭</th><th>발령번호</th><th>발령일</th><th>링크</th></tr></thead><tbody>")
        for it in items:
            url = it.get("url","")
            html.append("<tr>")
            html.append(f"<td>{it.get('source','')}</td>")
            html.append(f"<td>{it.get('code','')}</td>")
            html.append(f"<td>{it.get('title','')}</td>")
            html.append(f"<td>{it.get('noticeNo','')}</td>")
            html.append(f"<td>{it.get('announceDate','')}</td>")
            html.append(f"<td><a href='{url}' target='_blank'>원문</a></td>")
            html.append("</tr>")
        html.append("</tbody></table>")

    render_list("신규/변경 감지(추가)", added)
    render_list("직전 대비 제외(삭제/변경 추정)", removed)

    if lawgo_err or nfa_err:
        html.append("<h2>수집 오류</h2><ul>")
        if lawgo_err: html.append(f"<li>{lawgo_err}</li>")
        if nfa_err: html.append(f"<li>{nfa_err}</li>")
        html.append("</ul>")

    html.append("</body></html>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))

def main():
    snapshot = load("snapshot.json", {"last": None, "items": []})
    data = load("data.json", {"records": []})

    prev_items = snapshot.get("items", [])
    prev_keys = set(key_of(x) for x in prev_items)

    lawgo_items, lawgo_err = parse_lawgo_list()
    time.sleep(1.0)
    nfa_items, nfa_err = parse_nfa_list()

    cur_items = lawgo_items + nfa_items
    cur_keys = set(key_of(x) for x in cur_items)

    added = [x for x in cur_items if key_of(x) not in prev_keys]
    removed = [x for x in prev_items if key_of(x) not in cur_keys]

    if added or removed:
        result = "변경 있음"
        summary = f"추가 {len(added)}건 / 제외 {len(removed)}건"
    else:
        result = "변경 없음"
        summary = "직전 대비 변동 감지 없음"

    report_path = f"{REPORT_DIR}/{TODAY}.html"
    write_report(report_path, result, summary, added, removed, lawgo_err, nfa_err)

    record = {"date": TODAY, "result": result, "summary": summary, "added": added, "removed": removed, "report": report_path}
    data["records"] = [r for r in data.get("records", []) if r.get("date") != TODAY]
    data["records"].insert(0, record)

    snapshot["last"] = TODAY
    snapshot["items"] = cur_items

    save("data.json", data)
    save("snapshot.json", snapshot)

if __name__ == "__main__":
    main()
