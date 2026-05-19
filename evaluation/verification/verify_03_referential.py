"""L4 — Cross-parquet 논문ID 참조 무결성.

확인:
- papers.논문ID 가 primary key (unique, non-null)
- keywords·authors·references 의 논문ID ⊆ papers.논문ID (orphan 없음)
- 연도 일관성: papers.발행연도 vs keywords.발행연도 동일
"""
from __future__ import annotations

import sys

import pandas as pd

from _common import (AUTHORS_PARQUET, KEYWORDS_PARQUET, PAPERS_PARQUET,
                     REFERENCES_PARQUET, CheckRun, ensure_output_dir)


def main() -> int:
    run = CheckRun("L4")

    papers = pd.read_parquet(PAPERS_PARQUET)
    keywords = pd.read_parquet(KEYWORDS_PARQUET)
    authors = pd.read_parquet(AUTHORS_PARQUET)
    refs = pd.read_parquet(REFERENCES_PARQUET)

    # papers.논문ID 컬럼 식별
    paper_id_col = "논문 ID" if "논문 ID" in papers.columns else "논문ID"
    run.info("parquet_loaded",
             f"papers={len(papers)} kw={len(keywords)} authors={len(authors)} refs={len(refs)}",
             papers=len(papers), kw=len(keywords),
             authors=len(authors), refs=len(refs))

    # 1) papers.논문ID primary key
    n_total = len(papers)
    n_null = papers[paper_id_col].isna().sum()
    n_unique = papers[paper_id_col].nunique(dropna=True)
    if n_null > 0:
        run.fatal("papers_pk_null",
                  f"papers.{paper_id_col} 가 null 인 행 {n_null}개", n_affected=int(n_null))
    else:
        run.pass_("papers_pk_null", f"papers.{paper_id_col} 모두 non-null")
    if n_unique != n_total:
        run.fatal("papers_pk_unique",
                  f"papers.{paper_id_col} 중복 — total={n_total}, unique={n_unique}",
                  n_affected=n_total - n_unique)
    else:
        run.pass_("papers_pk_unique",
                  f"papers.{paper_id_col} 모두 unique (n={n_total})")

    papers_ids = set(papers[paper_id_col].dropna().astype(str))

    # 2) keywords.논문ID ⊆ papers
    kw_id_col = "논문ID" if "논문ID" in keywords.columns else "논문 ID"
    kw_orphans = set(keywords[kw_id_col].astype(str)) - papers_ids
    if kw_orphans:
        run.fatal("keywords_orphan",
                  f"keywords 의 {len(kw_orphans)}개 논문ID 가 papers 에 없음",
                  n_affected=len(kw_orphans))
    else:
        run.pass_("keywords_orphan", "keywords.논문ID ⊆ papers")

    # 3) authors.논문ID ⊆ papers
    auth_id_col = "논문ID" if "논문ID" in authors.columns else (
        "논문 ID" if "논문 ID" in authors.columns else authors.columns[0])
    auth_orphans = set(authors[auth_id_col].astype(str)) - papers_ids
    if auth_orphans:
        run.fatal("authors_orphan",
                  f"authors 의 {len(auth_orphans)}개 논문ID 가 papers 에 없음",
                  n_affected=len(auth_orphans))
    else:
        run.pass_("authors_orphan", "authors.논문ID ⊆ papers")

    # 4) references.논문ID ⊆ papers
    ref_id_col = "논문ID" if "논문ID" in refs.columns else "논문 ID"
    ref_orphans = set(refs[ref_id_col].astype(str)) - papers_ids
    if ref_orphans:
        run.fatal("references_orphan",
                  f"references 의 {len(ref_orphans)}개 논문ID 가 papers 에 없음",
                  n_affected=len(ref_orphans))
    else:
        run.pass_("references_orphan", "references.논문ID ⊆ papers")

    # 5) 연도 일관성 (papers vs keywords)
    if "발행연도" in keywords.columns and "발행연도" in papers.columns:
        merged = keywords.merge(
            papers[[paper_id_col, "발행연도"]].rename(columns={paper_id_col: kw_id_col}),
            on=kw_id_col, how="left", suffixes=("_kw", "_pap"))
        mismatch = (merged["발행연도_kw"].astype(str) != merged["발행연도_pap"].astype(str)).sum()
        if mismatch > 0:
            run.warn("keywords_year_consistency",
                     f"keywords 와 papers 발행연도 불일치 {mismatch} 건",
                     n_affected=int(mismatch))
        else:
            run.pass_("keywords_year_consistency",
                      "keywords.발행연도 == papers.발행연도")

    # 6) 모든 papers 가 author 를 가지나
    papers_with_author = set(authors[auth_id_col].astype(str))
    papers_no_author = papers_ids - papers_with_author
    if papers_no_author:
        run.warn("papers_without_author",
                 f"author 없는 논문 {len(papers_no_author)}건",
                 n_affected=len(papers_no_author))
    else:
        run.pass_("papers_without_author", "모든 논문이 1+ author 보유")

    # 7) papers 중 keyword 없는 것 (정보용)
    papers_with_kw = set(keywords[kw_id_col].astype(str))
    papers_no_kw = papers_ids - papers_with_kw
    if papers_no_kw:
        run.info("papers_without_keyword",
                 f"키워드 없는 논문 {len(papers_no_kw)}건 (저자 미입력 등)",
                 n_affected=len(papers_no_kw))

    # 8) papers 중 references 없는 것
    papers_with_ref = set(refs[ref_id_col].astype(str))
    papers_no_ref = papers_ids - papers_with_ref
    # CLAUDE.md: 482편 등록, 154편 미등록 (주로 1990년대 초)
    if abs(len(papers_no_ref) - 154) > 20:
        run.warn("papers_without_reference",
                 f"참고문헌 없는 논문 {len(papers_no_ref)}건 — "
                 f"기대 ~154편과 차이 {abs(len(papers_no_ref)-154)}",
                 n_affected=len(papers_no_ref))
    else:
        run.pass_("papers_without_reference",
                  f"참고문헌 없는 논문 {len(papers_no_ref)}건 (기대 ~154)",
                  n_affected=len(papers_no_ref))

    run.print_summary()
    run.to_csv(ensure_output_dir() / "verify_03_referential.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
