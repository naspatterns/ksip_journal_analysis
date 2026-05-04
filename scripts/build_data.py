"""raw .xls → processed parquet 빌드 스크립트.

`python -m scripts.build_data` 또는 `python scripts/build_data.py`로 실행.
"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가 (scripts/에서 직접 실행 시)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ksip.load import explode_authors, explode_keywords, load_papers
from ksip.normalize import add_canonical_column
from ksip.references import load_references

RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] 논문목록 로드…")
    papers = load_papers(RAW_DIR)
    papers.to_parquet(OUT_DIR / "papers.parquet", index=False)
    print(f"      papers.parquet : {len(papers):,} rows")

    print("[2/4] 저자 long-form 분해 + 정규화…")
    authors = explode_authors(papers)
    authors = add_canonical_column(authors, "저자_원본", "authors")
    authors.to_parquet(OUT_DIR / "authors.parquet", index=False)
    n_resolved = authors["canonical_id"].notna().sum()
    print(f"      authors.parquet: {len(authors):,} rows ({authors['저자_원본'].nunique():,} unique surface) "
          f"· 정규화 {n_resolved:,}건({n_resolved/len(authors):.1%})")

    print("[3/4] 키워드 long-form 분해 + 정규화…")
    keywords = explode_keywords(papers)
    keywords = add_canonical_column(keywords, "키워드_원본", "concepts")
    keywords.to_parquet(OUT_DIR / "keywords.parquet", index=False)
    n_resolved = keywords["canonical_id"].notna().sum()
    print(f"      keywords.parquet: {len(keywords):,} rows ({keywords['키워드_원본'].nunique():,} unique surface) "
          f"· 정규화 {n_resolved:,}건({n_resolved/len(keywords):.1%})")

    print("[4/4] 참고문헌 파싱 + 학술지 정규화…")
    refs = load_references(RAW_DIR)
    refs = add_canonical_column(refs, "학술지_원본", "journals", out_col="학술지_canonical")
    refs.to_parquet(OUT_DIR / "references.parquet", index=False)
    self_cite_count = int(refs["자기인용"].sum())
    n_journal_resolved = refs["학술지_canonical"].notna().sum()
    print(f"      references.parquet: {len(refs):,} rows "
          f"(자기인용 {self_cite_count:,}건={self_cite_count/len(refs):.1%}) "
          f"· 학술지 정규화 {n_journal_resolved:,}건")

    print()
    print("✓ 빌드 완료 →", OUT_DIR)


if __name__ == "__main__":
    main()
