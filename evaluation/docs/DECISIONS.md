# 결정 로그 (DECISIONS)

평가 프로젝트의 모든 설계·구현 결정. **새 결정은 끝에 append** — 시간순 보존.
각 결정은: 컨텍스트 / 옵션 / 사용자 확정 / 이유 / 영향 범위.

관련 문서: [`PIPELINE.md`](./PIPELINE.md), [`../taxonomy/SCHEMA.md`](../taxonomy/SCHEMA.md)

---

## Decision-01 — 평가 프로젝트의 8축 합의

**컨텍스트**: `<인도철학>` 학술지를 통합 평가. 사용자 제시 4축 + Claude 보강 4축.

**옵션**: 4축 / 8축 / 더 적게.

**확정**: **8축** — (1) 커버리지 (2) 의존도 (3) 대표성 (4) 주도성 (5) 시간 진화 (6) 학제 경계 (7) 국제 좌표 (8) 거버넌스.

**현 단계**: 축 1 + 축 6 부터 (KCI API 없이 기존 데이터로 가능).

---

## Decision-02 — 별도 프로젝트 폴더 (옵션 α)

**컨텍스트**: 기존 대시보드와 분리 진행. 별도 폴더 vs 별도 repo.

**옵션**:
- (α) 같은 repo + `evaluation/` 신규 폴더 + 별도 entry point
- (β) 별도 repo

**확정**: **옵션 α**. 데이터·`ksip/` 패키지 공유 이점.

**영향**: `evaluation/app.py` 가 별도 streamlit 진입점. `ksip/`·`data/` 공유.

---

## Decision-03 — 분류 체계 4축 (school × era × source_language × reception_horizon)

**컨텍스트**: A2 에서 자료(언어) 와 사상(학파) 의 직교성 식별.

**확정**:

| 변수 | 역할 |
|---|---|
| `school` (primary_school) | 사상 학파 |
| `era` | 시대 bucket (`vedic` / `upanishadic_sutra` / `classical` / `post_classical` / `late` / `modern` / `transversal`) |
| `source_language` | 1차 자료 언어 |
| `reception_horizon` | 사상이 다뤄진 지평 (축 6 의 핵심 변수) |

**핵심 룰**: 한역·티베트역 자료라도 사상 *원천* 이 인도면 `reception_horizon: india`.
**축 6 측정**: `reception_horizon == "india"` 비율 = "인도철학 비중".

---

## Decision-04 — 학파 입자 (옵션 2, 13~15개)

**옵션**:
- 1 (9개, 얕음) / 2 (13~15개, 중간) / 3 (25개+, 깊음)

**확정**: **옵션 2**. 데이터 636편을 25개로 쪼개면 cell 당 평균 25편 → sparse.

**리스트**: [`SCHEMA.md` §2](../taxonomy/SCHEMA.md) 참조.

---

## Decision-05 — 동아시아·티베트 처리 (2축 라벨)

**확정**:
- 한역·티베트역 자료로 인도 사상 연구 = `school=<인도 학파>, reception=india`
- 동아시아·티베트 자체 종파 연구 = `school=<해당 종파>, reception=east_asia` 또는 `tibet`

**판정 예**:

| 논문 | school | source_lang | reception |
|---|---|---|---|
| 玄奘 한역 『成唯識論』의 삼성설 | yogacara | chinese | india |
| 쫑카파의 중관 해석 | madhyamaka | tibetan | tibet (쫑카파 본인 사상) |
| 法藏 화엄교학의 십현문 | huayan | chinese | east_asia |
| 智訥 돈오점수 | chan | chinese | korea |

---

## Decision-06 — 시대 입자 (옵션 B, 6 bucket + transversal)

**확정**: `vedic` → `upanishadic_sutra` → `classical` → `post_classical` → `late` → `modern` + `transversal` (가로지름).

**기존 free-form era 처리**: 옛 `era: "7세기"` 같은 free-form 12개 → `century` 로 rename.

---

