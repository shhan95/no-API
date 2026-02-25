import json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

NFPC_LIST = "https://www.law.go.kr/lbook/lbInfoR.do?lbookSeq=105439"  # NFPC 전자법령집(목록)
NFTC_LIST = "https://www.law.go.kr/lbook/lbInfoR.do?lbookSeq=105413"  # NFTC 전자법령집(목록)

OUT_NFPC = Path("data/standards_nfpc.json")
OUT_NFTC = Path("data/standards_nftc.json")
OUT_NFPC.parent.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (compatible; nfpc-nftc-standards/1.0; +github-actions)"

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def extract_code(title: str) -> str:
    t = (title or "").upper()
    m = re.search(r"\b(NFPC|NFTC)\s*[-]?\s*(\d{2,4}[A-Z]?)\b", t)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return ""

def fetch_list(url: str, kind: str):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    items = []
    for a in soup.select("a[href]"):
        txt = norm(a.get_text(" ", strip=True))
        if not txt:
            continue
        if kind not in txt.upper():  # NFPC / NFTC만
            continue

        code = extract_code(txt)
        href = a.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://www.law.go.kr" + href
        if not href.startswith("http"):
            continue

        # title은 사람이 보기 좋게(앞쪽 “행정규칙” 같은 접두어 제거는 옵션)
        items.append({
            "code": code or "",
            "title": txt,
            "url": href
        })

    # code 없는 쓰레기 제거 + code 기준 정렬
    items = [x for x in items if x["code"]]
    items.sort(key=lambda x: x["code"])

    # 중복 code는 첫번째(최신 링크)만 남김
    dedup = {}
    for it in items:
        dedup.setdefault(it["code"], it)
    return list(dedup.values())

def main():
    nfpc_items = fetch_list(NFPC_LIST, "NFPC")
    nftc_items = fetch_list(NFTC_LIST, "NFTC")

    OUT_NFPC.write_text(json.dumps({"items": nfpc_items}, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_NFTC.write_text(json.dumps({"items": nftc_items}, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"NFPC items: {len(nfpc_items)}")
    print(f"NFTC items: {len(nftc_items)}")

if __name__ == "__main__":
    main()
