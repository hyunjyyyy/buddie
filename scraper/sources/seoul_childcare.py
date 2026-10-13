"""서울시육아종합지원센터 인력뱅크 > 어린이집구인. 서울 25개 구 공고가 모두 여기 모인다."""
import re
import time

from common import clean, cover_letter, deadline_hint, fetch, find_gu, to_text

ID = "seoul-ccef"
NAME = "서울시육아종합지원센터"
BASE = "https://seoul.childcare.go.kr/ccef/job/"
HOME = BASE + "JobOfferSlPL.jsp?flag=SlPL"


def detail_url(joseq):
    return f"{BASE}JobOfferSl.jsp?flag=Sl&JOSEQ={joseq}"


def list_open():
    # limit 을 크게 주면 한 번에 다 온다(1,800건 ≈ 4MB). endYn=N 이 '구인중'.
    t = fetch(BASE + "JobOfferSlPL.jsp", {"flag": "SlPL", "offset": 0, "limit": 5000, "endYn": "N"})
    rows = []
    for r in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        m = re.search(r"fnGoBoardSl\('(\d+)'\)", r)
        if not m:
            continue
        tds = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        title = re.search(r'title="([^"]*)"', r)
        rows.append({
            "joseq": m.group(1),
            "orgType": tds[1],
            "title": clean(title.group(1)) if title else tds[2],
            "org": tds[3],
            "job": tds[4],
            "addr": tds[5],
            "end": tds[6] or None,
            "posted": tds[7] or None,
        })
    return rows


def parse_detail(t):
    fields = {}
    for th, td in re.findall(r"<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>", t, re.S):
        fields[clean(th)] = clean(td)
    text = to_text(t)
    m = re.search(r"공유하기\s*\n(.*?)\n\s*목록\s*\n", text, re.S)
    body = m.group(1) if m else ""
    return {
        "addr": fields.get("소재지"),
        "qual": fields.get("자격사항"),
        "pay": fields.get("임금"),
        "deadlineHint": deadline_hint(body),
        "coverLetter": cover_letter(body),
    }


def collect(cache, max_details=3000, delay=0.2):
    """cache: joseq -> 상세 파싱 결과. 상세는 처음 본 공고만 받는다."""
    rows = list_open()
    jobs, fetched = [], 0
    for r in rows:
        d = cache.get(r["joseq"])
        if d is None and fetched < max_details:
            try:
                d = parse_detail(fetch(detail_url(r["joseq"]), timeout=30, retries=1))
                cache[r["joseq"]] = d
            except Exception:
                d = None
            fetched += 1
            time.sleep(delay)
        d = d or {}
        addr = d.get("addr") or r["addr"]
        jobs.append({
            "id": f"{ID}:{r['joseq']}",
            "source": ID,
            "kind": "어린이집",
            "title": r["title"],
            "org": r["org"],
            "orgType": r["orgType"],
            "job": r["job"],
            "gu": find_gu(addr),
            "addr": addr.replace("서울특별시 ", ""),
            "start": None,
            "posted": r["posted"],
            "end": r["end"],
            # 캐시에 남은 예전 추출 결과도 현재 규칙으로 다시 거른다.
            "deadlineHint": deadline_hint(d.get("deadlineHint")),
            "coverLetter": d.get("coverLetter"),
            "qual": d.get("qual"),
            "url": detail_url(r["joseq"]),
        })
    live = {r["joseq"] for r in rows}
    for k in list(cache):
        if k not in live:
            del cache[k]
    return jobs