## Decision-07 — 라벨 구조 (다중 라벨, 주 1 + 부 N)

**확정**: 한 논문이 학파 라벨을 여러 개 가질 수 있음. 주 라벨 1개로 streamgraph 등 정적 집계, 부 라벨은 검색·필터에 사용.

---

## Decision-08 — yoga 학파 era 필수

**컨텍스트**: 요가는 classical (파탄잘리) / post_classical (하타) / modern (글로벌 요가 운동) 의 사상사적·사회학적 차이가 큼.

**확정**: `school=yoga` 인 논문은 **`era` 변수 필수 입력**. 검수 표본에 자동 포함.

---

## Decision-09 — chan 3국 통합 / nyaya·vaisheshika·pramana 별도 / vedanta 단일

**확정**:
- `chan` = 중국·한국·일본 선종 모두 (지역 구분은 `reception_horizon`)
- `nyaya`, `vaisheshika` **별도** (통합 안 함)
- `pramana` **별도** 학파 (디그나가-다르마키르티 학통)
- `vedanta` **단일** — advaita/vishishtadvaita/dvaita 분리하지 않음

---

## Decision-10 — meta 옵션 C (이중 라벨)

**확정**: 학술사·서평·번역 소개·연구 동향 논문은:
- `primary_school` = 그 논문이 다루는 사상의 학파
- `secondary` 에 `meta` 추가

분석 단계에서 토글로 메타 논문 포함/제외 선택.

---

## Decision-11 — `yoga_school` → `yoga` (canonical_id 명 단순화)

**컨텍스트**: 기존 yoga(개념) entry 와 충돌 우려.

**확정**: school 라벨 *값* 은 `yoga` 로 단순. canonical_id 공간과 school 라벨 공간은
서로 다른 네임스페이스이므로 문자열 충돌 없음. SCHEMA.md `yoga_school` → `yoga` rename.

---

## Decision-12 — Phase 3 신규 entry 의사결정 (키워드 감사 결과 반영)

**컨텍스트**: 처음 제안한 ~46개 후보를 키워드 등장 감사 후 24개로 축소.

**확정 entry 목록** (총 ~24개):

### A. 학파 (6)

| canonical_id | school | reception | 데이터 빈도 |
|---|---|---|---|
| `mimamsa` | mimamsa | india | 3 |
| `huayan` | huayan | east_asia | 3 |
| `chan` | chan | east_asia | 9 |
| `pure_land_school` | pure_land | east_asia | 11 |
| `tantric_east_asia` | tantric_buddhism | east_asia | 14 (진언/밀교) |
| `tibetan_buddhism_general` | tibetan_other | tibet | 10 |

(천태·법상·삼론 학파 키워드는 0건이므로 학파 entry 없음. 인물 entry 로만 신호 잡음.)

### B. 인물 (8)

| canonical_id | school | reception | 빈도 |
|---|---|---|---|
| `kamalasila` | madhyamaka | india | 2 |
| `zhiyi` | tiantai | east_asia | 3 |
| `kuiji` | faxiang | east_asia | 3 |
| `kumarajiva` | madhyamaka | **east_asia** ★ | 4 |
| `jizang` | sanlun | east_asia | 1 |
| `wonchuk` | yogacara | korea | 3 |
| `iryeon` | korean_buddhism | korea | 1 |
| `tsongkhapa` | gelug | tibet | 8 |

### C. 텍스트 (6) — Q3 룰 적용

| canonical_id | school | reception | 빈도 |
|---|---|---|---|
| `awakening_of_faith` | **east_asian_other** ★ | east_asia | 4 |
| `avatamsaka` | (contextual) | east_asia | 3 |
| `lotus_sutra` | (contextual) | east_asia | 4 |
| `larger_sukhavativyuha` | pure_land | east_asia | 9 |
| `smaller_sukhavativyuha` | pure_land | east_asia | 3 |
| `contemplation_sutra` | pure_land | east_asia | 1 |

