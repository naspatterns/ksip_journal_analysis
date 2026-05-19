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

## 마지막 갱신: 2026-05-20 (Phase 4.2 + 4.3 완료 직후)

### 현재 위치 (한 줄 요약)

> Phase 4.1-4.3 완료. concepts.yml 96 entry rename 됨, references.parquet 의 `tier` 컬럼 분류됨 (primary 2,059 / secondary 10,592 / unknown 236). 다음은 **Phase 4.4 — paper-level 두 변수 계산** (`primary_source_basis` + `secondary_source_horizon`).

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
| **4.1** | 문서 갱신 (SCHEMA·DECISIONS·ISSUES·SESSION_STATE) | ✅ |
| **4.2** | `concepts.yml` 96 entry source_language → tradition_language rename | ✅ |
| **4.3** | references.parquet 의 `tier` 컬럼 분류 (primary 2,059 / secondary 10,592 / unknown 236) | ✅ |
| **4.4** | **paper-level 두 변수 계산** (`primary_source_basis` + `secondary_source_horizon`) | ⏳ **next** |
| 5 | 검수 표본 (랜덤 50 + 신뢰도 하위 50) → 사전 환류 | ⏸ |
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

자기인용 312건 모두 secondary ✓. unknown 236건 (기관명 39 + 인터넷자원 회색 197) 은 의도된 보수적 처리.

---

## ⏳ 진행 중인 토론 — 다음 세션에서 결정 필요

(현재 차단 결정 없음 — Decision-18 확정 후 Phase 4.2 부터 코드 작업 가능)

다만 Phase 4.3 의 일차/이차 분류 룰을 구현하며 **회색 케이스** (인터넷자원·매칭 안 되는 단행본) 의 fallback 결정이 발생할 수 있음. 그때 즉시 사용자 컨펌 요청.

---

## 직전 커밋 정보

```
branch: claude/festive-elgamal-1dd4b3  (origin 에 push 됨, main 으로 머지 X — 별도 트랙)
HEAD:   (이번 커밋) — Phase 4.2 + 4.3: concepts.yml rename + references tier 분류
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

2. **Phase 4.4 — paper-level 두 변수 계산** (Phase 4.3 까지 완료, 이게 next):
   - `evaluation/labeling/detect_language.py` 신규 — Unicode 휴리스틱 (Hangul/Kana/Hanja/Latin/Tibetan/Devanagari) + journals.yml publisher 메타 결합
   - `evaluation/labeling/compute_paper_source.py` 신규 — references 의 tier × language 를 paper 단위로 집계
   - 산출: 별도 `paper_labels.parquet` (논문ID × {primary_source_basis, secondary_source_horizon, 비율 벡터})
   - 154편 (references 없음) → 두 변수 모두 `unknown`
   - 검증: verify_all 회귀 점검 + 분포 sanity check

3. **Phase 5 — 검수 표본**:
   - 무작위 50 + 신뢰도 하위 50 → 사용자 검수
   - 사전·룰 환류

4. **Phase 6 — Streamlit 시각화**:
   - evaluation/app.py + pages/1_커버리지.py + pages/2_학제경계.py 에 6축 통합
   - 추가 page: 의존도 (primary_source_basis × secondary_source_horizon 분포)

---

## 환경 메모 (멀티 컴퓨터)

- Python 3.10+, venv at `.venv/`
- KCI API key: 메인 프로젝트 루트의 `KCI_OpenAPI_Key*.txt` (gitignored, 자동 탐지)
- raw 데이터: `data/raw/` (gitignored — cloud sync 필요)
- 워크트리에서 작업 시 자동으로 메인 프로젝트의 raw/key 사용

→ **새 컴퓨터 셋업 절차**: [`ENVIRONMENT.md`](./ENVIRONMENT.md)
→ **환경 검증**: `.venv/bin/python evaluation/scripts/check_env.py`
