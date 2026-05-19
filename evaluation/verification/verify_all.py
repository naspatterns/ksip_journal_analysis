"""마스터 — 9개 verifier 순차 실행 + verify_summary.md 생성.

각 verifier 의 CSV 결과를 합쳐 종합 판정·이슈 요약 작성.
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

import pandas as pd

from _common import OUTPUT_DIR, WORKTREE_ROOT, ensure_output_dir

# 실행 중인 python 을 그대로 사용 — venv 자동 상속, 멀티 컴퓨터 portable
PY = sys.executable
VERIF_DIR = WORKTREE_ROOT / "evaluation" / "verification"

VERIFIERS = [
    ("L1",  "verify_01_source.py",          "Source 파일 · 시트 · 행수"),
    ("L2",  "verify_02_transform.py",       "xls → parquet 변환 + artiId"),
    ("L4",  "verify_03_referential.py",     "Cross-parquet 논문ID 무결성"),
    ("L5",  "verify_04_cleaning.py",        "클리닝 (119/297/14)"),
    ("L6",  "verify_05_dictionary.py",      "Dictionary 일관성"),
    ("L7",  "verify_06_coverage_gap.py",    "Coverage gap (substring vs exact)"),
    ("L8",  "verify_07_references.py",      "Reference 파싱 (7유형, 자기인용)"),
    ("L9",  "verify_08_institutions.py",    "기관 부모(rollup)"),
    ("L10", "verify_09_kci_spotcheck.py",   "KCI API spot-check 30편"),
]


def run_one(script: str) -> int:
    print(f"\n{'='*60}")
    print(f"실행: {script}")
    print('='*60)
    r = subprocess.run([PY, str(VERIF_DIR / script)], cwd=str(WORKTREE_ROOT))
    return r.returncode


def load_csv_results(path: Path) -> list[dict]:
    if not path.exists():
        return []
    df = pd.read_csv(path, encoding="utf-8")
    return df.to_dict("records")


def main() -> int:
    out_dir = ensure_output_dir()
    print(f"# 데이터 무결성 검증 — 마스터 실행")
    print(f"시각: {dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"산출: {out_dir.relative_to(WORKTREE_ROOT)}")

    # 1) 9개 verifier 실행
    exit_codes = {}
    for layer, script, _ in VERIFIERS:
        rc = run_one(script)
        exit_codes[layer] = rc

    # 2) 각 CSV 결과 합산
    print(f"\n\n{'#'*60}")
    print("# 결과 요약")
    print('#'*60)

    summary_lines: list[str] = []
    summary_lines.append("# 무결성 검증 결과 — "
                         f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    summary_lines.append("")
    summary_lines.append("관련 문서: [`VERIFICATION_PLAN.md`](../../docs/VERIFICATION_PLAN.md), "
                         "[`ISSUES.md`](../../docs/ISSUES.md)")
    summary_lines.append("")

    # 전체 판정
    all_results = []
    for layer, script, desc in VERIFIERS:
        csv_name = script.replace(".py", ".csv")
        csv_path = out_dir / csv_name
        rows = load_csv_results(csv_path)
        all_results.append((layer, script, desc, rows))

    # 카운트
    total = {"FATAL": 0, "WARN": 0, "INFO": 0, "PASS": 0}
    layer_counts = {}
    for layer, _, _, rows in all_results:
        c = {"FATAL": 0, "WARN": 0, "INFO": 0, "PASS": 0}
        for r in rows:
            sev = r.get("severity")
            if sev in c:
                c[sev] += 1
                total[sev] += 1
        layer_counts[layer] = c

    verdict_overall = ("FAIL" if total["FATAL"] else
                       "WARN" if total["WARN"] else "PASS")

    summary_lines.append(f"## 전체 판정: **{verdict_overall}**")
    summary_lines.append("")
    summary_lines.append(f"- FATAL: {total['FATAL']}")
    summary_lines.append(f"- WARN: {total['WARN']}")
    summary_lines.append(f"- INFO: {total['INFO']}")
    summary_lines.append(f"- PASS: {total['PASS']}")
    summary_lines.append("")

    # 레이어별 표
    summary_lines.append("## 레이어별")
    summary_lines.append("")
    summary_lines.append("| L | 검증 항목 | 판정 | FATAL | WARN | INFO | PASS | CSV |")
    summary_lines.append("|---|---|---|---|---|---|---|---|")
    for layer, script, desc, rows in all_results:
        c = layer_counts[layer]
        v = ("FAIL" if c["FATAL"] else "WARN" if c["WARN"] else "PASS")
        csv_name = script.replace(".py", ".csv")
        summary_lines.append(
            f"| {layer} | {desc} | **{v}** | {c['FATAL']} | {c['WARN']} | "
            f"{c['INFO']} | {c['PASS']} | `{csv_name}` |")
    summary_lines.append("")

    # FATAL + WARN 이슈 목록 (action items)
    summary_lines.append("## 발견 이슈 (FATAL + WARN)")
    summary_lines.append("")
    found_any = False
    for layer, script, desc, rows in all_results:
        for r in rows:
            if r.get("severity") not in ("FATAL", "WARN"):
                continue
            found_any = True
            summary_lines.append(
                f"- **[{r['severity']}]** {layer} `{r['check']}` — "
                f"{r['message']}")
    if not found_any:
        summary_lines.append("(없음 — 모든 검증 PASS/INFO)")
    summary_lines.append("")

    # 산출 CSV 목록
    summary_lines.append("## 산출 CSV (영향분 detail)")
    summary_lines.append("")
    for f in sorted(out_dir.glob("*.csv")):
        summary_lines.append(f"- `{f.name}`")
    summary_lines.append("")

    # 권장 후속
    summary_lines.append("## 권장 후속")
    summary_lines.append("")
    if total["FATAL"] == 0 and total["WARN"] == 0:
        summary_lines.append("- 모든 검증 통과. Phase 4 라벨링 파이프라인 착수 가능.")
    else:
        summary_lines.append("- 위 FATAL/WARN 항목을 `evaluation/docs/ISSUES.md` 에 ticket 으로 등재")
        summary_lines.append("- FATAL 은 즉시 수정 → 해당 verifier 재실행")
        summary_lines.append("- WARN 은 Phase 4 검수 환류 또는 별도 해소")
    summary_lines.append("")

    summary_path = out_dir / "verify_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"\n요약 → {summary_path.relative_to(WORKTREE_ROOT)}")
    print(f"\n전체 판정: {verdict_overall}")
    print(f"  FATAL={total['FATAL']} WARN={total['WARN']} "
          f"INFO={total['INFO']} PASS={total['PASS']}")

    return 1 if total["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
