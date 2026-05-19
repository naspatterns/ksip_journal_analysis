"""Phase 4.3 — references.parquet 의 각 참고문헌을 일차/이차/unknown 으로 분류.

배경 (Decision-18, 2026-05-20):
    paper-level 변수 `primary_source_basis` (일차문헌 기반) 와
    `secondary_source_horizon` (이차문헌 학계) 를 계산하려면 먼저 각 reference 가
    어느 tier 에 속하는지 분류해야 함. 인도철학 분야의 일차문헌(원전)·이차문헌(학자
    연구) 분리 관습을 reflect.

분류 룰 (Decision-18 §일차/이차문헌 분류 룰):

    | 유형 | 건수 | 기본 |
    |---|---|---|
    | 자기인용 (인도철학) | — | 항상 secondary |
    | 학술지(정기간행물) | 3,578 | 거의 secondary |
    | 학위논문 / 학술대회 / 보고서 | 363 | secondary |
    | 기타자료 | 2,020 | 거의 primary (원전 카탈로그) |
    | 단행본 | 6,708 | 혼합 — 저자·제목 매칭 |
    | 인터넷자원 | 218 | 회색 — 매칭 시 primary |

    + 단행본·기타자료·인터넷자원에서:
        - 저자가 modern scholar (authors.yml) → secondary
        - 저자가 classical thinker (concepts.yml type=학자/인물) → primary
        - 제목이 classical text (concepts.yml type=원전/문헌) → 보조 신호
        - 기관명 마커 → unknown

산출:
    `data/processed/references.parquet` 에 `tier` 컬럼 추가.
    값: 'primary' / 'secondary' / 'unknown'

실행:
    .venv/bin/python evaluation/labeling/classify_reference_tier.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REFS_PATH = ROOT / "data" / "processed" / "references.parquet"
CONCEPTS_PATH = ROOT / "data" / "dictionaries" / "concepts.yml"
AUTHORS_PATH = ROOT / "data" / "dictionaries" / "authors.yml"

# 매칭 시 short surface 의 false positive 위험 회피
MIN_SURFACE_LEN = 3


def _norm(s: str) -> str:
    """NFC + 소문자화 + 양끝 공백 제거. 비교용."""
    if not isinstance(s, str):
        return ""
    return unicodedata.normalize("NFC", s).strip().lower()


def _load_yaml(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


@lru_cache(maxsize=1)
def _surface_sets() -> tuple[set[str], set[str], set[str]]:
    """concepts.yml + authors.yml → (classical_thinkers, classical_texts, modern_scholars).

    - classical_thinkers: concepts.yml 의 type=학자 또는 type=인물 entry surface
    - classical_texts:    concepts.yml 의 type=원전 또는 type=문헌 entry surface
    - modern_scholars:    authors.yml 의 모든 entry surface
    """
    concepts = _load_yaml(CONCEPTS_PATH)
    authors = _load_yaml(AUTHORS_PATH)

    thinkers: set[str] = set()
    texts: set[str] = set()
    scholars: set[str] = set()

    for e in concepts:
        if not e.get("verified", False):
            continue
        t = e.get("type")
        surfaces = [_norm(s) for s in (e.get("surface_forms") or []) if isinstance(s, str)]
        # canonical_kr / canonical_iast / canonical_zh 도 surface 로 활용
        for k in ("canonical_kr", "canonical_iast", "canonical_zh"):
            if e.get(k):
                surfaces.append(_norm(e[k]))
        surfaces = [s for s in surfaces if len(s) >= MIN_SURFACE_LEN]
        if t in ("학자", "인물"):
            thinkers.update(surfaces)
        elif t in ("원전", "문헌"):
            texts.update(surfaces)

    for e in authors:
        if not e.get("verified", False):
            continue
        surfaces = [_norm(s) for s in (e.get("surface_forms") or []) if isinstance(s, str)]
        if e.get("canonical_form"):
            surfaces.append(_norm(e["canonical_form"]))
        surfaces = [s for s in surfaces if len(s) >= MIN_SURFACE_LEN]
        scholars.update(surfaces)

    return thinkers, texts, scholars


_AUTHOR_TOKEN_RE = re.compile(r"[\s,;·/]+")
_PAREN_RE = re.compile(r"\([^)]*\)")  # 괄호 안 (편)/(역)/(주) 제거


def _author_tokens(name: str) -> list[str]:
    n = _norm(name)
    n = _PAREN_RE.sub(" ", n)
    return [t for t in _AUTHOR_TOKEN_RE.split(n) if len(t) >= 2]


def _author_in(name: str, surface_set: set[str]) -> bool:
    """저자 이름의 어느 토큰이라도 surface_set 에 있으면 True. modern_scholars 매칭 전용."""
    if not name:
        return False
    # full-string exact match 먼저 (e.g., "Jeong, Seung-seok" 같은 enrolled surface 형태)
    if _norm(name) in surface_set:
        return True
    for tok in _author_tokens(name):
        if tok in surface_set:
            return True
    return False


def _author_in_thinkers(name: str, thinkers: set[str]) -> bool:
    """저자가 classical thinker 매칭 여부. Western 'Last, First' 패턴의 first name 은 무시.

    이유 (false positive 방지): 'Tilakaratne, Asanga' 같은 modern 스리랑카 학자의
    first name 'Asanga' 가 고전 Yogācāra 의 Asaṅga 와 토큰 매칭되는 사례가 있음.
    Western 학자명 컨벤션상 comma 가 있으면 first name (post-comma) 은 modern 학자의
    given name 일 가능성이 압도. 그래서 comma 뒤 부분은 매칭에서 제외.
    """
    if not name:
        return False
    n = name
    if "," in n:
        # comma 전 부분만 사용 — Tilakaratne, Sastri, Gandhi 등 last name 만 확인
        n = n.split(",")[0]
    if _norm(n) in thinkers:
        return True
    for tok in _author_tokens(n):
        if tok in thinkers:
            return True
    return False


def _title_matches(title: str, surface_set: set[str]) -> bool:
    if not title:
        return False
    t = _norm(title)
    if t in surface_set:
        return True
    # substring fallback (short surface 는 미리 걸렀음)
    for s in surface_set:
        if s in t:
            return True
    return False


_CATALOG_ID_RE = re.compile(
    r"\b(?:[TKD]|TD|Taish[ōo])\.?\s*\d{2,}|Tib\.|bsTan|bKa['ʼ]|大藏經|藏經|事傳|大正"
)
_INST_RE = re.compile(
    r"(Universit[äa]t|University|大学|大学院|대학교|대학원|Akademie|Institute|研究所|연구원|재단|Verlag|Press)"
)
_MS_TEXT_RE = re.compile(
    r"(Tipiṭaka|tipitaka|大藏經|藏經|사본|寺本|敦煌|貝葉|寫本)"
)


def classify_tier(row: pd.Series, thinkers: set[str], texts: set[str],
                  scholars: set[str]) -> str:
    유형 = row["유형"]
    저자 = row.get("저자_원본") or ""
    제목 = row.get("제목_원본") or ""
    raw = row.get("원본_텍스트") or ""

    # (1) 자기인용 = secondary (학회 내부 학자 동료 연구)
    if row.get("자기인용", False):
        return "secondary"

    # (2) 항상 secondary 유형
    if 유형 in ("학위논문", "학술대회논문", "보고서", "학술지(정기간행물)"):
        return "secondary"

    # (3) 저자가 modern scholar → secondary
    if _author_in(저자, scholars):
        return "secondary"

    # (4) 저자가 classical thinker → primary (그 사상가의 원전·주석)
    if _author_in_thinkers(저자, thinkers):
        return "primary"

    # 유형별 fallback
    if 유형 == "기타자료":
        # 카탈로그 ID 패턴 (T 32, D 4203, Tib., bsTan/bKa', 大藏經) → primary
        if _CATALOG_ID_RE.search(raw):
            return "primary"
        # 기관명 마커 → unknown (ATBS Universität Wien 등)
        if _INST_RE.search(raw):
            return "unknown"
        # 제목이 classical text 매칭 → primary
        if _title_matches(제목, texts):
            return "primary"
        # 빈 데이터 → unknown
        if not 저자 and not 제목:
            return "unknown"
        # 기타자료 의 압도적 다수가 원전 → 기본 primary
        return "primary"

    if 유형 == "단행본":
        # 저자 없음 + 제목이 classical text → 원전 자체 → primary
        if not 저자 and _title_matches(제목, texts):
            return "primary"
        # 그 외 단행본 = 기본 secondary (학자 연구물·번역·편집본)
        return "secondary"

    if 유형 == "인터넷자원":
        # 사본·대장경·Tipiṭaka 등 magic words → primary
        if _MS_TEXT_RE.search(raw):
            return "primary"
        # 제목이 classical text → primary
        if _title_matches(제목, texts):
            return "primary"
        # 그 외 = unknown (스칼라 자료일 가능성도 있음, 보수적)
        return "unknown"

    return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="분포 통계만 출력, parquet 변경 안 함.")
    args = ap.parse_args()

    if not REFS_PATH.exists():
        print(f"❌ references.parquet not found at {REFS_PATH}", file=sys.stderr)
        return 1

    refs = pd.read_parquet(REFS_PATH)
    n_total = len(refs)
    print(f"=== references.parquet 로드 — {n_total:,} 행 ===")

    thinkers, texts, scholars = _surface_sets()
    print(f"사전 surface set:")
    print(f"  classical_thinkers (concepts type=학자/인물) : {len(thinkers)}")
    print(f"  classical_texts    (concepts type=원전/문헌) : {len(texts)}")
    print(f"  modern_scholars    (authors.yml verified)   : {len(scholars)}")

    # 분류
    refs["tier"] = refs.apply(
        lambda r: classify_tier(r, thinkers, texts, scholars), axis=1
    )

    # 통계
    print(f"\n=== tier 분포 (전체) ===")
    print(refs["tier"].value_counts(dropna=False).to_string())
    print(f"\n=== tier × 유형 cross-tab ===")
    ct = pd.crosstab(refs["유형"], refs["tier"], margins=True, margins_name="합계")
    # 정렬: 합계 빼고 자체 합계 내림차순
    유형순 = ct.iloc[:-1].sum(axis=1).sort_values(ascending=False).index.tolist() + ["합계"]
    ct = ct.reindex(유형순)
    print(ct.to_string())

    # 분류 sanity check — 자기인용 312 중 secondary 비율
    si_primary = ((refs["자기인용"]) & (refs["tier"] == "primary")).sum()
    si_secondary = ((refs["자기인용"]) & (refs["tier"] == "secondary")).sum()
    si_unknown = ((refs["자기인용"]) & (refs["tier"] == "unknown")).sum()
    print(f"\n자기인용 분류 (모두 secondary 예상): primary={si_primary} secondary={si_secondary} unknown={si_unknown}")

    if args.dry_run:
        print("\n[dry-run] parquet 변경 안 함.")
        return 0

    # 기존 컬럼 순서 보존 + tier 마지막에 추가
    refs.to_parquet(REFS_PATH, index=False)
    print(f"\n✅ {REFS_PATH.relative_to(ROOT)} 저장 완료 (tier 컬럼 추가).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
