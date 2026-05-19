"""키워드/제목에서 학파·인물·텍스트 후보의 실제 등장 빈도 감사.

사용자 원칙: "키워드 리스트에 등장하지 않으면 사전에 안 넣고, 등장하면 넣는다."
사전 entry 추가 의사결정의 근거 데이터.

산출:
    evaluation/output/keyword_audit.csv     — 후보 × (kw 빈도, title 빈도, surface 변형 수, 변형 샘플)

실행:
    .venv/bin/python evaluation/labeling/audit_keyword_coverage.py
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
PAPERS_PATH = ROOT / "data" / "processed" / "papers.parquet"
KEYWORDS_PATH = ROOT / "data" / "processed" / "keywords.parquet"
OUT_PATH = ROOT / "evaluation" / "output" / "keyword_audit.csv"


# ============================================================
# 감사 대상 후보 — 카테고리 × (한글/한자/IAST/영문 변형)
# 빈도 0 이라도 기록해 두면 "찾았으나 없었다" 의 증거가 됨.
# ============================================================

CANDIDATES: list[tuple[str, str, str]] = [
    # (카테고리, 라벨, 검색어 — 소문자 비교)
    ("동아시아_학파", "화엄(한글)",          "화엄"),
    ("동아시아_학파", "화엄(華嚴)",          "華嚴"),
    ("동아시아_학파", "천태(한글)",          "천태"),
    ("동아시아_학파", "천태(天台)",          "天台"),
    ("동아시아_학파", "선종(한글)",          "선종"),
    ("동아시아_학파", "선(禪)",              "禪"),
    ("동아시아_학파", "정토(한글)",          "정토"),
    ("동아시아_학파", "정토(淨土)",          "淨土"),
    ("동아시아_학파", "법상(한글)",          "법상"),
    ("동아시아_학파", "법상(法相)",          "法相"),
    ("동아시아_학파", "삼론(한글)",          "삼론"),
    ("동아시아_학파", "진언",                "진언"),
    ("동아시아_학파", "밀교(密敎)",          "密敎"),
    ("동아시아_학파", "동아시아",            "동아시아"),

    ("중국_인물", "법장(法藏 한자)",         "法藏"),
    ("중국_인물", "법장(한글)",              "법장"),
    ("중국_인물", "지엄(智儼)",              "智儼"),
    ("중국_인물", "지엄(한글)",              "지엄"),
    ("중국_인물", "지의(智顗)",              "智顗"),
    ("중국_인물", "지의(한글)",              "지의"),
    ("중국_인물", "혜능(慧能)",              "慧能"),
    ("중국_인물", "혜능(한글)",              "혜능"),
    ("중국_인물", "육조(六祖)",              "六祖"),
    ("중국_인물", "규기(窺基)",              "窺基"),
    ("중국_인물", "규기(한글)",              "규기"),
    ("중국_인물", "선도(善導)",              "善導"),
    ("중국_인물", "길장(吉藏)",              "吉藏"),
    ("중국_인물", "길장(한글)",              "길장"),
    ("중국_인물", "구마라집(鳩摩羅什)",      "羅什"),
    ("중국_인물", "구마라집(한글)",          "구마라"),

    ("일본_인물", "신란(親鸞)",              "親鸞"),
    ("일본_인물", "신란(한글)",              "신란"),
    ("일본_인물", "도원(道元)",              "道元"),
    ("일본_인물", "도원(한글)",              "도원"),
    ("일본_인물", "쿠우카이(空海)",          "空海"),

    ("한국_인물", "원효",                    "원효"),
    ("한국_인물", "의상",                    "의상"),
    ("한국_인물", "지눌",                    "지눌"),
    ("한국_인물", "보조",                    "보조"),
    ("한국_인물", "휴정",                    "휴정"),
    ("한국_인물", "서산대사",                "서산"),
    ("한국_인물", "의천",                    "의천"),
    ("한국_인물", "일연",                    "일연"),
    ("한국_인물", "균여",                    "균여"),
    ("한국_인물", "원측(한글)",              "원측"),
    ("한국_인물", "원측(圓測)",              "圓測"),

    ("동아시아_텍스트", "기신론",            "기신론"),
    ("동아시아_텍스트", "대승기신론",        "대승기신론"),
    ("동아시아_텍스트", "화엄경",            "화엄경"),
    ("동아시아_텍스트", "법화경",            "법화경"),
    ("동아시아_텍스트", "능엄경",            "능엄경"),
    ("동아시아_텍스트", "무량수경",          "무량수경"),
    ("동아시아_텍스트", "관무량수경",        "관무량수경"),
    ("동아시아_텍스트", "아미타경",          "아미타경"),
    ("동아시아_텍스트", "선문염송",          "선문염송"),
    ("동아시아_텍스트", "직지",              "직지"),
    ("동아시아_텍스트", "대각국사문집",      "대각국사"),
    ("동아시아_텍스트", "성유식론",          "성유식론"),

    ("티베트_학파", "겔룩",                  "겔룩"),
    ("티베트_학파", "닝마",                  "닝마"),
    ("티베트_학파", "카규",                  "카규"),
    ("티베트_학파", "사캬",                  "사캬"),
    ("티베트_학파", "티베트 불교",           "티베트"),
    ("티베트_학파", "티벳 불교",             "티벳"),
    ("티베트_학파", "서장",                  "서장"),

    ("티베트_인물", "쫑카파",                "쫑카"),
    ("티베트_인물", "Tsongkhapa",            "tsongkhapa"),
    ("티베트_인물", "빠드마삼바와",          "빠드마삼"),
    ("티베트_인물", "연화생",                "연화생"),
    ("티베트_인물", "까말라쉴라",            "까말라"),
    ("티베트_인물", "사꺄빤디타",            "사꺄"),
    ("티베트_인물", "미팜",                  "미팜"),

    ("근대_인도", "라마크리슈나",            "라마크리"),
    ("근대_인도", "비베카난다",              "비베카"),
    ("근대_인도", "라다크리슈난",            "라다크리"),
    ("근대_인도", "아우로빈도",              "아우로빈"),

    ("자료/방법", "한역",                    "한역"),
    ("자료/방법", "사본",                    "사본"),
    ("자료/방법", "돈황",                    "돈황"),
    ("자료/방법", "박티",                    "박티"),
    ("자료/방법", "bhakti",                  "bhakti"),
    ("자료/방법", "미맘사",                  "미맘사"),
    ("자료/방법", "하타 요가",               "하타"),
    ("자료/방법", "위빠사나",                "위빠사나"),
]


def main() -> None:
    papers = pd.read_parquet(PAPERS_PATH)
    kw = pd.read_parquet(KEYWORDS_PATH)

    all_keywords = kw["키워드_원본"].astype(str).str.lower()
    all_titles = papers["논문명"].astype(str).str.lower()

    rows = []
    for cat, label, term in CANDIDATES:
        t = term.lower()
        kw_mask = all_keywords.str.contains(t, regex=False, na=False)
        title_mask = all_titles.str.contains(t, regex=False, na=False)
        kw_hits = int(kw_mask.sum())
        title_hits = int(title_mask.sum())
        surfaces = sorted(kw.loc[kw_mask, "키워드_원본"].unique().tolist())
        n_surfaces = len(surfaces)
        surface_sample = " | ".join(surfaces[:5])
        verdict = (
            "INCLUDE" if (kw_hits + title_hits) >= 3
            else "MARGINAL" if (kw_hits + title_hits) >= 1
            else "SKIP"
        )
        rows.append({
            "category": cat,
            "label": label,
            "search_term": term,
            "kw_hits": kw_hits,
            "title_hits": title_hits,
            "n_surface_variants": n_surfaces,
            "surface_sample": surface_sample,
            "verdict": verdict,
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # 콘솔 요약
    df = pd.DataFrame(rows)
    print(f"전체 후보: {len(df)}")
    print(f"  INCLUDE  (≥3): {(df['verdict']=='INCLUDE').sum()}")
    print(f"  MARGINAL (1-2): {(df['verdict']=='MARGINAL').sum()}")
    print(f"  SKIP     (0):  {(df['verdict']=='SKIP').sum()}")
    print()
    print("=== 카테고리별 INCLUDE 후보 ===")
    inc = df[df["verdict"].isin(["INCLUDE", "MARGINAL"])]
    for cat, sub in inc.groupby("category"):
        print(f"\n[{cat}]")
        for _, r in sub.iterrows():
            print(f"  {r['verdict']:8s} {r['label']:25s} kw={r['kw_hits']:3d} title={r['title_hits']:3d}")

    print(f"\n저장 → {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
