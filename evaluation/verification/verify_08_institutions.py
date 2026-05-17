"""L9 — 기관 부모(rollup) 무결성.

확인:
- 모든 raw 소속이 parent_institution() 로 매핑됨 (미해결률)
- 부모별 자식 surface 종류 (동국대 14변형 외 다른 큰 부모는?)
- 부모 미해결 surface TOP 30 (사전 보강 후보)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ksip.institutions import parent_institution  # noqa: E402

from _common import PAPERS_PARQUET, CheckRun, ensure_output_dir


def main() -> int:
    run = CheckRun("L9")
    out_dir = ensure_output_dir()

    papers = pd.read_parquet(PAPERS_PARQUET)

    raw_col = "주저자 소속기관"
    parent_col = "기관_부모"

    if raw_col not in papers.columns:
        run.fatal("raw_col_missing",
                  f"papers 에 '{raw_col}' 컬럼 없음")
        run.print_summary()
        run.to_csv(out_dir / "verify_08_institutions.csv")
        return 1
    if parent_col not in papers.columns:
        run.fatal("parent_col_missing",
                  f"papers 에 '{parent_col}' 컬럼 없음")
        run.print_summary()
        run.to_csv(out_dir / "verify_08_institutions.csv")
        return 1

    # 1) 부모 미해결 (NaN 또는 빈 문자열)
    no_parent = papers[parent_col].isna() | (papers[parent_col].astype(str).str.strip() == "")
    n_no_parent = int(no_parent.sum())
    if n_no_parent > 0:
        run.info("no_parent_rows",
                 f"부모 미해결 논문 {n_no_parent}건 (raw 소속은 있지만 매핑 실패)",
                 n_affected=n_no_parent)
        unresolved = papers.loc[no_parent, raw_col].value_counts().head(30)
        path = out_dir / "verify_08_institutions_unresolved.csv"
        unresolved.to_csv(path, encoding="utf-8")
        run.info("no_parent_top",
                 f"미해결 raw 소속 TOP 30 → {path.name}",
                 n_affected=len(unresolved))
    else:
        run.pass_("no_parent_rows", "모든 raw 소속이 부모로 매핑됨")

    # 2) 부모별 자식 surface 종류
    by_parent = papers.dropna(subset=[parent_col]).groupby(parent_col).agg(
        n_papers=(raw_col, "count"),
        n_raw_variants=(raw_col, "nunique"),
    ).sort_values("n_papers", ascending=False)
    path = out_dir / "verify_08_institutions_by_parent.csv"
    by_parent.to_csv(path, encoding="utf-8")
    run.info("by_parent_saved",
             f"부모 {len(by_parent)}종 × 자식 surface 통계 → {path.name}",
             n_affected=len(by_parent))

    # 3) parent_institution() 함수 멱등 확인
    # 무작위 50 raw 소속을 parent_institution() 으로 재계산해 컬럼과 비교
    sample = papers.dropna(subset=[raw_col]).sample(min(100, len(papers)), random_state=42)
    recomputed = sample[raw_col].astype(str).map(parent_institution)
    mismatch = (recomputed != sample[parent_col]).sum()
    if mismatch > 0:
        # NaN 처리 차이 가능성 — None vs nan
        mismatch_real = ((recomputed.fillna("") != sample[parent_col].fillna(""))).sum()
        if mismatch_real > 0:
            run.warn("parent_function_mismatch",
                     f"무작위 100개 중 parent_institution() 재계산과 기존 컬럼 불일치 {mismatch_real}건",
                     n_affected=int(mismatch_real))
        else:
            run.pass_("parent_function_mismatch",
                      "parent_institution() 재계산 일치 (NaN 차이만)")
    else:
        run.pass_("parent_function_mismatch",
                  "parent_institution() 재계산 100% 일치")

    # 4) 동국대 자기점검
    dongguk = papers[papers[parent_col] == "동국대학교"]
    n_dongguk = len(dongguk)
    n_dongguk_variants = dongguk[raw_col].nunique()
    run.info("dongguk_summary",
             f"동국대학교 = {n_dongguk}편, raw surface {n_dongguk_variants}종",
             n_affected=n_dongguk)

    # 5) TOP 10 부모 출력
    top10 = by_parent.head(10)
    run.info("top10_parents",
             f"TOP 10 부모: {top10.index.tolist()}")

    run.print_summary()
    run.to_csv(out_dir / "verify_08_institutions.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