`(contextual)` = `school` 강하게 단정 안 함. Phase 4 라벨링 파이프라인의 룰 (Decision-15) 이 결정.

### D. 근대 인도 사상가 (3)

| canonical_id | school | reception |
|---|---|---|
| `ramakrishna` | hindu_modern | india |
| `vivekananda` | hindu_modern | india |
| `radhakrishnan` | hindu_modern | india |

(아우로빈도 0건 → skip.)

### E. 메타 / 보강 (4)

| canonical_id | 의미 |
|---|---|
| `hatha_yoga` | `school=yoga, era=post_classical` — 하타 요가 |
| `chinese_buddhist_canon` | `source_language=chinese` 표지 (한역 자료) |
| `tibetan_canon` | `source_language=tibetan` 표지 (티베트어·서장어) |
| `dunhuang` | 돈황 사본 — 동아시아 자료 + 방법론 표지 |

**★ Q1·Q2·Q3 별도 확정**:

- **Q1 (구마라집)**: 옵션 c — `school=madhyamaka, reception=east_asia`
  *이유*: 그의 활동 결과물(한역) 이 동아시아 불교의 토대. 인도 사상가지만 동아시아 영향의 매개로 자리매김.

- **Q2 (대승기신론)**: 옵션 c — `school=east_asian_other`
  *이유*: 동아시아 자체 형성 (위경 가능성), 인도 yogacara 와 분리.

- **Q3 (법화경·화엄경·기신론 류 모호 텍스트)**: **단일 라벨 미결정, 공출현 키워드 기반 contextual disambiguation** (Decision-15) 이 처리.

---

## Decision-13 — 키워드 감사 우선 원칙

**확정**: 사전 entry 는 *실제 keywords.parquet / papers.논문명 에 등장하는* 것만 추가.
빈도 0 인 후보(예: 親鸞·道元·空海) 는 제외 — 향후 등장 시 재고.

**도구**: [`audit_keyword_coverage.py`](../labeling/audit_keyword_coverage.py)

**판정 기준**:
- INCLUDE: kw + title 합산 ≥ 3
- MARGINAL: 합산 1~2 (검수 표본 자동 포함)
- SKIP: 0

---

## Decision-14 — 모호 텍스트의 라벨링 룰 (Q3 contextual disambiguation)

**컨텍스트**: 법화경·화엄경·반야심경 등은 인도 산스크리트 원전이면서 동아시아에서 활발히 다뤄짐. 단일 학파 부착은 의미 정보를 손실.

**확정 룰** (Phase 4 라벨링 파이프라인에서 구현):

```
for paper in 논문:
    if 텍스트 entry 가 모호 (school 미부착 or "contextual"):
        공출현 키워드를 본다
        if 공출현 키워드 중 인도 학파 사상가(世親·龍樹 등) 빈도 우세:
            → school = 그 인도 학파, reception = india
        elif 공출현 키워드 중 동아시아 종파/인물 우세:
            → school = 그 동아시아 종파, reception = east_asia
        else:
            → unclassified (검수 표본)
```

**구현 위치**: `evaluation/labeling/pipeline.py` (미구현).

**왜 사전이 아닌 파이프라인에서?**: 사전 entry 는 텍스트 *자체* 의 사실 정보 (위경 여부, 사상 영향). 라벨링은 *논문* 단위 의사결정 (이 논문이 무엇을 다루는가). 같은 텍스트라도 논문마다 맥락이 다름.

---

## Decision-15 — concepts.yml 의 era → century rename

**컨텍스트**: 기존 free-form `era: "7세기"` 와 신규 bucket `era: "post_classical"` 의 키 충돌.

**확정**: 기존 free-form 12개 → `century` 로 rename. 신규 bucket 이 `era` 점유.

**점검**: `ksip/normalize.py` 가 `extras["era"]` 를 직접 읽지 않음 (코멘트 한 줄에만 언급). 안전.

---

## Decision-16 — 문서화 (이 파일 작성 시점)

