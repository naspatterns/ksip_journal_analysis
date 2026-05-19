# 분류 체계 (Taxonomy Schema)

「인도철학」 학술지 평가 프로젝트에서 논문에 부착하는 라벨의 정의·값 목록·결정 룰.
사전(`data/dictionaries/concepts.yml`) 의 신규 메타필드와 1:1 대응.

## 1. 사전(`concepts.yml`) 신규 메타필드

기존 entry 의 끝에 다음 4개 concept-level 필드를 옵션으로 추가. `verified=true` 항목부터 우선 라벨링.

```yaml
- canonical_id: yogacara
  canonical_kr: 유가행파
  type: 학파
  # ── 신규 4필드 (concept-level) ──
  school: yogacara              # primary_school 라벨 (자기 자신과 동일하면 명시 또는 생략)
  era: classical                # 시대 (학파/원전/학자/개념에 부착 가능)
  tradition_language: sanskrit  # 사상의 원천 언어 (원전·개념에 부착) ★ 옛 source_language 의 의미 명확화 (Decision-18)
  reception_horizon: india      # 사상의 출처 지평
  # ── 기존 ──
  surface_forms: [...]
  verified: true
```

라벨링 파이프라인은 논문의 키워드/제목에서 발견된 entry 들의 메타필드를 집계해 논문 단위 라벨을 결정.

**paper-level 자료 의존도 변수 2개** (concept-level 메타에 없음 — `references.parquet` 에서 계산):
- `primary_source_basis` — 이 논문이 어떤 일차문헌(원전)에 기반? § 4.2 참조
- `secondary_source_horizon` — 이 논문이 어느 학계(영어권·일본어권·독일어권 등) 영향? § 4.3 참조

(2026-05-20 Decision-18 — 사용자의 일차/이차문헌 분리 인사이트로 4축 → 6축 확장.)

## 2. `primary_school` — 학파 (옵션 2 입자, 13~15개)

### 인도 본토 (reception_horizon=india)

| 값 | 한글 | 비고 |
|---|---|---|
| `samkhya` | 상키야 | |
| `yoga` | 요가 학파 | 요가수트라 학통 + 후기·근대 요가 (era 로 시대 분리, ★아래 별도 룰) |
| `nyaya` | 니야야 | **별도** (사용자 확정) |
| `vaisheshika` | 와이셰시카 | **별도** (사용자 확정) |
| `mimamsa` | 미맘사 | |
| `vedanta` | 베단타 | **단일** — advaita/vishishtadvaita/dvaita 분리 안 함 (사용자 확정) |
| `abhidharma` | 아비달마 | 설일체유부·경량부 통합 |
| `madhyamaka` | 중관 | |
| `yogacara` | 유식 (유가행파) | 인도 유식. 한역 자료 기반이라도 인도 사상 연구면 여기 |
| `pramana` | 인식론파 | **별도** (사용자 확정) — 디그나가-다르마키르티 학통 |
| `tantric_buddhism` | 후기/탄트라 불교 | |
| `jainism` | 자이나교 | |
| `charvaka` | 차르바카 | 빈도 낮으면 'other_indian' 으로 |
| `hindu_modern` | 근대 힌두 사상 | 라마크리슈나·간디·라다크리슈난·아우로빈도 등 |
| `sikh` | 시크 | (한국 데이터에 거의 없을 듯, 통합 후보) |
| `vedic` | 베다 (학파 이전) | 베다·우파니샤드·브라흐마나 일반 |

**★ `yoga` 학파의 시대 구분 룰 (사용자 확정)**

`yoga` 는 단일 학파 라벨이지만, 시대 구분이 분석상 critical 하므로 **`era` 변수를 반드시 채워야 함** (검수 표본 자동 포함):

- `yoga` + `era=classical` → **고전 요가**: 파탄잘리 요가수트라 + 비야사 주석 (c.200–800)
- `yoga` + `era=post_classical` → **하타 요가 / 후기 요가**: Hatha Yoga Pradīpikā, Gheraṇḍa Saṃhitā, 신체적 수행 전통 (c.1000–1700)
- `yoga` + `era=modern` → **근대 요가**: Vivekananda, Krishnamacharya, Iyengar, 글로벌 요가 운동 (c.1880–)

