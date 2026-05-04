"""기관명에서 부모 대학교/기관을 추출.

전략:
1. `data/dictionaries/institutions.yml`의 명시적 alias 우선
2. 정규식 `^(.+?대학교)\b` (첫 '대학교'까지 추출)
3. 둘 다 실패하면 surface form 그대로 반환

Authority Control 일관성: surface 보존, canonical만 별도 컬럼으로.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

DICT_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "dictionaries" / "institutions.yml"
)
_PARENT_REGEX = re.compile(r"^(.+?대학교)\b")


@lru_cache(maxsize=1)
def _alias_map() -> dict[str, str]:
    """institutions.yml의 surface_forms → canonical_form 매핑.

    verified=false 항목은 무시한다.
    """
    if not DICT_PATH.exists():
        return {}
    with DICT_PATH.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []
    m: dict[str, str] = {}
    for entry in raw:
        if not entry.get("verified", False):
            continue
        cf = entry["canonical_form"]
        for sf in entry.get("surface_forms", []):
            m[sf.strip()] = cf
    return m


def parent_institution(name: str | float | None) -> str:
    """기관명을 부모 기관(대학교 단위)으로 정규화.

    >>> parent_institution("동국대학교 불교학부")
    '동국대학교'
    >>> parent_institution("동국대 인도철학과")          # 사전 alias
    '동국대학교'
    >>> parent_institution("장경도량고려대장경연구소")  # 자체 보존
    '장경도량고려대장경연구소'
    """
    if not isinstance(name, str) or not name.strip():
        return name if isinstance(name, str) else "(미기재)"
    s = name.strip()
    aliases = _alias_map()
    if s in aliases:
        return aliases[s]
    if m := _PARENT_REGEX.match(s):
        return m.group(1)
    return s
