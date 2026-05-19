# 데이터 구축 파이프라인 (PIPELINE)

`<인도철학>` 학술지 평가 프로젝트(`evaluation/`) 의 **데이터 구축 과정** 을 단계별로
기술. 누구라도 이 문서만 보고 같은 결과를 재현할 수 있는 것을 목표로 함.

관련 문서:
- [`../README.md`](../README.md) — 서브프로젝트 입구
- [`../taxonomy/SCHEMA.md`](../taxonomy/SCHEMA.md) — 분류 체계 정의 (값 목록·결정 룰)
- [`./DECISIONS.md`](./DECISIONS.md) — 결정 로그 (시간순)
- [`./KEYWORD_AUDIT.md`](./KEYWORD_AUDIT.md) — 키워드 빈도 감사 결과 (사전 추가 의사결정 근거)

---

## 1. 프로젝트 컨텍스트

| 항목 | 값 |
|---|---|
| 분석 대상 | `<인도철학>` 학술지 1989–2025, **636편** |
| 데이터 원천 | KCI 다운로드 .xls 3개 + .csv 통합본 (이미 parquet 화) |
| 평가 축 | 8개 — 현 단계는 축 1 (커버리지) + 축 6 (학제 경계) |
| 분리 정책 | 기존 대시보드(`app.py`, `pages/1, 2`) 와 별도 프로젝트 (`evaluation/`) |

축 1·6 의 핵심 측정 정의:

- **축 1 — 커버리지**: 학파/시대/주제의 분포 (Shannon entropy 주, Gini·HHI 부)
- **축 6 — 학제 경계**: 논문의 `reception_horizon == "india"` 비율

축 1+6 은 KCI Open API 가 **거의 필요 없음** (기존 parquet 만으로 가능).

---

## 2. 데이터 입력 (이전 단계의 산출물)

`data/processed/` 의 4개 parquet (기존 `scripts/build_data.py` 가 생성):

| 파일 | 행 수 | 핵심 컬럼 |
|---|---|---|
| `papers.parquet` | 636 | 논문ID, 논문명, 저자키워드, 초록, 발행연도, 기관_부모 등 (29) |
| `keywords.parquet` | 3,089 | 논문ID, 발행연도, 키워드_원본, canonical_id (4) |
| `authors.parquet` | 654 | 저자명, 소속, canonical_id 등 |
| `references.parquet` | 12,887 | 인용 정보 7유형 슬래시 파싱 결과 |

본 프로젝트는 `papers` + `keywords` 두 개만 사용 (축 1·6 기준).

---

## 3. 단계별 작업 — 무엇을 했나

### Phase 0. 분류 체계 설계 (완료)

8개 평가 축을 사용자와 합의 → 축 1·6 부터 진행 결정.
17개 세부 결정(A1-A5, B1-B3, C1-C3, D1-D3, E1-E2)에 대해 옵션 검토 → 사용자 확정.

산출: [`../taxonomy/SCHEMA.md`](../taxonomy/SCHEMA.md)

**핵심 설계 결정** (전체 로그는 `DECISIONS.md`):

- **분류 4축**: `school` / `era` / `source_language` / `reception_horizon`
- **2축 라벨** (A2): `source_language` 와 `reception_horizon` 직교 — 한역 자료(`source=chinese`) 라도 사상이 인도면 `reception=india` → **인도철학**
- **다중 라벨** (A5): 주 1 + 부 N
- **요가 학파 era 필수**: classical / post_classical / modern 분리
- **chan 3국 통합**: 중·한·일 선종은 `school=chan`, 지역은 `reception_horizon` 으로
- **nyaya / vaisheshika / pramana 별도** (vedanta 단일)
- **meta 옵션 C** (학술사·서평): primary_school + meta 의 이중 라벨

### Phase 1. 사전 스키마 확장 (완료)

기존 `data/dictionaries/concepts.yml` (69 entry) 에 4개 메타필드 추가:

```yaml
- canonical_id: dharmakirti
  type: 학자
  # ── 신규 ──
  school: pramana
  era: post_classical              # 분류 bucket
  source_language: sanskrit
  reception_horizon: india
  century: 7세기                   # ← 옛 free-form `era` 이리로 rename
  surface_forms: [...]
```

**충돌 해소**: 기존 free-form `era: "7세기"` 와 신규 bucket `era: "classical"` 의
키 충돌을 막기 위해 옛 12개 entry 의 `era` 를 `century` 로 rename.

**스크립트**: [`../labeling/backfill_concepts_metadata.py`](../labeling/backfill_concepts_metadata.py)
- ruamel.yaml 기반 → 주석·섹션 구분·키 순서 보존
- 멱등 (재실행해도 안정) — `--dry-run` 으로 미리 통계만 확인 가능

