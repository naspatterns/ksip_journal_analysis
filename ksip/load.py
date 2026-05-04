"""인도철학 학술지 .xls 원본을 papers / authors / keywords long-form으로 변환.

Surface form은 그대로 유지한다. 정규화는 별도 단계(ksip.normalize)에서 적용.
다만 명백한 입력 오류(PUA 문자, 트레일링 underscore 등)는 ksip.clean 으로 정리.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .clean import clean_keyword, clean_title
from .institutions import parent_institution

ARTI_ID_RE = re.compile(r"artiId=(ART\d+)")

RAW_FILES = (
    "인도철학_1_300.xls",
    "인도철학_301_600.xls",
    "인도철학_601_636.xls",
)


def _extract_artiid(url: str | float | None) -> str | None:
    if not isinstance(url, str):
        return None
    m = ARTI_ID_RE.search(url)
    return m.group(1) if m else None


def load_papers(raw_dir: Path) -> pd.DataFrame:
    """3개 .xls의 논문목록 시트를 합쳐 통합 paper 테이블 반환.

    `논문 ID`가 없는 파일은 URL에서 artiId를 추출해서 채운다.
    """
    frames: list[pd.DataFrame] = []
    for fname in RAW_FILES:
        path = raw_dir / fname
        df = pd.read_excel(path, sheet_name="논문목록")
        if "논문 ID" not in df.columns:
            df["논문 ID"] = df["URL"].map(_extract_artiid)
        frames.append(df)

    papers = pd.concat(frames, ignore_index=True)
    papers["발행연도"] = pd.to_numeric(papers["발행연도"], errors="coerce").astype("Int64")
    papers = papers.dropna(subset=["논문 ID", "발행연도"]).copy()
    papers["발행연도"] = papers["발행연도"].astype(int)
    papers = papers.drop_duplicates(subset="논문 ID", keep="first").reset_index(drop=True)

    # 논문명 클리닝 — PUA / 트레일링 underscore 제거. 원본은 _원본 컬럼에 백업.
    papers["논문명_원본"] = papers["논문명"]
    papers["논문명"] = papers["논문명"].map(clean_title)

    # 기관 부모 단위 추출 — 시각화 디폴트는 부모, 토글로 상세 단위(주저자 소속기관) 표시.
    papers["기관_부모"] = papers["주저자 소속기관"].map(parent_institution)

    return papers


def explode_authors(papers: pd.DataFrame) -> pd.DataFrame:
    """논문당 다중 저자(',' 또는 ';' 구분)를 long-form으로 분해.

    Surface form 보존: `저자_원본`에 원래 표기 그대로(예: "안성두(安性斗)") 들어감.
    """
    rows: list[dict] = []
    for _, row in papers.iterrows():
        raw = "" if pd.isna(row["저자명"]) else str(row["저자명"]).strip()
        if not raw:
            continue
        for token in re.split(r"[;,]", raw):
            name = token.strip()
            if not name:
                continue
            rows.append(
                {
                    "논문ID": row["논문 ID"],
                    "발행연도": int(row["발행연도"]),
                    "저자_원본": name,
                }
            )
    return pd.DataFrame(rows)


_PUNCT_ONLY_RE = re.compile(r"^[\W_]+$", flags=re.UNICODE)


def _is_noise_keyword(kw: str) -> bool:
    """키워드 노이즈 필터: 1자 + 문장부호만, 빈 문자열 등."""
    if len(kw) <= 1 and _PUNCT_ONLY_RE.match(kw):
        return True
    if _PUNCT_ONLY_RE.match(kw):
        return True
    return False


def explode_keywords(papers: pd.DataFrame) -> pd.DataFrame:
    """저자키워드를 long-form으로 분해.

    Surface form은 PUA 제거 / NFKC 정규화 후 보존(`키워드_원본`).
    문장부호만으로 이뤄진 노이즈 키워드(예: '.')는 제외.
    """
    rows: list[dict] = []
    for _, row in papers.iterrows():
        raw = "" if pd.isna(row["저자키워드"]) else str(row["저자키워드"]).strip()
        if not raw:
            continue
        for token in raw.split(","):
            kw = clean_keyword(token)
            if not kw or _is_noise_keyword(kw):
                continue
            rows.append(
                {
                    "논문ID": row["논문 ID"],
                    "발행연도": int(row["발행연도"]),
                    "키워드_원본": kw,
                }
            )
    return pd.DataFrame(rows)
