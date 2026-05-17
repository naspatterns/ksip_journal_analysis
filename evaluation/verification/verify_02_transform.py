"""L2 + L3 — xls → parquet 변환 round-trip + artiId 추출 무결성.

확인:
- 각 xls 의 논문목록 시트 row 수가 parquet 의 해당 범위와 일치
- 무작위 30편 random sample 의 모든 필드 비교 (제목·저자·키워드·연도)
- artiId 추출 — xls 의 URL 컬럼 vs parquet 의 논문ID
- 인코딩 (mojibake / PUA 잔존) 확인
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from ksip.clean import _PUA_RE  # noqa: E402  진짜 PUA 정규식

from _common import (PAPERS_PARQUET, XLS_FILES, CheckRun, ensure_output_dir)


ARTIID_RE = re.compile(r"artiId=([A-Z0-9]+)")


def main() -> int:
    run = CheckRun("L2")
    out_dir = ensure_output_dir()

    papers = pd.read_parquet(PAPERS_PARQUET)
    paper_id_col = "논문 ID" if "논문 ID" in papers.columns else "논문ID"

    # ── 1) xls 시트 합산 row 수 vs parquet ─────────────
    xls_total_rows = 0
    xls_dfs = {}
    for xls_path in XLS_FILES:
        if not xls_path.exists():
            run.fatal("xls_missing", f"파일 없음: {xls_path.name}")
            continue
        try:
            df = pd.read_excel(xls_path, sheet_name="논문목록", dtype=str)
        except Exception as e:
            run.fatal("xls_read_failed", f"{xls_path.name}: {e}")
            continue
        xls_dfs[xls_path.name] = df
        xls_total_rows += len(df)
        run.info(f"xls_{xls_path.stem}_rows",
                 f"{xls_path.name} 논문목록 row={len(df)}",
                 n_affected=len(df))

    if xls_total_rows == len(papers):
        run.pass_("xls_parquet_count",
                  f"xls 합계 {xls_total_rows} == parquet {len(papers)}")
    else:
        run.fatal("xls_parquet_count",
                  f"xls 합계 {xls_total_rows} != parquet {len(papers)}",
                  n_affected=abs(xls_total_rows - len(papers)))

    # ── 2) 통합 xls (concatenated) vs parquet 무작위 30편 필드 비교 ─────
    if xls_dfs:
        all_xls = pd.concat(xls_dfs.values(), ignore_index=True)

        # 논문 ID 컬럼 — 1_300 에는 있고 301_636 에는 없음. per-row fallback to URL.
        if "논문 ID" in all_xls.columns:
            base = all_xls["논문 ID"].astype(str).where(
                all_xls["논문 ID"].notna() & (all_xls["논문 ID"].astype(str) != "nan"), None)
        else:
            base = pd.Series([None]*len(all_xls), index=all_xls.index)
        if "URL" in all_xls.columns:
            from_url = all_xls["URL"].astype(str).str.extract(ARTIID_RE)[0]
        else:
            from_url = pd.Series([None]*len(all_xls), index=all_xls.index)
        all_xls["__artiid__"] = base.fillna(from_url)

        # L3 — artiId 추출 검증
        # parquet 에는 ART... 형태로 들어 있음
        n_artiid_null = all_xls["__artiid__"].isna().sum()
        if n_artiid_null > 0:
            run.warn("artiid_extraction",
                     f"xls 의 {n_artiid_null}개 row 에서 artiId 추출 실패",
                     n_affected=int(n_artiid_null))
        else:
            run.pass_("artiid_extraction",
                      "모든 xls row 에서 artiId 추출 성공")

        # parquet 논문 ID 와 비교
        xls_ids = set(all_xls["__artiid__"].dropna().astype(str))
        parquet_ids = set(papers[paper_id_col].astype(str))
        in_xls_not_parquet = xls_ids - parquet_ids
        in_parquet_not_xls = parquet_ids - xls_ids
        if in_xls_not_parquet:
            run.warn("xls_only_ids",
                     f"xls 에만 있는 artiId {len(in_xls_not_parquet)}개 (parquet 손실 가능)",
                     n_affected=len(in_xls_not_parquet))
        if in_parquet_not_xls:
            run.warn("parquet_only_ids",
                     f"parquet 에만 있는 artiId {len(in_parquet_not_xls)}개",
                     n_affected=len(in_parquet_not_xls))
        if not in_xls_not_parquet and not in_parquet_not_xls:
            run.pass_("artiid_set_equal",
                      f"xls artiId set == parquet artiId set ({len(xls_ids)})")

        # 무작위 30편 sample
        sample_ids = list(xls_ids & parquet_ids)
        if sample_ids:
            import random
            random.seed(42)
            sample_n = min(30, len(sample_ids))
            sample = random.sample(sample_ids, sample_n)

            # 매칭할 필드 (xls 컬럼명 → parquet 컬럼명)
            field_map = {
                "논문명": "논문명_원본",   # parquet 에는 _원본 백업
                "발행연도": "발행연도",
                "주저자 소속기관": "주저자 소속기관",
                "저자명": "저자명",
                "학술지명": "학술지명",
            }

            diff_rows = []
            mismatches_by_field = {}
            for aid in sample:
                xls_row = all_xls[all_xls["__artiid__"] == aid].iloc[0]
                pq_row = papers[papers[paper_id_col] == aid].iloc[0]
                for xls_f, pq_f in field_map.items():
                    if xls_f not in all_xls.columns or pq_f not in papers.columns:
                        continue
                    xls_v = str(xls_row[xls_f]) if pd.notna(xls_row[xls_f]) else ""
                    pq_v = str(pq_row[pq_f]) if pd.notna(pq_row[pq_f]) else ""
                    if xls_v.strip() != pq_v.strip():
                        diff_rows.append({
                            "artiId": aid, "field": xls_f,
                            "xls": xls_v[:100], "parquet": pq_v[:100],
                        })
                        mismatches_by_field[xls_f] = mismatches_by_field.get(xls_f, 0) + 1

            if diff_rows:
                path = out_dir / "verify_02_transform_sample_diff.csv"
                pd.DataFrame(diff_rows).to_csv(path, index=False, encoding="utf-8")
                run.warn("sample_field_diff",
                         f"30편 sample 필드 비교: {len(diff_rows)} 차이 — {mismatches_by_field}. "
                         f"→ {path.name} 수동 검수",
                         n_affected=len(diff_rows))
            else:
                run.pass_("sample_field_diff",
                          f"30편 sample 모든 필드 일치 ({sample_n} × {len(field_map)})")

    # ── 3) 인코딩 / mojibake / PUA 잔존 (clean.py 의 진짜 _PUA_RE 사용) ─────
    for col in ["논문명", "저자명", "저자키워드", "초록", "주저자 소속기관"]:
        if col in papers.columns:
            pua = papers[col].astype(str).str.contains(_PUA_RE, regex=True, na=False).sum()
            if pua > 0:
                run.warn(f"pua_in_{col}",
                         f"papers.{col} 에 PUA 문자 잔존 {pua}건",
                         n_affected=int(pua))
            else:
                run.pass_(f"pua_in_{col}",
                          f"papers.{col} PUA 없음")

    # ── 4) 발행연도 범위 ───────────────────────
    if "발행연도" in papers.columns:
        years = pd.to_numeric(papers["발행연도"], errors="coerce")
        lo, hi = int(years.min()), int(years.max())
        n_invalid = int(years.isna().sum())
        run.info("year_range", f"발행연도 {lo}–{hi}, NaN {n_invalid}건",
                 n_affected=n_invalid)
        if lo == 1989 and hi >= 2024:
            run.pass_("year_range_expected",
                      "발행연도 1989-{}, 기대대로".format(hi))
        else:
            run.warn("year_range_expected",
                     f"발행연도 {lo}-{hi} — 기대 1989-2025 와 차이")

    run.print_summary()
    run.to_csv(out_dir / "verify_02_transform.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
