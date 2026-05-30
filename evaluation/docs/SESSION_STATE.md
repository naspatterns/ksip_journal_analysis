# Session State — 작업 인계 (단일 진입점)

> **컴퓨터를 바꿔 작업할 때 가장 먼저 읽는 파일.**
> 모든 세션 종료 시 갱신. 모든 세션 시작 시 확인.
>
> **세션 시작·종료 절차**: [`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md)
> **환경 설정**: [`ENVIRONMENT.md`](./ENVIRONMENT.md)
> **데이터 구축 과정**: [`PIPELINE.md`](./PIPELINE.md)
> **결정 로그**: [`DECISIONS.md`](./DECISIONS.md)
> **이슈 ticket**: [`ISSUES.md`](./ISSUES.md)

---

## 마지막 갱신: 2026-05-20 (Phase 5R3 완료 + 새 대시보드 작업 분기 시점)

### 현재 위치 (한 줄 요약)

> **Phase 5R3 완료** — primary_source_basis 의 unknown 320 → **114 (-64%)** 정정 (키워드/제목 fallback + CJK substring 매칭). evaluation/ 트랙은 **자원 산출 완료** 상태. 사용자는 이 폴더의 자원으로 **새 폴더에서 새 대시보드** 작업 시작 예정. evaluation/ 의 후속 (Phase 5 검수 / Phase 6 시각화) 은 보류.

### Phase 진행도

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | 분류 체계 설계 (8축 + 17 결정) | ✅ |
| 1 | 사전 메타필드 backfill (69 entry) | ✅ |
| 2 | 키워드 등장 빈도 감사 | ✅ |
| 3 | 신규 27 entry 추가 (Q1c·Q2c·Q3) | ✅ |
| — | 데이터 무결성 검증 10 레이어 (WARN=6) | ✅ |
| — | ISSUE-005 해소 (keywords.parquet 384→443 canonical) | ✅ |
| — | **Decision-18 확정** (4축 → **6축**, 일차/이차문헌 분리) | ✅ |
| 4.1 | 문서 갱신 (SCHEMA·DECISIONS·ISSUES·SESSION_STATE) | ✅ |
| 4.2 | `concepts.yml` 96 entry source_language → tradition_language rename | ✅ |
| 4.3 | references.parquet 의 `tier` 컬럼 분류 | ✅ |
| **4.4** | paper-level 두 변수 계산 (`paper_labels.parquet` 신규) | ✅ |
| **5R1** | **사전 보강 round 1** — authors.yml horizon 메타 + 외국 학자 11명 + 眞諦 entry + MIN_SURFACE_LEN 3→2 (世親·玄奘 매칭) | ✅ |
| **5R2** | **사전 보강 round 2** — 한국 학자 16명 추가 (modern_scholars 221→265). 분포 변화 미미 (예상대로 — Unicode dominance 가 이미 잡고 있음) | ✅ |
| **5 표본 추출** | **검수 표본 100 paper CSV** (`review_sample.csv`) — random 50 + low-confidence 50 (사유 균등) | ✅ |
| **5R3** | **primary fallback** — 키워드/제목 → concepts ALL types 매칭. unknown 320→**114 (-64%)**. CJK 2자 substring 허용 ("세친의" → "세친" 매칭) | ✅ |
| 5R4 | (옵션) 사전 보강 round 4 — 남은 unknown 114 의 TOP 키워드 (문법·빠알리어·목갈라나·깟짜야나·라마야나·힌두뜨바 등) entry 추가 | ⏸ |
| 5 검수 | 사용자가 CSV 검수 → 결과 환류 (사전 추가·룰 보강) | ⏸ (보류 — 새 대시보드 분기) |
| 6 | Streamlit 시각화 (커버리지 + 학제 경계 + 의존도) | ⏸ (보류 — 새 대시보드 분기) |
| **— ★** | **새 작업 분기 (2026-05-20)** — 사용자가 이 폴더 자원으로 별도 폴더에서 새 대시보드 개발 시작 | 🔀 |
| — | (사후) 축 3/4/5/7/8 확장 — 축 1+2+6 까지가 1차 범위 | 🚫 |

### Phase 4.3 결과 — `tier` 분류 분포

| 유형 | primary | secondary | unknown | 합계 |
|---|---:|---:|---:|---:|
| 단행본 | 84 | 6,624 | 0 | 6,708 |
| 학술지(정기간행물) | 0 | 3,578 | 0 | 3,578 |
| 기타자료 | 1,954 | 27 | 39 | 2,020 |
| 학위논문 | 0 | 245 | 0 | 245 |
| 인터넷자원 | 21 | 0 | 197 | 218 |
| 학술대회논문 | 0 | 77 | 0 | 77 |
| 보고서 | 0 | 41 | 0 | 41 |
| **합계** | **2,059** | **10,592** | **236** | **12,887** |

자기인용 312건 모두 secondary ✓.

### Phase 4.4 + 5R1 결과 — paper-level 두 변수 (636 논문)

`primary_source_basis` 분포 (Phase 5R1 후):

| 값 | 논문 수 | 비고 |
|---|---:|---|
| unknown | 319 | 154 (refs 없음) + 165 (refs 있지만 primary tier 0건) |
| sanskrit | 218 | 산스크리트 원전 중심 — 인도철학 본류 |
| chinese_canon | 53 | 한역 자료 (玄奘·眞諦·世親 매칭 강화로 +2) |
| pali | 24 | 빠알리 원전 중심 (남방불교) |
| mixed | 19 | 다언어 비교 |
| tibetan_canon | 3 | 티베트 자료 중심 (소수) |

`secondary_source_horizon` 분포 (Phase 5R1 후):

| 값 | 논문 수 | Phase 4.4 → 5R1 변화 |
|---|---:|---|
| english | 262 | 272 → 262 (-10, 외국 학자 정정) |
| unknown | 155 | (변화 없음) |
| korean | 113 | 118 → 113 (-5) |
| mixed | 54 | 44 → 54 (+10, 더 정확한 다양성) |
| japanese | 52 | 47 → 52 (+5, 일본 학자 매칭) |

reference-level (10,582건) 변화:
- german: 225 → 303 (+35%) — **가장 큰 정정** (Steinkellner·Frauwallner·Franco·Schmithausen·Halbfass)
- japanese: 1,572 → 1,690 (+7.5%) — 일본 학자 직접 매칭
- english: 5,506 → 5,364 (-2.6%) — 외국 학자가 잘못 분류되던 것 정정
- korean: 3,259 → 3,185 (-2.3%) — 단행본 default 정리

**Cross-tab (의존도 패턴 — Phase 6 시각화 핵심)**:

| primary \ secondary | english | japanese | korean | mixed | unknown | 합계 |
|---|---:|---:|---:|---:|---:|---:|
| sanskrit | 130 | 25 | 36 | 27 | 1 | 219 |
| chinese_canon | 16 | 9 | **20** | 6 | 0 | 51 |
| pali | 11 | 0 | 10 | 3 | 0 | 24 |
| mixed | 16 | 1 | 2 | 0 | 0 | 19 |
| tibetan_canon | 1 | 2 | 0 | 0 | 0 | 3 |
| unknown | 98 | 10 | 50 | 8 | 154 | 320 |

**해석 가능한 패턴**:
- `sanskrit + english` (130) — 서구 산스크리트학(Indology) 의존 패턴
- `sanskrit + korean` (36) — 한국 산스크리트학 자립
- `chinese_canon + korean` (20) — 가장 "한국적" 패턴 (한역불교학)
- `pali + english` (11) — 서구 팔리학(PTS) 영향
- `tibetan_canon + japanese` (2) — 일본 티베트학 (강세 학계)
- `unknown + korean` (50) — references 있지만 일차문헌 0 = 학설사·해설 위주 논문

---

## ⏳ 진행 중인 토론 — 다음 세션에서 결정 필요

(현재 차단 결정 없음 — Decision-18 확정 후 Phase 4.2 부터 코드 작업 가능)

다만 Phase 4.3 의 일차/이차 분류 룰을 구현하며 **회색 케이스** (인터넷자원·매칭 안 되는 단행본) 의 fallback 결정이 발생할 수 있음. 그때 즉시 사용자 컨펌 요청.

---

## 직전 커밋 정보

```
branch: claude/festive-elgamal-1dd4b3  (origin 에 push 됨, main 으로 머지 X — 별도 트랙)
HEAD:   5e75dc5 — Phase 5R3: primary fallback (키워드/제목 → unknown -64%)
이전:   dc26393 — Phase 5R2: 한국 학자 16명 + 검수 표본 CSV 추출
이전:   0dd8fd1 — Phase 5R1: authors horizon + 외국 학자 + 眞諦 + CJK 2자 매칭
이전:   6ae0a51 — Phase 4.4: paper-level 두 변수 계산
이전:   998d52e — Phase 4.2 + 4.3: concepts.yml rename + references tier 분류
이전:   b3d7fc9 — Phase 4.1: 문서 갱신 (Decision-18 확정 반영)
이전:   18c78fc — session: 멀티 컴퓨터 portable 환경
```

**main 과의 분기 상태** (의도된, 머지 안 함):
- claude 쪽 5 commits: evaluation/ Phase 0-3 + 검증 + ISSUE-005 + portable 환경
- main 쪽 5 commits: stlite + gh-pages + KCI integration + 사전 보강 + slash parsing fix
- **두 트랙은 분리 유지** — 평가 서브프로젝트(`evaluation/`)는 메인 대시보드와 별도 진행. push 만 origin 에 동기화.

---

## 마지막 검증 결과

```
판정: WARN  (FATAL=0  WARN=6  INFO=28  PASS=59)
- L1 Source ............... PASS
- L2 Transform ............ WARN (초록 PUA 2건, 의도된 raw 보존)
- L4 Referential .......... PASS
- L5 Cleaning ............. PASS (119/297/14 정확)
- L6 Dictionary ........... WARN (surface 중복 코스메틱)
- L7 Coverage gap ......... WARN (substring 56 등 surface 확장 환류)
- L8 References ........... PASS (자기인용 312 정확)
- L9 Institutions ......... PASS (75 부모, 동국대 297/14)
- L10 KCI spot-check ...... PASS (30/30 일치)
```

→ 전체 상세: `evaluation/output/verification/verify_summary.md`

---

## 잔여 OPEN 이슈 (분석 차단 X)

- **ISSUE-001** 초록 PUA 2건 (의도된 raw 보존)
- **ISSUE-002/003** concepts.yml surface 중복 (코스메틱, last-wins 동작)
- **ISSUE-004** journals.yml `佛敎學硏究` 충돌 (사용자 결정 필요, 축 2 단계 영향 — Phase 4.4 의 publisher 메타 활용 시 발견 가능)
- **ISSUE-006** surface 확장 (yoga 56 등) — Phase 4 환류로 자연 해소
- **ISSUE-007** 601-636 reference 부재 (KCI 원본 한계, Phase 4 단계 2 보강)
- ~~**ISSUE-008**~~ — **RESOLVED (설계)**, 2026-05-20. Decision-18 합의로 변수 재설계 확정. 구현은 Phase 4.2–4.4.

→ 상세: [`ISSUES.md`](./ISSUES.md)

---

## 다음 세션 권장 첫 행동

### 옵션 A — ★ 새 대시보드 작업 (사용자 2026-05-20 선언한 방향)

새 폴더에서 이 폴더의 자원 (`data/processed/*.parquet` + `data/dictionaries/*.yml` + `ksip/` 패키지) 을 활용. **자원 활용 가이드**: [`RESOURCE_INDEX.md`](./RESOURCE_INDEX.md).

핵심 산출물 (Phase 4+5 결과, 새 대시보드의 입력 데이터):
- `data/processed/paper_labels.parquet` — 636 논문 × {primary_source_basis, secondary_source_horizon, primary_basis_source, n_primary, n_secondary, n_inferred, primary_dist, secondary_dist}
- `data/processed/references.parquet` — 12,887 refs × {tier, 학술지_canonical, 자기인용, ...}
- `data/processed/papers.parquet` — 636 papers × 29 컬럼 (메타데이터)
- `data/processed/keywords.parquet` — 3,089 keyword × {canonical_id, ...}
- `data/processed/authors.parquet` — 654 author × canonical_id
- `data/dictionaries/concepts.yml` — 96 entry × 6 메타필드
- `data/dictionaries/authors.yml` — 63 entry × horizon
- `data/dictionaries/journals.yml` — 53 entry × publisher

### 옵션 B — evaluation/ 트랙 계속

평가 서브프로젝트 작업 재개:
1. **Phase 5 검수** — [`review_sample.csv`](../output/review_sample.csv) 사용자 검수 → 환류
2. **Phase 5R4** — 추가 사전 보강 (남은 unknown 114 의 TOP 키워드: 문법 15·빠알리어 9·목갈라나 8·깟짜야나 6 등)
3. **Phase 6** — Streamlit 시각화 (커버리지 + 학제 경계 + 의존도)

### 알려진 한계 (옵션 A·B 공통, 환류 대상)
- 단행본 secondary 의 english 비중 61% — Indian Indology 매체가 영어이기 때문 (실제 비율). Indian vs Anglo-American 구분 못 함.
- 한국 학자가 일본 학자 책의 한국어 번역서 인용 시 Hangul dominance 로 korean 분류 (예: 정토삼부경/中村元/岩波文庫).
- 학술지명 multi-slash 오류 30건 (main 에 fix, claude 엔 미적용) — paper 단위 통계 영향 미미.

---

## 환경 메모 (멀티 컴퓨터)

- Python 3.10+, venv at `.venv/`
- KCI API key: 메인 프로젝트 루트의 `KCI_OpenAPI_Key*.txt` (gitignored, 자동 탐지)
- raw 데이터: `data/raw/` (gitignored — cloud sync 필요)
- 워크트리에서 작업 시 자동으로 메인 프로젝트의 raw/key 사용

→ **새 컴퓨터 셋업 절차**: [`ENVIRONMENT.md`](./ENVIRONMENT.md)
→ **환경 검증**: `.venv/bin/python evaluation/scripts/check_env.py`
