"""개념 탐험기 페이지 — 키워드 한 개의 시계열 / 공출현 / 저자 / 대표 논문.

순수 Python (Streamlit 의존 없음).

`mode` 두 가지:
- "unified": 표기 변형(canonical_id)을 통합해 집계 (e.g., 다르마키르티 + 다르마끼르띠)
- "split":   surface form 그대로 분리해 집계
"""
from __future__ import annotations

from typing import Literal

import pandas as pd

from .data import load_authors, load_keywords, load_papers
from .normalize import load_authority

Mode = Literal["unified", "split"]


# ────────────────────────────────────────────────────────────
# 키워드 ↔ 캐노니컬 해상도
# ────────────────────────────────────────────────────────────
def resolve_keyword(surface: str) -> tuple[str | None, str]:
    """surface 키워드 → (canonical_id, canonical_form). 미등재면 (None, surface)."""
    auth = load_authority("concepts")
    cid = auth.resolve(surface)
    if cid:
        return cid, auth.canonical_form(cid)
    return None, surface


def variants_for(canonical_id: str | None, surface: str) -> pd.DataFrame:
    """캐노니컬에 속한 모든 surface 변형 + 본 데이터에 등장한 빈도(파일 내 사용수).

    canonical_id None이면 입력 surface 행만.
    """
    keywords = load_keywords()
    if canonical_id is None:
        sub = keywords[keywords["키워드_원본"] == surface]
    else:
        sub = keywords[keywords["canonical_id"] == canonical_id]
    counts = sub["키워드_원본"].value_counts().reset_index()
    counts.columns = ["variant", "count"]
    return counts


def _display_for(canonical_id: str | None, surface: str) -> str:
    """집계 단위 라벨: canonical 있으면 canonical_form, 없으면 surface."""
    if canonical_id:
        return load_authority("concepts").canonical_form(canonical_id)
    return surface


# ────────────────────────────────────────────────────────────
# 그 개념의 논문 집합
# ────────────────────────────────────────────────────────────
def papers_for_concept(focal: str, mode: Mode) -> tuple[set[str], str | None, str]:
    """focal에 해당하는 paper IDs + canonical_id + display_form."""
    keywords = load_keywords()
    canonical_id, canonical_form = resolve_keyword(focal)
    if mode == "unified" and canonical_id:
        paper_ids = set(keywords.loc[keywords["canonical_id"] == canonical_id, "논문ID"])
    else:
        paper_ids = set(keywords.loc[keywords["키워드_원본"] == focal, "논문ID"])
    return paper_ids, canonical_id, canonical_form


# ────────────────────────────────────────────────────────────
# 시계열 빈도
# ────────────────────────────────────────────────────────────
def time_series(paper_ids: set[str], focal: str, canonical_id: str | None, mode: Mode) -> pd.DataFrame:
    """연도별 빈도. unified: 단일 라인. split + canonical: variant별 라인."""
    keywords = load_keywords()
    sub = keywords[keywords["논문ID"].isin(paper_ids)].copy()

    if mode == "unified":
        # focal 캐노니컬에 속한 모든 행
        if canonical_id:
            sub = sub[sub["canonical_id"] == canonical_id]
            label = _display_for(canonical_id, focal)
        else:
            sub = sub[sub["키워드_원본"] == focal]
            label = focal
        # 한 논문에 같은 canonical이 여러 번 등장할 수 있으니 논문별 1회로 카운트
        per_year = (
            sub.drop_duplicates(["논문ID", "발행연도"])
            .groupby("발행연도").size()
            .reset_index(name="count")
        )
        per_year["label"] = label
        return per_year[["발행연도", "label", "count"]]

    # split: variant별
    if canonical_id:
        sub = sub[sub["canonical_id"] == canonical_id]
    else:
        sub = sub[sub["키워드_원본"] == focal]
    sub = sub.drop_duplicates(["논문ID", "발행연도", "키워드_원본"])
    per = sub.groupby(["발행연도", "키워드_원본"]).size().reset_index(name="count")
    per = per.rename(columns={"키워드_원본": "label"})
    return per