**실행**:
```bash
.venv/bin/python evaluation/labeling/backfill_concepts_metadata.py
```

**결과 분포** (사전 자체의 분포 — 학술지 데이터 분포 아님):

| 변수 | 분포 |
|---|---|
| `school` | yogacara 16 / madhyamaka 14 / vedanta 9 / pramana 7 / abhidharma 6 / yoga 4 / comparative 3 / samkhya 2 / vedic 2 / 나머지 6종 각 1 |
| `era` | classical 44 / post_classical 10 / upanishadic_sutra 7 / transversal 6 / modern 1 / vedic 1 |
| `source_language` | sanskrit 61 / pali 3 / chinese 2 / 나머지 3종 각 1 |
| `reception_horizon` | india 68 / korea 1 (원효) |

→ 사전이 **인도 본토 + 산스크리트 + 고전기 + 유식·중관 중심**.
동아시아·티베트·한국 entry 가 부족 → Phase 2 보강 대상.

### Phase 2. 키워드 등장 빈도 감사 (완료)

**원칙** (사용자 결정): 사전 entry 는 *실제 데이터에 등장하는* 것만 추가.
등장하지 않는 후보(예: 일본 불교 인물 親鸞·道元) 는 추가하지 않음.

**스크립트**: [`../labeling/audit_keyword_coverage.py`](../labeling/audit_keyword_coverage.py)
- 후보 ~85개 (학파·인물·텍스트·자료) × (한글/한자/IAST/영문 변형)
- `keywords.parquet` + `papers.논문명` 에서 substring 매칭
- 산출: `evaluation/output/keyword_audit.csv`

**실행**:
```bash
.venv/bin/python evaluation/labeling/audit_keyword_coverage.py
```

**주요 발견** (상세는 [`KEYWORD_AUDIT.md`](./KEYWORD_AUDIT.md)):

| 발견 | 의미 |
|---|---|
| 일본 불교 인물 0건 (親鸞·道元·空海) | 인도철학 학술지가 일본 불교를 거의 안 다룸 — 그 자체가 결과 |
| 중국 화엄/천태/정토 *인물* 거의 없음 (法藏·智儼·慧能·善導 모두 0) | 학파 일반어 (화엄·정토) 는 있어도 인물 단위 연구는 부재 |
| 한국 인물 = 원효 압도 (10건), 의상·지눌·휴정 등 0건 | "한국 불교" 부분은 사실상 원효-전용 |
| 티베트 = 쫑카파 (8건) + 까말라쉴라 (2건) 만 | 빠드마삼바와·미팜·사꺄빤디타·일본 진언 모두 부재 |
| 인도 6파 중 **미맘사** 등장 (3건) | 사전 누락 — 추가 필요 |

→ **신규 entry 추가 후보 ~46개 → ~24개로 축소.**

### Phase 3. 신규 사전 entry 추가 (완료)

Phase 2 에서 골라낸 27개 신규 entry 일괄 추가. Q1c·Q2c·Q3 contextual 룰 적용.

**스크립트**: [`../labeling/add_phase3_entries.py`](../labeling/add_phase3_entries.py) — 멱등.

**카테고리별**:
- 학파 6: `mimamsa` / `huayan` / `chan` / `pure_land` / `esoteric_east_asia` / `tibetan_buddhism_general`
- 인물 8: `kamalasila` / `zhiyi` / `kuiji` / **`kumarajiva` (Q1c)** / `jizang` / `wonchuk` / `iryeon` / `tsongkhapa`
- 텍스트 6: **`awakening_of_faith` (Q2c)** / **`avatamsaka` (Q3 contextual)** / **`lotus_sutra` (Q3 contextual)** / `larger_sukhavativyuha` / `smaller_sukhavativyuha` / `contemplation_sutra`
- 근대 인도 3: `ramakrishna` / `vivekananda` / `radhakrishnan`
- 메타 4: `hatha_yoga` / `chinese_buddhist_canon` / `tibetan_canon` / `dunhuang`

**사용자 결정 3건 적용**:
- **Q1c (구마라집)**: `school=madhyamaka, reception=east_asia`
- **Q2c (기신론)**: `school=east_asian_other, reception=east_asia`
- **Q3 (법화경·화엄경)**: `school=contextual, reception=contextual` — Phase 4 라벨링 파이프라인이 공출현 키워드 룰로 결정

**부수 결정**: `esoteric_east_asia` school 값 신설 (한국 5자 진언 등 비-일본 동아시아 밀교, `shingon` 과 분리).

**결과**:

| | 기존 | Phase 3 후 |
|---|---|---|
| concepts.yml entry | 69 | **96** |
| verified=True | 67 | **94** |
| keywords.parquet resolve 율 | 12.4% | **14.3%** (+59 rows) |

→ 상세는 [`DECISIONS.md`](./DECISIONS.md) Decision-12, Decision-17 참조.

