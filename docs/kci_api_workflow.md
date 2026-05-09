# KCI Open API 작업 순서 (5단계 플랜)

> KCI API 키로 우리 프로젝트 데이터를 정확하게 업데이트하고 입수 가능한 자료를 모두 보강하는 작업 흐름. 각 단계 끝에서 결과 보고 → 다음 단계 결정.

자세한 엔드포인트 개관은 [`kci_api_overview.md`](kci_api_overview.md) 참고.

---

## 단계 요약표

| 단계 | 작업 | API 호출 | 시간 | 잠금 해제 |
|---|---|---|---|---|
| **0** | Smoke test (키 + IP 검증) | 1~3 | 5분 | 모든 후속 단계의 전제 |
| **1** | `citationDetail`로 학술지 메타 시계열 | 1 | 10분 | 인용의 풍경 헤더 KPI(IF/ZIF/자기인용지수) |
| **2** | `referenceSearch`로 482편 REFARTIID 수집 | ~482 | 30분 (실행) + 1시간 (코드) | **정밀 인용 그래프** — 노드가 클릭 가능한 KCI 논문이 됨 |
| **3** | `articleDetail`로 cited 논문 메타 회수 | 1,000~3,000 | 30분~1시간 | ego-network 노드를 풀 메타로 표시 |
| **4** | `referenceSearch`로 154편 누락 보강 | ~154 | 15분 | 24% 공백 일부 메움 (KCI 미등록은 회복 불가) |

총 ~1,640~3,640 호출 / 일 한도 5,000 — 하루 안에 완료 가능. 단, 2와 3 사이에 코드/UI 작업이 들어가서 자연스럽게 며칠 분산.

---

## 단계별 상세

### 단계 0 — Smoke Test (전제 조건)
- **무엇**: `journalSearch`로 sereId=001529 조회 + `articleDetail`로 ART002870171 1건 조회
- **목적**: API 키 유효성 + 등록 IP 일치 + XML 파싱 동작 확인
- **막히면**: IP 불일치 → KCI 마이페이지에서 IP 갱신 필요
- **산출물**: `ksip/kci_api.py` (HTTP 클라이언트 + 재시도 + rate limit + XML 파싱) 골격

### 단계 1 — 학술지 메타 시계열 (즉각적 가치, 1회 호출)
- **무엇**: `citationDetail(sereId=001529)` → 연도별 IF/ZIF/자기인용지수/즉시성지수
- **산출물**: `data/processed/journal_metrics.parquet` (연도 × 지표)
- **즉시 효과**: 인용의 풍경 우측 사이드 또는 헤더에 **KPI 시계열 라인 차트**. 학술지 자체의 38년 영향력 변천이 한 화면에 보임.

### 단계 2 — REFARTIID 일괄 수집 (가장 큰 임팩트) ★
- **무엇**: 482편 × `referenceSearch` → 각 reference의 REFARTIID 추출
- **방법**:
  - 호출당 0.5초 간격 (정중함)
  - 캐시 파일에 응답 raw XML 저장 (`data/cache/refsearch/{artiId}.xml`)
  - resume 지원: 이미 캐시된 건 skip
  - 실패 시 3회 재시도 + exponential backoff
- **산출물**: `references.parquet`에 `REFARTIID` 컬럼 추가, `cited_sereId` 컬럼 추가(자기인용 정밀 판별용)
- **핵심 효과**:
  - 정확한 인용 그래프 — 변형된 텍스트 매칭 ambiguity 해소
  - 자기인용 정밀: `sereId=001529`로 판별 → 현재 312~314건 → 더 정확한 카운트 (학술지명 변형이나 빈 문자열 케이스도 잡힘)
  - **노드 클릭 시 KCI 페이지로 점프** 가능

### 단계 3 — Cited 논문 풀 메타 회수 (자연스럽게 단계 2 다음)
- **무엇**: 단계 2에서 수집된 REFARTIID들 (unique) × `articleDetail` → 각 cited 논문의 풀 메타
- **얼마나 많을까**: 12,887건 references 중 KCI 등재(=REFARTIID 있는) 비율 추정 30~50% × unique 비율 → 1,000~3,000 호출
- **산출물**: `data/processed/cited_papers.parquet` — artiId → (제목, 저자, 학술지, 연도, DOI, 기관)
- **효과**:
  - **ego-network 노드 호버에 풀 카드** — "강형철 / 가상현실을 통한 불교이론의 재검토 / 한국불교학 / 2017"
  - 인용된 학자 정규화 정확도 ↑ — 텍스트 변형(`Schmithausen, L.` vs `L. Schmithausen`)이 같은 artiId에 묶임
  - 인용 측 학술지명 정규화도 자동 (sereId 기반)

### 단계 4 — 누락 154편 보강 (best-effort)
- **무엇**: 154편 × `referenceSearch` → 일부 회복
- **현실 기대치**: KCI 자체에 미등재인 1990년대 초 논문이 다수 → 50~80% 빈손 응답 예상
- **산출물**: `references.parquet`에 추가 행 (가능한 만큼만)
- **부가 효과**: 회복 안 된 paper 목록 → "데이터 한계" 섹션에 솔직히 표시

---

## 체크포인트 (각 단계 끝에서)

각 단계 완료 후 다음을 보고하고 진행 여부 결정:
- 호출 수 사용량 (일 한도 대비)
- 회수율 (얼마나 가져왔나)
- 데이터 품질 샘플
- 다음 단계 cost 추정 갱신

---

## 인프라 (단계 0에서 한 번만 작성)

```
ksip/kci_api.py
  - load_api_key()           # KCI_OpenAPI_Key.txt에서 + .env 폴백
  - call(apiCode, **params)  # 재시도 + 캐시 + rate limit
  - parse_xml(xml)           # 공통 응답 구조 파싱
  - get_citation_detail(sereId)
  - get_reference_search(artiId)
  - get_article_detail(artiId)
  - get_article_search(**criteria)

data/cache/                  # gitignore (대용량 XML 다수)
  ├── citation_detail/       # 학술지 메타 시계열 캐시
  ├── refsearch/             # 단계 2 캐시
  └── articledetail/         # 단계 3 캐시
```

캐시 키는 (apiCode + sorted params hash). 재실행하면 캐시에서 응답하므로 quota 안 깎임.

---

## 배포 환경 분리 원칙

- **빌드 단계 (`scripts/*.py`)**: API 호출 → parquet에 저장
- **Streamlit 앱 (`app.py`, `pages/*.py`)**: parquet만 읽음. **API 호출 X**
- **이유**: stlite GitHub Pages 정적 배포에서 CORS + 키 노출 문제 회피. parquet은 build 산출물이라 git에 commit되어 배포에 포함됨.

---

## 인도철학 학술지 식별자 (참고)

| 키 | 값 |
|---|---|
| sereId | 001529 |
| insiId | INS000001578 |
| ISSN | 1226-3230 |
| 발행기관 | 인도철학회 |
| KCI 2년 IF | 0.59 |
| 자기인용지수 (2024) | 21.05% |
