# 이슈 ticket (ISSUES)

데이터 무결성 검증·라벨링 환류·사용자 검수 과정에서 발견된 이슈를 ticket 으로 추적.

관련 문서: [`VERIFICATION_PLAN.md`](./VERIFICATION_PLAN.md), [`DECISIONS.md`](./DECISIONS.md)

---

## ticket 형식

각 이슈는 다음 형식:

```
## ISSUE-NNN — <짧은 제목>

| 항목 | 값 |
|---|---|
| 분류 | FATAL / WARN / INFO |
| 발견 | 검증 레이어 (L1~L10) 또는 검수 환류 |
| 발견일 | YYYY-MM-DD |
| 상태 | OPEN / IN_PROGRESS / RESOLVED / WONTFIX |
| 영향 | 영향 받는 데이터·산출물 |

**현상**: ...

**원인 (분석 시)**: ...

**해소 방안**: ...

**완료 (resolve 시)**: 커밋 해시 + 후속 회귀 검증 결과
```

---

## 분류 가이드

- **FATAL**: 분석 자체를 막음 (데이터 손실, primary key 위반, 핵심 사전 미로드 등). 즉시 fix.
- **WARN**: 결과 정확도에 영향. Phase 4 검수 환류로 자연 해소되면 close, 아니면 ticket 유지.
- **INFO**: 단순 통계 / 참고 정보. ticket 으로 기록은 하되 처리 안 함.

---

## ticket 목록

---

## ISSUE-001 — 초록 컬럼에 BMP PUA 2건 잔존

| 항목 | 값 |
|---|---|
| 분류 | WARN |
| 발견 | L2 (verify_02_transform) |
| 발견일 | 2026-05-17 |
| 상태 | OPEN |
| 영향 | papers.초록 (2건) |

**현상**: papers.초록 컬럼에 BMP PUA (U+E000-U+F8FF) 문자 2건 잔존. 논문명·키워드·저자명·소속기관은 모두 클리닝되어 깨끗.

**원인**: `ksip/load.py` 의 build 단계에서 초록은 `clean_keyword`/`clean_title` 같은 PUA 제거를 호출하지 않음 — 의도된 동작 가능성 (초록은 raw 보존).

**해소 방안**:
- (a) 초록 표시 시점에 lazy 클리닝 (현재 분석 단계에서는 초록을 직접 라벨링에 안 씀)
- (b) build_data 단계에 `clean_keyword` 같은 함수를 초록에도 적용 (decision 필요)
- 권장: (a) — 초록 raw 보존이 의도, 라벨링 파이프라인에서 노출 시 clean

---

## ISSUE-002 — concepts.yml entry 내 surface 중복 5건 (NFKC+lower 충돌)

| 항목 | 값 |
|---|---|
| 분류 | WARN |
| 발견 | L6 (verify_05_dictionary) |
| 발견일 | 2026-05-17 |
| 상태 | OPEN |
| 영향 | 사전 cleanliness (검색 동작 영향 없음, last-wins) |

**현상**: 일부 entry 의 surface_forms 가 NFKC + lowercase 후 동일해지는 항목 5건. 예: `Dharmakīrti` / `dharmakirti` / `Dharmakirti` 가 모두 `dharmakīrti` 또는 `dharmakirti` 로 정규화되어 중복.

**원인**: 사전 작성 시 case-variant + diacritic-variant 를 모두 surface_forms 에 나열한 결과. `ksip/normalize.py` 의 `_nfkc().lower()` 가 같은 키로 매핑.

**해소 방안**: 중복 정리 — 한 가지 canonical 표기만 남기고 나머지 제거. 단 검색 동작에는 영향 없음 (last-wins 가 같은 cid 에 떨어짐). 코스메틱.

---

## ISSUE-003 — concepts.yml entry 간 surface 중복 (자기 자신과 중복)

| 항목 | 값 |
|---|---|
| 분류 | WARN (실제는 false positive, INFO 수준) |
| 발견 | L6 |
| 발견일 | 2026-05-17 |
| 상태 | OPEN (검증 스크립트 보강 필요) |
| 영향 | 검증 스크립트 진단 정확도 |

**현상**: `inter_surface_dup` 검출이 (예: dharmakirti, ['dharmakirti', 'dharmakirti']) 같은 *같은 cid 안의 다른 surface 가 정규화 후 일치* 케이스를 cross-entry 중복으로 잘못 보고.

**원인**: verify_05_dictionary.py 의 inter_dup 로직이 cid 가 같아도 별도 entry 로 카운트.

**해소 방안**: 검증 스크립트의 inter_dup 판정에 `len(set(cids)) > 1` 조건 추가하여 cid 가 같으면 intra 로만 카운트. INFO 로 다운그레이드.

---

## ISSUE-004 — journals.yml `佛敎學硏究` 가 2개 entry 에 공유

| 항목 | 값 |
|---|---|
| 분류 | WARN |
| 발견 | L6 |
| 발견일 | 2026-05-17 |
| 상태 | OPEN |
| 영향 | journals authority 해상도 (last-wins 로 한쪽이 가려짐) |

