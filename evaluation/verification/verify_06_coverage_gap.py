"""L7 — Coverage gap: substring audit vs exact-match resolve 차이 정량화.

확인:
- 키워드/제목에 substring 매칭되지만 exact-match resolve 못 잡는 surface 식별
- 사전 보강 우선순위 (빈도 상위) 제시
- 사전 dead surface (등록됐으나 데이터에 없는 surface) 식별
"""
from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import ksip.normalize  # noqa: E402
from ksip.normalize import load_authority  # noqa: E402

from _common import (DICT_DIR, KEYWORDS_PARQUET, PAPERS_PARQUET, CheckRun,
                     ensure_output_dir)


def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s).strip()


def main() -> int:
    run = CheckRun("L7")
    out_dir = ensure_output_dir()

    ksip.normalize.load_authority.cache_clear()
    # build_data.py 와 동일 모드: verified=True 만 사용
    auth = load_authority("concepts", include_unverified=False)
    auth_with_unverified = load_authority("concepts", include_unverified=True)
    n_unverified_gap = len(auth_with_unverified.records) - len(auth.records)
    if n_unverified_gap > 0:
        run.info("unverified_entries",
                 f"verified=False entry {n_unverified_gap}개 — 분석에 미적용 (의도)",
                 n_affected=n_unverified_gap)

    kw = pd.read_parquet(KEYWORDS_PARQUET)
    papers = pd.read_parquet(PAPERS_PARQUET)

    # 1) keywords resolve 율 (canonical_id 컬럼 vs 재계산)
    kw["resolve_now"] = kw["키워드_원본"].astype(str).map(auth.resolve)
    n = len(kw)
    n_resolved = int(kw["resolve_now"].notna().sum())
    coverage = n_resolved / n if n else 0
    run.info("keywords_coverage",
             f"keywords resolve 율: {n_resolved}/{n} ({coverage*100:.1f}%)")

    # parquet 의 기존 canonical_id 와 비교 (drift 점검)
    if "canonical_id" in kw.columns:
        old = kw["canonical_id"].notna().sum()
        if abs(int(old) - n_resolved) > 5:
            run.warn("coverage_drift",
                     f"기존 build {old} vs 현재 {n_resolved} 차이 — "
                     "사전 변경 후 build_data 재실행 필요할 수 있음",
                     n_affected=abs(int(old) - n_resolved))
        else:
            run.pass_("coverage_drift",
                      f"기존 build vs 현재 resolve 일치 (~ {n_resolved})")

    # 2) substring 매칭은 되는데 exact 못 잡는 surface — 사전 보강 후보
    #    사전에 등록된 모든 surface 의 NFKC-lower set
    registered = set()
    surface_orig_by_norm: dict[str, str] = {}
    for cid, rec in auth.records.items():
        for s in rec.surface_forms:
            k = _nfkc(s).lower()
            if k:
                registered.add(k)
                surface_orig_by_norm[k] = s

    # 미해상도 키워드 top
    unresolved = kw.loc[kw["resolve_now"].isna(), "키워드_원본"].astype(str)
    unresolved_top = unresolved.value_counts().head(50)

    # 미해상도 중 substring 으로 사전 surface 와 일부 겹치는 것 (정말 누락 가능성)
    candidates = []
    registered_normed = list(registered)
    for surf, cnt in unresolved_top.items():
        norm = _nfkc(surf).lower()
        # 사전의 어떤 등록 surface 와 substring 관계?
        matches = []
        for rs in registered_normed:
            if rs and rs in norm or norm in rs:
                if rs != norm:
                    matches.append(surface_orig_by_norm.get(rs, rs))
                    if len(matches) >= 3:
                        break
        candidates.append({
            "surface": surf, "count": int(cnt),
            "near_registered": " | ".join(matches[:3]),
        })

    if candidates:
        path = out_dir / "verify_06_coverage_gap_unresolved.csv"
        pd.DataFrame(candidates).to_csv(path, index=False, encoding="utf-8")
        run.info("unresolved_top_saved",
                 f"미해상도 TOP 50 → {path.name}",
                 n_affected=len(candidates))

    # 3) 사전 dead surface — 등록됐으나 데이터에서 0건
    all_data_norm = set()
    for s in kw["키워드_원본"].astype(str):
        all_data_norm.add(_nfkc(s).lower())
    # 제목도 살펴봄 (substring)
    title_concat = " ".join(papers["논문명"].astype(str).str.lower())

    dead_surfaces = []
    for cid, rec in auth.records.items():
        for s in rec.surface_forms:
            k = _nfkc(s).lower()
            if not k:
                continue
            in_kw = k in all_data_norm
            in_title = k in title_concat
            if not (in_kw or in_title):
                dead_surfaces.append({"canonical_id": cid, "surface": s})
    if dead_surfaces:
        path = out_dir / "verify_06_coverage_gap_dead_surfaces.csv"
        pd.DataFrame(dead_surfaces).to_csv(path, index=False, encoding="utf-8")
        run.info("dead_surfaces",
                 f"사전 등록됐으나 데이터에 0건인 surface {len(dead_surfaces)}개 → {path.name}",
                 n_affected=len(dead_surfaces))

    # 4) substring audit (Phase 2) 결과와 exact-match 의 gap 정량화
    #    audit_keyword_coverage.py 의 CANDIDATES 리스트를 다시 돌려도 되지만
    #    여기선 단순화: 사전의 각 canonical 의 surface 중 가장 짧은 것을 substring 으로 검색
    #    → 해당 surface 가 데이터에 substring 매칭되는 빈도 vs exact resolve 빈도
    rows = []
    for cid, rec in auth.records.items():
        # exact 매칭 빈도
        exact_hits = int(sum(auth.resolve(s) == cid for s in kw["키워드_원본"].astype(str)))
        # substring 매칭 — 가장 짧은 의미 있는 surface 사용
        short_surfaces = sorted([s for s in rec.surface_forms if len(s) >= 2],
                                key=len)[:2]
        if not short_surfaces:
            continue
        for s in short_surfaces:
            t = s.lower()
            sub_in_kw = kw["키워드_원본"].astype(str).str.lower().str.contains(t, regex=False, na=False).sum()
            sub_in_title = papers["논문명"].astype(str).str.lower().str.contains(t, regex=False, na=False).sum()
            rows.append({
                "canonical_id": cid,
                "surface_used": s,
                "substring_kw": int(sub_in_kw),
                "substring_title": int(sub_in_title),
                "exact_kw": exact_hits,
                "gap_kw": int(sub_in_kw) - exact_hits,
            })

    gap_df = pd.DataFrame(rows)
    # 의미 있는 gap (substring > exact, 빈도 ≥ 2)
    big_gap = gap_df[(gap_df["gap_kw"] >= 2)].sort_values("gap_kw", ascending=False).head(30)
    if not big_gap.empty:
        path = out_dir / "verify_06_coverage_gap_substring_vs_exact.csv"
        big_gap.to_csv(path, index=False, encoding="utf-8")
        run.warn("substring_exact_gap",
                 f"substring > exact gap 큰 entry TOP 30 → {path.name}. "
                 f"surface_forms 확장 필요. 예: "
                 f"{[(r['canonical_id'], r['gap_kw']) for _, r in big_gap.head(3).iterrows()]}",
                 n_affected=int(big_gap["gap_kw"].sum()))
    else:
        run.pass_("substring_exact_gap", "substring-exact gap 미미")

    run.print_summary()
    run.to_csv(out_dir / "verify_06_coverage_gap.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
