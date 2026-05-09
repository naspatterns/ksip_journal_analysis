"""참고문헌 시트의 슬래시 구분 텍스트를 long-form 테이블로 변환.

각 항목은 `[번호] [유형] 슬래시/구분/필드들` 형식이지만 슬래시 필드의 의미는
유형에 따라 다르다. 본 모듈은 유형별 파서로 안전하게 구조화 추출하고,
원본 텍스트는 항상 `원본_텍스트`로 보존한다.

제목 또는 학술지명에 "/" 가 들어 있는 경우(예: 'cakra/chakra' IAST 변형,
이중언어 학술지명 'Wiener Zeitschrift / Vienna Journal of South Asian
Studies') 는 단순 split 만으로 필드가 한 칸씩 밀린다. 이 경우 연도 슬롯을
anchor 로 삼아 역산해서 보정한다(`_realign_journal_type` 참조).
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

from .load import RAW_FILES

PREFIX_RE = re.compile(r"^\[(\d+)\]\s*\[([^\]]+)\]\s*(.*)$")
YEAR_RE = re.compile(r"(1[89]\d{2}|20\d{2})")
# 슬롯 anchor 용: 한 슬롯이 통째로 연도이거나 '2004a/b' / '(2004)' 형태일 때만 매치
YEAR_SLOT_RE = re.compile(r"^\(?(1[89]\d{2}|20\d{2})[a-z]?\)?$")
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

# 학술지명 슬롯이 있어 year-anchor 재정렬 가치가 있는 유형
REALIGNABLE_TYPES = frozenset({"학술지(정기간행물)", "학술대회논문"})

JOURNALS_YML = (
    Path(__file__).resolve().parent.parent / "data" / "dictionaries" / "journals.yml"
)


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


def _find_year_slot(parts: list[str]) -> int:
    """parts 에서 통째로 연도인 슬롯의 인덱스. 없으면 -1."""
    for i, p in enumerate(parts):
        if YEAR_SLOT_RE.match(p.strip()):
            return i
    return -1


def _norm_journal(s: str) -> str:
    """학술지명 비교용 정규화: NFC + 소문자화 + 모든 공백 제거.

    XLS 원본 데이터의 라틴 분음부호(ü, é 등) 는 NFD(분해형) 인 반면 YAML
    surface_form 은 NFC(합성형) 으로 들어가는 경우가 있어 바이트 수준 비교가
    실패한다. 양쪽을 NFC 로 강제 통일.
    """
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", s.strip().lower()))


@lru_cache(maxsize=1)
def _multi_slash_journals_norm() -> set[str]:
    """journals.yml 에서 surface_form 중 '/'를 포함하는 것만 평탄화한 정규화 집합.

    이중언어 표기('X / Y') 또는 분야결합 학술지('문학/사학/철학') 식별 전용.
    파일이 없거나 파싱 실패 시 빈 집합(=감지 비활성).
    """
    if not JOURNALS_YML.exists():
        return set()
    try:
        data = yaml.safe_load(JOURNALS_YML.read_text(encoding="utf-8")) or []
    except Exception:
        return set()
    out: set[str] = set()
    for entry in data:
        for s in entry.get("surface_forms") or []:
            if isinstance(s, str) and "/" in s:
                out.add(_norm_journal(s))
    return out


def _is_multi_slash_journal(candidate: str) -> bool:
    return _norm_journal(candidate) in _multi_slash_journals_norm()


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

    저자 = 제목 = 학술지 = ""
    연도_str = ""
    doi = url = ""

    realigned = False
    if ref_type in REALIGNABLE_TYPES:
        expected_year_pos = fmap.get("연도", 3) or 3
        year_idx = _find_year_slot(parts)
        if year_idx > expected_year_pos:
            # 시프트 발생: 제목 또는 학술지명에 '/' 가 끼어 있음.
            저자 = parts[0].strip() if parts else ""
            연도_str = parts[year_idx].strip()
            # 학술지 후보 = parts[2..year_idx-1] 를 "/"로 다시 합친 것.
            # 이게 알려진 multi-slash 학술지면 → 학술지명에 "/" 가 든 케이스(이중언어 등):
            #   학술지 = 후보 전체, 제목 = parts[1]
            # 아니면 → 제목에 "/" 가 든 케이스: 학술지 = parts[year_idx-1], 제목 = parts[1..year_idx-2]
            cand = "/".join(p.strip() for p in parts[2:year_idx]).strip()
            if cand and _is_multi_slash_journal(cand):
                제목 = parts[1].strip() if len(parts) > 1 else ""
                학술지 = cand
            else:
                제목 = "/".join(p.strip() for p in parts[1:year_idx - 1]).strip()
                학술지 = parts[year_idx - 1].strip() if year_idx - 1 >= 0 else ""
            doi_idx = fmap.get("DOI")
            if doi_idx is not None:
                shift = year_idx - expected_year_pos
                doi = _safe_get(parts, doi_idx + shift)
            realigned = True

    if not realigned:
        저자 = _safe_get(parts, fmap.get("저자"))
        제목 = _safe_get(parts, fmap.get("제목"))
        학술지 = _safe_get(parts, fmap.get("학술지"))
        연도_str = _safe_get(parts, fmap.get("연도"))
        doi = _safe_get(parts, fmap.get("DOI"))
        url = _safe_get(parts, fmap.get("URL"))

    연도 = _extract_year(연도_str) or _extract_year(rest)

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