(다른 학파는 era 가 옵션이지만 `yoga` 는 필수)

### 동아시아 (reception_horizon=east_asia)

| 값 | 한글 | 비고 |
|---|---|---|
| `huayan` | 화엄 | 法藏·智儼·澄觀 등 |
| `tiantai` | 천태 | 智顗·湛然 |
| `chan` | 선(禪) | **3국 통합** (사용자 확정) — 중국 선종·한국 선종·일본 선종 모두. 지역 구분은 `reception_horizon` 으로 잡힘 |
| `pure_land` | 정토 | |
| `faxiang` | 법상종 | 동아시아 유식. **유식(인도) 과 분리** |
| `sanlun` | 삼론종 | 동아시아 중관 |
| `tendai_japan` | 일본 천태 | 빈도 낮으면 tiantai 로 통합 |
| `shingon` | 진언종 (일본) | 일본 밀교 전용 (空海 학통) |
| `esoteric_east_asia` | 동아시아 밀교 / 진언 | **추가 (Phase 3)** — 한국 5자 진언·일반 동아시아 밀교 수용. `shingon` (일본 특정) 과 분리 |
| `nichiren` | 일련종 | |
| `korean_buddhism` | 한국 불교 (원효·의천·지눌·휴정 등) | |
| `east_asian_other` | 그 외 — 위경 가능성 있는 동아시아 자체 형성 텍스트 (예: 대승기신론) 포함 |

### 티베트 (reception_horizon=tibet)

| 값 | 한글 |
|---|---|
| `gelug` | 겔룩 (쫑카파) |
| `nyingma` | 닝마 |
| `kagyu` | 카규 |
| `sakya` | 사캬 |
| `bon` | 본교 |
| `tibetan_other` | 그 외 |

### 그 외

| 값 | 비고 |
|---|---|
| `comparative` | 비교철학·수용사 (학파 단일 식별 어려운 통섭 논문) |
| `meta` | 학술사·학설사·서평·번역 소개 (★ 옵션 C: 보조 라벨로도 사용) |
| `contextual` | **★ Q3 모호 텍스트 전용** — 사전에서 단일 단정 회피, 라벨링 파이프라인이 공출현 키워드로 결정. 예: 법화경·화엄경 |
| `unclassified` | 검수 대상 |

**★ `meta` 라벨 처리 (옵션 C, 사용자 확정)**

학술사·서평·번역 소개·연구 동향 논문은 **이중 라벨**:
- `primary_school` = 그 논문이 다루는 사상의 학파 (예: Schmithausen 의 Ālayavijñāna 연구 소개 → `yogacara`)
- `secondary` 에 `meta` 추가

분석 단계에서 토글로 메타 논문 포함/제외 선택 가능.

## 3. `era` — 시대 (옵션 B, 6구간 + 가로지름)

| 값 | 시기 | 비고 |
|---|---|---|
| `vedic` | ~기원전 600 | 베다·브라흐마나 |
| `upanishadic_sutra` | 기원전 600 ~ 기원후 400 | 우파니샤드·수트라 |
| `classical` | 400 ~ 800 | 수트라 주석·6파 정통화·초기 대승 |
| `post_classical` | 800 ~ 1200 | 후고전 (다르마키르티 후기·샹카라·아비나바굽타) |
| `late` | 1200 ~ 1800 | 이슬람 접촉기·후기 베단타·인도불교 멸절 후 |
| `modern` | 1800 ~ | 식민지·독립 이후 |
| `transversal` | (보조) | 사상사 통사 논문, 시대 가로지름 |

라벨링 결정 룰: 학파 + 인용 원전·인물의 시대로 추론. 모호하면 검수.

## 4. 자료 언어 변수군 — `tradition_language` + `primary_source_basis` + `secondary_source_horizon`

옛 단일 `source_language` 가 *사상의 원천 언어* (concept-level) 와 *저자가 실제 사용한 자료의 언어* (paper-level) 를 뭉개고 있었음. 사용자 지적 (2026-05-20, Decision-18) 으로 **3개 변수로 분리**. 또한 paper-level 은 인도철학 논문의 **일차/이차문헌 구분** 관습을 반영해 다시 2개로 나뉨.

