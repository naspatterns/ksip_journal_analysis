"""KCI Open API의 citationDetail에서 학술지 메타 + 17년 시계열 추출.

호출: 1회 (캐시되면 0회)
출력:
  data/processed/journal_metrics.parquet      ← Streamlit 앱이 읽음
  data/processed/journal_metrics.csv          ← 사람이 직접 열어보기 좋음
  data/processed/journal_change_history.parquet
  data/processed/journal_change_history.csv
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ksip.kci_api import get_citation_detail, text_of  # noqa: E402

OUT_DIR = ROOT / "data" / "processed"
SERE_ID = "001529"  # 인도철학


def _pct_to_float(s: str) -> float | None:
    """'21.05%' → 0.2105. 빈 값/'-' → None."""
    s = s.strip()
    if not s or s in ("-", "0%"):
        return 0.0 if s == "0%" else None
    if s.endswith("%"):
        try:
            return float(s.rstrip("%")) / 100.0
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_float(s: str) -> float | None:
    """'-' 또는 빈 값 → None, 숫자 문자열 → float."""
    s = s.strip()
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(s: str) -> int | None:
    s = s.strip()
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_journal_metrics(root: ET.Element) -> pd.DataFrame:
    """citationDetail 응답 → 연도별 시계열 DF."""
    rows = []
    for idx in root.findall(".//journal-citation-index"):
        year = idx.get("year")
        rows.append({
            "연도": int(year) if year else None,
            "IF_2년": _to_float(text_of(idx.find("impactFactor"))),
            "IF_3년": _to_float(text_of(idx.find("impactFactor3"))),
            "IF_4년": _to_float(text_of(idx.find("impactFactor4"))),
            "IF_5년": _to_float(text_of(idx.find("impactFactor5"))),
            "IF_2년_자기인용제외": _to_float(text_of(idx.find("exImpactFactor"))),
            "WoS_IF": _to_float(text_of(idx.find("wosImpactFactor"))),
            "SJR": _to_float(text_of(idx.find("sjr"))),
            "즉시성지수": _to_float(text_of(idx.find("immediacyIndex"))),
            "자기인용지수": _pct_to_float(text_of(idx.find("selfCitedRate"))),
            "발행논문수_2년창": _to_int(text_of(idx.find("yearsArticles2"))),
            "피인용수_2년창": _to_int(text_of(idx.find("yearsCited2"))),
        })
    df = pd.DataFrame(rows).dropna(subset=["연도"]).sort_values("연도")
    return df.reset_index(drop=True)


def parse_change_history(root: ET.Element) -> pd.DataFrame:
    """등재 단계 변천사 추출."""
    rows = []
    for ch in root.findall(".//journal-change"):
        rows.append({
            "날짜": ch.get("date"),
            "구분코드": ch.get("div-cd"),
            "내용": (ch.text or "").strip(),
        })
    return pd.DataFrame(rows)


def parse_static_meta(root: ET.Element) -> dict:
    """학술지 정적 메타(이름·ISSN·창간·발행자 등). 1행짜리 dict."""
    j = root.find(".//journalInfo")
    p = root.find(".//publisher") if j is not None else None
    reg = j.find("registration/kci-registration") if j is not None else None
    out = {
        "sereId": j.get("journal-id") if j is not None else None,
        "kor_name": text_of(j.find("journal-kor-name")) if j is not None else "",
        "fola_name": text_of(j.find("journal-fola-name")) if j is not None else "",
        "kor_abbr": text_of(j.find("journal-kor-abbr-name")) if j is not None else "",
        "ISSN": text_of(j.find("issn")) if j is not None else "",
        "분야": text_of(j.find("major")) if j is not None else "",
        "창간연도": text_of(j.find("fsed-yr")) if j is not None else "",
        "발행주기": text_of(j.find("impr")) if j is not None else "",
        "현재호": text_of(j.find("current-issue")) if j is not None else "",
        "현재_등재상태": text_of(reg) if reg is not None else "",
        "발행자_kor": text_of(p.find("publisher-kor-name")) if p is not None else "",
        "발행자_eng": text_of(p.find("publisher-eng-name")) if p is not None else "",
        "발행자_홈페이지": text_of(p.find("publisher-homp")) if p is not None else "",
        "발행자_주소": text_of(p.find("publisher-addr")) if p is not None else "",
    }
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[KCI] citationDetail 호출 (sereId={SERE_ID})…")
    resp = get_citation_detail(SERE_ID)
    print(f"     {'캐시 사용' if resp.from_cache else '새로 호출'} · {len(resp.raw_xml):,} bytes")

    root = resp.root
    err = root.find(".//resultMsg")
    if err is not None and "등록되지" in (err.text or ""):
        print(f"  ERROR: {err.text}")
        sys.exit(1)

    metrics = parse_journal_metrics(root)
    history = parse_change_history(root)
    static = parse_static_meta(root)

    metrics_pq = OUT_DIR / "journal_metrics.parquet"
    metrics_csv = OUT_DIR / "journal_metrics.csv"
    history_pq = OUT_DIR / "journal_change_history.parquet"
    history_csv = OUT_DIR / "journal_change_history.csv"
    static_csv = OUT_DIR / "journal_static_meta.csv"

    metrics.to_parquet(metrics_pq, index=False)
    metrics.to_csv(metrics_csv, index=False, encoding="utf-8-sig")
    history.to_parquet(history_pq, index=False)
    history.to_csv(history_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame([static]).to_csv(static_csv, index=False, encoding="utf-8-sig")

    print()
    print("=== 학술지 정적 메타 ===")
    for k, v in static.items():
        print(f"  {k:18s}: {v}")

    print()
    print("=== 시계열 메트릭 (17년) ===")
    print(metrics.to_string(index=False))

    print()
    print("=== 등재 단계 변천사 ===")
    print(history.to_string(index=False) if not history.empty else "(데이터 없음)")

    print()
    print("✓ 저장됨:")
    for p in [metrics_pq, metrics_csv, history_pq, history_csv, static_csv]:
        print(f"  {p.relative_to(ROOT)}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
