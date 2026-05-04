"""인도철학 학술지 — 지형도(메인 페이지).

순수 거시 풍경. 인터랙션 규칙 1개: 클릭 = 그 항목의 상세 화면으로 이동.
- 사이드바: 연도 슬라이더(유일한 필터) + 화면 네비게이션
- 4분할: 연도 라인(읽기 전용) / 기관 트리맵(클릭→인용 풍경) /
         키워드 워드클라우드+셀렉터(→개념 탐험기) / 저자 막대(클릭→인용 풍경)
"""
from __future__ import annotations

import platform
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

from ksip.data import load_authors, load_keywords, load_papers

# ────────────────────────────────────────────────────────────
# 페이지 설정
# ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="인도철학 지형도",
    layout="wide",
    initial_sidebar_state="expanded",
)

KOREAN_FONT_PATH = (
    "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    if platform.system() == "Darwin"
    else None
)
PLOTLY_TEMPLATE = "plotly_white"


# ────────────────────────────────────────────────────────────
# 데이터 로딩 (캐시)
# ────────────────────────────────────────────────────────────
@st.cache_data
def get_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_papers(), load_authors(), load_keywords()


papers_all, authors_all, keywords_all = get_data()
year_min = int(papers_all["발행연도"].min())
year_max = int(papers_all["발행연도"].max())

ss = st.session_state
ss.setdefault("year_range", (year_min, year_max))


# ────────────────────────────────────────────────────────────
# 사이드바 — 연도 + 네비게이션
# ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("연도 범위")
    new_year = st.slider(
        " ",
        min_value=year_min,
        max_value=year_max,
        value=ss["year_range"],
        step=1,
        label_visibility="collapsed",
    )
    if new_year != ss["year_range"]:
        ss["year_range"] = new_year

    st.markdown("---")
    st.subheader("다른 화면")
    st.page_link("pages/1_개념_탐험기.py", label="🔍 개념 탐험기")
    st.page_link("pages/2_인용의_풍경.py", label="📚 인용의 풍경")


# ────────────────────────────────────────────────────────────
# 연도 필터 적용
# ────────────────────────────────────────────────────────────
lo, hi = ss["year_range"]
papers = papers_all[papers_all["발행연도"].between(lo, hi)]
paper_ids = set(papers["논문 ID"])
authors = authors_all[authors_all["논문ID"].isin(paper_ids)]
keywords = keywords_all[keywords_all["논문ID"].isin(paper_ids)]


# ────────────────────────────────────────────────────────────
# 헤더
# ────────────────────────────────────────────────────────────
st.title("인도철학 학술지 지형도")
st.caption(
    f"{lo}–{hi} · 패널의 항목을 클릭하면 그 항목의 상세 화면으로 이동합니다."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("논문 수", f"{len(papers):,}")
c2.metric("저자 수 (unique)", f"{authors['저자_원본'].nunique():,}")
c3.metric("기관 수", f"{papers['주저자 소속기관'].dropna().nunique():,}")
c4.metric("키워드 종 수", f"{keywords['키워드_원본'].nunique():,}")

if len(papers) == 0:
    st.warning("선택한 연도 범위에 논문이 없습니다.")
    st.stop()


# ────────────────────────────────────────────────────────────
# 4분할 그리드
# ────────────────────────────────────────────────────────────
top_left, top_right = st.columns(2)
bot_left, bot_right = st.columns(2)


# ① 연도별 논문 수 라인 (읽기 전용)
with top_left:
    st.subheader("① 연도별 논문 수")
    yearly = papers.groupby("발행연도").size().reset_index(name="논문 수")
    fig1 = px.line(
        yearly, x="발행연도", y="논문 수",
        markers=True, template=PLOTLY_TEMPLATE,
    )
    fig1.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                       hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)


# ② 기관 트리맵 — 클릭 시 인용의 풍경(기관)으로 이동
with top_right:
    st.subheader("② 기관 분포")
    st.caption("셀을 클릭하면 그 기관의 인용 풍경으로 이동합니다.")

    inst = (
        papers["주저자 소속기관"].fillna("(미기재)").value_counts().reset_index()
    )
    inst.columns = ["기관", "논문 수"]
    fig2 = px.treemap(
        inst.head(50), path=["기관"], values="논문 수",
        color="논문 수", color_continuous_scale="Blues",
    )
    fig2.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    event2 = st.plotly_chart(
        fig2, use_container_width=True,
        on_select="rerun", selection_mode="points", key="treemap_inst",
    )
    if event2 and event2.selection and event2.selection["points"]:
        clicked = event2.selection["points"][0].get("label")
        sig = ("inst", clicked)
        if (clicked
                and clicked != "(미기재)"
                and ss.get("treemap_last_sig") != sig):
            ss["treemap_last_sig"] = sig
            ss.pop("treemap_inst", None)
            st.query_params.update({"entity": "institution", "id": clicked})
            st.switch_page("pages/2_인용의_풍경.py")


# ③ 키워드 워드클라우드 + 셀렉터
with bot_left:
    st.subheader("③ 키워드 워드클라우드")
    st.caption("아래 셀렉터에서 키워드를 골라 개념 탐험기로 이동하세요.")

    if len(keywords) > 0:
        kw_text = " ".join(keywords["키워드_원본"].astype(str).tolist())
        wc = WordCloud(
            font_path=KOREAN_FONT_PATH,
            width=900, height=430,
            background_color="white",
            collocations=False,
            max_words=80,
        ).generate(kw_text)
        fig_wc, ax = plt.subplots(figsize=(9, 4.3), dpi=120)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        buf = BytesIO()
        fig_wc.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig_wc)
        st.image(buf.getvalue(), use_container_width=True)
    else:
        st.info("키워드 데이터 없음.")

    top_kw_list = keywords["키워드_원본"].value_counts().head(50).index.tolist()
    selected_kw = st.selectbox(
        "키워드 선택 → 개념 탐험기",
        options=["—"] + top_kw_list,
        index=0,
        key="kw_jump_select",
    )
    if selected_kw and selected_kw != "—":
        st.query_params["keyword"] = selected_kw
        st.switch_page("pages/1_개념_탐험기.py")


# ④ 저자 TOP 20 막대 — 클릭 시 인용의 풍경(저자)으로 이동
with bot_right:
    st.subheader("④ 저자 TOP 20")
    st.caption("막대를 클릭하면 그 저자의 인용 풍경으로 이동합니다.")

    top_authors = (
        authors["저자_원본"].value_counts().head(20).reset_index()
    )
    top_authors.columns = ["저자", "논문 수"]
    fig4 = px.bar(
        top_authors, x="논문 수", y="저자",
        orientation="h", template=PLOTLY_TEMPLATE,
    )
    fig4.update_layout(
        height=430, margin=dict(l=10, r=10, t=10, b=10),
        yaxis={"categoryorder": "total ascending"},
    )
    event4 = st.plotly_chart(
        fig4, use_container_width=True,
        on_select="rerun", selection_mode="points", key="bar_authors",
    )
    if event4 and event4.selection and event4.selection["points"]:
        clicked = event4.selection["points"][0].get("y")
        sig = ("author", clicked)
        if clicked and ss.get("bar_last_sig") != sig:
            ss["bar_last_sig"] = sig
            ss.pop("bar_authors", None)
            st.query_params.update({"entity": "author", "id": clicked})
            st.switch_page("pages/2_인용의_풍경.py")


# ────────────────────────────────────────────────────────────
# 푸터
# ────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("데이터: 인도철학 학술지 KCI 반출본 · 총 636편 (1989–2025)")
