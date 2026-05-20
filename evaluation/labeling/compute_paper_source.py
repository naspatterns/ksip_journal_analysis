"""Phase 4.4 + 5R3 — paper-level 두 변수 계산.

각 논문의 references 를 tier 별로 분리, 언어/horizon 탐지(`detect_language.py`)
후 분포로 집계. references 가 primary tier 0건이거나 부재하면 **키워드 + 제목 +
keyword canonical_id** 로 fallback 추론. 결과는 `data/processed/paper_labels.parquet`.

primary_source_basis 결정 우선순위 (Phase 5R3 추가):
    (1) tier=primary references → detect_primary_language → 분포 → aggregate
    (2) (1) 이 unknown 일 때 fallback:
        (a) keywords.parquet 의 canonical_id → tradition_language
        (b) 키워드_원본 텍스트 → concepts surface 매칭
        (c) 논문 제목 → concepts surface 매칭
        → 분포 → aggregate
    (3) 둘 다 실패 → 'unknown'

secondary_source_horizon: refs 기반 단독 (paper-level fallback 없음 — 학계 horizon 은
저자·publisher 외엔 추론 어렵).

집계 룰: 0 refs → unknown / single value → 그 값 / top ≥50% OR top ≥ 1.5×2nd → top / else mixed.

산출 컬럼:
- 논문ID, primary_source_basis, secondary_source_horizon
- primary_basis_source: 'refs' / 'keywords_title' / 'none'
- n_primary, n_secondary (refs 개수)
- n_inferred (keyword/title 에서 매칭된 evidence 개수, fallback 시)
- primary_dist, secondary_dist (json string)

실행:
    .venv/bin/python evaluation/labeling/compute_paper_source.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.labeling.detect_language import (  # noqa: E402
    build_authors_horizon_lookup,
    build_canonical_id_primary_lookup,
    build_concepts_all_lookup,
    build_concepts_primary_lookup,
    build_journals_horizon_lookups,
    detect_primary_from_text,
    detect_primary_language,
    detect_secondary_horizon,
)

REFS_PATH = ROOT / "data" / "processed" / "references.parquet"
PAPERS_PATH = ROOT / "data" / "processed" / "papers.parquet"
KEYWORDS_PATH = ROOT / "data" / "processed" / "keywords.parquet"
OUT_PATH = ROOT / "data" / "processed" / "paper_labels.parquet"


def aggregate_label(dist: Counter) -> str:
    """분포 dict → 단일 라벨 ('unknown' / 단일값 / 'mixed').

    룰:
    - 비어있음 → 'unknown'
    - 단일 distinct value → 그 값
    - 2+ distinct: top 이 ≥50% of total OR top ≥ 1.5× 2nd → top
    - 그 외 → 'mixed'
    """
    if not dist:
        return "unknown"
    total = sum(dist.values())
    if total == 0:
        return "unknown"

    items = sorted(dist.items(), key=lambda x: -x[1])
    top_val, top_count = items[0]

    if len(items) == 1:
        return top_val

    second_count = items[1][1]

    if top_count / total >= 0.5:
        return top_val
    if top_count >= second_count * 1.5:
        return top_val

    return "mixed"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="분포 통계만 출력, parquet 저장 안 함.")
    args = ap.parse_args()

    if not REFS_PATH.exists():
        print(f"❌ references.parquet not found at {REFS_PATH}", file=sys.stderr)
        return 1
    if not PAPERS_PATH.exists():
        print(f"❌ papers.parquet not found at {PAPERS_PATH}", file=sys.stderr)
        return 1

    refs = pd.read_parquet(REFS_PATH)
    papers = pd.read_parquet(PAPERS_PATH)
    keywords = pd.read_parquet(KEYWORDS_PATH)

    if "tier" not in refs.columns:
        print(f"❌ references.parquet 에 'tier' 컬럼 없음 — Phase 4.3 먼저 실행 필요.",
              file=sys.stderr)
        return 2

    n_refs = len(refs)
    n_papers = len(papers)
    n_papers_with_refs = refs["논문ID"].nunique()
    n_papers_without = n_papers - n_papers_with_refs
    print(f"=== 입력 ===")
    print(f"  refs.parquet      : {n_refs:,} 행")
    print(f"  papers.parquet    : {n_papers:,} 행")
    print(f"  keywords.parquet  : {len(keywords):,} 행 (fallback 용)")
    print(f"  references 보유 논문 : {n_papers_with_refs:,}")
    print(f"  references 부재 논문 : {n_papers_without:,} (refs-fallback 으로 시도)")

    # 사전 lookup 빌드
    concepts_lookup = build_concepts_primary_lookup()
    concepts_all_lookup = build_concepts_all_lookup()
    canonical_id_primary = build_canonical_id_primary_lookup()
    journals_by_id, journals_by_surface = build_journals_horizon_lookups()
    authors_horizon = build_authors_horizon_lookup()
    print(f"\n=== 사전 lookup ===")
    print(f"  concepts primary surfaces (학자/인물/원전/문헌) : {len(concepts_lookup):,}")
    print(f"  concepts ALL surfaces      (+ 학파/개념)        : {len(concepts_all_lookup):,}")
    print(f"  canonical_id → primary 매핑                     : {len(canonical_id_primary):,}")
    print(f"  journals by canonical_id   : {len(journals_by_id):,}")
    print(f"  journals by surface        : {len(journals_by_surface):,}")
    print(f"  authors horizon surfaces   : {len(authors_horizon):,}")

    # 언어 / horizon 탐지
    print(f"\n=== Detection ===")
    primary_mask = refs["tier"] == "primary"
    secondary_mask = refs["tier"] == "secondary"
    print(f"  tier=primary   : {primary_mask.sum():,}건 → primary_source_basis 탐지")
    print(f"  tier=secondary : {secondary_mask.sum():,}건 → secondary_source_horizon 탐지")

    refs["_detected_primary"] = ""
    refs["_detected_secondary"] = ""

    refs.loc[primary_mask, "_detected_primary"] = (
        refs.loc[primary_mask].apply(
            lambda r: detect_primary_language(r, concepts_lookup), axis=1
        )
    )
    refs.loc[secondary_mask, "_detected_secondary"] = (
        refs.loc[secondary_mask].apply(
            lambda r: detect_secondary_horizon(
                r, journals_by_id, journals_by_surface, authors_horizon
            ),
            axis=1,
        )
    )

    print(f"\n--- reference-level primary 분포 (tier=primary {primary_mask.sum():,}건) ---")
    print(refs.loc[primary_mask, "_detected_primary"].value_counts().to_string())

    print(f"\n--- reference-level secondary 분포 (tier=secondary {secondary_mask.sum():,}건) ---")
    print(refs.loc[secondary_mask, "_detected_secondary"].value_counts().to_string())

    # paper 인덱싱 (제목 lookup)
    title_by_id = dict(zip(papers["논문 ID"], papers["논문명"].fillna("")))
    # 키워드 인덱싱 (paper → keyword list + canonical_id list)
    kw_grouped = keywords.groupby("논문ID")
    kw_text_by_id: dict[str, list[str]] = {}
    kw_canon_by_id: dict[str, list[str]] = {}
    for pid, g in kw_grouped:
        kw_text_by_id[pid] = g["키워드_원본"].fillna("").astype(str).tolist()
        kw_canon_by_id[pid] = g["canonical_id"].dropna().astype(str).tolist()

    def _infer_primary_from_keywords_title(pid: str) -> Counter:
        """키워드 + canonical_id + 제목 에서 primary 값 분포 추정."""
        c: Counter = Counter()
        # (a) keyword canonical_id 매칭
        for cid in kw_canon_by_id.get(pid, []):
            if cid in canonical_id_primary:
                c[canonical_id_primary[cid]] += 1
        # (b) keyword 원본 surface 매칭 (ALL types — 학파·개념 포함)
        for kw in kw_text_by_id.get(pid, []):
            for v in detect_primary_from_text(kw, concepts_all_lookup):
                c[v] += 1
        # (c) 제목 surface 매칭
        title = title_by_id.get(pid, "")
        for v in detect_primary_from_text(title, concepts_all_lookup):
            c[v] += 1
        return c

    # paper 단위 집계
    print(f"\n=== Paper-level 집계 ===")
    rows: list[dict] = []
    n_refs_based = 0
    n_kw_title_fallback = 0
    n_still_unknown = 0
    for paper_id, group in refs.groupby("논문ID"):
        primary_vals = group.loc[group["tier"] == "primary", "_detected_primary"]
        secondary_vals = group.loc[group["tier"] == "secondary", "_detected_secondary"]
        primary_dist = Counter(primary_vals.tolist())
        secondary_dist = Counter(secondary_vals.tolist())
        primary_basis = aggregate_label(primary_dist)
        basis_source = "refs"
        n_inferred = 0

        # fallback: refs 기반 unknown 인 경우 키워드/제목 으로 추정
        if primary_basis == "unknown":
            inferred_dist = _infer_primary_from_keywords_title(paper_id)
            if inferred_dist:
                inferred_basis = aggregate_label(inferred_dist)
                if inferred_basis != "unknown":
                    primary_basis = inferred_basis
                    primary_dist = inferred_dist  # 분포도 fallback 으로 교체
                    basis_source = "keywords_title"
                    n_inferred = sum(inferred_dist.values())

        if basis_source == "refs" and primary_basis != "unknown":
            n_refs_based += 1
        elif basis_source == "keywords_title":
            n_kw_title_fallback += 1
        else:
            n_still_unknown += 1

        rows.append({
            "논문ID": paper_id,
            "primary_source_basis": primary_basis,
            "secondary_source_horizon": aggregate_label(secondary_dist),
            "primary_basis_source": basis_source,
            "n_primary": int(group.loc[group["tier"] == "primary"].shape[0]),
            "n_secondary": int(sum(secondary_dist.values())),
            "n_inferred": n_inferred,
            "primary_dist": json.dumps(dict(primary_dist), ensure_ascii=False),
            "secondary_dist": json.dumps(dict(secondary_dist), ensure_ascii=False),
        })

    # references 없는 논문 — 키워드/제목 fallback 시도
    paper_ids_in_refs = set(refs["논문ID"].unique())
    all_paper_ids = set(papers["논문 ID"].dropna().unique())
    missing = all_paper_ids - paper_ids_in_refs
    for pid in missing:
        inferred_dist = _infer_primary_from_keywords_title(pid)
        primary_basis = "unknown"
        basis_source = "none"
        n_inferred = 0
        if inferred_dist:
            inferred_basis = aggregate_label(inferred_dist)
            if inferred_basis != "unknown":
                primary_basis = inferred_basis
                basis_source = "keywords_title"
                n_inferred = sum(inferred_dist.values())
                n_kw_title_fallback += 1
            else:
                n_still_unknown += 1
        else:
            n_still_unknown += 1

        rows.append({
            "논문ID": pid,
            "primary_source_basis": primary_basis,
            "secondary_source_horizon": "unknown",
            "primary_basis_source": basis_source,
            "n_primary": 0,
            "n_secondary": 0,
            "n_inferred": n_inferred,
            "primary_dist": json.dumps(dict(inferred_dist), ensure_ascii=False) if inferred_dist else "{}",
            "secondary_dist": "{}",
        })

    print(f"\n  primary basis source 분포 (전체 {len(rows)} 논문):")
    print(f"    refs 기반 (refs)            : {n_refs_based}")
    print(f"    keyword/title fallback      : {n_kw_title_fallback}")
    print(f"    여전히 unknown (none)       : {n_still_unknown}")

    out = pd.DataFrame(rows)
    print(f"  paper rows : {len(out):,} (refs 보유 {n_papers_with_refs} + 부재 {len(missing)})")

    print(f"\n--- primary_source_basis 분포 (636 논문) ---")
    print(out["primary_source_basis"].value_counts().to_string())
    print(f"\n--- secondary_source_horizon 분포 (636 논문) ---")
    print(out["secondary_source_horizon"].value_counts().to_string())

    # 교차 분포 (의존도 패턴 미리보기)
    print(f"\n--- cross-tab: primary × secondary ---")
    ct = pd.crosstab(
        out["primary_source_basis"], out["secondary_source_horizon"],
        margins=True, margins_name="합계",
    )
    print(ct.to_string())

    if args.dry_run:
        print("\n[dry-run] paper_labels.parquet 저장 안 함.")
        return 0

    out.to_parquet(OUT_PATH, index=False)
    print(f"\n✅ {OUT_PATH.relative_to(ROOT)} 저장 완료 ({len(out):,} 행).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
