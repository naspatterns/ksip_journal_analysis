# 데이터 무결성 검증 계획

`<인도철학>` 학술지 데이터셋이 원본을 정확히 반영하는지, 우리가 부착한 라벨이 일관되는지 **10개 레이어** 로 검증.

관련 문서:
- [`PIPELINE.md`](./PIPELINE.md) — 데이터 구축 과정
- [`DECISIONS.md`](./DECISIONS.md) — 결정 로그
- [`ISSUES.md`](./ISSUES.md) — 발견된 이슈 ticket 추적

---

## 0. 무결성의 4개 차원

| 차원 | 질문 | 깨질 때 증상 |
|---|---|---|
| **Source** (원본) | KCI 원본이 우리 손에 정확히 들어왔나 | xls 파일 결손, 인코딩 깨짐 |
| **Transform** (변환) | xls → parquet 에서 손실·왜곡이 없나 | row 수 불일치, 필드 누락, artiId 미추출 |
| **Annotation** (라벨링) | 우리가 부착한 canonical_id·메타필드가 일관되나 | duplicate surface, orphan canonical_id, enum 위반 |
| **Coverage** (포괄) | 데이터에 있는 것을 사전이 다 잡나 | 사전 누락, surface 변형 미등록, audit·exact-match gap |

---

## 1. 10개 검증 레이어

| L | 검증 항목 | 위험도 | 자동화 | 산출물 |
|---|---|---|---|---|
| L1 | Source 파일 존재·시트·행 수 | Low | 100% | `verify_01_source.csv` |
| L2 | xls → parquet 변환 round-trip + L3 (artiId) | High | 90% | `verify_02_transform_*.csv` |
| L4 | Cross-parquet 논문ID 무결성 | Medium | 100% | `verify_03_referential.csv` |
| L5 | 클리닝 단계 검증 (119 titles, 14 keywords, 297 동국대) | Medium | 100% | `verify_04_cleaning.csv` |
| L6 | Dictionary 내부 일관성 (4 yml, Authority Control) | **High** | 100% | `verify_05_dictionary.csv` |
| L7 | Coverage gap (substring audit vs exact-match resolve) | **High** | 100% | `verify_06_coverage_gap.csv` |
| L8 | Reference parsing (12,887건 × 7유형, 자기인용 312) | High | 80% | `verify_07_references_*.csv` |
| L9 | 기관 부모(rollup) 무결성 | Medium | 100% | `verify_08_institutions.csv` |
| L10 | KCI website spot-check (random 30편) | Medium | 90% | `verify_09_kci_spotcheck.csv` |

---

## 2. 우선순위 (Tier)

| Tier | 레이어 | 이유 |
|---|---|---|
| **Tier 1 — 즉시** | L4 / L6 / L7 | 분석 모든 단계가 의존. 깨져 있으면 Phase 4 라벨링 결과가 무의미 |
| **Tier 2 — Phase 4 전** | L2+L3 / L5 / L8 | 데이터 자체 신뢰성 — 결과 보고에 직접 영향 |
| **Tier 3 — 보고서 단계** | L1 / L9 / L10 | 모서리 케이스 — 발견되면 좋지만 막진 않음 |

---

## 3. 산출 폴더 구조

```
evaluation/
├── verification/                       검증 스크립트
│   ├── verify_01_source.py
│   ├── verify_02_transform.py
│   ├── verify_03_referential.py
│   ├── verify_04_cleaning.py
│   ├── verify_05_dictionary.py
│   ├── verify_06_coverage_gap.py
│   ├── verify_07_references.py
│   ├── verify_08_institutions.py
│   ├── verify_09_kci_spotcheck.py      (KCI API 필요)
│   └── verify_all.py                   마스터
├── output/verification/                산출물 CSV + 마스터 리포트
│   ├── verify_01_source.csv
│   ├── verify_02_transform_count.csv
│   ├── verify_02_transform_sample.csv
│   ├── verify_03_referential.csv
│   ├── verify_04_cleaning.csv
│   ├── verify_05_dictionary.csv
│   ├── verify_06_coverage_gap.csv
│   ├── verify_07_references_count.csv
│   ├── verify_07_references_sample.csv
│   ├── verify_08_institutions.csv
│   ├── verify_09_kci_spotcheck.csv
│   └── verify_summary.md               최종 종합
└── docs/
    └── ISSUES.md                       발견된 이슈 ticket
```

---

## 4. 데이터 위치

| 데이터 | 경로 |
|---|---|
| raw .xls | 메인 프로젝트 `/Users/.../ksip_journal_analysis/data/raw/` (워크트리에는 없음, .gitignore) |
| processed .parquet | 워크트리 `data/processed/` (git 포함) |
| dictionaries .yml | 워크트리 `data/dictionaries/` (git 포함) |

스크립트는 환경변수 또는 자동 탐지로 raw 경로를 찾는다 (`KSIP_RAW_DIR` 또는 `../../../data/raw`).

---

## 5. 이슈 처리 룰

발견된 불일치는 `evaluation/docs/ISSUES.md` 에 ticket 으로 기록:

| 분류 | 의미 | 처리 |
|---|---|---|
| FATAL | 분석을 막는 오류 (데이터 손실, 핵심 무결성 위반) | 즉시 수정 → 재실행 |
| WARN | 결과의 정확도에 영향 (커버리지 gap, surface 누락 등) | Phase 4 검수 환류로 자동 처리되는 것은 close, 아니면 ticket |
| INFO | 단순 통계 (참고용) | 무시 가능 |

---

## 6. 실행 명령

```bash
PY=.venv/bin/python    # 메인 프로젝트 루트의 venv. ENVIRONMENT.md 참조

# 개별
$PY evaluation/verification/verify_01_source.py
$PY evaluation/verification/verify_02_transform.py
# ... etc

# 마스터 (모두 실행 + 요약 생성)
$PY evaluation/verification/verify_all.py
```

산출물 = `evaluation/output/verification/verify_summary.md` + 9개 카테고리 CSV.

---

## 7. 결정 사항 (사용자 확정)

- **(a)** 9개 레이어 전부 수행
- **(b)** KCI spot-check 표본 = **30편**
- **(c)** 산출 위치 = `evaluation/verification/` + `evaluation/output/verification/`
- **(d)** 이슈 추적 = `evaluation/docs/ISSUES.md` (신설)
- **(e)** 본 계획 = `evaluation/docs/VERIFICATION_PLAN.md` (이 파일)
