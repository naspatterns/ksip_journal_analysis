# 「인도철학」 학술지 평가 프로젝트

기존 대시보드(루트 `app.py` + `pages/1, 2`) 와 분리된 별도 Streamlit 앱.
학술지 「인도철학」(1989–2025, 636편) 을 통합 평가·진단하는 워크벤치.

## 1. 평가의 8축

| 축 | 질문 | 단계 |
|---|---|---|
| 1. 커버리지 | 인도철학 전 분야를 고루 다루는가 | **현재** |
| 2. 의존도 | 인용된 연구의 권역·학파 분포 | 다음 |
| 3. 대표성 | 학자들이 한국 인도철학을 대표하는가 | 후속 |
| 4. 주도성 | 한국 학계 인도철학을 주도하는가 | 후속 (인접 학술지 필요) |
| 5. 시간 진화 | 36년간 어떻게 변했는가 | 종합 |
| 6. 학제 경계 | 인도철학 vs 불교학 vs 동아시아·티베트 | **현재** |
| 7. 국제 좌표 | 국내 매체인가 국제 발신구인가 | 후속 |
| 8. 거버넌스 | 닫힌 클럽인가 광장인가 | 후속 |

축 1+6 은 KCI API 없이 기존 parquet 만으로 가능.

## 2. 문서 — 어디부터 읽나

| 문서 | 역할 |
|---|---|
| 본 파일 (README) | 입구 — 폴더 구조 + 실행 명령 + 현황 |
| [`docs/PIPELINE.md`](docs/PIPELINE.md) | 데이터 구축 과정 전체 — 재현 절차 포함 |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | 결정 로그 (시간순, append-only) |
| [`docs/KEYWORD_AUDIT.md`](docs/KEYWORD_AUDIT.md) | 키워드 등장 빈도 감사 결과 분석 |
| [`taxonomy/SCHEMA.md`](taxonomy/SCHEMA.md) | 분류 4축 값 목록·결정 룰 |

**새로 들어오는 사람** → `PIPELINE.md` 먼저, 그 다음 `SCHEMA.md`.
**결정 이유가 궁금하면** → `DECISIONS.md`.
**데이터 자체에 대해서** → `KEYWORD_AUDIT.md`.

## 3. 폴더 구조

```
evaluation/
├── README.md                           이 파일
├── app.py                              (스캐폴드) Streamlit 진입점
├── docs/
│   ├── PIPELINE.md                     데이터 구축 과정 + 재현 절차
│   ├── DECISIONS.md                    결정 로그
│   └── KEYWORD_AUDIT.md                키워드 감사 결과
├── taxonomy/
│   └── SCHEMA.md                       분류 4축 정의
├── labeling/
│   ├── backfill_concepts_metadata.py   Phase 1 — 사전 메타필드 backfill (멱등)
│   ├── audit_keyword_coverage.py       Phase 2 — 키워드 등장 빈도 감사
│   ├── add_phase3_entries.py           Phase 3 — 신규 27 entry 일괄 추가 (멱등)
│   └── (pipeline.py — 미구현)          Phase 4 — 라벨링 파이프라인
├── pages/
│   ├── 1_커버리지.py                   (스캐폴드) 축 1
│   └── 2_학제경계.py                   (스캐폴드) 축 6
└── output/
    ├── keyword_audit.csv               Phase 2 산출물
    └── (paper_labels.parquet)          Phase 4 산출 예정
```

## 4. 실행

```bash
PY=/Users/jibak/Documents/@CLASSES/2026-1/DigitalHumanities/ksip_journal_analysis/.venv/bin/python

# 사전 메타필드 backfill (멱등)
$PY evaluation/labeling/backfill_concepts_metadata.py

# 키워드 등장 빈도 감사 → CSV
$PY evaluation/labeling/audit_keyword_coverage.py

# Phase 3 신규 27 entry 일괄 추가 (멱등)
$PY evaluation/labeling/add_phase3_entries.py

# (미구현) 라벨링 파이프라인
# $PY evaluation/labeling/pipeline.py

# (미구현) Streamlit 평가 대시보드
# $PY -m streamlit run evaluation/app.py
```

## 5. 분류 체계 요약

논문 1편당 다중 라벨 (주 1 + 부 N):

| 변수 | 값 예시 | 의미 |
|---|---|---|
| `primary_school` | yogacara / madhyamaka / vedanta / huayan / chan / gelug … | 다루는 사상 |
| `era` | vedic / upanishadic_sutra / classical / post_classical / late / modern / transversal | 사상 시대 |
| `source_language` | sanskrit / pali / chinese / tibetan / modern_korean / mixed | 자료 언어 |
| `reception_horizon` | india / east_asia / tibet / korea / west / mixed | 사상이 다뤄진 지평 |

축 6 (학제 경계) 측정: **`reception_horizon == india`** 비율 = "인도철학 비중".

전체 값 목록·결정 룰: [`taxonomy/SCHEMA.md`](taxonomy/SCHEMA.md)

## 6. 운영 규칙

- **인접 학술지 비교** (축 4) 는 사용자에게 *반드시* 사전 문의. 자의적 선정 금지.
- 라벨링 정확도 목표 = **80%** → 시각화 → 시간 남으면 검수 재반복.
- 검수 표본 = 100편 (무작위 50 + 신뢰도 하위 50).
- 모호 텍스트(법화경류) 의 학파 = **공출현 키워드 기반 contextual rule** (사전 단정 회피, Phase 4 에서 처리).
- Surface form 절대 덮어쓰지 않음. canonical_id 만 추가.
- `verified=false` 항목은 분석에 자동 사용 안 됨.

## 7. 현황 (작업 진행 단계)

| Phase | 상태 |
|---|---|
| 0. 분류 체계 설계 (8축 합의 + 17개 세부 결정) | ✅ |
| 1. 사전 스키마 확장 + 69 entry backfill | ✅ |
| 2. 키워드 등장 빈도 감사 | ✅ |
| 3. 신규 27 entry 추가 (Q1c·Q2c 적용, Q3 contextual) — 커버리지 12.4% → 14.3% | ✅ |
| 4. 라벨링 파이프라인 | 🚫 |
| 5. 검수 표본 추출 | 🚫 |
| 6. Streamlit 시각화 페이지 | 🚫 |
| 7. 결과 보고 | 🚫 |
