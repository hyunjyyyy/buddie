"""삼성복지재단 > 삼성어린이집 교직원 채용. 전국 공고이고 주소 칸이 없어 연락처 지역번호(02)로 서울만 남긴다."""
import re
import time
from datetime import datetime, timedelta, timezone

from common import clean, cover_letter, fetch, job_of, to_text
from sources import seoul_childcare

ID = "samsung"
NAME = "삼성복지재단"
BASE = "http://www.samsungwelfare.org/html/welfare/nursery/"
FOUNDATION = True
HOME = BASE + "recruit.asp"


def detail_url(seq):
    return f"{BASE}recruit_view.asp?seq={seq}&page=1&prc_seq=view"


def ymd(s):
    s = re.sub(r"\D", "", s)
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 else None


def list_all(max_pages=5):
    rows = []
    for page in range(1, max_pages + 1):
        t = fetch(HOME, {"page": page, "smode": "all", "svalue": ""})
        body = t[t.find("<tbody"):t.find("</tbody>")]
        for r in re.findall(r"<tr>(.*?)</tr>", body, re.S):
            m = re.search(r"_view\((\d+),", r)
            tds = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            if not m or len(tds) < 6:
                continue
            period = re.findall(r"\d{8}", tds[3])
            rows.append({
                "seq": m.group(1), "org": tds[1], "job": tds[2],
                "start": ymd(period[0]) if period else None,
                "end": ymd(period[1]) if len(period) > 1 else None,
                "status": tds[4], "posted": tds[5].replace(".", "-"),
            })
        if f"_gotoPage2(goPage,{page + 1}," not in t:
            break
    return rows


def parse_detail(t):
    text = to_text(t)
    get = lambda k: (re.search(rf"\n\s*{k}\s*\n([^\n]*)", text) or [None, None])[1]
    phone = (get("연락처") or "").strip()
    period = (get("서류접수기간") or "").strip()
    return {
        "seoul": phone.startswith("02"),
        "qual": (get("자격정도") or "").strip() or None,
        # 날짜는 목록에 이미 있으니 마감 시각이 적힌 경우만 남긴다.
        "deadlineHint": period if re.search(r"\d{1,2}:\d{2}|\d{1,2}\s*시", period) else None,
        "coverLetter": cover_letter(text),
    }


def collect(cache, delay=0.3):
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    jobs = []
    for r in list_all():
        if r["end"] and r["end"] < today:
            continue
        d = cache.get(r["seq"])
        if d is None:
            try:
                d = parse_detail(fetch(detail_url(r["seq"]), timeout=30, retries=1))
                cache[r["seq"]] = d
            except Exception:
                d = {}
            time.sleep(delay)
        if not d.get("seoul"):
            continue
        gu = seoul_childcare.gu_of(r["org"], cache.setdefault("_gu", {}))
        jobs.append({
            "id": f"{ID}:{r['seq']}",
            "source": ID,
            "foundation": NAME,
            "kind": "어린이집",
            "title": f"{r['org']} {r['job']}",
            "org": r["org"],
            "orgType": "직장",
            "job": job_of(r["job"]),
            "gu": gu,
            "addr": gu or "서울",
            "start": r["start"],
            "posted": r["posted"],
            "end": r["end"],
            "deadlineHint": d.get("deadlineHint"),
            "coverLetter": d.get("coverLetter"),
            "qual": d.get("qual"),
            "url": detail_url(r["seq"]),
        })
    return jobs
