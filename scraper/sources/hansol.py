"""한솔어린이보육재단 채용공고. 전국 공고라 상세의 '근무지'로 서울만 남긴다."""
import re
import time

from common import clean, cover_letter, deadline_hint, fetch, find_gu, job_of, to_text

ID = "hansol"
NAME = "한솔어린이보육재단"
BASE = "https://docu.hansolhope.or.kr/recruit/"
FOUNDATION = True
HOME = BASE + "index.do"


def detail_url(sn):
    # 사람이 여는 주소. 본문은 이 페이지 안의 iframe(recruit.do)에 있다.
    return f"{BASE}index.do?flg=view&mCurrent=2&sCurrent=3&empmn_sn={sn}"


def list_open(max_pages=15):
    """최신순 목록에서 접수중(001)만 모은다. 마감(002)만 있는 페이지가 두 번 이어지면 멈춘다."""
    rows, closed_pages = [], 0
    for page in range(1, max_pages + 1):
        t = fetch(HOME, {"pageNum": page, "listNum": 8})
        found = re.findall(
            r"fnView\('(\d+)','(\d+)',\s*'(\d+)'\s*\);\">(.*?)<font.*?<td>\s*([\d-]{10})\s*~\s*([\d-]{10})", t, re.S)
        if not found:
            break
        for jose, sn, status, title, start, end in found:
            if status == "001":
                rows.append({"sn": sn, "title": clean(title), "start": start, "end": end})
        closed_pages = closed_pages + 1 if all(f[2] != "001" for f in found) else 0
        if closed_pages >= 2:
            break
    return rows


def parse_detail(t):
    body = to_text(t)
    place = re.search(r"근무지\s*:\s*([^\n]+)", body)
    job = re.search(r"모집분야\s*:\s*([^\n]+)", body)
    qual = re.search(r"응시자격\s*\n([^\n]+)", body)
    return {
        "addr": place.group(1).strip() if place else None,
        "job": job.group(1).strip() if job else None,
        "qual": qual.group(1).strip() if qual else None,
        "deadlineHint": deadline_hint(body) if re.search(r"\d{1,2}:\d{2}|\d{1,2}\s*시", body) else None,
        "coverLetter": cover_letter(body),
    }


def collect(cache, delay=0.3):
    rows = list_open()
    jobs = []
    for r in rows:
        d = cache.get(r["sn"])
        if d is None:
            try:
                d = parse_detail(fetch(f"{BASE}recruit.do?flg=view&mCurrent=2&sCurrent=3&empmn_sn={r['sn']}",
                                       timeout=30, retries=1))
                cache[r["sn"]] = d
            except Exception:
                d = {}
            time.sleep(delay)
        addr = d.get("addr") or ""
        if "서울" not in addr:
            continue
        # 이름이 '[용산소방서 직장어린이집] 보조교사…' 처럼 대괄호 안에만 있는 공고가 있다.
        bracket = re.match(r"\s*\[([^\]]*어린이집[^\]]*)\]", r["title"])
        title = re.sub(r"^\s*\[[^\]]*\]\s*", "", r["title"])
        org = bracket.group(1).strip() if bracket else (re.search(r"(\S*어린이집)", title) or re.search(r"(\S+)", title)).group(1)
        if bracket:
            title = f"{org} {title}"
        jobs.append({
            "id": f"{ID}:{r['sn']}",
            "source": ID,
            "foundation": NAME,
            "kind": "어린이집",
            "title": title,
            "org": org,
            "orgType": "직장",
            "job": job_of(title + " " + (d.get("job") or "")),
            "gu": find_gu(addr),
            "addr": addr.replace("서울특별시 ", ""),
            "start": r["start"],
            "posted": None,
            "end": r["end"],
            "deadlineHint": d.get("deadlineHint"),
            "coverLetter": d.get("coverLetter"),
            "qual": d.get("qual"),
            "url": detail_url(r["sn"]),
        })
    live = {r["sn"] for r in rows}
    for k in list(cache):
        if k not in live:
            del cache[k]
    return jobs
