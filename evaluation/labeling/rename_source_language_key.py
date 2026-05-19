"""Phase 4.2 — concepts.yml 의 `source_language` 키를 `tradition_language` 로 일괄 rename.

배경 (Decision-18, 2026-05-20):
    옛 `source_language` 가 *사상의 원천 언어* (concept-level) 와 *논문 저자가 사용한
    자료 언어* (paper-level) 두 의미를 뭉개고 있었음. concept-level 용도로 의미를
    명확화해서 `tradition_language` 로 rename. paper-level 변수는 별도 두 개
    (`primary_source_basis`, `secondary_source_horizon`) 로 분리되어 Phase 4.3-4.4
    에서 references.parquet 기반으로 계산.

원칙:
    - 값(enum) 은 변경 없음 — sanskrit/pali/prakrit/chinese/tibetan/modern_korean/mixed/n/a
    - 키 이름만 변경
    - ruamel.yaml 로 주석·키 순서·들여쓰기 보존
    - 멱등 — 이미 `tradition_language` 가 있고 `source_language` 가 없으면 no-op
    - 두 키 동시 존재하면 (이전 부분 실행 흔적) 에러로 중단

실행:
    .venv/bin/python evaluation/labeling/rename_source_language_key.py
    .venv/bin/python evaluation/labeling/rename_source_language_key.py --dry-run

이 스크립트가 다루지 못하는 것 (별도 수동 수정 필요):
    - concepts.yml 의 파일 헤더 주석 ("source_language : 1차 자료 언어 ..." 줄)
    - Python 코드들 (verify_05_dictionary, add_phase3_entries, backfill_concepts_metadata,
      labeling/__init__, evaluation/app.py, evaluation/pages/2_학제경계.py)
    → 이들은 별도 Edit 로 처리.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parent.parent.parent
CONCEPTS_PATH = ROOT / "data" / "dictionaries" / "concepts.yml"

OLD_KEY = "source_language"
NEW_KEY = "tradition_language"


def _make_yaml() -> YAML:
    """concepts.yml 의 기존 스타일과 일치하는 ruamel.yaml 설정."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=2, offset=0)
    yaml.width = 4096  # 줄바꿈 방지
    return yaml


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="변경 통계만 출력, 파일은 수정 안 함.")
    args = ap.parse_args()

    if not CONCEPTS_PATH.exists():
        print(f"❌ concepts.yml not found at {CONCEPTS_PATH}", file=sys.stderr)
        return 1

    yaml = _make_yaml()
    with CONCEPTS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not isinstance(data, list):
        print(f"❌ 예상치 못한 최상위 구조: {type(data).__name__} (list 이어야 함)",
              file=sys.stderr)
        return 1

    total = len(data)
    renamed = 0
    already_new = 0
    both_present = 0
    neither_present = 0
    examples_renamed: list[str] = []

    for entry in data:
        cid = entry.get("canonical_id", "<no-id>")
        has_old = OLD_KEY in entry
        has_new = NEW_KEY in entry

        if has_old and has_new:
            both_present += 1
            print(f"⚠️  [{cid}] 두 키 모두 존재 — 부분 실행 흔적 의심. 중단.",
                  file=sys.stderr)
            return 2
        elif has_old:
            value = entry[OLD_KEY]
            # 키 순서 보존: 같은 위치에 새 키 삽입 → 옛 키 삭제
            keys = list(entry.keys())
            idx = keys.index(OLD_KEY)
            # ruamel.yaml CommentedMap 은 insert(index, key, value) 지원
            entry.insert(idx, NEW_KEY, value)
            del entry[OLD_KEY]
            renamed += 1
            if len(examples_renamed) < 5:
                examples_renamed.append(f"{cid} ({value})")
        elif has_new:
            already_new += 1
        else:
            neither_present += 1

    print(f"=== 통계 (concepts.yml, {total} entry) ===")
    print(f"  rename ({OLD_KEY} → {NEW_KEY}): {renamed}")
    print(f"  이미 {NEW_KEY} 보유 (no-op)   : {already_new}")
    print(f"  둘 다 없음 (skip)             : {neither_present}")
    print(f"  둘 다 존재 (에러)             : {both_present}")
    if examples_renamed:
        print(f"\n  rename 예시:")
        for e in examples_renamed:
            print(f"    - {e}")

    if args.dry_run:
        print("\n[dry-run] 파일 변경 안 함.")
        return 0

    if renamed == 0:
        print("\n변경 사항 없음. 파일 그대로 둠.")
        return 0

    # 백업 없이 직접 덮어쓰기 (git 으로 추적되므로)
    with CONCEPTS_PATH.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print(f"\n✅ {CONCEPTS_PATH.relative_to(ROOT)} 저장 완료 ({renamed} entry rename).")
    print(f"   다음 단계: 파일 헤더 주석 + Python 코드 6개 파일의 '{OLD_KEY}' → '{NEW_KEY}' 수동 수정.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
