"""푸르니보육지원재단 위탁 어린이집 채용공고. 전국 공고라 제목의 [구] 표기로 서울만 남긴다."""
import re
import time

from common import clean, cover_letter, deadline_hint, fetch, find_gu, to_text

ID = "puruni"
NAME = "푸르니보육지원재단"
BASE = "https://recruit.puruni.com/recruit/notice"
FOUNDATION = True
HOME = BASE


def detail_url(idx):
    return f"{BASE}/view?page=1&idx={idx}"


def list_all(max_pages=10):
    rows = []
    for page in range(1, max_pages + 1):
        t = fetch(f"{BASE}?page={page}")
        found = re.findall(r"pageView\(\d+,\s*(\d+)\);\">(.*?)</a>.*?<td>\s*([\d-]{10})\s*~\s*([\d-]{10})\s*</td>", t, re.S)
        for idx, title, start, end in found:
            rows.append({"idx": idx, "title": clean(title), "start": start, "end": end})
        if f"pageSubmit({page + 1})" not in t:
            break
    return rows


def collect(cache, delay=0.3):
    jobs = []
    for r in list_all():
        # 제목 앞 [양천구] 같은 표기. '[서울]' 처럼 구가 없으면 본문 주소에서 찾는다.
        head = re.match(r"\s*\[([^\]]+)\]", r["title"])
        region = head.group(1) if head else ""
        d = cache.get(r["idx"])
        if d is None and (find_gu(region) or "서울" in region or not head):
            try:
                body = to_text(fetch(detail_url(r["idx"]), timeout=30, retries=1))
                m = re.search(r"근무\s*(?:지역|장소|지)\s*:?\s*([^\n]+)", body)
                d = {
                    "addr": m.group(1).strip() if m else None,
                    "deadlineHint": deadline_hint(body),
                    "coverLetter": cover_letter(body),
                }
            except Exception:
                d = {}
            cache[r["idx"]] = d
            time.sleep(delay)
        d = d or {}
        gu = find_gu(region) or find_gu(d.get("addr"))
        if not gu:
            continue
        org = re.sub(r"^\s*\[[^\]]+\]\s*", "", r["title"])
        org = re.split(r"\s+(?:보육|기간제|교사|대체|연장|조리|영양|간호|교직원|정교사|담임)", org)[0].strip()
        jobs.append({
            "id": f"{ID}:{r['idx']}",
            "source": ID,
            "foundation": NAME,
            "kind": "어린이집",
            "title": re.sub(r"^\s*\[[^\]]+\]\s*", "", r["title"]),
            "org": org,
            "orgType": "직장",
            "job": "보육교사" if re.search(r"교사", r["title"]) else "기타",
            "gu": gu,
            "addr": d.get("addr") or gu,
            "start": r["start"],
            "posted": None,
            "end": r["end"],
            "deadlineHint": d.get("deadlineHint"),
            "coverLetter": d.get("coverLetter"),
            "qual": None,
            "url": detail_url(r["idx"]),
        })
    return jobs
