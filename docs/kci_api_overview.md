# KCI Open API 활용 개관 — KSIP 프로젝트 맥락

> KCI Open API 키가 도착한 시점에 작성. 우리 프로젝트(`<인도철학>` 학술지 분석)에서 무엇이 가능한지 임팩트 순으로 정리.

---

## API 키가 잠금 해제하는 5개 엔드포인트

기본 형태:
```
https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode={code}&key={KEY}&...
```

| apiCode | 무엇을 받나 | 응답 형식 |
|---|---|---|
| `articleSearch` | 검색어/저자/연도/학술지로 논문 검색 → 논문 메타데이터 리스트 | XML |
| `articleDetail` | artiId 1개 → 논문 풀 메타데이터(저자·기관·키워드·DOI 등) | XML |
| **`referenceSearch`** | artiId 1개 → 그 논문의 참고문헌 리스트 + **REFARTIID** | XML |
| `citationDetail` | sereId(학술지) 1개 → 연도별 IF/ZIF/자기인용지수 시계열 | XML |
| `journalSearch` | 학술지 검색 (sereId 등 식별자 회수) | XML |

---

## 우리 프로젝트에 미치는 임팩트 (순서대로)

### 🥇 ① REFARTIID로 정확한 인용 그래프 (`referenceSearch`)
지금까지 발견의 **핵심**. 응답에 `REFARTIID` 필드가 있어, 인용된 논문이 KCI 등재면 그 논문의 artiId가 직접 반환됨.

- **현재 한계**: 12,887건 references는 슬래시 구분 텍스트만 있음 → 노드들이 surface 텍스트 매칭(저자+제목+연도)으로 합산. 정확도 한계.
- **API 도입 후**: artiId → artiId 정밀 매칭. 노드 클릭 시 KCI URL로 점프 가능. 자기인용도 텍스트 매칭이 아니라 sereId=001529인지로 정확 판별.
- **호출 비용**: 482편 × 1회 = 482 호출 (일 한도 5,000 중 약 10%)

### 🥈 ② 학술지 메타 시계열 (`citationDetail`)
- sereId=001529(인도철학)로 호출 → **연도별 IF / ZIF / 자기인용비율 / 즉시성지수** 시계열
- 이거로 「인용의 풍경」 페이지 우측 사이드 또는 헤더에 **KPI 카드** 추가 가능: "2024 IF 0.59 / 자기인용지수 21%"
- **호출 비용**: 1회로 끝 (한 학술지 전체 시계열)

### 🥉 ③ 누락 참고문헌 보강 (`referenceSearch` + `articleDetail`)
- 154편(24%)이 .xls에 참고문헌 누락 — 일부는 KCI에 등록된 후 .xls 반출 시 누락된 것일 가능성
- referenceSearch로 154편 전부 호출 → 일부 회수 가능 (단, KCI 자체 미등록도 있음 → 사용자 직접 검증 필요)

### 🏃 ④ 현대 학자 정규화 보조 (`articleSearch`)
- 인용 측 저자명이 `Schmithausen, Lambert` / `Schmithausen` / `L. Schmithausen` 식으로 변형되는데, articleSearch로 KCI 외 저자 표기 패턴 확인 가능
- 단, KCI는 한국 학술지 색인이라 외국 학자 정보 빈약 → ROI 낮음

---

## 실용적 제약

| 항목 | 값 |
|---|---|
| 일일 호출 한도 | **5,000 / 일** (자동 발급 키) |
| 시간당 한도 | 명시 없음 — 정중하게 1초당 1~2건 |
| **IP 바인딩** | 신청 시 등록한 공인 IP에서만 호출 가능. 회선 변경 시 키 갱신 필요. |
| 응답 형식 | XML (Python `xml.etree.ElementTree` 또는 `lxml`로 파싱) |
| 인증 | URL 쿼리 파라미터 `key=...` (간단함, 헤더 X) |
| 인코딩 | UTF-8 |
| 키 노출 | **절대 git에 커밋 금지** — `.gitignore`에 `KCI_OpenAPI_Key.txt`, `*.key`, `.env` 등록 완료 |

---

## API로 못 하는 것

- ❌ 본문 PDF 다운로드 (저작권 — DBpia/누리미디어 영역)
- ❌ **피인용 데이터** (이 학술지를 인용한 논문 목록) — 별도 신청 필요한 영역, 현재 키로는 안 됨
- ❌ 1990년대 초 일부 논문 — KCI 자체 등재 시기 이전이라 데이터 빈약
- ❌ 외국 학술지 색인 (KCI는 한국 학술지 전용)

---

## 추천 첫 액션

```
단계 2-A: 학술지 메타 시계열 (5분, 1 호출)
  citationDetail(sereId=001529) → 인용 풍경 헤더 KPI

  ↓ 위가 잘 되면

단계 2-B: REFARTIID 일괄 보강 (1~2시간, ~482 호출)
  482편 artiId × referenceSearch → REFARTIID 추출 → references.parquet에 새 컬럼
  → 정밀 인용 그래프 가능
```

**왜 이 순서**: 단계 2-A는 호출 1회로 결과물 즉시 확인 → API 키 + 코드가 동작하는지 빠른 검증. 그 다음 본격적인 일괄 처리.

---

## 작업 단위 제안

1. **`ksip/kci_api.py`** 작성 — XML 응답 파싱 + 재시도/rate-limit + 키 로딩 (env 또는 `KCI_OpenAPI_Key.txt`에서)
2. **`scripts/fetch_citation_detail.py`** — 단계 2-A 단일 호출
3. **`scripts/fetch_references.py`** — 단계 2-B 일괄 (cache + resume 지원)
4. **`references.parquet` 스키마 확장** — `REFARTIID` 컬럼 추가
5. **citations.py 갱신** — REFARTIID 매칭 우선, 텍스트 매칭은 fallback

---

## 검토 포인트 (작업 시작 전)

1. **단계 2-A 먼저 시도**(권장)? 아니면 곧장 2-B로?
2. API 키 파일 위치 — 현재 `KCI_OpenAPI_Key.txt` 그대로? 아니면 `.env`로 옮길까?
3. **신청 IP** — KCI 신청 시 등록한 IP 그대로 사용 중인지? (다른 회선이면 호출 거부됨, `curl -s https://api.ipify.org` 로 확인)

---

## 인도철학 학술지 식별자 (참고)

| 키 | 값 |
|---|---|
| sereId | 001529 |
| insiId | INS000001578 |
| ISSN | 1226-3230 |
| 발행기관 | 인도철학회 (Korea Society for Indian Philosophy) |
| KCI 2년 IF | 0.59 |
| 자기인용지수 (2024) | 21.05% |
