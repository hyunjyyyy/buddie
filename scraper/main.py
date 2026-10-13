import json
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sources import hansol, kacew, puruni, samsung, seoul_childcare  # noqa: E402

SOURCES = [seoul_childcare, puruni, samsung, hansol, kacew]
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data" / "jobs.json"
CACHE = ROOT / "data" / "detail-cache.json"
KST = timezone(timedelta(hours=9))


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def main():
    now = datetime.now(KST).isoformat(timespec="minutes")
    prev = load(OUT, {"jobs": [], "sources": []})
    prev_status = {s["id"]: s for s in prev.get("sources", [])}
    cache = load(CACHE, {})
    jobs, status = [], []
    for src in SOURCES:
        c = cache.setdefault(src.ID, {})
        try:
            got = src.collect(c)
            status.append({"id": src.ID, "name": src.NAME, "url": src.HOME, "ok": True, "foundation": getattr(src, "FOUNDATION", False),
                           "count": len(got), "checkedAt": now, "lastOkAt": now})
        except Exception:
            traceback.print_exc()
            # 실패한 출처는 직전 결과를 그대로 두고, 화면에는 실패로 표시한다.
            got = [j for j in prev["jobs"] if j["source"] == src.ID]
            p = prev_status.get(src.ID, {})
            status.append({"id": src.ID, "name": src.NAME, "url": src.HOME, "ok": False, "foundation": getattr(src, "FOUNDATION", False),
                           "count": len(got), "checkedAt": now, "lastOkAt": p.get("lastOkAt")})
        jobs.extend(got)
        print(f"{src.ID}: {len(got)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updatedAt": now, "sources": status, "jobs": jobs},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if not any(s["ok"] for s in status):
        sys.exit(1)


if __name__ == "__main__":
    main()
