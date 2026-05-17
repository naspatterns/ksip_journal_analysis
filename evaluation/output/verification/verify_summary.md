# 무결성 검증 결과 — 2026-05-18 00:01

관련 문서: [`VERIFICATION_PLAN.md`](../../docs/VERIFICATION_PLAN.md), [`ISSUES.md`](../../docs/ISSUES.md)

## 전체 판정: **WARN**

- FATAL: 0
- WARN: 6
- INFO: 28
- PASS: 59

## 레이어별

| L | 검증 항목 | 판정 | FATAL | WARN | INFO | PASS | CSV |
|---|---|---|---|---|---|---|---|
| L1 | Source 파일 · 시트 · 행수 | **PASS** | 0 | 0 | 7 | 4 | `verify_01_source.csv` |
| L2 | xls → parquet 변환 + artiId | **WARN** | 0 | 1 | 4 | 9 | `verify_02_transform.csv` |
| L4 | Cross-parquet 논문ID 무결성 | **PASS** | 0 | 0 | 2 | 8 | `verify_03_referential.csv` |
| L5 | 클리닝 (119/297/14) | **PASS** | 0 | 0 | 1 | 8 | `verify_04_cleaning.csv` |
| L6 | Dictionary 일관성 | **WARN** | 0 | 4 | 2 | 23 | `verify_05_dictionary.csv` |
| L7 | Coverage gap (substring vs exact) | **WARN** | 0 | 1 | 4 | 1 | `verify_06_coverage_gap.csv` |
| L8 | Reference 파싱 (7유형, 자기인용) | **PASS** | 0 | 0 | 5 | 4 | `verify_07_references.csv` |
| L9 | 기관 부모(rollup) | **PASS** | 0 | 0 | 3 | 2 | `verify_08_institutions.csv` |
| L10 | KCI API spot-check 30편 | **PASS** | 0 | 0 | 0 | 0 | `verify_09_kci_spotcheck.csv` |

## 발견 이슈 (FATAL + WARN)

- **[WARN]** L2 `pua_in_초록` — papers.초록 에 PUA 문자 잔존 2건
- **[WARN]** L6 `concepts_intra_surface_dup` — concepts.yml: entry 내 surface_forms 중복 5건
- **[WARN]** L6 `concepts_inter_surface_dup` — concepts.yml: 여러 entry 가 공유하는 surface 5건 — normalize.py 는 last-wins. 예: [('dharmakirti', ['dharmakirti', 'dharmakirti']), ('dignaga', ['dignaga', 'dignaga']), ('나가르주나', ['nagarjuna', 'nagarjuna'])]
- **[WARN]** L6 `journals_intra_surface_dup` — journals.yml: entry 내 surface_forms 중복 2건
- **[WARN]** L6 `journals_inter_surface_dup` — journals.yml: 여러 entry 가 공유하는 surface 3건 — normalize.py 는 last-wins. 예: [('印度學佛敎學硏究', ['jibs_japan', 'jibs_japan']), ('佛敎學硏究', ['bukkyogaku_kenkyu', 'buddhist_studies_research']), ('annual report of the international research institute for advanced buddhology', ['arir_iab', 'arir_iab'])]
- **[WARN]** L7 `substring_exact_gap` — substring > exact gap 큰 entry TOP 30 → verify_06_coverage_gap_substring_vs_exact.csv. surface_forms 확장 필요. 예: [('yoga', 56), ('vijnanavada', 29), ('prajna', 19)]

## 산출 CSV (영향분 detail)

- `verify_01_source.csv`
- `verify_02_transform.csv`
- `verify_03_referential.csv`
- `verify_04_cleaning.csv`
- `verify_05_dictionary.csv`
- `verify_06_coverage_gap.csv`
- `verify_06_coverage_gap_dead_surfaces.csv`
- `verify_06_coverage_gap_substring_vs_exact.csv`
- `verify_06_coverage_gap_unresolved.csv`
- `verify_07_references.csv`
- `verify_07_references_sample.csv`
- `verify_08_institutions.csv`
- `verify_08_institutions_by_parent.csv`
- `verify_09_kci_spotcheck.csv`
- `verify_09_kci_spotcheck_results.csv`

## 권장 후속

- 위 FATAL/WARN 항목을 `evaluation/docs/ISSUES.md` 에 ticket 으로 등재
- FATAL 은 즉시 수정 → 해당 verifier 재실행
- WARN 은 Phase 4 검수 환류 또는 별도 해소
