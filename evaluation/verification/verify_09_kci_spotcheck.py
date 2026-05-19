"""L10 — KCI Open API 로 무작위 30편을 원본 검증.

확인:
- 무작위 30편의 artiId 를 KCI articleSearch 로 조회
- 응답 vs parquet 의 (논문명·발행연도·저자명) 비교
- 불일치 row 만 별도 CSV 로 export → 수동 검수

API:
    https://open.kci.go.kr/po/openapi/openApiSearch.kci
      ?apiCode=articleSearch&key={KEY}&id={artiId}

API 키:
    1) 환경변수 KSIP_KCI_API_KEY
    2) 메인 프로젝트 루트의 'KCI_OpenAPI_Key 2.txt' (또는 'KCI_OpenAPI_Key 3.txt')

응답이 XML 또는 JSON 일 수 있어 robust 파싱.
"""
from __future__ import annotations

import os
import random
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

from _common import PAPERS_PARQUET, CheckRun, ensure_output_dir, find_kci_key_file

SAMPLE_N = 30
RANDOM_SEED = 42
API_URL = "https://open.kci.go.kr/po/openapi/openApiSearch.kci"
RATE_LIMIT_SEC = 1.0


def load_api_key() -> str | None:
    """KCI API key 로드. 멀티 컴퓨터 portable.

    탐지 우선순위:
    1. 환경변수 KSIP_KCI_API_KEY (값 자체)
    2. 환경변수 KSIP_KCI_KEY_FILE 이 가리키는 파일
    3. 메인 프로젝트 루트의 KCI_OpenAPI_Key*.txt (_common.find_kci_key_file)

    파일 형식: 'KCI OpenAPI Key: 12345678' (라벨 포함) 또는 그냥 키 — 모두 처리.
    """
    import re
    raw = os.environ.get("KSIP_KCI_API_KEY")
    if not raw:
        key_file = find_kci_key_file()
        if key_file and key_file.exists():
            raw = key_file.read_text(encoding="utf-8")
    if not raw:
        return None
    raw = raw.strip()
    # KCI 키는 영숫자 토큰 — "KCI OpenAPI Key" 같은 라벨 단어 제거
    # 1) "KCI OpenAPI Key" 라벨 명시적 제거 (대소문자·공백 무관)
    raw = re.sub(r"KCI\s*OpenAPI\s*Key", "", raw, flags=re.IGNORECASE)
    # 2) 콜론 분리도 처리
    if ":" in raw:
        raw = raw.split(":", 1)[1]
    # 3) 공백·따옴표·newline 제거 → 토큰만
    return re.sub(r"\s+", "", raw).strip("'\"")


