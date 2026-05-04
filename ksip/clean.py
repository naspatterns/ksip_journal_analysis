"""문자열 클리닝 — PUA 제거, 트레일링 언더스코어 제거, NFKC 정규화.

원본 보존이 필요한 경우 호출자가 _원본 컬럼을 백업한 뒤 적용할 것.
"""
from __future__ import annotations

import re
import unicodedata

# Unicode Private Use Area (BMP, U+E000–U+F8FF) — KCI 데이터에 산발적으로 등장.
# Supplementary PUA-A/B (U+F0000+)는 거의 없으나 동일하게 처리.
_PUA_RE = re.compile("[-\U000f0000-\U0010fffd]")

# 양 끝의 underscore 묶음 (KCI는 부제를 _ … _로 감싼 케이스가 많음)
_TRIM_UNDERSCORES_RE = re.compile(r"^_+|_+$")
_MULTI_WS_RE = re.compile(r"\s+")


def clean_title(s: str) -> str:
    """논문명 클리닝: PUA 제거 → 양끝 underscore 제거 → 공백 정규화.

    부제 구분자로 쓰인 중간 underscore는 보존한다.
    """
    if not isinstance(s, str):
        return s
    s = _PUA_RE.sub("", s)
    s = _TRIM_UNDERSCORES_RE.sub("", s)
    s = _MULTI_WS_RE.sub(" ", s)
    return s.strip()


def clean_keyword(s: str) -> str:
    """키워드 클리닝: PUA 제거 + NFKC 정규화 + 공백 정규화."""
    if not isinstance(s, str):
        return s
    s = _PUA_RE.sub("", s)
    s = unicodedata.normalize("NFKC", s)
    s = _MULTI_WS_RE.sub(" ", s)
    return s.strip()