**현상**: 한자 surface `佛敎學硏究` 가 두 journals.yml entry 에 등록 — `bukkyogaku_kenkyu` (일본 仏教学研究) + `buddhist_studies_research` (한국 佛敎學硏究).

**원인**: 일본 학술지의 한국식 표기 (佛敎學硏究) 와 한국 학술지의 정식 명칭이 동일.

**해소 방안**:
- 사용자 결정 필요: 어느 학술지가 `佛敎學硏究` 한자 표기를 가져야 하나?
- 일본 학술지는 일본식 표기(仏教学研究) 만 남기고 한국식 표기 surface 제거 권장.

---

## ISSUE-005 — coverage drift: parquet build 시점 384 vs 현재 사전 적용 455

| 항목 | 값 |
|---|---|
| 분류 | WARN |
| 발견 | L7 (verify_06_coverage_gap) |
| 발견일 | 2026-05-17 |
| 상태 | **RESOLVED** |
| 영향 | `keywords.parquet.canonical_id` 컬럼의 stale 상태 |

**현상**: `keywords.parquet` 의 `canonical_id` 컬럼은 build 시점 사전 (69 entry) 으로 채워졌는데, Phase 3 후 사전이 96 entry 로 확장됨. 현재 사전으로 재 resolve 시 455 (vs 기존 384 — 차이 71). 데이터 자체는 무손실, 단지 stale.

**원인**: `scripts/build_data.py` 가 사전 변경 후 자동 재실행되지 않음.

**해소 방안**: Phase 3 후 `build_data.py` 한 번 재실행해서 `keywords.parquet` 의 `canonical_id` 컬럼을 새 사전 기준으로 갱신. Phase 4 라벨링 파이프라인 착수 전 필수.

**완료** (2026-05-18):

1. `data/raw/` 를 메인 프로젝트로 symlink (워크트리에는 raw 데이터 부재)
2. `.venv/bin/python scripts/build_data.py` 재실행
3. 결과:
   - keywords.parquet: 384 → **443** resolved (14.3%) — Phase 3 entry 59건 신규 매칭
   - papers/authors/references: bit-for-bit 동일 (변경 없음)
4. verify_06_coverage_gap.py 보강: `include_unverified=False` (build 와 동일 모드) → drift 0
5. 검증 재실행: L7 PASS (coverage_drift), 마스터 WARN 7 → 6

**부수 발견**: verify_06 의 원래 측정은 `include_unverified=True` 라 verified-only build 와 12 row 차이가 났음. 이는 upanishad·meditation 두 unverified entry 의 surface (각 6 row). CLAUDE.md 의 "verified=false 항목은 분석에 자동 적용 안 됨" 원칙대로, build 와 검증 모두 verified-only 가 표준.

**커밋**: (이번 커밋)

---

## ISSUE-006 — surface_forms 확장 필요: yoga(56), vijnanavada(29), prajna(19)

| 항목 | 값 |
|---|---|
| 분류 | WARN |
| 발견 | L7 |
| 발견일 | 2026-05-17 |
| 상태 | OPEN |
| 영향 | 라벨링 커버리지 (Phase 4 의 정확도) |

**현상**: 사전 entry 의 `surface_forms` 가 실제 데이터의 표기 변형을 다 잡지 못함. substring 매칭은 yoga 가 56건 잡지만 exact match 는 누락. vijnanavada 29건, prajna 19건 등.

**원인**: 사전 작성 시 가장 흔한 변형만 등록. "8지 요가", "고전 요가", "하타 요가" 같은 복합어가 yoga concept 으로 자동 매핑 안 됨.

**해소 방안**: 빈도 TOP 30 surface 를 사전에 추가 (검수 후) → `verify_06_coverage_gap_substring_vs_exact.csv` 참조. **이건 Phase 4 의 검수 환류로 자연 해소** — Phase 4 라벨링 후 검수 단계에서 발견되는 미해결 surface 를 사전에 환류.

---

## ISSUE-007 — 601-636 xls 의 참고문헌 시트가 비어 있음

| 항목 | 값 |
|---|---|
| 분류 | INFO (FATAL 아님 — 원본 KCI 가 그렇게 줌) |
| 발견 | L1 |
| 발견일 | 2026-05-17 |
| 상태 | OPEN |
| 영향 | 최근 36편의 참고문헌 데이터 부재 |

**현상**: `인도철학_601_636.xls` 의 `참고문헌` 시트가 0 row. 1_300 (7,480) + 301_600 (5,407) = 12,887 만 존재.

**원인**: KCI 다운로드 시점에 그 36편의 참고문헌이 KCI 자체에 미등록이었거나, 다운로드 도구의 누락.

**해소 방안**:
- 단기: 그대로 진행. CLAUDE.md 가 이미 154편(주로 1990년대 초)이 references 미보유로 설명. 이 36편은 가장 최근 (2024-2025) 이라 별도 누락.
- 장기: KCI Open API 의 `referenceSearch` 로 그 36편의 artiId 를 조회해 references 보강 (Phase 4 단계 2 에 포함).

---

## 변경 이력 가이드

새 ticket 은 `ISSUE-NNN` 로 다음 번호 사용. RESOLVED 처리 시 "완료" 항목에 커밋 해시 + 회귀 검증 결과 기록.
