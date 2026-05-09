"""KCI articleDetail × 636 — 모든 논문의 풀 메타 + references + REFARTIID 일괄 회수.

이 스크립트는 raw XML을 data/cache/articleDetail/ 에 저장만 한다.
파싱(structured 추출)은 별도 scripts/parse_articles.py.

비용: ~636 호출 (rate limit 0.5s → ~5.3분)
캐시: 이미 받은 건 skip — 재실행 안전. resume 자동.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ksip.data import load_papers  # noqa: E402
from ksip.kci_api import _cache_path, get_article_detail  # noqa: E402


def main() -> None:
    papers = load_papers()
    arti_ids = papers["논문 ID"].dropna().unique().tolist()
    total = len(arti_ids)
    print(f"[KCI] articleDetail × {total} 시작")
    print(f"      rate limit 0.5s → 예상 시간 ~{total * 0.5 / 60:.1f}분 (캐시는 skip)")
    print()

    t0 = time.monotonic()
    n_cache = 0
    n_new = 0
    n_err = 0

    for i, aid in enumerate(arti_ids, 1):
        # 사전 캐시 존재 여부로 진행 표시 메시지 분기
        cached = _cache_path("articleDetail", {"id": aid}).exists()
        try:
            resp = get_article_detail(aid)
            if resp.from_cache:
                n_cache += 1
            else:
                n_new += 1
        except Exception as e:
            n_err += 1
            print(f"  [{i}/{total}] {aid} ERR: {e!r}")
            continue

        # 50건마다 진행 상황
        if i % 50 == 0 or i == total:
            elapsed = time.monotonic() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (total - i) / rate if rate > 0 else 0
            print(
                f"  [{i:>4}/{total}] cache={n_cache} new={n_new} err={n_err} "
                f"· {rate:.1f} req/s · ETA {eta:.0f}s"
            )

    print()
    print(f"✓ 완료 — 캐시 hit {n_cache} / 신규 호출 {n_new} / 오류 {n_err}")
    print(f"  raw XMLs at: data/cache/articleDetail/")


if __name__ == "__main__":
    main()