### 4.1 `tradition_language` — 사상의 원천 언어 (concept-level)

`concepts.yml` 의 entry 메타. 다르마키르티 → sanskrit, 龍樹의 中論 → sanskrit (한역 자료라도 원천이 인도면 sanskrit), 法藏 → chinese, 쫑카파 → tibetan.

| 값 | 비고 |
|---|---|
| `sanskrit` | 산스크리트 원전 |
| `pali` | 빠알리 원전 |
| `prakrit` | 자이나 등 프라크리트 |
| `chinese` | 동아시아 자체 저술의 한문 (法藏·智儼 등) |
| `tibetan` | 티베트어 자체 저작 (쫑카파 등) |
| `modern_korean` | 현대 한국어 1차 텍스트 (간디 한국 수용 등 드문 케이스) |
| `mixed` | 다언어 비교 |
| `n/a` | 학술사·메타 논문 등 1차 자료 무관 |

→ 옛 `source_language` 와 enum 동일, **의미만 명확화** (Decision-18). `concepts.yml` 96 entry 의 키 일괄 rename 은 Phase 4.2 에서.

### 4.2 `primary_source_basis` — 이 논문이 어떤 일차문헌에 기반? (paper-level)

`references.parquet` 의 *일차문헌 reference* 들의 언어 분포 → 다수결 + 비율 벡터로 저장.

| 값 | 비고 |
|---|---|
| `sanskrit` | 산스크리트 원전 다수 (Pramāṇasamuccaya·Yogasūtra 등) |
| `pali` | 빠알리 니까야·아비담마 중심 |
| `prakrit` | 자이나 아가마 등 |
| `chinese_canon` | 한역 대장경 (大正藏·續藏·고려대장경) — `tradition_language=chinese` 와 다른 점: 인도 원전의 한역도 포함 |
| `tibetan_canon` | bKa' 'gyur / bsTan 'gyur — 인도 원전의 티베트역 포함 |
| `mixed` | 다언어 균형 (예: 산스크리트 원전 + 티베트역 비교) |
| `unknown` | references 부재 (154편) 또는 미판정 |

→ Phase 4.3 에서 `references.parquet` 에 `tier` 컬럼 (primary/secondary/unknown) 분류 + Phase 4.4 에서 paper-level 집계.

### 4.3 `secondary_source_horizon` — 이 논문이 어느 학계 영향? (paper-level)

`references.parquet` 의 *이차문헌 reference* 들의 학계 horizon 분포. 인도철학회 자기인용은 별도 추적.

| 값 | 비고 |
|---|---|
| `korean` | 한국어권 (한국 학술지·단행본·학위논문) |
| `japanese` | 일본어권 (印度学仏教学研究·密教文化 등) |
| `english` | 영어권 (JIP·JIABS·PEW·BSOAS·JAOS + Brill·Springer·Oxford 등) |
| `german` | 독일어권 (WZKS·Austrian/German 대학 출판 + 독일어 단행본) |
| `french` | 프랑스어권 (드물 예상) |
| `mixed` | 다국적 균형 |
| `unknown` | references 부재 또는 미판정 |

→ Decision-18 의 추가 인사이트: 이 변수는 **축 2 (의존도) 의 직접 답** — 학계 lineage 측정. 예: 한국·일본 80% / 영어권 15% / 독일어권 5% → 동아시아 의존 패턴. 영어권 60% / 독일어권 30% / 한국 10% → 서구 학계 의존 패턴.

### 4.4 일차/이차문헌 분류 룰 (Phase 4.3 구현)

`references.parquet` 의 7유형 + 사전 매칭 결합:

| 유형 | 건수 | 일/이차 결정 |
|---|---|---|
| 기타자료 | 2,020 | **거의 일차** — 원전 카탈로그 (D 4203, T 32, Tib. 등). 단 ATBS·시리즈명 등은 사전 매칭으로 확인. |
| 단행본 | 6,708 | **혼합** — 저자가 사상가(고전, concepts.yml 매칭) 또는 제목이 텍스트명이면 일차. 학자명+학자 저작이면 이차. |
| 학술지(정기간행물) | 3,578 | **거의 이차** — 학자 연구. 자기인용(인도철학) 제외. |
| 학위논문 / 학술대회 / 보고서 | 363 | **이차** |
| 인터넷자원 | 218 | **회색** — 매칭 가능하면 일차, 아니면 unknown |

