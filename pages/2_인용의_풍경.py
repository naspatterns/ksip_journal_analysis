"""인용의 풍경 — 단일 엔터티(저자/기관)의 ego-network + 우측 정적 풍경.

진입: 지형도의 기관 트리맵 / 저자 막대 클릭 → query param `?entity=…&id=…`
디폴트: 동국대학교 (기관, 297편).
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ksip.citations import (
    REF_TYPE_COLORS,
    aggregate_targets,
    ego_network_figure,
    entity_summary,
    landscape_stats,
    paper_ids_for_entity,
    references_for,
)
from ksip.data import (
    load_authors,
    load_journal_metrics,
    load_journal_static_meta,
    load_papers,
)
import plotly.graph_objects as go

st.set_page_config(page_title="인용의 풍경", layout="wide")

# ────────────────────────────────────────────────────────────
# 사이드바
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.page_link("app.py", label="← 🗺️ 지형도로 돌아가기")
    st.markdown("---")
    st.subheader("다른 화면")
    st.page_link("pages/1_개념_탐험기.py", label="🔍 개념 탐험기")


# ────────────────────────────────────────────────────────────
# 캐시 데이터 로딩
# ────────────────────────────────────────────────────────────
@st.cache_data
def _institution_options() -> list[str]:
    papers = load_papers()
    return (
        papers["기관_부모"]
        .fillna("(미기재)")
        .value_counts()
        .index.tolist()
    )


@st.cache_data
def _author_options() -> list[str]:
    authors = load_authors()
    return authors["저자_원본"].value_counts().index.tolist()


@st.cache_data
def _refs_for_entity(entity_type: str, entity_id: str) -> pd.DataFrame:
    return references_for(paper_ids_for_entity(entity_type, entity_id))


@st.cache_data
def _summary(entity_type: str, entity_id: str) -> dict:
    return entity_summary(entity_type, entity_id)


@st.cache_data
def _landscape() -> dict:
    return landscape_stats()


@st.cache_data
def _journal_kpi() -> tuple[pd.DataFrame, dict]:
    return load_journal_metrics(), load_journal_static_meta()


# ────────────────────────────────────────────────────────────
# URL → 초기 entity
# ────────────────────────────────────────────────────────────
qs_entity = st.query_params.get("entity", "institution")
qs_id = st.query_params.get("id", "동국대학교")
if qs_entity not in ("institution", "author"):
    qs_entity = "institution"


# ────────────────────────────────────────────────────────────
# 헤더 + 엔터티 선택
# ────────────────────────────────────────────────────────────
st.title("📚 인용의 풍경")

sel_col1, sel_col2 = st.columns([1, 3])
with sel_col1:
    type_label = st.radio(
        "유형",
        ["기관", "저자"],
        horizontal=True,
        index=(0 if qs_entity == "institution" else 1),
        key="entity_type_radio",
    )
new_entity_type = "institution" if type_label == "기관" else "author"

with sel_col2:
    options = _institution_options() if new_entity_type == "institution" else _author_options()
    default_idx = options.index(qs_id) if qs_id in options else 0
    selected = st.selectbox(
        f"{type_label} 선택",
        options=options,
        index=default_idx,
        key=f"entity_id_select_{new_entity_type}",
    )

# URL 동기화
if st.query_params.get("entity") != new_entity_type:
    st.query_params["entity"] = new_entity_type
if st.query_params.get("id") != selected:
    st.query_params["id"] = selected


# ────────────────────────────────────────────────────────────
# 메인 데이터
# ────────────────────────────────────────────────────────────
summary = _summary(new_entity_type, selected)
all_refs = _refs_for_entity(new_entity_type, selected)
landscape = _landscape()


# ────────────────────────────────────────────────────────────
# 좌측(ego-network) | 우측(전체 풍경)
# ────────────────────────────────────────────────────────────
left, right = st.columns([3, 1])

# ═══════════════ 좌측 ═══════════════
with left:
    # 헤더 카드
    if summary["papers"] == 0:
        st.warning(f"'{selected}'에 해당하는 논문이 없습니다.")
        st.stop()
    yr = (
        f"{summary['year_min']}–{summary['year_max']}"
        if summary["year_min"] != summary["year_max"]
        else f"{summary['year_min']}"
    )
    st.markdown(f"### {selected}")
    st.markdown(
        f"논문 **{summary['papers']:,}편** · "
        f"인용 **{summary['refs']:,}건** · 활동 **{yr}**"
    )
    # KCI enrichment 메트릭 (있을 때만)
    if summary.get("avg_fwci") is not None or summary.get("total_kci_cite") is not None:
        m1, m2, m3, m4 = st.columns(4)
        if summary.get("avg_fwci") is not None:
            m1.metric("평균 FWCI", f"{summary['avg_fwci']:.2f}",
                      help="Field-Weighted Citation Impact 평균. "
                           "1.0 = 동분야 평균. 1보다 높으면 평균 이상의 영향력.")
        if summary.get("max_fwci") is not None:
            m2.metric("최대 FWCI", f"{summary['max_fwci']:.2f}")
        if summary.get("total_kci_cite") is not None:
            m3.metric("KCI 총 피인용", f"{summary['total_kci_cite']:,}",
                      help="이 엔터티의 논문들이 KCI에서 받은 피인용 횟수의 합.")
        if summary.get("avg_kci_cite") is not None:
            m4.metric("논문당 평균 피인용", f"{summary['avg_kci_cite']:.1f}")

    if all_refs.empty:
        st.info("이 엔터티의 논문에 등록된 참고문헌이 없습니다.")
        st.stop()

    # 필터
    f_col1, f_col2, f_col3 = st.columns([3, 1, 1])
    with f_col1:
        all_types = list(REF_TYPE_COLORS.keys())
        present_types = [t for t in all_types if t in all_refs["유형"].unique()]
        selected_types = st.multiselect(
            "인용 유형 (혼합 탭에서 표시될 유형들)",
            options=present_types,
            default=present_types,
            key="type_filter",
        )
    with f_col2:
        exclude_self = st.checkbox("자기인용 제외", value=False, key="excl_self")
    with f_col3:
        n_top = st.slider("표시 노드 수", 10, 50, 30, step=5, key="n_top")

    # 탭
    tab_mix, tab_journal, tab_book, tab_classic, tab_scholar = st.tabs(
        ["혼합", "학술지", "단행본", "원전(기타자료)", "학자"]
    )

    def _render_tab(types: list[str], hint: str = ""):
        agg = aggregate_targets(
            all_refs,
            n=n_top,
            type_filter=types if types else None,
            exclude_self=exclude_self,
        )
        if agg.empty:
            st.info("표시할 인용 대상이 없습니다 (필터 결과 비어있음).")
            return
        if hint:
            st.caption(hint)
        fig = ego_network_figure(selected, agg, height=580)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("표로 보기"):
            st.dataframe(
                agg[["label", "type", "count", "is_self"]].rename(
                    columns={"label": "인용 대상", "type": "유형",
                             "count": "횟수", "is_self": "자기인용"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_mix:
        _render_tab(selected_types, hint="여러 유형을 한 그래프에 색상으로 구분하여 표시합니다.")

    with tab_journal:
        _render_tab(["학술지(정기간행물)"],
                    hint="학술지명으로 집계 (canonical 적용).")

    with tab_book:
        _render_tab(["단행본"],
                    hint="단행본 저자로 집계.")

    with tab_classic:
        _render_tab(["기타자료"],
                    hint="원전 / 고전 텍스트 (제목으로 집계).")

    with tab_scholar:
        _render_tab(
            ["학술지(정기간행물)", "단행본", "학위논문", "학술대회논문", "보고서"],
            hint="저자가 명시된 모든 인용을 합산해 학자 단위로 집계.",
        )


# ═══════════════ 우측: 전체 풍경 (정적) ═══════════════
with right:
    # ─── 학술지 메타 카드 (KCI citationDetail 산출) ───
    metrics_df, journal_meta = _journal_kpi()
    if journal_meta:
        st.markdown(
            f"### 📖 {journal_meta.get('kor_name', '인도철학')}"
            f"  <span style='font-size:0.75em; color:#888'>"
            f"({journal_meta.get('kor_abbr', '')})</span>",
            unsafe_allow_html=True,
        )
        # 한 줄 메타: 창간 / 발행주기 / 현재호 / 등재상태
        st.caption(
            f"{journal_meta.get('창간연도', '')} 창간 · "
            f"ISSN {journal_meta.get('ISSN', '')} · "
            f"{journal_meta.get('현재_등재상태', '')} · "
            f"{journal_meta.get('현재호', '')}"
        )

    # ─── IF / 자기인용지수 시계열 (KCI citationDetail 산출) ───
    if not metrics_df.empty:
        st.markdown("**KCI 인용 지수 시계열**")
        fig_kpi = go.Figure()
        # IF (좌축, 파랑)
        fig_kpi.add_trace(go.Scatter(
            x=metrics_df["연도"], y=metrics_df["IF_2년"],
            mode="lines+markers", name="2년 IF",
            line=dict(color="#1f6feb", width=2),
            marker=dict(size=5),
            hovertemplate="%{x}년<br>IF=%{y:.2f}<extra></extra>",
        ))
        fig_kpi.add_trace(go.Scatter(
            x=metrics_df["연도"], y=metrics_df["IF_2년_자기인용제외"],
            mode="lines", name="자기인용 제외 IF",
            line=dict(color="#1f6feb", width=1, dash="dot"),
            hovertemplate="%{x}년<br>제외 IF=%{y:.2f}<extra></extra>",
        ))
        # 자기인용지수 (우축, 빨강) — 0~1 → %로 환산해 표시
        fig_kpi.add_trace(go.Scatter(
            x=metrics_df["연도"],
            y=metrics_df["자기인용지수"] * 100,
            mode="lines+markers", name="자기인용 %",
            line=dict(color="#E63946", width=1.5, dash="dash"),
            marker=dict(size=4, symbol="x"),
            yaxis="y2",
            hovertemplate="%{x}년<br>자기인용 %{y:.1f}%<extra></extra>",
        ))
        fig_kpi.update_layout(
            height=220,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(title="IF", title_standoff=4),
            yaxis2=dict(title="자기인용 %", overlaying="y", side="right",
                        title_standoff=4, range=[0, 60]),
            legend=dict(orientation="h", yanchor="top", y=-0.15,
                        xanchor="center", x=0.5, font=dict(size=9)),
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_kpi, use_container_width=True)
        st.caption(
            f"📊 17년치 KCI 공식 지수. "
            f"최근 IF {metrics_df['IF_2년'].iloc[-1]:.2f} · "
            f"자기인용 {metrics_df['자기인용지수'].iloc[-1]:.1%}"
        )

    st.markdown("---")
    st.markdown("### 인용 풍경 (전체)")
    st.caption(
        f"학술지 전체 {landscape['total_refs']:,}건 인용 · "
        f"자기인용 {landscape['self_cite_count']}건 ({landscape['self_cite_rate']:.1%})"
    )

    # 인용 유형 도넛
    type_dist = landscape["type_dist"]
    fig_donut = px.pie(
        names=type_dist.index,
        values=type_dist.values,
        hole=0.45,
        color=type_dist.index,
        color_discrete_map=REF_TYPE_COLORS,
    )
    fig_donut.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    fig_donut.update_traces(
        textposition="auto",
        textinfo="percent",
        textfont_size=11,
        hovertemplate="%{label}<br>%{value:,}건 (%{percent})<extra></extra>",
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    def _mini_bar(series: pd.Series, title: str, color: str):
        st.markdown(f"**{title}**")
        df = series.reset_index()
        df.columns = ["name", "count"]
        fig = px.bar(
            df, x="count", y="name",
            orientation="h",
            template="plotly_white",
        )
        fig.update_traces(marker_color=color)
        fig.update_layout(
            height=max(180, 22 * len(df)),
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(categoryorder="total ascending", title=None),
            xaxis=dict(title=None),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    _mini_bar(landscape["top_journals"],
              "TOP 인용 학술지",
              REF_TYPE_COLORS["학술지(정기간행물)"])
    _mini_bar(landscape["top_classics"],
              "TOP 인용 원전",
              REF_TYPE_COLORS["기타자료"])
    _mini_bar(landscape["top_scholars"],
              "TOP 인용 학자",
              REF_TYPE_COLORS["단행본"])
