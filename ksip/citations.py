"""인용의 풍경 페이지 — ego network 데이터 집계 + 시각화 헬퍼.

순수 Python (Streamlit 의존 없음). 호출자가 @st.cache_data로 감쌀 것.
"""
from __future__ import annotations

from typing import Literal

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from .data import load_authors, load_papers, load_references
from .normalize import load_authority, resolve_person

EntityType = Literal["author", "institution"]

# 유형별 색상 (시각적 일관성)
REF_TYPE_COLORS: dict[str, str] = {
    "학술지(정기간행물)": "#4C72B0",  # blue
    "단행본": "#55A868",              # green
    "학위논문": "#C44E52",            # red
    "학술대회논문": "#8172B2",        # purple
    "보고서": "#CCB974",              # tan
    "인터넷자원": "#937860",          # brown
    "기타자료": "#DA8BC3",            # pink (원전류 다수)
}
SELF_CITE_COLOR = "#E63946"            # 자기인용 강조색


# ────────────────────────────────────────────────────────────
# Entity → paper IDs → references
# ────────────────────────────────────────────────────────────
def paper_ids_for_entity(entity_type: EntityType, entity_id: str) -> set[str]:
    """선택된 entity의 논문 ID 집합."""
    if entity_type == "institution":
        papers = load_papers()
        return set(papers.loc[papers["기관_부모"] == entity_id, "논문 ID"])
    if entity_type == "author":
        authors = load_authors()
        return set(authors.loc[authors["저자_원본"] == entity_id, "논문ID"])
    raise ValueError(f"unknown entity_type: {entity_type}")


def references_for(paper_ids: set[str]) -> pd.DataFrame:
    """주어진 논문들이 작성한 참고문헌 long-form."""
    refs = load_references()
    return refs[refs["논문ID"].isin(paper_ids)].copy()


# ────────────────────────────────────────────────────────────
# Cited target 라벨 추출 (유형별로 의미 있는 노드 키)
# ────────────────────────────────────────────────────────────
def _journal_display(canon_id: str | None, surface: str | None) -> str | None:
    if canon_id:
        return load_authority("journals").canonical_form(canon_id)
    return surface or None


def _is_noise_title(s: str) -> bool:
    """제목이 노이즈 패턴(URL 조각 등)인지 판정. ego-network 노드에서 제외."""
    if not s:
        return True
    low = s.strip().lower()
    if low.startswith(("http:", "https:", "www.", "ftp:")):
        return True
    return False


def _cited_label(row: pd.Series) -> str | None:
    """유형별로 ego-network의 target 노드 라벨 결정.

    저자 단위 집계는 resolve_person()으로 인물 정규화(concepts.학자 + authors).
    인터넷자원/기타자료의 URL 조각 노이즈는 제외.
    """
    typ = row["유형"]
    if typ == "학술지(정기간행물)":
        return _journal_display(row.get("학술지_canonical"), row.get("학술지_원본"))
    if typ in ("단행본", "학위논문", "학술대회논문", "보고서"):
        author = (row.get("저자_원본") or "").strip()
        if author:
            _, display = resolve_person(author)
            return display
        title = (row.get("제목_원본") or "").strip()
        return title if title and not _is_noise_title(title) else None
    if typ in ("인터넷자원", "기타자료"):
        title = (row.get("제목_원본") or "").strip()
        if title and not _is_noise_title(title):
            return title
        return None
    return None


# ────────────────────────────────────────────────────────────
# 집계
# ────────────────────────────────────────────────────────────
def aggregate_targets(
    refs: pd.DataFrame,
    n: int = 30,
    type_filter: list[str] | None = None,
    exclude_self: bool = False,
) -> pd.DataFrame:
    """refs(long-form) → (label, type, count)의 TOP N."""
    df = refs
    if type_filter is not None:
        df = df[df["유형"].isin(type_filter)]
    if exclude_self:
        df = df[~df["자기인용"]]
    if df.empty:
        return pd.DataFrame(columns=["label", "type", "count", "is_self"])

    rows = []
    for _, r in df.iterrows():
        lbl = _cited_label(r)
        if lbl:
            rows.append({"label": lbl, "type": r["유형"], "is_self": bool(r["자기인용"])})
    if not rows:
        return pd.DataFrame(columns=["label", "type", "count", "is_self"])

    long = pd.DataFrame(rows)
    agg = (
        long.groupby(["label", "type"])
        .agg(count=("label", "size"), is_self=("is_self", "any"))
        .reset_index()
        .sort_values("count", ascending=False)
        .head(n)
    )
    return agg


