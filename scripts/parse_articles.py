"""캐시된 articleDetail XML 636개를 구조화된 parquet 3종으로 파싱.

산출물 (data/processed/):
  kci_papers.parquet      — 논문 단위 enrichment (FWCI/citation-count/categories/영문제목 등)
  kci_authors.parquet     — long-form per (논문, 저자) — 영문이름/소속/저자분담
  kci_references.parquet  — long-form per (인용 논문, 참조번호) — REFARTIID + 구조화 필드

기존 papers.parquet / references.parquet 와 별개 파일. 시각화 시 JOIN.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ksip.data import load_papers  # noqa: E402
from ksip.kci_api import _cache_path, text_of  # noqa: E402

OUT_DIR = ROOT / "data" / "processed"


def _safe_int(s: str | None) -> int | None:
    if not s:
        return None
    s = s.strip()
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _safe_float(s: str | None) -> float | None:
    if not s:
        return None
    s = s.strip()
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_one(arti_id: str, xml: str) -> tuple[dict, list[dict], list[dict]]:
    """한 articleDetail 응답 → (paper_row, author_rows, ref_rows)."""
    root = ET.fromstring(xml)

    # 에러 응답 체크
    err = root.find(".//resultMsg")
    if err is not None and "등록되지" in (err.text or ""):
        return ({}, [], [])

    record = root.find(".//record")
    if record is None:
        return ({}, [], [])

    j_info = record.find("journalInfo")
    a_info = record.find("articleInfo")
    if a_info is None:
        return ({}, [], [])

    # ── 논문 단위 ────────────────────────────────────────────
    titles = {
        t.get("lang", "?"): text_of(t)
        for t in a_info.findall("title-group/article-title")
    }
    abstracts = {
        a.get("lang", "?"): text_of(a)
        for a in a_info.findall("abstract-group/abstract")
    }
    keywords_kci = [text_of(k) for k in a_info.findall("keyword-group/keyword")]

    paper = {
        "논문ID": a_info.get("article-id") or arti_id,
        "kci_categories": text_of(a_info.find("article-categories")),
        "kci_regularity": text_of(a_info.find("article-regularity")),
        "kci_language": text_of(a_info.find("article-language")),
        "title_original": titles.get("original", ""),
        "title_foreign": titles.get("foreign", ""),
        "title_english": titles.get("english", ""),
        "abstract_original_len": len(abstracts.get("original", "")),
        "abstract_english_len": len(abstracts.get("english", "")),
        "kci_keyword_count": len(keywords_kci),
        "kci_keywords_joined": " | ".join(keywords_kci),
        "fpage": text_of(a_info.find("fpage")),
        "lpage": text_of(a_info.find("lpage")),
        "doi_kci": text_of(a_info.find("doi")),
        "kci_citation_count": _safe_int(text_of(a_info.find("citation-count"))),
        "fwci": _safe_float(text_of(a_info.find("fwci"))),
        "kci_url": text_of(a_info.find("url")),
        "kci_verified": text_of(a_info.find("verified")) == "Y",
    }
    # journalInfo에서 발행 시점 보강 (월까지)
    if j_info is not None:
        paper["pub_year_kci"] = _safe_int(text_of(j_info.find("pub-year")))
        paper["pub_month_kci"] = text_of(j_info.find("pub-mon"))
        paper["volume_kci"] = text_of(j_info.find("volume"))
        paper["issue_kci"] = text_of(j_info.find("issue"))

    # ── 저자 단위 (long-form) ──────────────────────────────
    authors_long = []
    for au in a_info.findall("author-group/author"):
        authors_long.append({
            "논문ID": paper["논문ID"],
            "저자_원본": text_of(au.find("name")),
            "저자_영문": text_of(au.find("name-eng")),
            "저자_소속_kci": text_of(au.find("institution")),
            "author_division": _safe_int(au.get("author-division")),
            "author_part": au.get("author-part") or "",
        })

    # ── 참조 단위 (long-form) — KCI 등재 cited paper는 arti-id 보유 ─
    # referenceInfo 는 record 레벨의 sibling (articleInfo와 같은 부모)
    refs_long = []
    ref_info = record.find("referenceInfo")
    refs_iter = ref_info.findall("reference") if ref_info is not None else []
    for ref in refs_iter:
        refs_long.append({
            "논문ID": paper["논문ID"],
            "참조ID_kci": ref.get("refebibl-id"),
            "cited_artiId": ref.get("arti-id") or None,  # ★ REFARTIID 핵심
            "유형코드": ref.get("type-code"),
            "유형": ref.get("type-name"),
            "cited_제목": text_of(ref.find("title")),
            "cited_저자": text_of(ref.find("author")),
            "cited_학술지": text_of(ref.find("journal-name")),
            "cited_연도": _safe_int(text_of(ref.find("pubi-year"))),
            "cited_권": text_of(ref.find("volume")),
            "cited_호": text_of(ref.find("isseue")),  # KCI 응답 typo 그대로
            "cited_페이지": text_of(ref.find("page")),
            "cited_발행기관": text_of(ref.find("pubilisher")),  # KCI 응답 typo 그대로
            "cited_DOI": text_of(ref.find("doi")),
        })

    return paper, authors_long, refs_long


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    papers = load_papers()
    arti_ids = papers["논문 ID"].dropna().unique().tolist()

    print(f"[parse] 캐시된 articleDetail × {len(arti_ids)} 파싱…")

    paper_rows = []
    author_rows = []
    ref_rows = []

    n_skip = 0
    for aid in arti_ids:
        cache_path = _cache_path("articleDetail", {"id": aid})
        if not cache_path.exists():
            n_skip += 1
            continue
        xml = cache_path.read_text(encoding="utf-8")
        try:
            p, alist, rlist = parse_one(aid, xml)
        except Exception as e:
            print(f"  ERR {aid}: {e!r}")
            continue
        if not p:
            n_skip += 1
            continue
        paper_rows.append(p)
        author_rows.extend(alist)
        ref_rows.extend(rlist)

    df_papers = pd.DataFrame(paper_rows)
    df_authors = pd.DataFrame(author_rows)
    df_refs = pd.DataFrame(ref_rows)

    out_paper = OUT_DIR / "kci_papers.parquet"
    out_author = OUT_DIR / "kci_authors.parquet"
    out_ref = OUT_DIR / "kci_references.parquet"

    df_papers.to_parquet(out_paper, index=False)
    df_authors.to_parquet(out_author, index=False)
    df_refs.to_parquet(out_ref, index=False)

    # CSV 미러 (작은 것만)
    df_papers.to_csv(out_paper.with_suffix(".csv"),
                     index=False, encoding="utf-8-sig")
    df_authors.to_csv(out_author.with_suffix(".csv"),
                      index=False, encoding="utf-8-sig")
    # references는 12k+ 행이라 CSV 미러 생략 (parquet만)

    print()
    print(f"✓ 파싱 완료 (skip {n_skip}건):")
    print(f"  kci_papers.parquet    : {len(df_papers):,} rows × {len(df_papers.columns)} cols")
    print(f"  kci_authors.parquet   : {len(df_authors):,} rows × {len(df_authors.columns)} cols")
    print(f"  kci_references.parquet: {len(df_refs):,} rows × {len(df_refs.columns)} cols")
    print()

    # ── 핵심 지표 요약 ────────────────────────────
    print("=== 논문 enrichment 지표 ===")
    print(f"  FWCI 보유: {df_papers['fwci'].notna().sum()}/{len(df_papers)} "
          f"({df_papers['fwci'].notna().sum()/len(df_papers):.1%})")
    print(f"  KCI citation-count 보유: {df_papers['kci_citation_count'].notna().sum()}")
    print(f"  영문 제목 보유: {(df_papers['title_english']!='').sum()}")
    print(f"  영문 초록 보유 (length>0): {(df_papers['abstract_english_len']>0).sum()}")
    print(f"  KCI verified=Y: {df_papers['kci_verified'].sum()}")
    print(f"  FWCI 분포 (있는 것만):")
    print(df_papers["fwci"].dropna().describe().to_string())
    print()

    print("=== 저자 enrichment 지표 ===")
    print(f"  영문 저자명 보유: {(df_authors['저자_영문']!='').sum()}/{len(df_authors)} "
          f"({(df_authors['저자_영문']!='').sum()/len(df_authors):.1%})")
    print(f"  저자 분담 분포: {df_authors['author_part'].value_counts().to_dict()}")
    print()

    print("=== 참조 enrichment 지표 (★ 핵심) ===")
    n_refs = len(df_refs)
    n_with_id = df_refs["cited_artiId"].notna().sum()
    print(f"  REFARTIID(cited_artiId) 보유: {n_with_id}/{n_refs} ({n_with_id/n_refs:.1%})")
    by_type = df_refs.groupby("유형")["cited_artiId"].apply(
        lambda s: f"{s.notna().sum()}/{len(s)}"
    )
    print(f"  유형별 REFARTIID 비율:")
    for t, v in by_type.items():
        print(f"    {t:18s} {v}")
    print()

    print("=== unique cited papers (그래프 노드 후보) ===")
    unique_cited = df_refs["cited_artiId"].dropna().nunique()
    print(f"  unique REFARTIID: {unique_cited}")

    # 자기인용: cited 학술지 = '인도철학'
    self_cited = df_refs[df_refs["cited_artiId"].notna() &
                          (df_refs["cited_학술지"].str.strip() == "인도철학")]
    print(f"  KCI-기반 자기인용 (cited_학술지='인도철학' & 등재논문): {len(self_cited)}건")


if __name__ == "__main__":
    main()
