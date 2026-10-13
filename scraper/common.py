import html
import re
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; bomo-jobs/1.0; +https://github.com/)"

SEOUL_GU = [
    "종로구", "중구", "용산구", "성동구", "광진구", "동대문구", "중랑구", "성북구", "강북구",
    "도봉구", "노원구", "은평구", "서대문구", "마포구", "양천구", "강서구", "구로구", "금천구",
    "영등포구", "동작구", "관악구", "서초구", "강남구", "송파구", "강동구",
]


def fetch(url, data=None, timeout=60, retries=2):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, body, {"User-Agent": UA})
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if i == retries:
                raise
            time.sleep(3 * (i + 1))


def to_text(fragment):
    s = re.sub(r"<(script|style)\b.*?</\1>", "", fragment, flags=re.S | re.I)
    s = re.sub(r"<(br|/tr|/p|/div|/li|/h\d)[^>]*>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t\r]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).replace("\xa0", " ").strip()


def find_gu(text):
    for gu in SEOUL_GU:
        if gu in (text or ""):
            return gu
    return None


def deadline_hint(body):
    """본문에서 접수기간/마감이 적힌 줄 하나를 뽑는다. 형식이 제각각이라 해석하지 않고 원문 줄을 보여준다."""
    for line in (body or "").split("\n"):
        line = re.sub(r"^[\s■□▨▶►○●◎◆◇\-·※*]*(?:\d{1,2}\s*[.)]\s*)?", "", line).strip()
        if len(line) > 120 or "@" in line or not re.search(r"접수|마감|모집\s*기간|공고\s*기간", line):
            continue
        if re.search(r"\d{1,2}\s*(?:[./]\s*\d{1,2}|월\s*\d{1,2}\s*일)", line):
            return line
    return None


def cover_letter(body):
    if re.search(r"자기\s*소개서|자소서", body):
        return True
    return None
