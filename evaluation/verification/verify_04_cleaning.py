"""L5 — 클리닝 단계 (단계 0.5) 검증.

확인:
- 논문명 클리닝: 119편 (CLAUDE.md) — papers.논문명 != papers.논문명_원본 인 행 수
- 키워드 PUA: 클리닝 후 keywords.키워드_원본 에 PUA 잔존 없음
- 동국대 14변형 → 297편 통합 — 기관_부모 == "동국대학교" 인 행 수
- clean_title / clean_keyword 함수의 멱등성 (재호출 동일 결과)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ksip.clean import _PUA_RE, clean_keyword, clean_title  # noqa: E402

from _common import (KEYWORDS_PARQUET, PAPERS_PARQUET, CheckRun,
                     ensure_output_dir)




def main() -> int:
    run = CheckRun("L5")

    papers = pd.read_parquet(PAPERS_PARQUET)
    keywords = pd.read_parquet(KEYWORDS_PARQUET)

    # 1) 논문명 클리닝 발생 수
    if "논문명_원본" in papers.columns:
        changed = (papers["논문명"].astype(str) != papers["논문명_원본"].astype(str))
        n_changed = int(changed.sum())
        # CLAUDE.md 기준 119편
        if 100 <= n_changed <= 140:
            run.pass_("title_cleaned_count",
                      f"논문명 클리닝 {n_changed}편 (기대 ~119)",
                      n_affected=n_changed)
        else:
            run.warn("title_cleaned_count",
                     f"논문명 클리닝 {n_changed}편 (기대 ~119, 차이 {abs(n_changed-119)})",
                     n_affected=n_changed)
    else:
        run.fatal("title_origin_backup",
                  "papers.논문명_원본 컬럼이 없음 — 원본 백업 누락")

    # 2) 클리닝 함수 멱등성 (논문명)
    re_cleaned = papers["논문명"].astype(str).map(clean_title)
    still_changing = (re_cleaned != papers["논문명"].astype(str)).sum()
    if still_changing > 0:
        run.warn("title_clean_idempotent",
                 f"clean_title 재호출 시 {still_changing}편이 추가 변경 — 멱등성 깨짐",
                 n_affected=int(still_changing))
    else:
        run.pass_("title_clean_idempotent",
                  "clean_title 멱등 (재호출 시 변경 없음)")

    # 3) 키워드 PUA 잔존 확인
    pua_remaining = keywords["키워드_원본"].astype(str).str.contains(_PUA_RE, regex=True, na=False)
    n_pua = int(pua_remaining.sum())
    if n_pua > 0:
        run.fatal("keyword_pua_remaining",
                  f"키워드에 PUA 문자 잔존 {n_pua}건",
                  n_affected=n_pua)
    else:
        run.pass_("keyword_pua_remaining", "키워드에 PUA 문자 없음")

    # 4) 키워드 클리닝 멱등성
    kw_recleaned = keywords["키워드_원본"].astype(str).map(clean_keyword)
    kw_change = (kw_recleaned != keywords["키워드_원본"].astype(str)).sum()
    if kw_change > 0:
        run.warn("keyword_clean_idempotent",
                 f"clean_keyword 재호출 시 {kw_change}건 변경 — 멱등성 깨짐",
                 n_affected=int(kw_change))
    else:
        run.pass_("keyword_clean_idempotent",
                  "clean_keyword 멱등")

    # 5) 동국대 통합 — 297편 기대
    if "기관_부모" in papers.columns:
        dongguk = (papers["기관_부모"] == "동국대학교").sum()
        if 280 <= dongguk <= 310:
            run.pass_("dongguk_rollup",
                      f"기관_부모 == '동국대학교' 인 논문 {dongguk}편 (기대 ~297)",
                      n_affected=int(dongguk))
        else:
            run.warn("dongguk_rollup",
                     f"기관_부모 == '동국대학교' 인 논문 {dongguk}편 (기대 ~297, 차이 {abs(dongguk-297)})",
                     n_affected=int(dongguk))

        # 동국대 surface form variants (raw 소속 → 부모=동국대 매핑된 surface 종류 수)
        raw_col = "주저자 소속기관" if "주저자 소속기관" in papers.columns else None
        if raw_col:
            dongguk_surfaces = papers.loc[papers["기관_부모"] == "동국대학교", raw_col].dropna().unique()
            n_variants = len(dongguk_surfaces)
            if 10 <= n_variants <= 25:
                run.pass_("dongguk_variants",
                          f"동국대로 매핑된 raw surface 변형 {n_variants}종 (기대 ~14)",
                          n_affected=n_variants)
            else:
                run.warn("dongguk_variants",
                         f"동국대로 매핑된 raw surface 변형 {n_variants}종 (기대 ~14)",
                         n_affected=n_variants)
            run.info("dongguk_variant_list",
                     f"동국대 surface: {sorted(dongguk_surfaces)[:5]} ...")

    # 6) 트레일링 underscore 잔존 확인 (논문명)
    trailing_us = papers["논문명"].astype(str).str.match(r".*_+\s*$")
    n_trail = int(trailing_us.sum())
    if n_trail > 0:
        run.warn("title_trailing_underscore",
                 f"논문명에 트레일링 underscore 잔존 {n_trail}건",
                 n_affected=n_trail)
    else:
        run.pass_("title_trailing_underscore",
                  "논문명 트레일링 underscore 없음")

    # 7) 빈 키워드 / 문장부호 단독 키워드 잔존
    bad_keywords = keywords["키워드_원본"].astype(str).str.match(r"^[\s.,;:!?\-\"'()]*$")
    n_bad = int(bad_keywords.sum())
    if n_bad > 0:
        run.warn("keyword_noise",
                 f"빈/문장부호 단독 키워드 {n_bad}건 — 노이즈",
                 n_affected=n_bad)
    else:
        run.pass_("keyword_noise", "노이즈 키워드 없음")

    run.print_summary()
    run.to_csv(ensure_output_dir() / "verify_04_cleaning.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
