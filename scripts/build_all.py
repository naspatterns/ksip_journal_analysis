"""마스터 빌드 — raw 데이터 + KCI API → 모든 processed parquet 일괄 생성.

다른 환경(다른 컴퓨터, GitHub Actions 등)에서 한 번에 빌드하려면 이거 하나만:
    python scripts/build_all.py

KCI API 키(KCI_OpenAPI_Key.txt)가 없으면 단계 2-3은 자동 skip.
캐시된 응답이 이미 있으면 단계 3은 빠르게 끝남.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable  # 현재 인터프리터 그대로 사용


# (label, script_path, needs_api)
STAGES: list[tuple[str, str, bool]] = [
    ("[1/4] raw .xls → papers/authors/keywords/references parquet",
     "scripts/build_data.py", False),
    ("[2/4] KCI citationDetail → journal_metrics + history",
     "scripts/fetch_journal_metrics.py", True),
    ("[3/4] KCI articleDetail × 636 (cached XML)",
     "scripts/fetch_articles.py", True),
    ("[4/4] cached XML → kci_papers + kci_authors + kci_references parquet",
     "scripts/parse_articles.py", False),
]


def has_api_key() -> bool:
    return (ROOT / "KCI_OpenAPI_Key.txt").exists()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-api", action="store_true",
        help="KCI API 호출 단계(2-3) 건너뛰기. 캐시·기존 parquet만 사용.",
    )
    parser.add_argument(
        "--only", choices=["1", "2", "3", "4"], action="append", default=[],
        help="특정 단계만 실행 (반복 가능: --only 1 --only 4).",
    )
    args = parser.parse_args()

    api_ok = has_api_key()
    if not api_ok and not args.skip_api:
        print("⚠️  KCI_OpenAPI_Key.txt 없음 — 단계 2-3 자동 skip.")
    skip_api = args.skip_api or not api_ok

    only = set(args.only) if args.only else None

    print()
    t_total = time.monotonic()
    failed: list[str] = []

    for i, (label, script, needs_api) in enumerate(STAGES, 1):
        if only is not None and str(i) not in only:
            continue
        if needs_api and skip_api:
            print(f"⏭️  {label}  — SKIP (no API key)")
            print()
            continue

        print(f"━━━ {label}")
        t0 = time.monotonic()
        try:
            subprocess.run([PYTHON, script], cwd=ROOT, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ {label} — exit {e.returncode}")
            failed.append(script)
            # 단계 1 실패 시는 fail-fast (이후 단계가 papers.parquet 의존)
            if i == 1:
                print("❌ 단계 1 실패 — 이후 단계 의존성 충족 불가, 중단.")
                sys.exit(1)
        else:
            elapsed = time.monotonic() - t0
            print(f"✓ ({elapsed:.1f}s)")
        print()

    elapsed_total = time.monotonic() - t_total
    print(f"━━━ 완료 (총 {elapsed_total:.1f}s)")
    if failed:
        print(f"⚠️  실패한 스크립트: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