### Phase 4 이후 (계획)

| Phase | 내용 | 산출 |
|---|---|---|
| 4. 라벨링 파이프라인 | 사전 1차 매칭 → BERTopic 보조 → 논문 단위 라벨 집계 (다수결·가중) → 모호 텍스트 contextual disambiguation 룰 적용 | `evaluation/labeling/pipeline.py`, `output/paper_labels.parquet` |
| 5. 검수 표본 | 무작위 50 + 자동 라벨 신뢰도 하위 50 = 100편 추출. CSV 로 export → 수동 검수 → 사전 환류 | `evaluation/labeling/review_sample.py`, `output/review_sample.csv` |
| 6. 시각화 | Streamlit 페이지 2개: 커버리지 (학파 × 시기 streamgraph + entropy 시계열) + 학제경계 (reception 비율 시계열 + 불교/비불교 break) | `evaluation/pages/1_커버리지.py`, `2_학제경계.py` |
| 7. 결과 보고 | 80% 정확도에서 1차 결과 → 시간 남으면 검수 환류 후 재실행 | (보고서) |

---

## 4. 재현 절차 — 0 에서 현재까지

```bash
# 0. 환경 확인 (venv 는 메인 프로젝트의 것 사용)
PY=.venv/bin/python                    # 또는 sys.executable 의 path. 자세한건 ENVIRONMENT.md
$PY --version                          # Python 3.14.x
$PY -m pip install ruamel.yaml         # backfill 스크립트 의존

# 1. 원본 parquet 가 존재한다는 가정
ls data/processed/papers.parquet data/processed/keywords.parquet

# 2. 사전 메타필드 backfill (Phase 1 재실행)
$PY evaluation/labeling/backfill_concepts_metadata.py --dry-run    # 미리 확인
$PY evaluation/labeling/backfill_concepts_metadata.py              # 실 저장

# 3. 키워드 등장 감사 (Phase 2 재실행)
$PY evaluation/labeling/audit_keyword_coverage.py
ls evaluation/output/keyword_audit.csv

# 4. Phase 3 신규 entry 일괄 추가 (멱등)
$PY evaluation/labeling/add_phase3_entries.py --dry-run    # 미리 확인
$PY evaluation/labeling/add_phase3_entries.py              # 실 저장 (27 entries)

# 5. (미구현) Phase 4 라벨링
# $PY evaluation/labeling/pipeline.py

# 6. (미구현) Phase 6 Streamlit
# $PY -m streamlit run evaluation/app.py
```

---

## 5. 디렉토리 매핑 — 무엇이 어디에 있나

```
evaluation/
├── README.md                           프로젝트 입구 (요약 + 8축 표 + 폴더 구조)
├── app.py                              (스캐폴드) Streamlit 진입점
├── docs/
│   ├── PIPELINE.md                     ← 이 문서. 데이터 구축 과정 전체
│   ├── DECISIONS.md                    결정 로그 (시간순)
│   └── KEYWORD_AUDIT.md                키워드 감사 결과 분석
├── taxonomy/
│   └── SCHEMA.md                       분류 4축 값 목록·결정 룰
├── labeling/
│   ├── backfill_concepts_metadata.py   Phase 1 — 사전 메타필드 backfill (멱등)
│   ├── audit_keyword_coverage.py       Phase 2 — 키워드 등장 빈도 감사
│   ├── add_phase3_entries.py           Phase 3 — 신규 27 entry 일괄 추가 (멱등)
│   └── (pipeline.py — 미구현)          Phase 4 — 라벨링 파이프라인
├── pages/
│   ├── 1_커버리지.py                   (스캐폴드) 축 1 시각화
│   └── 2_학제경계.py                   (스캐폴드) 축 6 시각화
└── output/
    ├── keyword_audit.csv               Phase 2 산출물
    └── (paper_labels.parquet — Phase 4 산출 예정)

data/dictionaries/concepts.yml          ← Phase 1 에서 확장됨 (69 entry, 신규 4필드)
```

---

## 6. 핵심 운영 규칙 (재선언)

- **인접 학술지 비교** (축 4 단계) 는 사용자에게 *반드시* 사전 문의. 자의적 선정 금지.
- 라벨링 정확도 목표 = 80% → 시각화 → 시간 남으면 검수 재반복.
- 검수 표본 100편 = 무작위 50 + 신뢰도 하위 50.
- 모호 텍스트 (Q3) 의 학파 결정 = **공출현 키워드 기반 contextual rule**. Phase 4 에서 구현. 사전에는 강한 단정 회피.
- Surface form 은 절대 덮어쓰지 않음. canonical_id 만 추가 (`ksip/normalize.py` 의 기존 원칙).
- `verified=false` 항목은 분석에 자동 사용 안 됨 (`include_unverified=True` 명시 필요).