분류 결과 → `references.parquet` 의 신규 컬럼 `tier` (`primary` / `secondary` / `unknown`).

### 4.5 언어 detection 방법 (Phase 4.4 구현)

Unicode 휴리스틱 1차 + `journals.yml` 의 `publisher` 메타 보강 (Decision-18 확정):

- Hangul U+AC00–U+D7AF → `korean`
- Kana U+3040–U+30FF (Hiragana/Katakana) → `japanese`
- Han(CJK) only, no Kana → `chinese` (한역 + 대만/중국 현대)
- Latin → 1차로 `english`, publisher 메타로 정밀화 (Austrian Academy·Brill 독일어권 → `german`, Springer/Oxford → `english` 등)
- Tibetan U+0F00–U+0FFF → `tibetan` (대부분 일차문헌)
- Devanagari U+0900–U+097F → `sanskrit` (대부분 일차문헌)

## 5. `reception_horizon` — 지평 (축 6 핵심 변수)

| 값 | 정의 | 학제 경계상 |
|---|---|---|
| `india` | 사상 자체가 인도에서 형성·전개 (한역·티베트역 자료 기반이어도) | **인도철학** |
| `east_asia` | 동아시아에서 형성된 종파/사상 (화엄·천태·선·정토·법상·삼론 등) | 동아시아 불교 |
| `tibet` | 티베트에서 형성된 종파 (겔룩·닝마·카규·사캬) | 티베트 불교 |
| `korea` | 한국 자체 사상 (원효·지눌 본인 사상·동학 등) | 한국 사상 |
| `west` | 서구의 인도 수용·비교철학 | 비교철학 |
| `mixed` | 가로지름 (인도 사상의 동아시아 수용사) | 보조 검토 |

**핵심 룰**: 한역·티베트역 자료를 사용해도, 그 사상의 *원천* 이 인도면 `india`. 동아시아·티베트 자체 종파를 다루면 그쪽.

## 6. 라벨링 흐름

```
키워드 (정규화 → canonical_id) ─┐
제목 (사전 매칭)             ─┤── concept-level 메타 집계 ──┐
[초록 — 보조, 모호 시]        ─┘     (다수결 / 가중)         │
                                                            ▼
                                              논문 × { school+, era+,
                                                       tradition_language?,
                                                       reception_horizon }

references.parquet ────► tier 분류 (primary/secondary) ────► paper-level 집계
                                                            ▼
                                              논문 × { primary_source_basis,
                                                       secondary_source_horizon }
                                                            │
                                                            ▼
                                              BERTopic 으로 미해결·저신뢰 보강
                                                            │
                                                            ▼
                                              검수 표본 (Phase 5) → 사전 환류
```

**두 개의 독립 집계 경로**:
- (위) 키워드·제목·초록 → 사전 매칭 → concept-level 메타 (school·era·tradition_language·reception_horizon) 집계
- (아래) references → 일/이차 분류 + Unicode·publisher detection → paper-level 두 변수 (primary_source_basis·secondary_source_horizon) 계산

두 경로의 산출을 논문 단위로 join → 6축 라벨 완성.

## 7. 결정 사항 (사용자 확정 / 변경 시 환류)

