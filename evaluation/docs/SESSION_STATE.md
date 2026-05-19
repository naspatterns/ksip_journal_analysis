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

## 마지막 갱신: 2026-05-20

### 현재 위치 (한 줄 요약)

> Phase 3 (사전 96 entry) + 무결성 검증 (WARN 6) + ISSUE-005 해소 완료.
> **다음 단계는 Phase 4 라벨링 파이프라인. 단, source_language 재설계 (Decision-18) 가 선행되어야 함.**

### Phase 진행도

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | 분류 체계 설계 (8축 + 17 결정) | ✅ |
| 1 | 사전 메타필드 backfill (69 entry) | ✅ |
| 2 | 키워드 등장 빈도 감사 | ✅ |
| 3 | 신규 27 entry 추가 (Q1c·Q2c·Q3) | ✅ |
| — | 데이터 무결성 검증 10 레이어 | ✅ |
| — | ISSUE-005 해소 (keywords.parquet 갱신) | ✅ |
| — | **Decision-18 (source_language 재설계)** | **⏳ 사용자 결정 대기** |
| 4 | 라벨링 파이프라인 | ⏸ |
| 5 | 검수 표본 (랜덤 50 + 신뢰도 하위 50) | ⏸ |
| 6 | Streamlit 시각화 (커버리지 + 학제 경계) | ⏸ |
| — | (사후) 축 2/3/4/5/7/8 확장 | 🚫 |

---

## ⏳ 진행 중인 토론 — 다음 세션에서 결정 필요

### Decision-18 — `source_language` 변수의 의미론 재설계

**배경 (2026-05-20 토론)**:
사용자가 sharp 지적함 — 현재 `concepts.yml` 의 `source_language` 는 *사상의 원천 언어* (예: dharmakirti → sanskrit) 인데, 이는 *논문 저자가 실제로 사용한 자료의 언어* 와 다른 변수임. 두 가지를 같은 이름으로 뭉개고 있었음.

**제안된 redesign**:
- `concepts.yml` 의 `source_language` → **`tradition_language`** 로 rename (사상의 원천)
- 새 변수 **`paper_source_profile`** 추가 — `references.parquet` 의 언어 detection 으로 계산 (저자의 실제 자료 분포)
- SCHEMA.md 의 4축 → 5축 확장

**대기 결정 3가지** (사용자 답변 필요):

1. **변수 재설계 방향**:
   - (a, 권장) rename + 신규 변수 두 개 분리
   - (b) 현재 source_language 유지 + 신규 paper_source_profile 만 추가
   - (c) 다른 안

2. **언어 detection 방법**:
   - (a, 권장) Unicode 범위 휴리스틱 (Hangul / Kana / Hanja-only / Latin / Tibetan)
   - (b) journals.yml 에 `lang` 메타필드 추가 → 학술지 단위 룰북 (더 정확, 더 작업 필요)
   - (a+b 결합 가능)

3. **references 없는 154편 처리**:
   - (a, 권장) `source_profile = "unknown"`
   - (b) `tradition_language` 로 fallback

**다음 세션 첫 행동**: 위 3개 답 받고 → SCHEMA·concepts.yml 재설계 → Phase 4 착수.

---

## 직전 커밋 정보

```
brnch: claude/festive-elgamal-1dd4b3 (worktree, [ahead 4, behind 4] vs origin/main)
HEAD:  994b563 — data: ISSUE-005 해소 — build_data.py 재실행, keywords.parquet 갱신
```

**워크트리 ↔ origin/main 의 4↑/4↓ 분기 상태**:
- 우리 쪽 4 commits: evaluation/ Phase 0-3 + 검증 + ISSUE-005
- main 쪽 4 commits: stlite + gh-pages + KCI integration + 사전 보강 + slash parsing

→ 다음 세션 또는 다른 컴퓨터로 옮길 때 **merge 가 필요**. [`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md) 의 "git sync 전략" 참조.

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
- **ISSUE-004** journals.yml `佛敎學硏究` 충돌 (사용자 결정 필요, 축 2 단계 영향)
- **ISSUE-006** surface 확장 (yoga 56 등) — Phase 4 환류로 자연 해소
- **ISSUE-007** 601-636 reference 부재 (KCI 원본 한계, Phase 4 단계 2 보강)
- **ISSUE-008** (아직 미등록) — Decision-18 의 source_language 재설계

→ 상세: [`ISSUES.md`](./ISSUES.md)

---

## 다음 세션 권장 첫 행동

1. **시작 절차** ([`HANDOFF_PROTOCOL.md`](./HANDOFF_PROTOCOL.md)):
   ```bash
   git pull origin main          # 또는 워크트리 동기화
   .venv/bin/python evaluation/scripts/check_env.py
   cat evaluation/docs/SESSION_STATE.md
   ```

2. **Decision-18 의 3개 결정 답하기** (위 § "진행 중인 토론")

3. **결정 받은 후 Phase 4 착수**:
   - SCHEMA 갱신 (variable rename + 신규 변수)
   - `concepts.yml` 의 `source_language` → `tradition_language` 일괄 rename
   - `paper_source_profile` 계산 로직 (references 언어 detection)
   - 라벨링 파이프라인 본체 구현

---

## 환경 메모 (멀티 컴퓨터)

- Python 3.10+, venv at `.venv/`
- KCI API key: 메인 프로젝트 루트의 `KCI_OpenAPI_Key*.txt` (gitignored, 자동 탐지)
- raw 데이터: `data/raw/` (gitignored — cloud sync 필요)
- 워크트리에서 작업 시 자동으로 메인 프로젝트의 raw/key 사용

→ **새 컴퓨터 셋업 절차**: [`ENVIRONMENT.md`](./ENVIRONMENT.md)
→ **환경 검증**: `.venv/bin/python evaluation/scripts/check_env.py`
