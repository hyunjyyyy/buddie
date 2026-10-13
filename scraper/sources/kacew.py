"""한국아동보육복지협회 채용 게시판(Wix 블로그). 1년에 몇 번 올리는 통합 공고뿐이고 본문이 이미지라
접수기간을 읽을 수 없다. 게시일 60일 이내의 어린이집 채용 글만 남긴다.
개별 어린이집 공고는 서울시육아종합지원센터 게시판에 따로 올라온다."""
import re
from datetime import datetime, timedelta, timezone

from common import clean, fetch, job_of

ID = "kacew"
NAME = "한국아동보육복지협회"
FOUNDATION = True
HOME = "https://www.kacew.or.kr/hire"
KEEP_DAYS = 60


def post_date(s, now):
    m = re.search(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일", s)
    if not m:
        return None
    d = datetime(int(m.group(1) or now.year), int(m.group(2)), int(m.group(3)))
    # 연도 없는 날짜가 미래로 계산되면 작년 글이다.
    if not m.group(1) and d.date() > now.date():
        d = d.replace(year=now.year - 1)
    return d.strftime("%Y-%m-%d")


def collect(cache):
    now = datetime.now(timezone(timedelta(hours=9)))
    since = (now - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
    t = fetch(HOME)
    jobs = []
    # 글마다 <a href=".../post/...">제목</a> 뒤, 다음 글 링크 전까지 어딘가에 게시일이 온다.
    parts = re.split(r'href="(https://www\.kacew\.or\.kr/post/[^"]+)"', t)
    for url, chunk in zip(parts[1::2], parts[2::2]):
        inner, _, tail = chunk.partition("</a>")
        title = clean(inner.split(">", 1)[-1])
        if not title or not re.search(r"어린이집|보육교|원장", title) or re.search(r"결과", title):
            continue
        posted = post_date(clean(tail), now)
        if not posted or posted < since:
            continue
        jobs.append({
            "id": f"{ID}:{url.rsplit('/', 1)[-1]}",
            "source": ID,
            "foundation": NAME,
            "kind": "어린이집",
            "title": title,
            "org": NAME,
            "orgType": "직장",
            "job": job_of(title),
            "gu": None,
            "addr": "여러 어린이집 통합 공고",
            "start": None,
            "posted": posted,
            "end": None,
            "deadlineHint": "접수기간은 원문 공고문(이미지·첨부)을 확인하세요",
            "coverLetter": None,
            "qual": None,
            "url": url,
        })
    return list({j["id"]: j for j in jobs}.values())
