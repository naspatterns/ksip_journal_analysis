"""개념 탐험기 — 키워드 한 개의 시계열 / 공출현 / 저자 / 대표 논문.

진입: 지형도의 키워드 셀렉터 → query param `?keyword=…`
디폴트: 키워드 없으면 '다르마키르티'로 데모.
표기 변형 처리: 통합(canonical) ↔ 표기별 분리 토글.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ksip.concepts import (
    authors_for_concept,
    concept_summary,
    cooccurrence,
    papers_for_concept,
    representative_papers,
    time_series,
)
from ksip.data import load_keywords

st.set_page_config(page_title="개념 탐험기", layout="wide")

# ────────────────────────────────────────────────────────────
# 사이드바
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("app.py", label="← 🗺️ 지형도로 돌아가기")
    st.markdown("---")
    st.subheader("다른 화면")
    st.page_link("pages/2_인용의_풍경.py", label="📚 인용의 풍경")


# ────────────────────────────────────────────────────────────
# 캐시 데이터
# ────────────────────────────────────────────────────────────
@st.cache_data
def _keyword_options() -> list[str]:
    return load_keywords()["키워드_원본"].value_counts().index.tolist()


@st.cache_data
def _summary(focal: str, mode: str) -> dict:
    return concept_summary(focal, mode)  # type: ignore[arg-type]


@st.cache_data
def _papers_for(focal: str, mode: str) -> tuple[list[str], str | None, str]:
    ids, cid, cf = papers_for_concept(focal, mode)  # type: ignore[arg-type]
    return list(ids), cid, cf


@st.cache_data
def _time_series(paper_ids: tuple, focal: str, cid: str | None, mode: str) -> pd.DataFrame:
    return time_series(set(paper_ids), focal, cid, mode)  # type: ignore[arg-type]


@st.cache_data
def _cooccurrence(paper_ids: tuple, focal: str, cid: str | None, mode: str, n: int) -> pd.DataFrame:
    return cooccurrence(set(paper_ids), focal, cid, mode, n)  # type: ignore[arg-type]


@st.cache_data
def _authors(paper_ids: tuple, n: int) -> pd.DataFrame:
    return authors_for_concept(set(paper_ids), n)


@st.cache_data
def _representative(paper_ids: tuple, n: int) -> pd.DataFrame:
    return representative_papers(set(paper_ids), n)


# ────────────────────────────────────────────────────────────
# URL → 초기 키워드
# ────────────────────────────────────────────────────────────
qs_keyword = st.query_params.get("keyword", "다르마키르티")
options = _keyword_options()
if qs_keyword not in options:
    qs_keyword = options[0] if options else "다르마키르티"


# ────────────────────────────────────────────────────────────
# 헤더 + 키워드 선택 + 모드 토글
# ────────────────────────────────────────────────────────────
st.title("🔍 개념 탐험기")

c1, c2 = st.columns([3, 1])
with c1:
    selected = st.selectbox(
        "키워드 선택",
        options=options,
        index=options.index(qs_keyword),
        key="kw_select",
    )
with c2:
    mode_label = st.radio(
        "표기 처리",
        ["통합", "표기별 분리"],
        horizontal=True,
        key="mode_radio",
        help="통합: 같은 개념의 표기 변형(예: 다르마키르티 / 다르마끼르띠)을 합산. "
             "분리: 각 표기를 별도로 표시.",
    )
mode = "unified" if mode_label == "통합" else "split"

# URL 동기화
if st.query_params.get("keyword") != selected:
    st.query_params["keyword"] = selected


# ────────────────────────────────────────────────────────────
# 데이터
# ────────────────────────────────────────────────────────────
summary = _summary(selected, mode)
paper_ids_list, cid, cf = _papers_for(selected, mode)
paper_ids_tuple = tuple(sorted(paper_ids_list))


# ────────────────────────────────────────────────────────────
# 헤더 카드
# ────────────────────────────────────────────────────────────
title_line = f"### {summary['canonical_form']}"
if summary["canonical_form"] != selected and mode == "unified":
    title_line += f" *(선택: {selected})*"

extras = summary["extras"] or {}
meta_bits = []
if extras.get("type"):
    meta_bits.append(f"**{extras['type']}**")
if extras.get("era"):
    meta_bits.append(extras["era"])
if extras.get("canonical_iast"):
    meta_bits.append(f"*{extras['canonical_iast']}*")
if extras.get("canonical_zh"):
    meta_bits.append(extras["canonical_zh"])

if summary["papers_count"] == 0:
    st.warning(f"'{selected}'에 해당하는 논문이 없습니다.")
    st.stop()

yr = (
    f"{summary['year_min']}–{summary['year_max']}"
    if summary["year_min"] != summary["year_max"]
    else f"{summary['year_min']}"
)

st.markdown(title_line)
if meta_bits:
    st.caption(" · ".join(meta_bits))
st.markdown(
    f"**{summary['papers_count']}편**의 논문 · 활동 **{yr}**"
)

# 별칭 표
variants = summary["variants"]
if cid and len(variants) > 1:
    with st.expander(f"이 개념의 표기 변형 {len(variants)}개 통합 보기", expanded=False):
        st.dataframe(variants, use_container_width=True, hide_index=True)
elif extras.get("notes"):
    st.caption(f"💡 {extras['notes']}")

st.markdown("---")


# ────────────────────────────────────────────────────────────
# 4분할 그리드
# ────────────────────────────────────────────────────────────
top_left, top_right = st.columns(2)
bot_left, bot_right = st.columns(2)


# ① 시계열 빈도
with top_left:
    st.subheader("① 연도별 등장 빈도")
    ts = _time_series(paper_ids_tuple, selected, cid, mode)
    if ts.empty:
        st.info("시계열 데이터 없음.")
    else:
        fig = px.line(
            ts, x="발행연도", y="count", color="label",
            markers=True, template="plotly_white",
        )
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=10),
            hovermode="x unified",
            yaxis_title="논문 수",
            legend_title="표기" if mode == "split" else None,
            showlegend=(mode == "split"),
        )
        st.plotly_chart(fig, use_container_width=True)


# ② 공출현 키워드
with top_right:
    st.subheader("② 공출현 키워드 TOP 10")
    co = _cooccurrence(paper_ids_tuple, selected, cid, mode, 10)
    if co.empty:
        st.info("공출현 데이터 없음.")
    else:
        fig = px.bar(
            co, x="count", y="display",
            orientation="h", template="plotly_white",
        )
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(categoryorder="total ascending", title=None),
            xaxis_title="공출현 논문 수",
        )
        fig.update_traces(marker_color="#4C72B0")
        st.plotly_chart(fig, use_container_width=True)


# ③ 저자 TOP 10
with bot_left:
    st.subheader("③ 이 개념을 다룬 저자 TOP 10")
    au = _authors(paper_ids_tuple, 10)
    if au.empty:
        st.info("저자 데이터 없음.")
    else:
        fig = px.bar(
            au, x="논문 수", y="저자",
            orientation="h", template="plotly_white",
        )
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(categoryorder="total ascending", title=None),
        )
        fig.update_traces(marker_color="#55A868")
        st.plotly_chart(fig, use_container_width=True)


# ④ 대표 논문 카드
with bot_right:
    st.subheader("④ 대표 논문 (인용 순)")
    rp = _representative(paper_ids_tuple, 10)
    if rp.empty:
        st.info("논문 데이터 없음.")
    else:
        for _, r in rp.iterrows():
            with st.container(border=True):
                title = r.get("논문명", "(제목 없음)")
                year = r.get("발행연도", "?")
                authors = r.get("저자명", "")
                cite = int(r.get("인용된 총 횟수", 0))
                inst = r.get("주저자 소속기관", "") or ""
                doi = r.get("DOI", "") or ""
                url = r.get("URL", "") or ""
                abstract = r.get("초록", "") or ""

                st.markdown(f"**{title}**")
                meta_row = f"`{year}` · {authors}"
                if inst:
                    meta_row += f" · {inst}"
                meta_row += f" · 인용 **{cite}**회"
                st.caption(meta_row)
                if abstract:
                    abs_short = abstract.strip()[:200]
                    if len(abstract) > 200:
                        abs_short += "…"
                    st.write(abs_short)
                links = []
                if url:
                    links.append(f"[KCI 원문]({url})")
                if doi and isinstance(doi, str) and doi.strip():
                    if not doi.startswith("http"):
                        links.append(f"[DOI](https://doi.org/{doi})")
                    else:
                        links.append(f"[DOI]({doi})")
                if links:
                    st.markdown(" · ".join(links))
