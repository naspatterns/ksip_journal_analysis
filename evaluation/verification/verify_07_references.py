"""L8 — 참고문헌 파싱 무결성.

확인:
- 12,887건 reference 가 7유형으로 분류
- 각 유형의 null 필드 비율 (저자·연도·제목 등 누락)
- 자기인용 312건 (학술지명 == "인도철학")
- 유형별 sample 30건 export → 수동 검수
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from _common import REFERENCES_PARQUET, CheckRun, ensure_output_dir


def main() -> int:
    run = CheckRun("L8")
    out_dir = ensure_output_dir()

    refs = pd.read_parquet(REFERENCES_PARQUET)
    run.info("refs_total", f"references rows = {len(refs)}", n_affected=len(refs))
    run.info("refs_cols", f"cols = {list(refs.columns)}")

    # 1) 유형 분포 — 기대 7유형
    type_col = "유형" if "유형" in refs.columns else (
        "참고문헌_유형" if "참고문헌_유형" in refs.columns else None)
    if not type_col:
        # 컬럼 이름 추측
        candidates = [c for c in refs.columns if "유형" in c or "type" in c.lower()]
        if candidates:
            type_col = candidates[0]
    if type_col:
        type_dist = refs[type_col].value_counts(dropna=False)
        run.info("refs_type_dist",
                 f"{type_col} 분포: {dict(type_dist)}", n_affected=len(type_dist))
        # 7유형 (단행본/학술지/학위논문/학술대회/보고서/인터넷자원/기타자료) 기대
        n_types = type_dist[type_dist > 0].shape[0]
        if n_types == 7:
            run.pass_("refs_seven_types", f"7유형 분류 정확 (실제 {n_types})")
        elif 5 <= n_types <= 9:
            run.info("refs_seven_types",
                     f"{n_types}유형 — 기대 7과 차이",
                     n_affected=n_types)
        else:
            run.warn("refs_seven_types",
                     f"{n_types}유형 — 기대 7에서 큰 차이",
                     n_affected=n_types)
    else:
        run.fatal("refs_type_col",
                  "references.parquet 에 유형 컬럼을 찾을 수 없음")

    # 2) 핵심 필드 null 비율
    for col in ["저자", "발행연도", "제목", "학술지명", "출판사"]:
        if col in refs.columns:
            n_null = refs[col].isna().sum()
            ratio = n_null / len(refs) * 100
            sev = "info"
            msg = f"refs.{col} null = {n_null} ({ratio:.1f}%)"
            if ratio > 80:
                run.warn(f"refs_null_{col}", msg + " — 매우 높음", n_affected=int(n_null))
            else:
                run.info(f"refs_null_{col}", msg, n_affected=int(n_null))

    # 3) 자기인용 — boolean 컬럼 우선, 없으면 학술지_원본 매칭
    if "자기인용" in refs.columns:
        n_self_flag = int(refs["자기인용"].fillna(False).astype(bool).sum())
        if 280 <= n_self_flag <= 350:
            run.pass_("refs_self_citation_flag",
                      f"자기인용 boolean 컬럼 합 {n_self_flag} (기대 ~312)",
                      n_affected=n_self_flag)
        else:
            run.warn("refs_self_citation_flag",
                     f"자기인용 boolean 합 {n_self_flag} — 기대 312 과 차이",
                     n_affected=n_self_flag)
    journal_col = "학술지_원본" if "학술지_원본" in refs.columns else (
        "학술지명" if "학술지명" in refs.columns else None)
    if journal_col:
        # 대소문자 / 한글 표기 변형 고려: exact "인도철학" 매칭
        self_cite = refs[journal_col].astype(str).str.strip() == "인도철학"
        n_self = int(self_cite.sum())
        # CLAUDE.md 기대: 312건 / 2.4%
        ratio = n_self / len(refs) * 100
        if 280 <= n_self <= 350:
            run.pass_("refs_self_citation",
                      f"자기인용 {n_self}건 ({ratio:.2f}%) — 기대 ~312, 2.4%",
                      n_affected=n_self)
        else:
            run.warn("refs_self_citation",
                     f"자기인용 {n_self}건 — 기대 312과 차이 {abs(n_self-312)}",
                     n_affected=n_self)

        # 학술지명 변형 점검 — 인도철학 변형으로 누락된 자기인용이 있을 가능성
        possible_self = refs[journal_col].astype(str).str.contains("인도철학", regex=False, na=False).sum()
        if possible_self > n_self:
            run.info("refs_self_citation_variants",
                     f"'인도철학' substring 매칭 {possible_self} > exact {n_self}",
                     n_affected=int(possible_self - n_self))

    # 4) 유형별 sample 30건 (수동 검수용)
    if type_col:
        samples = []
        for t, sub in refs.groupby(type_col):
            samples.append(sub.sample(min(30, len(sub)), random_state=42))
        if samples:
            sample_df = pd.concat(samples, ignore_index=True)
            path = out_dir / "verify_07_references_sample.csv"
            sample_df.to_csv(path, index=False, encoding="utf-8")
            run.info("refs_sample_saved",
                     f"유형별 sample {len(sample_df)}건 → {path.name}",
                     n_affected=len(sample_df))

    # 5) 빈 row (모든 필드 null) 점검
    if refs.shape[1] >= 2:
        empty = refs.drop(columns=[refs.columns[0]]).isna().all(axis=1)
        n_empty = int(empty.sum())
        if n_empty > 0:
            run.warn("refs_empty_rows",
                     f"모든 필드 null 인 row {n_empty}건", n_affected=n_empty)
        else:
            run.pass_("refs_empty_rows", "빈 row 없음")

    run.print_summary()
    run.to_csv(out_dir / "verify_07_references.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
