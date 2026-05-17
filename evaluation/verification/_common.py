"""검증 스크립트 공통 헬퍼.

- 경로 상수 (raw 는 메인 프로젝트, processed/dictionaries 는 워크트리)
- 검증 결과를 FATAL/WARN/INFO 로 누적해 CSV·요약 출력
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================
# 경로
# ============================================================

# 워크트리 루트
WORKTREE_ROOT = Path(__file__).resolve().parent.parent.parent

# raw 는 메인 프로젝트에. KSIP_RAW_DIR 환경변수로 override 가능.
DEFAULT_RAW = Path(
    "/Users/jibak/Documents/@CLASSES/2026-1/DigitalHumanities/"
    "ksip_journal_analysis/data/raw"
)
RAW_DIR = Path(os.environ.get("KSIP_RAW_DIR", DEFAULT_RAW))

PROCESSED_DIR = WORKTREE_ROOT / "data" / "processed"
DICT_DIR = WORKTREE_ROOT / "data" / "dictionaries"
OUTPUT_DIR = WORKTREE_ROOT / "evaluation" / "output" / "verification"

PAPERS_PARQUET = PROCESSED_DIR / "papers.parquet"
KEYWORDS_PARQUET = PROCESSED_DIR / "keywords.parquet"
AUTHORS_PARQUET = PROCESSED_DIR / "authors.parquet"
REFERENCES_PARQUET = PROCESSED_DIR / "references.parquet"

XLS_FILES = [
    RAW_DIR / "인도철학_1_300.xls",
    RAW_DIR / "인도철학_301_600.xls",
    RAW_DIR / "인도철학_601_636.xls",
]


# ============================================================
# 결과 누적기
# ============================================================

@dataclass
class CheckResult:
    layer: str           # L1 ~ L10
    check: str           # 짧은 라벨
    severity: str        # FATAL / WARN / INFO / PASS
    message: str         # 사람이 읽는 설명
    n_affected: int = 0  # 영향 받은 row 수
    details: dict = field(default_factory=dict)


@dataclass
class CheckRun:
    """한 verifier 의 모든 체크 결과."""
    layer: str
    results: list[CheckResult] = field(default_factory=list)

    def add(self, check: str, severity: str, message: str,
            n_affected: int = 0, **details) -> CheckResult:
        r = CheckResult(
            layer=self.layer, check=check, severity=severity,
            message=message, n_affected=n_affected, details=details,
        )
        self.results.append(r)
        return r

    def pass_(self, check: str, message: str = "", n_affected: int = 0, **details):
        return self.add(check, "PASS", message or check, n_affected, **details)

    def info(self, check: str, message: str, n_affected: int = 0, **details):
        return self.add(check, "INFO", message, n_affected, **details)

    def warn(self, check: str, message: str, n_affected: int = 0, **details):
        return self.add(check, "WARN", message, n_affected, **details)

    def fatal(self, check: str, message: str, n_affected: int = 0, **details):
        return self.add(check, "FATAL", message, n_affected, **details)

    def counts(self) -> dict[str, int]:
        c = {"FATAL": 0, "WARN": 0, "INFO": 0, "PASS": 0}
        for r in self.results:
            c[r.severity] = c.get(r.severity, 0) + 1
        return c

    def print_summary(self) -> None:
        c = self.counts()
        verdict = "FAIL" if c["FATAL"] else ("WARN" if c["WARN"] else "PASS")
        print(f"\n[{self.layer}] 판정: {verdict}  "
              f"(FATAL={c['FATAL']} WARN={c['WARN']} INFO={c['INFO']} PASS={c['PASS']})")
        for r in self.results:
            tag = {"FATAL": "✗", "WARN": "·", "INFO": "i", "PASS": "✓"}[r.severity]
            line = f"  {tag} [{r.severity:5s}] {r.check:35s} {r.message}"
            if r.n_affected:
                line += f"  (n={r.n_affected})"
            print(line)

    def to_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["layer", "check", "severity", "message",
                        "n_affected", "details"])
            for r in self.results:
                w.writerow([r.layer, r.check, r.severity, r.message,
                            r.n_affected, str(r.details) if r.details else ""])


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
