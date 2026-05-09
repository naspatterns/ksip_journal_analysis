"""processed parquet 4종을 읽고 공통 필터를 적용하는 데이터 액세스 레이어.

Streamlit-독립 (캐시는 호출자가 @st.cache_data로 감쌀 것).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def load_papers() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "papers.parquet")


def load_authors() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "authors.parquet")


def load_keywords() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "keywords.parquet")


def load_references() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED_DIR / "references.parquet")


def load_journal_metrics() -> pd.DataFrame:
    """KCI citationDetail의 17년 시계열 (단계 1 산출). 파일 없으면 빈 DF."""
    p = PROCESSED_DIR / "journal_metrics.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def load_journal_history() -> pd.DataFrame:
    """학술지 등재 단계 변천사 (단계 1 산출). 파일 없으면 빈 DF."""
    p = PROCESSED_DIR / "journal_change_history.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def load_journal_static_meta() -> dict:
    """학술지 정적 메타(이름·ISSN·창간·발행자 등) 1행 dict.

    journal_static_meta.csv를 사용. 파일 없으면 빈 dict.
    """
    p = PROCESSED_DIR / "journal_static_meta.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


# ────────────────────────────────────────────────────────────
# KCI articleDetail 산출물 (단계 2 — articleDetail × 636)
# 별도 파일로 유지. 페이지에서 필요 시 JOIN.
# ────────────────────────────────────────────────────────────
def load_kci_papers() -> pd.DataFrame:
    """KCI articleDetail에서 회수한 논문 단위 enrichment.

    핵심 컬럼: 논문ID, fwci, kci_citation_count, title_english, kci_categories,
    kci_verified, kci_url, abstract_english_len 등.
    파일 없으면 빈 DF.
    """
    p = PROCESSED_DIR / "kci_papers.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def load_kci_authors() -> pd.DataFrame:
    """KCI articleDetail에서 회수한 저자 long-form (영문 저자명 포함).

    핵심 컬럼: 논문ID, 저자_원본, 저자_영문, 저자_소속_kci,
    author_division, author_part.
    """
    p = PROCESSED_DIR / "kci_authors.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def load_kci_references() -> pd.DataFrame:
    """KCI articleDetail에서 회수한 참고문헌 long-form (REFARTIID 포함).

    핵심 컬럼: 논문ID, 참조ID_kci, **cited_artiId**(REFARTIID),
    유형/유형코드, cited_제목, cited_저자, cited_학술지, cited_연도,
    cited_권/호/페이지, cited_발행기관, cited_DOI.

    A안: 인용 그래프의 권위 source. .xls 기반 references.parquet는
    fallback으로만 사용 (REFARTIID 정밀도 + KCI 검증 우선).
    """
    p = PROCESSED_DIR / "kci_references.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


@dataclass
class Filter:
    """페이지에 적용 가능한 필터 슬라이스. None = 미설정.

    지형도(app.py)는 year_range만 사용한다(클릭은 필터가 아니라 이동).
    인용의 풍경 페이지는 institution / author 필드를 활용해 ego-network 대상을
    좁힐 때 사용한다.
    """
    year_range: tuple[int, int] | None = None
    institution: str | None = None
    author: str | None = None

    def is_empty(self) -> bool:
        return self.year_range is None and self.institution is None and self.author is None

    def description(self) -> str:
        parts: list[str] = []
        if self.year_range:
            parts.append(f"{self.year_range[0]}–{self.year_range[1]}")
        if self.institution:
            parts.append(f"기관: {self.institution}")
        if self.author:
            parts.append(f"저자: {self.author}")
        return " · ".join(parts) if parts else "전체"


def apply_filter(papers: pd.DataFrame, authors: pd.DataFrame, f: Filter) -> pd.DataFrame:
    """필터 적용 후 살아남는 paper IDs(집합)을 정렬된 papers DF로 반환.

    저자 필터는 long-form authors 테이블을 거쳐서 paper 집합을 좁힌다.
    """
    df = papers
    if f.year_range is not None:
        lo, hi = f.year_range
        df = df[df["발행연도"].between(lo, hi)]
    if f.institution is not None:
        df = df[df["주저자 소속기관"].fillna("") == f.institution]
    if f.author is not None:
        author_paper_ids = set(
            authors.loc[authors["저자_원본"] == f.author, "논문ID"]
        )
        df = df[df["논문 ID"].isin(author_paper_ids)]
    return df


def filtered_views(f: Filter) -> dict[str, pd.DataFrame]:
    """필터 적용된 4개 집계용 long-form 뷰를 한꺼번에 반환.

    호출자가 한 번 받아서 4개 패널에 나눠 쓰면 됨.
    """
    papers = load_papers()
    authors = load_authors()
    keywords = load_keywords()

    f_papers = apply_filter(papers, authors, f)
    paper_ids = set(f_papers["논문 ID"])

    f_authors = authors[authors["논문ID"].isin(paper_ids)]
    f_keywords = keywords[keywords["논문ID"].isin(paper_ids)]

    return {
        "papers": f_papers,
        "authors": f_authors,
        "keywords": f_keywords,
    }