- ✅ A1 학파 입자: 옵션 2 (13~15개) + Authority Control 로 철자 통일
- ✅ A2 동아시아/티베트: **2축 라벨** (primary_school + reception_horizon + source_language)
- ✅ A3 시대 입자: 옵션 B (6구간 + transversal)
- ✅ A4 주제: 옵션 3 — 키워드 클러스터링, 사용자 판단 (별도 라벨 변수 두지 않음)
- ✅ A5 다중 라벨: 주 1 + 부 N
- ✅ 결정 1 — `pramana` 별도 학파
- ✅ 결정 2 — `nyaya` / `vaisheshika` 별도 학파
- ✅ 결정 3 — `vedanta` 단일 (하위 분리 없음)
- ✅ 결정 4 — `chan` 3국 통합 (지역은 `reception_horizon`)
- ✅ 결정 5 — `meta` 옵션 C (이중 라벨)
- ✅ 추가 — `yoga_school` → `yoga`, era 필수 (classical/post_classical/modern)
- ✅ **Q1 (구마라집)** — 옵션 c: `school=madhyamaka, reception=east_asia` (한역 작업이 동아시아 불교의 토대)
- ✅ **Q2 (대승기신론)** — 옵션 c: `school=east_asian_other` (동아시아 자체 형성, 인도 yogacara 와 분리)
- ✅ **Q3 (법화경·화엄경 류 모호 텍스트)** — 사전에서 단일 학파 단정 안 함. **공출현 키워드 기반 contextual disambiguation** 룰을 Phase 4 라벨링 파이프라인이 처리 (§8 참조).
- ✅ **신규 entry 후보 키워드 빈도 감사 기반 선정** — `docs/KEYWORD_AUDIT.md` 참조. 빈도 0 후보(法藏·智儼·親鸞·道元·空海·의상·지눌·휴정 등) 는 사전 추가 안 함.
- ✅ **Decision-18 (2026-05-20)** — `source_language` → `tradition_language` (concept-level) rename. paper-level 두 신규 변수 추가: `primary_source_basis` (일차문헌 기반) + `secondary_source_horizon` (이차문헌 학계). 인도철학 학계의 일차/이차문헌 분리 관습을 반영. 4축 → **6축 확장**.
- ✅ **Decision-18 (언어 detection)** — Unicode 휴리스틱 1차 + `journals.yml` 의 publisher 메타 보강.
- ✅ **Decision-18 (154편 references 부재)** — `primary_source_basis=unknown` + `secondary_source_horizon=unknown` (tradition_language fallback 안 함).

전체 결정 로그는 [`../docs/DECISIONS.md`](../docs/DECISIONS.md) 참조.

## 8. Q3 — 모호 텍스트의 contextual disambiguation 룰

법화경·화엄경·반야심경 같은 텍스트는 인도 산스크리트 원전이면서 동아시아에서도 활발히 다뤄짐. **사전에 단일 학파를 단정하면 정보 손실**.

### 룰 정의 (Phase 4 라벨링 파이프라인에서 구현)

```
모호 텍스트 entry 의 처리:
  사전에 school 미부착 또는 school="contextual" 로 표기

각 논문 라벨링 시:
  if 논문의 키워드 중 모호 텍스트가 등장:
      공출현 키워드 집합 C 를 수집
      if C 에서 인도 학파 사상가 빈도 우세 (世親·龍樹·디그나가·샹까라 등):
          → 그 인도 학파, reception=india
      elif C 에서 동아시아 종파/인물 빈도 우세 (법장·지의·규기·원효):
          → 그 동아시아 종파, reception=east_asia
      elif C 에서 티베트 인물 빈도 우세 (쫑카파·까말라쉴라):
          → 그 티베트 학파, reception=tibet
      else (신호 부족):
          → unclassified → 검수 표본 자동 포함
```

### 왜 사전이 아닌 파이프라인에서?

- **사전 entry** = 텍스트 *자체* 의 사실 정보 (저작 시기, 원어, 위경 여부)
- **라벨링** = *논문* 단위 의사결정 (이 논문이 무엇을 다루는가)
- 같은 텍스트라도 논문마다 맥락이 달라지므로 사전 단정은 정확도를 떨어뜨림.

### 처리 대상 (예시)

| 텍스트 | 단일 단정의 위험 | 가능한 reception |
|---|---|---|
| 법화경 | 인도 원전 vs 천태 vs 일련 | india / east_asia |
| 화엄경 | 인도 원전 vs 화엄종 | india / east_asia |
| 반야심경 | 인도 반야부 vs 동아시아 선·정토 | india / east_asia |
| 능가경 | 인도 yogacara vs 선·여래장 동아시아 수용 | india / east_asia |
| 금강경 | 인도 반야부 vs 선·동아시아 | india / east_asia |

(기신론(Q2)·구마라집(Q1) 은 단일 단정 = `school=east_asian_other` / `reception=east_asia`로 확정. contextual 처리 대상 아님.)
