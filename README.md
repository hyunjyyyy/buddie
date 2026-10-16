# buddie

서울 어린이집 보육교사 채용공고를 하루 두 번(KST 08:00, 18:00) 모아 마감순으로 보여주는 정적 사이트.
보육교사(가정보육교사 포함)만 모으고 보조·대체교사, 조리원 등 다른 직종은 수집 단계에서 뺀다.
같은 어린이집이 같은 공고를 다시 올린 것은 가장 최근 글 하나만 남긴다.

- `scraper/` — 출처별 수집기(Python 표준 라이브러리만 사용). 결과는 `docs/data/jobs.json`
- `docs/` — GitHub Pages 로 배포되는 화면
- `.github/workflows/scrape.yml` — 일정 실행 후 바뀐 데이터를 커밋

## 출처

| id | 출처 | 비고 |
| --- | --- | --- |
| `seoul-ccef` | 서울시육아종합지원센터 어린이집구인 | 서울 25개 구 전체. 상세는 처음 본 공고만 받아 `data/detail-cache.json` 에 둔다 |
| `puruni` | 푸르니보육지원재단 채용공고 | 전국 공고 중 서울만 |
| `samsung` | 삼성복지재단 삼성어린이집 교직원 채용 | 주소 칸이 없어 연락처 02 로 서울 판별, 구는 센터 게시판에서 어린이집 이름으로 찾음 |
| `hansol` | 한솔어린이보육재단 채용공고 | 상세의 '근무지'로 서울 판별. 본문은 `recruit.do` iframe 에 있음 |
| `kacew` | 한국아동보육복지협회 채용 게시판 | 본문이 이미지라 게시일 60일 이내 글만 표시 |

출처 추가: `scraper/sources/` 에 `ID`, `NAME`, `HOME`, `collect(cache)` 를 가진 모듈을 만들고
(재단 사이트면 `FOUNDATION = True` 와 공고마다 `foundation` 을 넣어 재단별 보기에 묶이게 한다)
`scraper/main.py` 의 `SOURCES` 에 넣는다. `collect` 는 `seoul_childcare.py` 와 같은 모양의 dict 목록을 돌려준다.

## 로컬 실행

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scraper\main.py
python -m http.server 8000 -d docs
```

## 배포

1. GitHub 저장소 Settings → Pages → Source: `Deploy from a branch`, Branch: `main` / `/docs`
2. Actions 탭에서 `scrape` 를 한 번 수동 실행(`Run workflow`)해 동작 확인
