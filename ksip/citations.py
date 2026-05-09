"""인용의 풍경 페이지 — ego network 데이터 집계 + 시각화 헬퍼.

순수 Python (Streamlit 의존 없음). 호출자가 @st.cache_data로 감쌀 것.

데이터 source: A안 — KCI articleDetail에서 회수한 `kci_references.parquet`가
권위 source. cited_artiId(REFARTIID) 정밀 매칭을 사용.
.xls 텍스트 파싱 기반 `references.parquet`는 fallback용 (kci 빌드 안 됐을 때).
"""
from __future__ import annotations

from typing import Literal

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from .data import (
    load_authors,
    load_kci_papers,
    load_kci_references,
    load_papers,
    load_references,
)
from .normalize import add_canonical_column, load_authority, resolve_person

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


SELF_JOURNAL_NAME = "인도철학"


def _normalize_kci_refs(refs: pd.DataFrame) -> pd.DataFrame:
    """KCI references 컬럼명을 legacy schema와 호환되게 재명명 + 자기인용/canonical 계산.

    legacy 스키마 핵심: 저자_원본 / 제목_원본 / 학술지_원본 / 연도 / DOI / 자기인용 / 학술지_canonical
    추가: cited_artiId (REFARTIID), 참조ID_kci, cited_권/호/페이지/발행기관
    """
    if refs.empty:
        return refs

    sub = refs.copy()
    sub = sub.rename(columns={
        "cited_저자": "저자_원본",
        "cited_제목": "제목_원본",
        "cited_학술지": "학술지_원본",
        "cited_연도": "연도",
        "cited_DOI": "DOI",
    })
    # 자기인용: cited_학술지 == '인도철학' (KCI 정밀 매칭)
    sub["자기인용"] = sub["학술지_원본"].fillna("").str.strip() == SELF_JOURNAL_NAME
    # 학술지 canonical 적용 (journals.yml)
    sub = add_canonical_column(sub, "학술지_원본", "journals",
                               out_col="학술지_canonical")
    return sub


def _all_refs_kci_authoritative() -> pd.DataFrame:
    """전체 references (KCI 권위 + legacy fallback).

    KCI parquet이 빌드돼 있으면 그것을 사용 (cited_artiId 포함).
    아니면 legacy .xls 기반 references.parquet로 fallback (cited_artiId 없음).
    """
    kci = load_kci_references()
    if not kci.empty:
        return _normalize_kci_refs(kci)
    return load_references().copy()


def references_for(paper_ids: set[str]) -> pd.DataFrame:
    """주어진 논문들이 작성한 참고문헌 long-form (KCI 권위 source)."""
    refs = _all_refs_kci_authoritative()
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
    """refs(long-form) → (label, type, count, is_self, sample_artiId)의 TOP N.

    sample_artiId: KCI 등재 cited paper면 REFARTIID (KCI URL 점프 가능),
    아니면 None.
    """
    df = refs
    if type_filter is not None:
        df = df[df["유형"].isin(type_filter)]
    if exclude_self:
        df = df[~df["자기인용"]]
    if df.empty:
        return pd.DataFrame(columns=["label", "type", "count", "is_self", "sample_artiId"])

    has_arti_id = "cited_artiId" in df.columns

    rows = []
    for _, r in df.iterrows():
        lbl = _cited_label(r)
        if not lbl:
            continue
        rows.append({
            "label": lbl,
            "type": r["유형"],
            "is_self": bool(r["자기인용"]),
            "cited_artiId": (r["cited_artiId"] if has_arti_id else None),
        })
    if not rows:
        return pd.DataFrame(columns=["label", "type", "count", "is_self", "sample_artiId"])

    long = pd.DataFrame(rows)

    def _first_artiid(s: pd.Series) -> str | None:
        valid = s.dropna()
        valid = valid[valid.astype(str).str.strip() != ""]
        return valid.iloc[0] if not valid.empty else None

    agg = (
        long.groupby(["label", "type"])
        .agg(
            count=("label", "size"),
            is_self=("is_self", "any"),
            sample_artiId=("cited_artiId", _first_artiid),
        )
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
            arti_id=(t.get("sample_artiId") if "sample_artiId" in targets.columns else None),
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
            def _hover_for(n: str) -> str:
                lines = [
                    f"<b>{n}</b>",
                    f"유형: {typ}",
                    f"인용 횟수: {G.nodes[n]['count']}",
                ]
                if self_flag:
                    lines.append("<b>(자기인용)</b>")
                aid = G.nodes[n].get("arti_id")
                if aid:
                    lines.append(f"KCI artiId: {aid}")
                    lines.append(f"<i>https://www.kci.go.kr/...artiId={aid}</i>")
                return "<br>".join(lines)

            hover = [_hover_for(n) for n in sub]
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
        return {
            "papers": 0, "refs": 0,
            "year_min": None, "year_max": None,
            "avg_fwci": None, "max_fwci": None,
            "total_kci_cite": None, "avg_kci_cite": None,
        }
    papers = load_papers()
    sub = papers[papers["논문 ID"].isin(paper_ids)]
    refs = references_for(paper_ids)

    # KCI enrichment (단계 2 산출). 빌드 안 됐으면 None.
    kci_papers = load_kci_papers()
    avg_fwci = max_fwci = total_kci_cite = avg_kci_cite = None
    if not kci_papers.empty:
        sub_kci = kci_papers[kci_papers["논문ID"].isin(paper_ids)]
        fwci_series = sub_kci["fwci"].dropna() if "fwci" in sub_kci.columns else pd.Series(dtype=float)
        cc_series = (
            sub_kci["kci_citation_count"].dropna()
            if "kci_citation_count" in sub_kci.columns else pd.Series(dtype=float)
        )
        if not fwci_series.empty:
            avg_fwci = float(fwci_series.mean())
            max_fwci = float(fwci_series.max())
        if not cc_series.empty:
            total_kci_cite = int(cc_series.sum())
            avg_kci_cite = float(cc_series.mean())

    return {
        "papers": len(paper_ids),
        "refs": len(refs),
        "year_min": int(sub["발행연도"].min()),
        "year_max": int(sub["발행연도"].max()),
        "avg_fwci": avg_fwci,
        "max_fwci": max_fwci,
        "total_kci_cite": total_kci_cite,
        "avg_kci_cite": avg_kci_cite,
    }


# ────────────────────────────────────────────────────────────
# 전체 풍경 (정적, 캐시 가능)
# ────────────────────────────────────────────────────────────
def landscape_stats() -> dict:
    """전체 학술지 인용 풍경 (KCI 권위 source)."""
    refs = _all_refs_kci_authoritative()
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
