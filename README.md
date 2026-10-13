# MOA · 보육공고

서울 어린이집 채용공고를 하루 두 번(KST 08:00, 18:00) 모아 마감순으로 보여주는 정적 사이트.

- `scraper/` — 출처별 수집기(Python 표준 라이브러리만 사용). 결과는 `docs/data/jobs.json`
- `docs/` — GitHub Pages 로 배포되는 화면
- `.github/workflows/scrape.yml` — 일정 실행 후 바뀐 데이터를 커밋

## 출처

| id | 출처 | 비고 |
| --- | --- | --- |
| `seoul-ccef` | 서울시육아종합지원센터 어린이집구인 | 서울 25개 구 전체. 상세는 처음 본 공고만 받아 `data/detail-cache.json` 에 둔다 |
| `puruni` | 푸르니보육지원재단 채용공고 | 전국 공고 중 서울만 |

출처 추가: `scraper/sources/` 에 `ID`, `NAME`, `HOME`, `collect(cache)` 를 가진 모듈을 만들고
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
