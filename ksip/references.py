"""참고문헌 시트의 슬래시 구분 텍스트를 long-form 테이블로 변환.

각 항목은 `[번호] [유형] 슬래시/구분/필드들` 형식이지만 슬래시 필드의 의미는
유형에 따라 다르다. 본 모듈은 유형별 파서로 안전하게 구조화 추출하고,
원본 텍스트는 항상 `원본_텍스트`로 보존한다.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .load import RAW_FILES

PREFIX_RE = re.compile(r"^\[(\d+)\]\s*\[([^\]]+)\]\s*(.*)$")
YEAR_RE = re.compile(r"(1[89]\d{2}|20\d{2})")
SELF_JOURNAL_NAME = "인도철학"

# 유형별 슬래시 필드 인덱스. None = 해당 유형에 그 필드가 없거나 신뢰할 수 없음.
# 인덱스는 prefix("[N] [유형] ") 제거 후 슬래시 split의 0-based 위치.
TYPE_FIELDS: dict[str, dict[str, int | None]] = {
    "학술지(정기간행물)": {
        "저자": 0, "제목": 1, "학술지": 2, "연도": 3,
        "권호": 4, "페이지": 5, "기관": 6, "DOI": 7,
    },
    "단행본":     {"제목": 0, "저자": 1, "출판사": 2, "연도": 3},
    "학위논문":   {"저자": 0, "제목": 1, "학위": 2, "대학원": 3, "연도": 5},
    "학술대회논문": {"저자": 0, "제목": 1, "학술지": 2, "연도": 3},
    "보고서":     {"제목": 0, "저자": 1, "기관": 2, "연도": 3},
    "인터넷자원": {"제목": 0, "URL": 1, "저자": 2, "연도": 5},
    "기타자료":   {"저자": 0, "제목": 1, "연도": 3},  # 매우 가변, 베스트 에포트
}


def _safe_get(parts: list[str], idx: int | None) -> str:
    if idx is None:
        return ""
    if 0 <= idx < len(parts):
        return parts[idx].strip()
    return ""


def _extract_year(text: str) -> int | None:
    if not text:
        return None
    m = YEAR_RE.search(text)
    return int(m.group(1)) if m else None


def parse_one(raw: str) -> dict | None:
    """참고문헌 한 건의 원본 텍스트를 dict로 파싱. 실패 시 None."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    m = PREFIX_RE.match(raw.strip())
    if not m:
        return {
            "참조번호": None, "유형": None,
            "저자_원본": "", "제목_원본": "", "학술지_원본": "",
            "연도": None, "DOI": "", "URL": "",
            "원본_텍스트": raw,
        }
    ref_no, ref_type, rest = m.group(1), m.group(2), m.group(3)
    parts = rest.split("/")
    fmap = TYPE_FIELDS.get(ref_type, {})

    저자 = _safe_get(parts, fmap.get("저자"))
    제목 = _safe_get(parts, fmap.get("제목"))
    학술지 = _safe_get(parts, fmap.get("학술지"))
    연도_str = _safe_get(parts, fmap.get("연도"))
    연도 = _extract_year(연도_str) or _extract_year(rest)
    doi = _safe_get(parts, fmap.get("DOI"))
    url = _safe_get(parts, fmap.get("URL"))

    return {
        "참조번호": int(ref_no),
        "유형": ref_type,
        "저자_원본": 저자,
        "제목_원본": 제목,
        "학술지_원본": 학술지,
        "연도": 연도,
        "DOI": doi,
        "URL": url,
        "원본_텍스트": raw,
    }


def load_references(raw_dir: Path) -> pd.DataFrame:
    """3개 .xls의 참고문헌 시트를 합쳐 long-form 테이블 반환."""
    frames: list[pd.DataFrame] = []
    for fname in RAW_FILES:
        path = raw_dir / fname
        df = pd.read_excel(path, sheet_name="참고문헌")
        if df.empty:
            continue
        df = df.rename(columns={"논문 ID": "논문ID", "참고문헌": "원본"})
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)

    parsed_rows: list[dict] = []
    for _, row in raw.iterrows():
        d = parse_one(row["원본"])
        if d is None:
            continue
        d["논문ID"] = row["논문ID"]
        parsed_rows.append(d)

    refs = pd.DataFrame(parsed_rows)
    refs["자기인용"] = refs["학술지_원본"].fillna("").str.contains(SELF_JOURNAL_NAME, regex=False)
    refs["연도"] = refs["연도"].astype("Int64")

    cols = ["논문ID", "참조번호", "유형",
            "저자_원본", "제목_원본", "학술지_원본",
            "연도", "DOI", "URL", "자기인용", "원본_텍스트"]
    return refs[cols]