# ────────────────────────────────────────────────────────────
# 공출현 키워드 TOP N
# ────────────────────────────────────────────────────────────
def cooccurrence(
    paper_ids: set[str],
    focal: str,
    canonical_id: str | None,
    mode: Mode,
    n: int = 10,
) -> pd.DataFrame:
    keywords = load_keywords()
    sub = keywords[keywords["논문ID"].isin(paper_ids)].copy()

    # focal 자기 자신은 제외
    if mode == "unified" and canonical_id:
        sub = sub[sub["canonical_id"].fillna("") != canonical_id]
    else:
        sub = sub[sub["키워드_원본"] != focal]

    if mode == "unified":
        # display: canonical이 있으면 canonical_form, 없으면 surface
        sub["display"] = sub.apply(
            lambda r: _display_for(r.get("canonical_id"), r["키워드_원본"]),
            axis=1,
        )
    else:
        sub["display"] = sub["키워드_원본"]

    if sub.empty:
        return pd.DataFrame(columns=["display", "count"])

    # 같은 (논문ID, display)를 한 번만 카운트 (논문 단위 공출현)
    sub = sub.drop_duplicates(["논문ID", "display"])
    counts = (
        sub["display"].value_counts().head(n).reset_index()
    )
    counts.columns = ["display", "count"]
    return counts


# ────────────────────────────────────────────────────────────
# 그 개념을 다룬 저자 TOP N
# ────────────────────────────────────────────────────────────
def authors_for_concept(paper_ids: set[str], n: int = 10) -> pd.DataFrame:
    authors = load_authors()
    sub = authors[authors["논문ID"].isin(paper_ids)]
    if sub.empty:
        return pd.DataFrame(columns=["저자", "논문 수"])
    counts = (
        sub["저자_원본"]
        .value_counts()
        .head(n)
        .reset_index()
    )
    counts.columns = ["저자", "논문 수"]
    return counts


# ────────────────────────────────────────────────────────────
# 대표 논문 (인용수 → 연도)
# ────────────────────────────────────────────────────────────
def representative_papers(paper_ids: set[str], n: int = 10) -> pd.DataFrame:
    papers = load_papers()
    sub = papers[papers["논문 ID"].isin(paper_ids)].copy()
    if sub.empty:
        return sub
    sub["인용된 총 횟수"] = pd.to_numeric(
        sub["인용된 총 횟수"], errors="coerce"
    ).fillna(0).astype(int)
    cols = ["논문명", "저자명", "발행연도", "인용된 총 횟수", "초록", "URL", "DOI", "주저자 소속기관"]
    cols = [c for c in cols if c in sub.columns]
    sub = sub[cols].sort_values(
        ["인용된 총 횟수", "발행연도"], ascending=[False, False]
    ).head(n)
    return sub


# ────────────────────────────────────────────────────────────
# 헤더용 요약
# ────────────────────────────────────────────────────────────
def concept_summary(focal: str, mode: Mode) -> dict:
    paper_ids, canonical_id, canonical_form = papers_for_concept(focal, mode)
    keywords = load_keywords()
    sub = keywords[keywords["논문ID"].isin(paper_ids)].copy()

    # variants
    if canonical_id:
        sub_focal = sub[sub["canonical_id"] == canonical_id]
    else:
        sub_focal = sub[sub["키워드_원본"] == focal]
    variants = (
        sub_focal["키워드_원본"]
        .value_counts()
        .reset_index()
    )
    variants.columns = ["variant", "count"]

    # 활동 연도
    if not sub_focal.empty:
        year_min = int(sub_focal["발행연도"].min())
        year_max = int(sub_focal["발행연도"].max())
    else:
        year_min = year_max = None

    # 캐노니컬 메타 (concepts.yml의 type, era 등)
    extras: dict = {}
    if canonical_id:
        rec = load_authority("concepts").records.get(canonical_id)
        if rec:
            extras = rec.extras

    return {
        "focal": focal,
        "canonical_id": canonical_id,
        "canonical_form": canonical_form,
        "papers_count": len(paper_ids),
        "year_min": year_min,
        "year_max": year_max,
        "variants": variants,
        "extras": extras,
    }
