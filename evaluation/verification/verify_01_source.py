"""L1 — Source 파일 존재·열림·시트·행 수 검증.

확인:
- 3개 xls 파일 + 통합 csv 가 존재하고 열림
- 각 xls 의 시트 이름 / 행 수
- 통합 csv 의 행 수
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from _common import (CheckRun, OUTPUT_DIR, RAW_DIR, XLS_FILES, ensure_output_dir)


def main() -> int:
    run = CheckRun("L1")

    # raw 디렉토리 자체
    if not RAW_DIR.exists():
        run.fatal("raw_dir_exists", f"raw 디렉토리 없음: {RAW_DIR}")
        run.print_summary()
        run.to_csv(ensure_output_dir() / "verify_01_source.csv")
        return 1
    run.pass_("raw_dir_exists", f"raw 디렉토리: {RAW_DIR}")

    # 각 xls
    expected_papers_in_xls = {
        "인도철학_1_300.xls": (1, 300),
        "인도철학_301_600.xls": (301, 600),
        "인도철학_601_636.xls": (601, 636),
    }
    for xls in XLS_FILES:
        if not xls.exists():
            run.fatal("xls_exists", f"파일 없음: {xls.name}")
            continue
        try:
            xl = pd.ExcelFile(xls)
        except Exception as e:
            run.fatal("xls_openable", f"{xls.name}: {e}")
            continue

        sheets = xl.sheet_names
        run.info("xls_sheets", f"{xls.name}: 시트 = {sheets}",
                 n_sheets=len(sheets))

        # 논문목록 시트 (가장 중요)
        # 시트명이 정확히 뭔지 모를 수 있으니 우선순위로 찾기
        candidates = [s for s in sheets if "논문" in s or "목록" in s
                      or s == "Sheet1" or s.startswith("논문목록")]
        if not candidates:
            candidates = [sheets[0]]
        main_sheet = candidates[0]
        try:
            df = pd.read_excel(xls, sheet_name=main_sheet, dtype=str)
        except Exception as e:
            run.fatal("xls_main_sheet_read",
                      f"{xls.name}/{main_sheet}: {e}")
            continue

        n_rows = len(df)
        lo, hi = expected_papers_in_xls[xls.name]
        expected_n = hi - lo + 1
        msg = (f"{xls.name}/{main_sheet}: row={n_rows}, "
               f"기대 ~{expected_n}편 (#{lo}-{hi})")
        if abs(n_rows - expected_n) <= 2:
            run.pass_("xls_main_sheet_rows", msg, n_rows=n_rows)
        else:
            run.warn("xls_main_sheet_rows",
                     msg + " — 차이 발생", n_affected=abs(n_rows-expected_n))

        # 참고문헌 / 저자 / 키워드 등 추가 시트 식별
        for s in sheets:
            if s == main_sheet:
                continue
            try:
                df_s = pd.read_excel(xls, sheet_name=s, dtype=str)
                run.info(f"xls_sheet_{s[:15]}",
                         f"{xls.name}/{s}: row={len(df_s)}",
                         n_rows=len(df_s))
            except Exception as e:
                run.warn(f"xls_sheet_{s[:15]}",
                         f"{xls.name}/{s}: 읽기 실패 — {e}")

    # 통합 csv
    csv_path = RAW_DIR / "인도철학_통합.csv"
    if csv_path.exists():
        try:
            df_csv = pd.read_csv(csv_path, dtype=str, low_memory=False)
            run.info("csv_unified",
                     f"통합 csv row={len(df_csv)}", n_rows=len(df_csv))
            if abs(len(df_csv) - 636) > 5:
                run.warn("csv_unified_row_count",
                         f"통합 csv 행 수 {len(df_csv)} != 기대 636 ± 5")
        except Exception as e:
            run.warn("csv_unified", f"읽기 실패 — {e}")
    else:
        run.info("csv_unified", "통합 csv 없음 (선택 파일)")

    run.print_summary()
    run.to_csv(ensure_output_dir() / "verify_01_source.csv")

    c = run.counts()
    return 1 if c["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
