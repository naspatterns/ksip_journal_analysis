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

## 마지막 갱신: 2026-05-20 (Phase 5 사전 보강 round 1 완료 직후)

### 현재 위치 (한 줄 요약)

> **Phase 5 round 1 (사전 보강) 완료** — authors.yml 에 horizon 메타 추가 (52 + 11 신규 외국 학자), concepts.yml 에 眞諦 신규, 玄奘 기존 활용. MIN_SURFACE_LEN 2→1로 CJK 2자 인명 매칭. 효과: 비엔나학파(독일권) 영향 ref-level +35% 정확화. 다음은 **Phase 5 검수 표본** 또는 **Phase 6 시각화**.

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
| 5 | 검수 표본 (랜덤 50 + 신뢰도 하위 50) → 사전 환류 | ⏳ **next** |
| 6 | Streamlit 시각화 (커버리지 + 학제 경계 + 의존도) | ⏸ |
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
HEAD:   (이번 커밋) — Phase 5R1: 사전 보강 (authors horizon + 외국 학자 11명 + 眞諦 + CJK 2자 매칭)
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

1. **시작 절차** ([`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md)):
   ```bash
   git checkout claude/festive-elgamal-1dd4b3   # 평가 트랙 (main 머지 X)
   git pull origin claude/festive-elgamal-1dd4b3
   .venv/bin/python evaluation/scripts/check_env.py
   cat evaluation/docs/SESSION_STATE.md
   ```

2. **Phase 5 — 검수 표본** (next, 우선):
   - 무작위 50 + 신뢰도 하위 50 → 사용자 검수
   - 신뢰도 하위 = paper_labels 의 분포에서 plurality 가 약한 (mixed 잡힘) 논문 + 단일 ref 만 가진 paper 등
   - 검수 결과 → 사전·룰 환류 (concepts.yml surface 추가, 룰 보강 등)
   - 회귀: 환류 후 verify_all + compute_paper_source 재실행

3. **Phase 6 — Streamlit 시각화**:
   - evaluation/app.py + pages/1_커버리지.py + pages/2_학제경계.py 에 6축 통합
   - 추가 page: 의존도 시각화
     - heatmap: primary_source_basis × secondary_source_horizon (Phase 4.4 cross-tab)
     - 시간 추이: 연도별 의존도 변화 (한국·일본·서구 학계 영향력 시계열)
     - 학자별 의존도 패턴 (개별 저자의 학적 정체성)

4. **알려진 한계** (Phase 5 검수에서 환류 가능):
   - 단행본 secondary 의 english 비중이 61% — Indian Indology 가 영어 매체이기 때문 (실제 비율). 단 Indian 학계와 영미 학계 구분 못 함.
   - 한국 학자의 일본 학자 인용(예: 中村元 책의 한국어 번역서) 은 raw 텍스트 우세에 따라 korean 으로 분류됨 — japanese 가 더 적절할 수도. authors.yml 에 일본 학자 + country 메타 추가로 보강 가능.
   - 학술지명 multi-slash 오류 30건(메인 브랜치엔 fix 됨, claude 브랜치엔 아직 없음) — paper 단위 통계엔 영향 미미.

---

## 환경 메모 (멀티 컴퓨터)

- Python 3.10+, venv at `.venv/`
- KCI API key: 메인 프로젝트 루트의 `KCI_OpenAPI_Key*.txt` (gitignored, 자동 탐지)
- raw 데이터: `data/raw/` (gitignored — cloud sync 필요)
- 워크트리에서 작업 시 자동으로 메인 프로젝트의 raw/key 사용

→ **새 컴퓨터 셋업 절차**: [`ENVIRONMENT.md`](./ENVIRONMENT.md)
→ **환경 검증**: `.venv/bin/python evaluation/scripts/check_env.py`