**컨텍스트**: 사용자가 작업을 일시 중단하고 "체계적 데이터 구축 과정 문서화" 를 요청.

**확정**: `evaluation/docs/` 폴더에 3개 문서:
- `PIPELINE.md` — 전체 흐름·재현 절차
- `DECISIONS.md` — 이 파일 (시간순 결정 로그)
- `KEYWORD_AUDIT.md` — 키워드 감사 결과 분석

상위 문서 갱신:
- `evaluation/README.md` — docs/ 링크
- `evaluation/taxonomy/SCHEMA.md` — Q1·Q2·Q3 + contextual rule 추가
- 루트 `CLAUDE.md` — evaluation 서브프로젝트 등록 section

---

## Decision-17 — Phase 3 신규 entry 일괄 추가 (실행)

**컨텍스트**: Decision-12 (대기) 의 실제 실행. Q1c·Q2c·Q3 룰 적용.

**스크립트**: [`../labeling/add_phase3_entries.py`](../labeling/add_phase3_entries.py) — 멱등 실행 가능 (이미 있는 canonical_id 는 skip).

**확정 결과**:

| 항목 | 수 |
|---|---|
| 신규 entry 추가 | **27개** |
| concepts.yml 총 entry | 69 → **96** |
| verified=True | 67 → **94** (unverified 2 unchanged: upanishad·meditation) |

**카테고리별 추가**:

| 카테고리 | canonical_id 목록 |
|---|---|
| 학파 (6) | mimamsa / huayan / chan / pure_land / esoteric_east_asia / tibetan_buddhism_general |
| 인물 (8) | kamalasila / zhiyi / kuiji / **kumarajiva (Q1c)** / jizang / wonchuk / iryeon / tsongkhapa |
| 텍스트 (6) | **awakening_of_faith (Q2c)** / **avatamsaka (Q3)** / **lotus_sutra (Q3)** / larger_sukhavativyuha / smaller_sukhavativyuha / contemplation_sutra |
| 근대 인도 (3) | ramakrishna / vivekananda / radhakrishnan |
| 메타 (4) | hatha_yoga / chinese_buddhist_canon / tibetan_canon / dunhuang |

**Q1c·Q2c·Q3 적용 결과**:
- `kumarajiva`: `school=madhyamaka, reception=east_asia` (Q1c — 동아시아 영향 매개)
- `awakening_of_faith`: `school=east_asian_other, reception=east_asia` (Q2c — 동아시아 자체 형성)
- `avatamsaka` / `lotus_sutra`: `school=contextual, reception=contextual` (Q3 — 라벨링 파이프라인이 공출현 키워드로 결정)

**부수 결정**: `esoteric_east_asia` school 값 신설. SCHEMA.md 동아시아 section 에 추가. (한국 5자 진언 등 비-일본 동아시아 밀교 수용을 `shingon` 과 분리.)

**커버리지 영향**:

| | 기존 | Phase 3 후 |
|---|---|---|
| keywords.parquet resolve 율 | 12.4% (384/3,089) | **14.3% (443/3,089)** |
| 증가량 | — | **+59 rows** |

**새 school 분포 (resolved 키워드 기준)**: korean_buddhism 8 / pure_land 7 / gelug 6 / hindu_modern 6 / tantric_buddhism 5 / contextual 4 / sanlun 3 / esoteric_east_asia 3 / tibetan_other 2 / mimamsa 2 / tiantai 1 / faxiang 1 / chan 1.

**잔여 노이즈**: `chan` school 이 1건만 잡힘 (audit 의 substring 매칭은 9건). exact-match 한계 — surface_forms 확장은 Phase 4 검수 환류에서.

---

## 변경 이력 가이드

새 결정을 append 할 때:
1. 다음 번호 (Decision-N) 사용
2. 컨텍스트 / 옵션 / 확정 / 이유 / 영향 5개 항목
3. 영향이 다른 문서(SCHEMA, PIPELINE, README) 면 그곳도 동시 갱신
