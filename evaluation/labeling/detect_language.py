"""Phase 4.4 — references row 의 언어/학계 horizon 탐지.

Decision-18 의 paper-level 변수 계산 모듈. 두 함수:

- `detect_primary_language(row, concepts_lookup)` — tier=primary reference 의
  원전 언어. 값: sanskrit / pali / prakrit / chinese_canon / tibetan_canon /
  mixed / unknown
- `detect_secondary_horizon(row, journals_horizon_by_id, journals_horizon_by_surface)`
  — tier=secondary reference 의 학계 horizon. 값: korean / japanese / english /
  german / french / unknown

Detection 전략:
- **primary**: (1) 저자/제목 → concepts.yml 매칭 → tradition_language → 매핑
  (2) fallback: Unicode + 카탈로그 ID 패턴 (T 32, D 4203, Tib., bsTan, 大藏經)
- **secondary**: (1) 학술지_canonical → journals.yml publisher → horizon
  (2) fallback: Unicode dominance + 독일어/프랑스어 키워드 (raw 전체 텍스트)

설계 노트:
- 자기인용 (학술지=인도철학) 은 tier=secondary 이미 처리됨. horizon=korean 으로
  자연스럽게 잡힘.
- Han-only secondary (中村元/印度思想/講談社 같은 Kana 없는 일본 학자) 는
  publisher 의 일본 키워드 + 보수적 default 'japanese' 적용.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
CONCEPTS_PATH = ROOT / "data" / "dictionaries" / "concepts.yml"
JOURNALS_PATH = ROOT / "data" / "dictionaries" / "journals.yml"
AUTHORS_PATH = ROOT / "data" / "dictionaries" / "authors.yml"

MIN_SURFACE_LEN = 2  # 2자 CJK 인명 (世親·玄奘·眞諦·中村 등) 까지 매칭. 1자는 너무 일반적.


_AUTHOR_TOKEN_RE = re.compile(r"[\s,;·/]+")
_PAREN_RE = re.compile(r"\([^)]*\)")
# Latin/숫자/공백만 으로 이루어진 2자 surface 는 false positive 위험 (PV, TS, JR 등)
# CJK·한글 2자는 keep. 이 함수로 indexing/lookup 양쪽에서 일관 적용.
_ALL_LATIN_NUM_RE = re.compile(r"^[A-Za-z0-9 \-.]+$")


def _surface_keep(s: str) -> bool:
    """surface 가 indexing/lookup 가치 있는지 (false positive 회피).

    - 빈 문자열 / 1자 → False
    - 2자 Latin/숫자 only → False (PV/TS 등 노이즈)
    - 2자 CJK·Hangul → True (世親·玄奘 등)
    - 3자 이상 → True
    """
    if not s or len(s) < 2:
        return False
    if len(s) >= 3:
        return True
    # len == 2
    return not bool(_ALL_LATIN_NUM_RE.fullmatch(s))


def _author_tokens(name: str) -> list[str]:
    """저자 문자열을 토큰화 — 공백·쉼표·세미콜론·괄호 분리. NFC + lower."""
    if not isinstance(name, str):
        return []
    n = unicodedata.normalize("NFC", name).lower()
    n = _PAREN_RE.sub(" ", n)
    return [t.strip() for t in _AUTHOR_TOKEN_RE.split(n) if len(t.strip()) >= 2]


# ============================================================
# concepts.yml lookup — surface → tradition_language → primary_source_basis
# ============================================================

# concept-level tradition_language → paper-level primary_source_basis
TRADITION_TO_PRIMARY = {
    "sanskrit": "sanskrit",
    "pali": "pali",
    "prakrit": "prakrit",
    "chinese": "chinese_canon",
    "tibetan": "tibetan_canon",
    "mixed": "mixed",
    "modern_korean": "unknown",  # primary 에 modern korean 은 의미 없음
    "n/a": "unknown",
}


def _norm(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return unicodedata.normalize("NFC", s).strip().lower()


@lru_cache(maxsize=1)
def build_concepts_primary_lookup() -> dict[str, str]:
    """concepts.yml 의 surface → primary_source_basis 매핑.

    type=학자/인물/원전/문헌 entry 만 포함 (저자·텍스트 후보).
    surface_forms + canonical_kr/iast/zh 모두 인덱싱.
    """
    if not CONCEPTS_PATH.exists():
        return {}
    data = yaml.safe_load(CONCEPTS_PATH.read_text(encoding="utf-8")) or []
    out: dict[str, str] = {}
    for e in data:
        if not e.get("verified", False):
            continue
        t = e.get("type")
        if t not in ("학자", "인물", "원전", "문헌"):
            continue
        tlang = e.get("tradition_language")
        if not tlang or tlang not in TRADITION_TO_PRIMARY:
            continue
        primary_basis = TRADITION_TO_PRIMARY[tlang]
        # surface forms (NFC + lower normalized)
        surfaces = list(e.get("surface_forms") or [])
        for k in ("canonical_kr", "canonical_iast", "canonical_zh", "canonical_form"):
            if e.get(k):
                surfaces.append(e[k])
        for s in surfaces:
            if not isinstance(s, str):
                continue
            n = _norm(s)
            if _surface_keep(n):
                # last-wins: if collision, later entry overwrites. Acceptable since
                # collision cases (e.g., '구사론' could be vasubandhu's or sanghabhadra's)
                # would both have sanskrit anyway.
                out[n] = primary_basis
    return out


# ============================================================
# journals.yml lookup — canonical_id → horizon
# ============================================================

# Publisher 문자열 → horizon 룰
def _publisher_to_horizon(pub: str) -> str:
    if not isinstance(pub, str) or not pub.strip():
        return "unknown"
    p = pub.strip()
    # Hangul → korean
    if re.search(r"[가-힯]", p):
        return "korean"
    # Kana (Hiragana/Katakana) → japanese
    if re.search(r"[぀-ヿ]", p):
        return "japanese"
    # Han only with Japanese institutional keywords → japanese
    if re.search(r"[一-鿿]", p):
        japan_kws = ("日本", "京都", "東京", "龍谷", "大谷", "密教", "高野",
                     "南都", "智山", "創価", "長谷川", "広島", "東方", "印度学")
        if any(kw in p for kw in japan_kws):
            return "japanese"
        # 学会/学院 등 일본·중국 양쪽 — corpus 컨텍스트상 일본 default
        return "japanese"
    # Latin publishers
    germ_kws = ("Austrian", "Schweizerische", "Wiener", "Wien", "Vienna",
                "Deutsche", "Akademie", "Universität", "Verlag", "Berlin",
                "München", "Heidelberg", "Hamburg", "Tübingen")
    if any(kw in p for kw in germ_kws):
        return "german"
    fr_kws = ("française", "Française", "France", "Paris", "École", "Lyon")
    if any(kw in p for kw in fr_kws):
        return "french"
    # Default Latin → english (Springer/Brill/Cambridge/IABS/Pali Text/American Oriental/etc.)
    if re.search(r"[A-Za-z]", p):
        return "english"
    return "unknown"


@lru_cache(maxsize=1)
def build_authors_horizon_lookup() -> dict[str, str]:
    """authors.yml 의 verified entry → surface_form → horizon 매핑.

    값 enum: korean / japanese / english / german / french
    canonical_form + surface_forms 모두 인덱싱. NFC + lower 정규화 키.
    """
    if not AUTHORS_PATH.exists():
        return {}
    data = yaml.safe_load(AUTHORS_PATH.read_text(encoding="utf-8")) or []
    out: dict[str, str] = {}
    for e in data:
        if not e.get("verified", False):
            continue
        horizon = e.get("horizon")
        if not horizon:
            continue
        surfaces = list(e.get("surface_forms") or [])
        if e.get("canonical_form"):
            surfaces.append(e["canonical_form"])
        for s in surfaces:
            if not isinstance(s, str):
                continue
            n = _norm(s)
            if _surface_keep(n):
                out[n] = horizon
    return out


@lru_cache(maxsize=1)
def build_journals_horizon_lookups() -> tuple[dict[str, str], dict[str, str]]:
    """journals.yml 의 lookup 2종.

    Returns:
        (by_canonical_id, by_surface) — 두 인덱스
        by_canonical_id: canonical_id → horizon
        by_surface:      normalized surface_form → horizon (fallback 매칭용)
    """
    if not JOURNALS_PATH.exists():
        return {}, {}
    data = yaml.safe_load(JOURNALS_PATH.read_text(encoding="utf-8")) or []
    by_id: dict[str, str] = {}
    by_surface: dict[str, str] = {}
    for e in data:
        if not e.get("verified", False):
            continue
        cid = e.get("canonical_id")
        if not cid:
            continue
        horizon = _publisher_to_horizon(e.get("publisher", ""))
        # canonical_form 자체에서 horizon 추론 보강 (publisher 가 없는 entry 대비)
        if horizon == "unknown":
            horizon = _publisher_to_horizon(e.get("canonical_form", ""))
        by_id[cid] = horizon
        for s in e.get("surface_forms") or []:
            if isinstance(s, str):
                n = _norm(s)
                if _surface_keep(n):
                    by_surface[n] = horizon
        if e.get("canonical_form"):
            n = _norm(e["canonical_form"])
            if _surface_keep(n):
                by_surface[n] = horizon
    return by_id, by_surface


# ============================================================
# Primary language detection
# ============================================================

# 카탈로그 ID / 권위 마커 패턴
_TIB_RE = re.compile(r"(\bbsTan\b|\bbKa['ʼ]\b|\bTib\.|티베트|Kangyur|Tengyur|bstan\s*'gyur|bka['ʼ]\s*'gyur)")
_CHI_CANON_RE = re.compile(r"(\bT\s*[\d]{2,}|\bTD\s*\d|\bK\s*\d{2,}|大正藏|大藏經|高麗大藏經|續藏經|嘉興藏)")
_PALI_RE = re.compile(r"(Tipiṭaka|tipitaka|Nikāya|nikaya|Visuddhimagga|Dīgha|Majjhima|Saṃyutta|Aṅguttara|PTS|Pali Text Society|빠알리|팔리|니까야)", re.IGNORECASE)
_PRAKRIT_RE = re.compile(r"(Prakrit|prakrit|Āgama|āgama|Ardha-?māgadhī|자이나|Jain\b)", re.IGNORECASE)
_DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")
_IAST_RE = re.compile(r"[āīūṛṝḷḹṅñṭḍṇśṣ]")


def detect_primary_language(row, concepts_lookup: dict[str, str]) -> str:
    """tier=primary 인 reference 의 primary_source_basis 값.

    Args:
        row: references row (dict-like, with 저자_원본/제목_원본/원본_텍스트)
        concepts_lookup: build_concepts_primary_lookup() 결과
    """
    저자 = row.get("저자_원본") or ""
    제목 = row.get("제목_원본") or ""
    raw = row.get("원본_텍스트") or ""

    # (1) concepts.yml 매칭 — 저자 (Western 'Last, First' 의 first name 무시는 굳이 안 함;
    # 일차문헌의 저자는 고전 사상가니 토큰 매칭 OK)
    for name in (저자, 제목):
        if not name:
            continue
        n = _norm(name)
        if n in concepts_lookup:
            return concepts_lookup[n]
    # 토큰 분해 후 매칭
    for name in (저자, 제목):
        if not name:
            continue
        n_nfc = unicodedata.normalize("NFC", name).lower()
        n_nfc = re.sub(r"\([^)]*\)", " ", n_nfc)  # 괄호 안 (편)/(역) 제거
        tokens = re.split(r"[\s,;·/]+", n_nfc)
        for tok in tokens:
            tok = tok.strip()
            if _surface_keep(tok) and tok in concepts_lookup:
                return concepts_lookup[tok]

    # (2) Tibetan markers (Tib.·bsTan·bKa' 등) → tibetan_canon
    if _TIB_RE.search(raw):
        return "tibetan_canon"

    # (3) Chinese canon markers (T 32·大藏經 등)
    if _CHI_CANON_RE.search(raw):
        return "chinese_canon"

    # (4) Pali markers
    if _PALI_RE.search(raw):
        return "pali"

    # (5) Prakrit / Jain markers
    if _PRAKRIT_RE.search(raw):
        return "prakrit"

    # (6) Devanagari → sanskrit
    if _DEVANAGARI_RE.search(raw):
        return "sanskrit"

    # (7) IAST diacritics → sanskrit (단 Pali 이미 위에서 잡힘)
    if _IAST_RE.search(raw):
        return "sanskrit"

    # (8) Fallback default: sanskrit (인도철학 corpus 의 primary 압도 다수)
    return "sanskrit"


# ============================================================
# Secondary horizon detection
# ============================================================

# Unicode 점유율 임계값
_HORIZON_MIN_CHARS = 3


def _unicode_dominance(text: str) -> str | None:
    """raw 텍스트의 Unicode 분포 → korean/japanese/english/unknown.

    독일·프랑스어 키워드는 별도 호출자에서 처리.
    Han-only 는 corpus 컨텍스트상 japanese 로 보수 default.
    """
    if not text:
        return None
    hangul = len(re.findall(r"[가-힯]", text))
    kana = len(re.findall(r"[぀-ヿ]", text))
    han = len(re.findall(r"[一-鿿]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    total = hangul + kana + han + latin
    if total < _HORIZON_MIN_CHARS:
        return None
    # Kana 존재 → japanese
    if kana >= 2:
        return "japanese"
    # Hangul 비중 ≥ 25% → korean
    if hangul / total >= 0.25:
        return "korean"
    # Latin 비중 ≥ 50% → english (독일·프랑스 키워드는 호출자에서 우선 처리)
    if latin / total >= 0.5:
        return "english"
    # Han 다수, Kana 없음, Hangul 없음 → japanese (corpus default)
    if han > hangul and han > kana and han > latin:
        return "japanese"
    return None


_GERM_TEXT_RE = re.compile(
    r"(?:\bfür\b|\büber\b|\bStudien\b|\bZeitschrift\b|\bWiener\b|\bWien\b"
    r"|\bDeutsche\b|\bVerlag\b|\bAkademie\b|\bUniversit[äa]t\b|\bBerlin\b"
    r"|\bMünchen\b|\bHeidelberg\b|\bHamburg\b|\bTübingen\b)"
)
_FR_TEXT_RE = re.compile(
    r"(?:\bÉtudes\b|\bfrançaise\b|\bRevue\b|\bParis\b|\bÉcole\b|\bLyon\b)",
    re.IGNORECASE,
)


def detect_secondary_horizon(
    row,
    journals_by_id: dict[str, str],
    journals_by_surface: dict[str, str],
    authors_horizon: dict[str, str] | None = None,
) -> str:
    """tier=secondary reference 의 secondary_source_horizon 값.

    우선순위 (가장 신뢰도 높은 신호 → 낮은 신호):
        (1) 저자가 authors.yml 매칭 → 그 학자의 horizon
            (예: 中村元 → japanese, 정승석 → korean, Schmithausen → german)
        (2) 학술지_canonical → journals.yml publisher → horizon
        (3) 학술지명 surface 매칭
        (4) raw 텍스트의 publisher 룰 + Unicode dominance 검증
        (5) Unicode dominance 단독 (독일·프랑스어 키워드 보강)
    """
    raw = row.get("원본_텍스트") or ""
    저자 = row.get("저자_원본") or ""
    학술지 = row.get("학술지_원본") or ""
    학술지_canon = row.get("학술지_canonical")

    # (1) 저자 → authors.yml horizon — 가장 신뢰도 높은 신호
    if authors_horizon and 저자:
        n_full = _norm(저자)
        if n_full in authors_horizon:
            return authors_horizon[n_full]
        for tok in _author_tokens(저자):
            if tok in authors_horizon:
                return authors_horizon[tok]

    # (2) 학술지_canonical → horizon
    if isinstance(학술지_canon, str) and 학술지_canon in journals_by_id:
        return journals_by_id[학술지_canon]

    # (3) 학술지명 surface 매칭
    if 학술지:
        n = _norm(학술지)
        if n in journals_by_surface:
            return journals_by_surface[n]

    # (4) Publisher 가 raw 안 어딘가에 있으면 룰 적용 시도
    # (단행본·기타자료의 경우 publisher 가 raw 안에 있음 — 슬래시 split 의 출판사 슬롯)
    horizon_from_raw_pub = _publisher_to_horizon(raw)
    if horizon_from_raw_pub != "unknown":
        dom = _unicode_dominance(raw)
        if dom is not None and dom == horizon_from_raw_pub:
            return horizon_from_raw_pub
        if dom is None:
            return horizon_from_raw_pub

    # (5) Unicode dominance
    dom = _unicode_dominance(raw)
    if dom == "english":
        if _GERM_TEXT_RE.search(raw):
            return "german"
        if _FR_TEXT_RE.search(raw):
            return "french"
        return "english"
    if dom is not None:
        return dom

    return "unknown"
