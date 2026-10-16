import html
import re
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; buddie-jobs/1.0; +https://github.com/)"

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


# 보여주는 직종. 보조·대체교사, 조리원 등 다른 직종은 수집 단계에서 뺀다.
TEACHER_JOBS = ("보육교사", "가정보육교사")


def is_teacher(job):
    return job in TEACHER_JOBS


def job_of(text):
    """재단 사이트의 자유 서술 직종을 센터 게시판 직종 이름으로 맞춘다."""
    for key, job in (("보조", "보조교사"), ("대체", "대체교사"), ("조리", "조리원"), ("영양", "영양사"),
                     ("간호", "간호사"), ("원장", "원장"), ("교사", "보육교사")):
        if key in (text or ""):
            return job
    return "기타"


# 센터 게시판 본문에 적힌 위탁 재단 이름 → 재단별 보기의 이름. 재단 사이트 출처의 NAME 과 같게 둬야 한 묶음이 된다.
FOUNDATIONS = {
    "한국아동보육복지협회": r"한국\s*아동\s*보육\s*복지\s*협회",
    "킨더슐레": r"킨더\s*슐레",
    "한빛바른보육경영원": r"한빛\s*바른\s*보육",
    "푸르니보육지원재단": r"푸르니",
    "한솔어린이보육재단": r"한솔\s*어린이\s*보육\s*재단",
    "삼성복지재단": r"삼성\s*복지\s*재단",
}


def foundation_of(text):
    for name, pat in FOUNDATIONS.items():
        if re.search(pat, text or ""):
            return name
    return None


def cover_letter(body):
    if re.search(r"자기\s*소개서|자소서", body):
        return True
    return None