def fetch_article(api_key: str, arti_id: str) -> dict | None:
    """KCI articleSearch 호출 → 파싱한 dict 반환. 실패 시 None."""
    params = {"apiCode": "articleSearch", "key": api_key, "id": arti_id}
    try:
        r = requests.get(API_URL, params=params, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return {"_error": str(e)}

    text = r.text
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {"_error": "XML parse failed", "_raw": text[:400]}

    fields: dict[str, str] = {}

    # 제목: article-title @lang="original" (한글)
    for el in root.iter("article-title"):
        if el.get("lang") == "original" and el.text:
            fields["article_title_kor"] = el.text.strip()
            break

    # 저자: author 태그 다수, "최현성(동국대학교)" 형식
    authors = []
    for el in root.iter("author"):
        if el.text:
            # 괄호 안 소속 분리
            name = el.text.split("(")[0].strip()
            if name:
                authors.append(name)
    if authors:
        fields["authors_list"] = ";".join(authors)

    # 발행연도
    for el in root.iter("pub-year"):
        if el.text:
            fields["pub_year"] = el.text.strip()
            break

    # 학술지명 (자기 인용 검증용 — 모두 "인도철학" 이어야)
    for el in root.iter("journal-name"):
        if el.text:
            fields["journal_name"] = el.text.strip()
            break

    # 에러 메시지
    for el in root.iter("resultMsg"):
        if el.text:
            fields["_api_msg"] = el.text.strip()

    return fields


def normalize_text(s: str) -> str:
    """공백/특수문자 차이 무시 비교."""
    import re
    import unicodedata
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", "", s)
    return s.lower()


def main() -> int:
    run = CheckRun("L10")
    out_dir = ensure_output_dir()

    api_key = load_api_key()
    if not api_key:
        run.warn("api_key_missing",
                 "KCI API key 를 못 찾음 — L10 skip. "
                 "KSIP_KCI_API_KEY 환경변수 또는 KCI_OpenAPI_Key*.txt 파일 필요")
        run.print_summary()
        run.to_csv(out_dir / "verify_09_kci_spotcheck.csv")
        return 0
    run.info("api_key_loaded", f"API key loaded (length {len(api_key)})")

    papers = pd.read_parquet(PAPERS_PARQUET)
    paper_id_col = "논문 ID" if "논문 ID" in papers.columns else "논문ID"

    # 무작위 30편 sample (재현 가능)
    rng = random.Random(RANDOM_SEED)
    arti_ids = papers[paper_id_col].dropna().astype(str).tolist()
    sample_ids = rng.sample(arti_ids, min(SAMPLE_N, len(arti_ids)))
    run.info("sample_drawn",
             f"무작위 {len(sample_ids)}편 추출 (seed={RANDOM_SEED})",
             n_affected=len(sample_ids))

    # 호출 + 비교
    rows = []
    n_success = n_error = n_match = n_mismatch_any = 0
    field_mismatches = {"논문명": 0, "발행연도": 0, "저자명": 0}

    print(f"\nKCI API 30회 호출 (rate {RATE_LIMIT_SEC}s)...")
    for i, aid in enumerate(sample_ids, 1):
        sys.stdout.write(f"\r  [{i:2d}/{len(sample_ids)}] {aid}")
        sys.stdout.flush()
        resp = fetch_article(api_key, aid)
        time.sleep(RATE_LIMIT_SEC)

        pq_row = papers[papers[paper_id_col] == aid].iloc[0]
        row = {
            "artiId": aid,
            "parquet_title": str(pq_row.get("논문명", "")),
            "parquet_year": str(pq_row.get("발행연도", "")),
            "parquet_author": str(pq_row.get("저자명", "")),
        }

        if not resp or "_error" in (resp or {}):
            row["api_status"] = "ERROR"
            row["api_detail"] = (resp or {}).get("_error", "no response")
            n_error += 1
            rows.append(row)
            continue
        n_success += 1

        api_title = resp.get("article_title_kor", "")
        api_year = resp.get("pub_year", "")
        api_author = resp.get("authors_list", "")
        api_journal = resp.get("journal_name", "")
        row["api_journal"] = api_journal

        row["api_title"] = api_title
        row["api_year"] = api_year
        row["api_author"] = api_author

        # 비교 (정규화 후) — cleaned title vs raw title 양쪽 시도
        # KCI API 는 원본 (trailing underscore 등 포함), parquet 는 clean_title 적용됐을 수 있음
        parquet_origin = str(pq_row.get("논문명_원본", "") or "")
        row["parquet_title_origin"] = parquet_origin
        t_match_cleaned = normalize_text(row["parquet_title"]) == normalize_text(api_title)
        t_match_origin = normalize_text(parquet_origin) == normalize_text(api_title) if parquet_origin else False
        t_match = t_match_cleaned or t_match_origin
        row["title_match_cleaned"] = t_match_cleaned
        row["title_match_origin"] = t_match_origin
        y_match = (str(row["parquet_year"]).strip() == str(api_year).strip()
                   or not api_year)  # 연도 없으면 skip
        # 저자명: parquet 은 multi-author 일 수 있음. parquet 첫 저자가 api 응답에 포함되면 OK
        first_pq_author = row["parquet_author"].split(",")[0].split(";")[0].strip()
        a_match = (normalize_text(first_pq_author) in normalize_text(api_author)
                   or not api_author)

        row["title_match"] = t_match
        row["year_match"] = y_match
        row["author_match"] = a_match
        row["all_match"] = t_match and y_match and a_match
        if row["all_match"]:
            n_match += 1
        else:
            n_mismatch_any += 1
            if not t_match: field_mismatches["논문명"] += 1
            if not y_match: field_mismatches["발행연도"] += 1
            if not a_match: field_mismatches["저자명"] += 1

        rows.append(row)
    print()  # newline after progress

    # 결과 저장
    df = pd.DataFrame(rows)
    path = out_dir / "verify_09_kci_spotcheck.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    run.info("results_saved", f"30편 비교 결과 → {path.name}",
             n_affected=len(df))

    # 요약
    run.info("api_success",
             f"API 호출: 성공 {n_success} / 실패 {n_error}",
             n_affected=n_success)
    if n_error >= len(sample_ids) // 3:
        run.warn("api_error_high",
                 f"API 호출 실패 {n_error}건 — 키 또는 네트워크 점검",
                 n_affected=n_error)

    if n_success > 0:
        # 모든 응답이 비어있으면 (API 응답 파싱 실패)
        empty_response = sum(1 for r in rows if r.get("api_title", "") == "" and r.get("api_status") != "ERROR")
        if empty_response >= n_success:
            run.warn("empty_responses",
                     f"성공 응답 {n_success}건 모두 title 필드 추출 실패 — "
                     "응답 스키마 확인 필요. raw 응답 sample 을 verify_09_kci_raw.json 으로 검토",
                     n_affected=empty_response)
            # 첫 응답을 raw 로 저장
            first_aid = rows[0]["artiId"]
            params = {"apiCode": "articleSearch", "key": api_key, "id": first_aid}
            try:
                r = requests.get(API_URL, params=params, timeout=15)
                (out_dir / "verify_09_kci_raw.xml").write_text(r.text, encoding="utf-8")
                run.info("raw_response_saved",
                         f"첫 응답 → verify_09_kci_raw.xml ({len(r.text)} bytes)")
            except Exception as e:
                run.info("raw_response_save_fail", f"raw 저장 실패: {e}")
        else:
            run.info("field_match_count",
                     f"30편 중 전 필드 일치 {n_match}, 차이 있음 {n_mismatch_any} "
                     f"(field 별: {field_mismatches})",
                     n_affected=n_mismatch_any)
            if n_mismatch_any > n_success // 5:  # 20% 초과
                run.warn("field_mismatch_high",
                         f"필드 불일치 {n_mismatch_any}건 / 성공 {n_success}건 — 검수 필요")
            elif n_mismatch_any > 0:
                run.info("field_mismatch_low",
                         f"필드 불일치 {n_mismatch_any}건 — 정규화 차이 가능, sample CSV 확인")
            else:
                run.pass_("field_match_all",
                          f"30편 모두 모든 필드 일치")

    run.print_summary()
    run.to_csv(out_dir / "verify_09_kci_spotcheck_results.csv")
    return 1 if run.counts()["FATAL"] else 0


if __name__ == "__main__":
    sys.exit(main())