# ────────────────────────────────────────────────────────────
# Ego network figure
# ────────────────────────────────────────────────────────────
def ego_network_figure(
    focal: str,
    targets: pd.DataFrame,
    height: int = 600,
) -> go.Figure | None:
    """focal 노드 중심 + targets 별자리. 색상은 유형별, 자기인용 강조."""
    if targets.empty:
        return None

    G = nx.Graph()
    G.add_node(focal, kind="focal")
    for _, t in targets.iterrows():
        G.add_node(
            t["label"],
            kind="target",
            type=t["type"],
            count=int(t["count"]),
            is_self=bool(t["is_self"]),
        )
        G.add_edge(focal, t["label"], weight=int(t["count"]))

    # Shell layout: focal 중앙, target들이 원 주위
    other_nodes = [n for n in G.nodes() if n != focal]
    pos = nx.shell_layout(G, [[focal], other_nodes])

    # 엣지 trace
    edge_x: list[float] = []
    edge_y: list[float] = []
    for u, v in G.edges():
        edge_x.extend([pos[u][0], pos[v][0], None])
        edge_y.extend([pos[u][1], pos[v][1], None])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(color="rgba(150,150,150,0.4)", width=0.7),
            hoverinfo="none",
            showlegend=False,
        )
    )

    # focal 노드 (한 개)
    fig.add_trace(
        go.Scatter(
            x=[pos[focal][0]],
            y=[pos[focal][1]],
            mode="markers+text",
            marker=dict(size=44, color="#1F1F1F", line=dict(width=2, color="white")),
            text=[focal],
            textposition="middle center",
            textfont=dict(color="white", size=11),
            hoverinfo="text",
            showlegend=False,
            name="(focal)",
        )
    )

    # target 노드들 — 유형별로 trace 분리(범례)
    counts_for_size = [G.nodes[n]["count"] for n in other_nodes]
    cmin = min(counts_for_size) if counts_for_size else 1
    cmax = max(counts_for_size) if counts_for_size else 1
    def size_of(c: int) -> float:
        # 16 ~ 56 px
        if cmax == cmin:
            return 30
        return 16 + 40 * (c - cmin) / (cmax - cmin)

    types_present = list(targets["type"].unique())
    for typ in types_present:
        type_nodes = [n for n in other_nodes if G.nodes[n].get("type") == typ]
        if not type_nodes:
            continue
        # 자기인용 노드는 별도 trace로 분리 — 강조 마커(빨간 채움 + 굵은 테두리)
        for self_flag, marker_extras in [
            (False, dict(line=dict(width=1, color="white"))),
            (True, dict(line=dict(width=3, color="#1F1F1F"))),
        ]:
            sub = [n for n in type_nodes if G.nodes[n]["is_self"] == self_flag]
            if not sub:
                continue
            xs = [pos[n][0] for n in sub]
            ys = [pos[n][1] for n in sub]
            labels = [n for n in sub]
            sizes = [size_of(G.nodes[n]["count"]) for n in sub]
            colors = [
                (SELF_CITE_COLOR if self_flag else REF_TYPE_COLORS.get(typ, "#888"))
                for _ in sub
            ]
            hover = [
                f"<b>{n}</b><br>유형: {typ}<br>인용 횟수: {G.nodes[n]['count']}"
                f"{'<br><b>(자기인용)</b>' if self_flag else ''}"
                for n in sub
            ]
            name = f"{typ} (자기인용)" if self_flag else typ
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text",
                    marker=dict(
                        size=sizes,
                        color=colors,
                        symbol=("star" if self_flag else "circle"),
                        **marker_extras,
                    ),
                    text=[(l if len(l) <= 14 else l[:13] + "…") for l in labels],
                    textposition="top center",
                    textfont=dict(size=9),
                    hovertext=hover,
                    hoverinfo="text",
                    name=name,
                )
            )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.02,
            xanchor="center", x=0.5,
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=10, t=10, b=40),
        hoverlabel=dict(font_size=12),
    )
    return fig


# ────────────────────────────────────────────────────────────
# Entity 메타 (헤더 카드용)
# ────────────────────────────────────────────────────────────
def entity_summary(entity_type: EntityType, entity_id: str) -> dict:
    paper_ids = paper_ids_for_entity(entity_type, entity_id)
    if not paper_ids:
        return {"papers": 0, "refs": 0, "year_min": None, "year_max": None}
    papers = load_papers()
    sub = papers[papers["논문 ID"].isin(paper_ids)]
    refs = references_for(paper_ids)
    return {
        "papers": len(paper_ids),
        "refs": len(refs),
        "year_min": int(sub["발행연도"].min()),
        "year_max": int(sub["발행연도"].max()),
    }


# ────────────────────────────────────────────────────────────
# 전체 풍경 (정적, 캐시 가능)
# ────────────────────────────────────────────────────────────
def landscape_stats() -> dict:
    refs = load_references()
    type_dist = refs["유형"].value_counts()

    # TOP 인용 학술지 (canonical 우선, 없으면 surface)
    journal_refs = refs[refs["유형"] == "학술지(정기간행물)"].copy()
    journal_refs["display"] = journal_refs.apply(
        lambda r: _journal_display(r.get("학술지_canonical"), r.get("학술지_원본")),
        axis=1,
    )
    top_journals = (
        journal_refs.dropna(subset=["display"])
        .loc[journal_refs["display"].astype(str).str.strip() != "", "display"]
        .value_counts()
        .head(10)
    )

    # TOP 인용 원전 (기타자료의 제목)
    classics_refs = refs[refs["유형"] == "기타자료"]
    top_classics = (
        classics_refs["제목_원본"].dropna().loc[lambda s: s.str.strip() != ""]
        .value_counts()
        .head(10)
    )

    # TOP 인용 학자 (학술지/단행본/학위/학술대회/보고서의 저자)
    # — resolve_person()으로 고전 학자 + 현대 학자 모두 정규화
    scholar_refs = refs[
        refs["유형"].isin(
            ["학술지(정기간행물)", "단행본", "학위논문", "학술대회논문", "보고서"]
        )
    ].copy()
    scholar_refs["author_display"] = (
        scholar_refs["저자_원본"]
        .fillna("")
        .map(lambda s: resolve_person(s)[1] if s.strip() else "")
    )
    top_scholars = (
        scholar_refs.loc[scholar_refs["author_display"] != "", "author_display"]
        .value_counts()
        .head(10)
    )

    return {
        "total_refs": int(len(refs)),
        "self_cite_count": int(refs["자기인용"].sum()),
        "self_cite_rate": float(refs["자기인용"].mean()),
        "type_dist": type_dist,
        "top_journals": top_journals,
        "top_classics": top_classics,
        "top_scholars": top_scholars,
    }
