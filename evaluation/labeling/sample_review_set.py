"""Phase 5 — 검수 표본 추출 (random 50 + low-confidence 50).

목적: Phase 4.4 의 자동 라벨링 (primary_source_basis + secondary_source_horizon)
결과를 사용자가 손으로 검수 → 잘못된 라벨 발견 → 사전·룰 환류.

표본 구성 (총 100 paper):
- random 50: 전체 636 paper 에서 무작위 (seed 고정).
- low-confidence 50: 다음 기준 중 하나라도 해당하는 paper 중 우선순위 순:
    (1) 두 라벨 중 하나라도 'mixed' (top 분포 50% 미만 plurality)
    (2) n_primary + n_secondary <= 3 (적은 refs)
    (3) primary_source_basis 가 unknown 이지만 secondary 가 있음 (왜 일차 없는지)
    (4) n_primary == 1 (single primary ref 만 가진 paper — 결정의 신뢰도 낮음)

산출 CSV (UTF-8 BOM, Excel 호환):
    evaluation/output/review_sample.csv

CSV columns:
    sampling_reason  | random / low_conf:<reason>
    논문ID
    발행연도
    논문명
    주저자_소속기관
    저자명
    primary_source_basis     | 자동 라벨
    secondary_source_horizon | 자동 라벨
    n_primary, n_secondary   | refs 카운트
    primary_dist             | json (분포)
    secondary_dist           | json
    검수_상태                | (빈칸 — 사용자 입력: OK / FIX / SKIP)
    교정_primary             | (빈칸 — FIX 시 수정값)
    교정_secondary           | (빈칸 — FIX 시 수정값)
    비고                     | (빈칸 — 검수 메모)

실행:
    .venv/bin/python evaluation/labeling/sample_review_set.py [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
PAPER_LABELS_PATH = ROOT / "data" / "processed" / "paper_labels.parquet"
PAPERS_PATH = ROOT / "data" / "processed" / "papers.parquet"
OUT_DIR = ROOT / "evaluation" / "output"
OUT_PATH = OUT_DIR / "review_sample.csv"


def _low_confidence_reasons(row) -> list[str]:
    """row 가 low-confidence 인지 판정 + 사유 list."""
    reasons: list[str] = []
    pb = row["primary_source_basis"]
    sh = row["secondary_source_horizon"]
    np_ = int(row["n_primary"])
    ns_ = int(row["n_secondary"])

    if pb == "mixed" or sh == "mixed":
        reasons.append("mixed_label")
    if np_ + ns_ <= 3 and np_ + ns_ > 0:
        reasons.append("few_refs")
    if pb == "unknown" and ns_ > 0:
        reasons.append("primary_unknown_with_secondary")
    if np_ == 1 and pb not in ("unknown",):
        reasons.append("single_primary_ref")

    return reasons


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42, help="random seed (재현용)")
    ap.add_argument("--n-random", type=int, default=50)
    ap.add_argument("--n-low", type=int, default=50)
    args = ap.parse_args()

    if not PAPER_LABELS_PATH.exists():
        print(f"❌ paper_labels.parquet not found at {PAPER_LABELS_PATH}", file=sys.stderr)
        return 1

    labels = pd.read_parquet(PAPER_LABELS_PATH)
    papers = pd.read_parquet(PAPERS_PATH)

    # join (labels.논문ID = papers.논문 ID)
    papers_subset = papers[["논문 ID", "논문명", "저자명", "주저자 소속기관", "발행연도"]].rename(
        columns={"논문 ID": "논문ID"}
    )
    merged = labels.merge(papers_subset, on="논문ID", how="left")

    print(f"=== 입력 ===")
    print(f"  paper_labels.parquet : {len(labels):,} 행")
    print(f"  papers.parquet       : {len(papers):,} 행")
    print(f"  merged               : {len(merged):,} 행")

    # low-confidence 식별
    merged["_low_reasons"] = merged.apply(_low_confidence_reasons, axis=1)
    merged["_is_low"] = merged["_low_reasons"].str.len() > 0
    low_pool = merged[merged["_is_low"]].copy()

    print(f"\n=== Low-confidence 집계 ===")
    print(f"  low-confidence 후보 : {len(low_pool):,} / {len(merged):,} ({len(low_pool)/len(merged):.1%})")
    # 사유별 카운트
    reason_counts: dict[str, int] = {}
    for reasons in merged["_low_reasons"]:
        for r in reasons:
            reason_counts[r] = reason_counts.get(r, 0) + 1
    for r, n in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"    {r:35} {n}")

    # low-confidence 50 추출 — 사유 다양성 위해 priority sort:
    # 우선순위: (1) primary_unknown_with_secondary > (2) mixed_label > (3) few_refs > (4) single_primary_ref
    priority_order = [
        "primary_unknown_with_secondary",
        "mixed_label",
        "few_refs",
        "single_primary_ref",
    ]
    def _priority(reasons: list[str]) -> int:
        for i, p in enumerate(priority_order):
            if p in reasons:
                return i
        return len(priority_order)
    low_pool["_priority"] = low_pool["_low_reasons"].apply(_priority)

    # 각 priority 그룹에서 골고루 추출
    low_sample = (
        low_pool.sort_values(["_priority", "논문ID"])
                .groupby("_priority", group_keys=False)
                .apply(lambda g: g.sample(n=min(len(g), args.n_low // 2), random_state=args.seed))
    )
    if len(low_sample) > args.n_low:
        low_sample = low_sample.sample(n=args.n_low, random_state=args.seed)
    elif len(low_sample) < args.n_low:
        # priority 그룹 부족 시 나머지에서 채우기
        remaining = low_pool[~low_pool["논문ID"].isin(low_sample["논문ID"])]
        more = remaining.sample(n=min(len(remaining), args.n_low - len(low_sample)),
                                 random_state=args.seed)
        low_sample = pd.concat([low_sample, more])

    low_sample = low_sample.copy()
    low_sample["sampling_reason"] = low_sample["_low_reasons"].apply(
        lambda rs: "low_conf:" + "+".join(sorted(rs))
    )

    # random 50: low_sample 와 겹치지 않게
    remaining_pool = merged[~merged["논문ID"].isin(low_sample["논문ID"])]
    random_sample = remaining_pool.sample(
        n=min(args.n_random, len(remaining_pool)), random_state=args.seed
    ).copy()
    random_sample["sampling_reason"] = "random"

    # 합치고 정렬 (random 먼저, 그 다음 low_conf)
    combined = pd.concat([random_sample, low_sample], ignore_index=True)
    combined = combined.sort_values(["sampling_reason", "발행연도", "논문ID"]).reset_index(drop=True)

    # 출력 컬럼 정리
    out_cols = [
        "sampling_reason",
        "논문ID",
        "발행연도",
        "논문명",
        "저자명",
        "주저자 소속기관",
        "primary_source_basis",
        "secondary_source_horizon",
        "n_primary",
        "n_secondary",
        "primary_dist",
        "secondary_dist",
    ]
    out = combined[out_cols].copy()
    # 검수 입력용 빈 컬럼
    out["검수_상태"] = ""           # OK / FIX / SKIP
    out["교정_primary"] = ""        # FIX 시 새 값 (sanskrit/pali/...)
    out["교정_secondary"] = ""      # FIX 시 새 값 (korean/japanese/...)
    out["비고"] = ""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # UTF-8 BOM → Excel 한글 호환
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n✅ {OUT_PATH.relative_to(ROOT)} 저장 완료 ({len(out)} rows).")

    # 통계
    print(f"\n=== 표본 통계 ({len(out)} rows) ===")
    print(f"  sampling_reason 분포:")
    for r, n in out["sampling_reason"].value_counts().items():
        print(f"    {r:50} {n}")

    print(f"\n  연도 분포:")
    print(out["발행연도"].value_counts().sort_index().to_string())

    print(f"\n  primary_source_basis 분포 (표본):")
    print(out["primary_source_basis"].value_counts().to_string())

    print(f"\n  secondary_source_horizon 분포 (표본):")
    print(out["secondary_source_horizon"].value_counts().to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
