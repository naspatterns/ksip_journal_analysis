"""정규화 사전(YAML) 로드 + surface form → canonical_id 해상도(resolve).

핵심 원칙:
- surface form은 절대 덮어쓰지 않는다(원본 보존).
- canonical_id를 별도 컬럼으로 추가한다.
- 사전 미등재 surface는 canonical_id=NULL로 둔다 → 나중에 빈도 분석으로 보강 우선순위 추출.
- verified=False 항목은 별도 모드에서만 사용(`include_unverified=True`).
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml


@dataclass
class AuthorityRecord:
    canonical_id: str
    canonical_form: str
    surface_forms: list[str]
    verified: bool = False
    extras: dict = field(default_factory=dict)


def _nfkc(s: str) -> str:
    """유니코드 정규화 + 양끝 공백 제거. 표층 비교용."""
    if not isinstance(s, str):
        return ""
    return unicodedata.normalize("NFKC", s).strip()


@dataclass
class Authority:
    """단일 사전(YAML 파일)에 대응하는 surface→canonical_id 인덱스."""
    records: dict[str, AuthorityRecord]                 # canonical_id → record
    surface_to_id: dict[str, str]                       # NFKC(lower) surface → canonical_id

    @classmethod
    def from_yaml(cls, path: Path, include_unverified: bool = False) -> "Authority":
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or []

        records: dict[str, AuthorityRecord] = {}
        surface_to_id: dict[str, str] = {}
        for entry in raw:
            verified = bool(entry.get("verified", False))
            if not verified and not include_unverified:
                continue
            cid = entry["canonical_id"]
            canonical_form = (
                entry.get("canonical_form")
                or entry.get("canonical_kr")
                or entry.get("canonical_iast")
                or cid
            )
            surface_list = list(entry.get("surface_forms", []))
            extras = {k: v for k, v in entry.items()
                      if k not in {"canonical_id", "canonical_form", "surface_forms", "verified"}}
            records[cid] = AuthorityRecord(
                canonical_id=cid,
                canonical_form=canonical_form,
                surface_forms=surface_list,
                verified=verified,
                extras=extras,
            )
            for s in surface_list:
                key = _nfkc(s).lower()
                if not key:
                    continue
                # 중복 surface는 마지막 entry가 이긴다 — 사전 작성자가 의도해야 함
                surface_to_id[key] = cid
        return cls(records=records, surface_to_id=surface_to_id)

    def resolve(self, surface: str) -> str | None:
        return self.surface_to_id.get(_nfkc(surface).lower())

    def canonical_form(self, canonical_id: str) -> str:
        rec = self.records.get(canonical_id)
        return rec.canonical_form if rec else canonical_id


# ============================================================
# 사전 로딩 (캐시) + DataFrame 적용
# ============================================================

DICT_DIR = Path(__file__).resolve().parent.parent / "data" / "dictionaries"


@lru_cache(maxsize=None)
def load_authority(name: str, include_unverified: bool = False) -> Authority:
    """사전 이름(예: 'concepts', 'authors', 'journals')으로 로드. 캐시 적용."""
    return Authority.from_yaml(DICT_DIR / f"{name}.yml", include_unverified=include_unverified)


def resolve_person(surface: str) -> tuple[str | None, str]:
    """저자(인물) 통합 해상도 — concepts.yml(학자) + authors.yml.

    인용된 저자에는 고전 학자(世親, 龍樹 등 → concepts.yml)와 현대 학자
    (정승석, Schmithausen 등 → authors.yml)가 섞여 있어, 두 사전을 함께 본다.

    우선순위: concepts.yml 학자 > authors.yml > surface 그대로.
    반환: (canonical_id_namespaced, display_form)
        - 매칭되면 canonical_id에 'concepts:' 또는 'authors:' 네임스페이스 prefix
        - 미매칭이면 (None, surface)
    """
    if not isinstance(surface, str) or not surface.strip():
        return None, surface or ""
    s = surface.strip()

    # 1) concepts.yml에서 type=학자인 항목 (또는 인물)
    concepts_auth = load_authority("concepts")
    cid = concepts_auth.resolve(s)
    if cid:
        rec = concepts_auth.records[cid]
        if rec.extras.get("type") in ("학자", "인물"):
            return f"concepts:{cid}", rec.canonical_form

    # 2) authors.yml
    authors_auth = load_authority("authors")
    cid = authors_auth.resolve(s)
    if cid:
        return f"authors:{cid}", authors_auth.canonical_form(cid)

    return None, s


def add_canonical_column(
    df: pd.DataFrame,
    surface_col: str,
    authority_name: str,
    out_col: str = "canonical_id",
    include_unverified: bool = False,
) -> pd.DataFrame:
    """`surface_col`을 사전으로 해상도해 `out_col`을 추가한 새 DataFrame 반환.

    원본 surface 컬럼은 그대로 유지된다. 미해상도(unresolved) 행은 NaN.
    """
    auth = load_authority(authority_name, include_unverified=include_unverified)
    result = df.copy()
    result[out_col] = result[surface_col].map(auth.resolve)
    return result


def coverage_report(
    df: pd.DataFrame,
    surface_col: str,
    authority_name: str,
    include_unverified: bool = False,
) -> pd.Series:
    """사전 적용 커버리지(=resolved 행의 비율)와 미해상도 TOP 빈도를 반환."""
    out = add_canonical_column(
        df, surface_col, authority_name, include_unverified=include_unverified
    )
    n_total = len(out)
    n_resolved = out["canonical_id"].notna().sum()
    n_rows_unresolved = n_total - n_resolved
    unresolved_top = (
        out.loc[out["canonical_id"].isna(), surface_col]
        .value_counts()
        .head(20)
    )
    return pd.Series(
        {
            "total_rows": n_total,
            "resolved_rows": n_resolved,
            "coverage": n_resolved / n_total if n_total else 0.0,
            "unresolved_rows": n_rows_unresolved,
            "unresolved_top": unresolved_top.to_dict(),
        }
    )
