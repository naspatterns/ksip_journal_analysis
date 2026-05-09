# CLAUDE.md — KSIP 인도철학 학술지 분석 대시보드

다른 세션에서도 동일한 작업을 이어가기 위한 프로젝트 캐논 문서.
이 폴더에 처음 들어오면 이 파일을 먼저 읽을 것.

---

## 1. 프로젝트 목적

2026-1학기 디지털 인문학 수업 과제. 학술지 `<인도철학>`(KCI 등재, 인도철학회) 의 1989–2025년 서지 데이터(636편) 를 분석하는 **Streamlit 대시보드** 구축.

목표는 *연구 영감*: 사용자가 거시적 풍경 → 개념 탐험 → 인용 네트워크 순서로 들어가며 논문 주제를 발굴할 수 있는 도구.

---

## 2. 데이터 — 가능한 분석과 불가능한 분석

원본 3개의 .xls 파일과 통합 .csv 가 `data/raw/` 에 있다(.gitignore).

| 항목 | 값 / 의미 |
|---|---|
| 논문 수 | 636편 (1989–2025, 37년) |
| 단독저자 비율 | **97.3%** → 공저자 네트워크 분석 의미 없음 |
| 동국대 비율 | **44%** (277편 raw → 297편 family rollup) — 압도적 |
| 주제분야 | 전부 "철학" → 분류 변수로 무용 |
| 키워드 surface unique | 2,333개 (국문/영문/IAST 혼재) |
| 초록 보유 | ~80% |
| **참고문헌** | **.xls 별도 시트에 12,887건** (CSV 변환 시 누락됐음). 482편(76%)에 등록, 154편(주로 1990년대 초)은 KCI 자체 미등록. 슬래시 구분 텍스트, 유형별 7종(단행본/학술지/학위논문/학술대회/보고서/인터넷자원/기타자료) |
| 자기인용 | 학술지명 == "인도철학" 매칭 312건(2.4%). KCI 공식 자기인용지수 21%(2024)는 다른 정의 |

**파싱 핵심 주의:**
- `인도철학_301_600.xls` , `인도철학_601_636.xls` 의 논문목록 시트는 `논문 ID` 컬럼이 **없음**. URL 의 `artiId=ART…` 를 정규식으로 추출해서 채워야 함 ([ksip/load.py:13](ksip/load.py:13)).
- 다중 저자: `,` 또는 `;` 구분.
- 1989년 저자는 모두 신규(시작 연도 컨벤션).
- 키워드 분리: `,` 만. 빈 토큰·문장부호 단독(`.` 49건 등)은 노이즈로 제거.

---

## 3. 대시보드 설계 — 3개 화면 (Plan A: 클릭=이동)

이전 설계(공저자 네트워크 중심)는 단독저자 97% 데이터에 맞지 않아 폐기. 이전 인터랙션 모델(좌클릭=교차필터)은 갇힘 현상 때문에 폐기 → **클릭=그 항목의 상세 화면으로 이동**으로 통일.

### 3.1 메인 「학술지 지형도」 ([app.py](app.py))
4분할 그리드. 사이드바: 연도 슬라이더(유일한 필터) + 다른 화면 링크.

```
① 연도별 논문 수 라인 (읽기 전용)   ② 기관 트리맵 (셀 클릭→인용의 풍경)
③ 키워드 워드클라우드 + 셀렉터       ④ 저자 TOP 20 막대
   (셀렉터→개념 탐험기)                  (막대 클릭→인용의 풍경)
```

### 3.2 「개념 탐험기」 ([pages/1_개념_탐험기.py](pages/1_개념_탐험기.py))
URL `?keyword=…` 으로 진입. 헤더 카드(canonical_form + 메타) + 4분할:
- ① 시계열 빈도 / ② 공출현 키워드 TOP 10 / ③ 저자 TOP 10 / ④ 대표 논문 카드
- **표기 변형 토글**: `통합 (canonical)` ↔ `표기별 분리 (surface)` — Authority Control 결과 노출
- 통합 모드 + 변형 ≥2 일 때 expander로 별칭 목록 표시

### 3.3 「인용의 풍경」 ([pages/2_인용의_풍경.py](pages/2_인용의_풍경.py)) — **사용자 채택 디자인**
URL `?entity=author|institution&id=…`. 디폴트 = 동국대학교.

- **좌측 (메인)**: 엔터티 선택(라디오+셀렉트박스) → 헤더 카드 → 필터(유형 multiselect, 자기인용 제외, 표시 노드 수) → **5개 탭**(혼합/학술지/단행본/원전(기타자료)/학자) 각각 ego-network + 표 뷰
- **우측 (사이드)**: 학술지 전체 풍경 정적 KPI — 인용 유형 도넛 + TOP 학술지/원전/학자 미니 막대
- **자기인용 강조**: 별 모양 마커 + 굵은 외곽선 + 빨강 채움
- ego-network 노드 색상 = 인용 유형, 크기 = 인용 횟수

---

## 4. 디렉토리 구조

```
ksip_journal_analysis/
├── CLAUDE.md                         이 문서
├── README.md
├── GEMINI.md                         (Gemini용 컨텍스트, 옛 설계 기준 — 무시)
├── requirements.txt
├── app.py                            ★ 지형도 (Plan A)
├── data_utils.py, visualize.py       (옛 미사용 파일, 어디서도 import 안 됨)
├── KCI_OpenAPI_Key.txt               (.gitignore — 절대 커밋 금지)
├── ksip/                             ★ 순수 Python 패키지 (Streamlit 의존 없음)
│   ├── __init__.py
│   ├── load.py                       papers/authors/keywords long-form 추출 + 클리닝/정규화 적용
│   ├── references.py                 12,887 참고문헌 유형별 슬래시 파서 (legacy fallback)
│   ├── normalize.py                  Authority + load_authority + resolve_person (인물 통합)
│   ├── clean.py                      PUA 제거 / 트레일링 underscore / NFKC
│   ├── institutions.py               parent_institution() — 사전 + 정규식 하이브리드
│   ├── data.py                       parquet 로더 (legacy + KCI 6종)
│   ├── citations.py                  ego-network 집계 (KCI 권위 source) + landscape_stats
│   ├── concepts.py                   개념 탐험기 집계
│   └── kci_api.py                    KCI Open API 클라이언트 (재시도/캐시/rate limit)
├── pages/
│   ├── 1_개념_탐험기.py
│   └── 2_인용의_풍경.py
├── data/
│   ├── raw/                          .xls 3개 + .csv 통합본 (.gitignore)
│   ├── processed/                    parquet (git 포함 — stlite 배포용)
│   │   ├── papers.parquet            논문 메타 (xls 기반)
│   │   ├── authors.parquet           저자 long-form (xls)
│   │   ├── keywords.parquet          키워드 long-form (xls)
│   │   ├── references.parquet        참고문헌 (xls, fallback 전용)
│   │   ├── kci_papers.parquet        ★ KCI 논문 enrichment (FWCI / citation-count / 영문제목)
│   │   ├── kci_authors.parquet       ★ KCI 저자 (영문 저자명 90.2%)
│   │   ├── kci_references.parquet    ★ KCI 참고문헌 (REFARTIID — 권위 source)
│   │   ├── journal_metrics.{parquet,csv}        17년 IF/ZIF 시계열
│   │   ├── journal_change_history.{parquet,csv} 등재 변천사
│   │   └── journal_static_meta.csv              학술지 정적 메타
│   ├── cache/                        ★ KCI API 응답 raw XML (.gitignore)
│   │   ├── articleDetail/            636 파일
│   │   ├── citationDetail/           1 파일
│   │   └── ...
│   └── dictionaries/                 ★ Authority files (git 포함)
│       ├── concepts.yml              학자/학파/개념/원전/인물 (~70 entries)
│       ├── authors.yml               한국·일본·서구 학자 (~45 entries, 모두 verified)
│       ├── journals.yml              한·일·영문 인용 학술지 (~52 entries)
│       └── institutions.yml          기관 alias 예외 (정규식 미해결 케이스만)
├── scripts/
│   ├── build_all.py                  ★ 마스터 빌드 — 4단계 일괄 실행
│   ├── build_data.py                 raw .xls → processed (xls 기반 4종)
│   ├── fetch_journal_metrics.py      KCI citationDetail → 학술지 시계열
│   ├── fetch_articles.py             KCI articleDetail × 636 → cache (5분, resume)
│   ├── parse_articles.py             cache XML → kci_*.parquet
│   └── diagnose_data.py              데이터 품질 진단
├── .streamlit/
│   └── config.toml                   showSidebarNavigation = false
├── .claude/
│   ├── settings.local.json
│   └── launch.json                   preview_start로 실행할 streamlit 설정
└── ksip_jouyrnal_analysis/           (오타 폴더, 빈 .git만 — 무시)
```

---

## 5. 구현 상황 (2026-05-09 기준)

### ✅ 완료
- **데이터 파이프라인** — xls 기반 (`scripts/build_data.py`):
    - `papers.parquet` 636 rows + `기관_부모` + `논문명_원본` 백업
    - `authors.parquet` 654 rows (208 surface, canonical 266/40.7%)
    - `keywords.parquet` 3,089 rows (2,333 surface, canonical 384/12.4%)
    - `references.parquet` 12,887 rows (legacy fallback 전용)
- **KCI Open API 통합 (단계 1-3 완료)** — `scripts/build_all.py`로 일괄 빌드:
    - `journal_metrics.{parquet,csv}` 17년 시계열 (IF/ZIF/SJR/자기인용/즉시성지수)
    - `journal_change_history.{parquet,csv}` 등재 변천 12개 이정표
    - `journal_static_meta.csv` 학술지 정적 메타 (창간/발행/등재상태/홈페이지)
    - **`kci_papers.parquet`** 636 rows (FWCI 96.7%, kci_citation_count 100%, 영문제목 99.8%)
    - **`kci_authors.parquet`** 654 rows (영문 저자명 90.2%)
    - **`kci_references.parquet`** 12,357 rows (cited_artiId/REFARTIID 843건 = 학술지 type 24.7%)
    - 자기인용 KCI 정밀 매칭: 247건 (학술지명 정확 일치)
- **데이터 클리닝 (단계 0.5)**: 논문명 119편 / 키워드 PUA 14건 / 동국대 14변형 → 297편 통합
- **Authority Control**: YAML 사전 + surface 보존 + verified 토글 + `resolve_person()` (concepts.학자 + authors 통합)
- **사전 v3**: concepts.yml 70+, journals.yml 52+, authors.yml 45+(모두 verified), institutions.yml 예외만
- **3개 화면 Streamlit 대시보드** (Plan A: 클릭=이동):
    - 지형도(`app.py`) — 4분할 + 등재 변천 12개 이정표 vertical line overlay
    - 개념 탐험기(`pages/1_개념_탐험기.py`) — 4분할 + 통합/분리 토글
    - 인용의 풍경(`pages/2_인용의_풍경.py`) — ego-network (KCI 권위 source) + entity FWCI 4-메트릭 + 우측 IF 시계열 + 학술지 메타 헤더 + cited_artiId hover
- **stlite + GitHub Pages 정적 배포** (gh-pages 브랜치): https://naspatterns.github.io/ksip_journal_analysis/

### ⏸ 진행 예정
1. **사전 보강 라운드 3** (선택): kci_authors의 영문 저자명을 `authors.yml`에 자동 추가 (외국인 인용 매칭 ↑)
2. **시각화 보강** (선택):
    - 「개념 탐험기」 대표 논문 카드 FWCI 정렬 + 영문제목 옵션
    - 「지형도」 ④ 저자 막대 KCI verified 마크 또는 평균 FWCI 색상
    - 「인용의 풍경」 학자 탭에 영문 저자명 부가 표시
3. **단계 4 (선택, ROI 낮음)**: 피인용 데이터 — KCI Open API에 없음. WoS-KJD(학교 구독) 또는 KCI 데이터 신청(서면) 필요.

### 🚫 의도적 비범위
- 공저자 네트워크 (단독저자 97%)
- 주제분야 분포 (단일값 "철학")
- WoS / Crossref / OpenAlex 자료원 (인도철학 커버리지 약함, ROI 낮음)

---

## 6. KCI 데이터 수집 4단계 (요약)

| # | 내용 | 의존 | 상태 |
|---|---|---|---|
| 0 | 로컬 .xls 파싱 → references.parquet | 없음 | ✅ 완료 |
| 1 | KCI Open API 키 신청 + IP 등록 | kci.go.kr | ✅ 완료 |
| 2 | `articleDetail × 636` → REFARTIID + FWCI + 영문메타 + structured refs | 단계 1 키 | ✅ 완료 |
| 3 | `citationDetail` → IF/ZIF/등재 변천 시계열 | 단계 1 키 | ✅ 완료 |
| 4 (선택) | 피인용 데이터 (누가 인도철학을 인용?) — KCI 데이터 신청 또는 WoS-KJD | 별도 신청 | 우선순위 낮음 |

**탐침 결과 사용 가능한 endpoint = 4개**: articleSearch / articleDetail / referenceSearch / citationDetail. `citingArticleSearch`, `authorDetail`, `journalSearch`, `institutionSearch` 등은 모두 "등록되지 않은 서비스".

**핵심 단순화:** 원래 계획은 단계 2(`referenceSearch`) + 단계 3(`articleDetail` for cited papers)로 분리였으나, **`articleDetail` 한 endpoint가 reference list + REFARTIID + cited 논문 메타를 모두 포함**한다는 것이 smoke test에서 발견됨. → 단계 2/3 통합, `referenceSearch`는 무용함이 판명(text-only). `articleDetail × 636`만 호출하면 끝.

엔드포인트: `https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode={code}&key={KEY}&id={artiId}`. 인도철학 학술지 식별자: sereId=001529, ISSN 1226-3230.

---

## 7. 데이터 클리닝 (단계 0.5)

원본 데이터의 명백한 오류만 정리. Authority Control(정규화)과는 다른 층:

| 항목 | 처리 | 모듈 |
|---|---|---|
| 논문명 PUA 문자, 트레일링 `_` | `clean_title()` | `ksip/clean.py` |
| 키워드 PUA 문자, NFKC 정규화 | `clean_keyword()` | `ksip/clean.py` |
| 기관 부모 단위 (동국대학교 14변형 → 297편) | `parent_institution()` (정규식 `^.+?대학교\b` + `institutions.yml` alias) | `ksip/institutions.py` |
| ego-network 노드 노이즈 (`http:` 등 URL 조각) | `_is_noise_title()` | `ksip/citations.py` |

원본은 항상 백업: `논문명_원본` + `주저자 소속기관`(surface) + `기관_부모`(canonical) 둘 다 보존.

**참고문헌 권위 source 전환 (2026-05-09)**: 슬래시 텍스트 파싱 기반 `references.parquet`(.xls) 12,887건 → KCI articleDetail 기반 `kci_references.parquet` 12,357건으로 전환. 530건 차이는 .xls 파서의 false positive로 추정. KCI 기반은 구조화 + REFARTIID 보유로 정밀 자기인용/그래프 매칭 가능. legacy 파일은 KCI 미빌드 환경의 fallback으로만 사용.

---

## 8. Authority Control (정규화) 시스템

**원칙: 통일하지 않고 인식만 한다.** Surface form은 절대 덮어쓰지 않고, `canonical_id` 컬럼을 별도로 추가해 그루핑 키로 사용. UI는 토글로 통합/분리 모드를 선택할 수 있게 함.

### 사전 4종
- `concepts.yml` — 학자(고전), 학파, 개념, 원전, 인물 (예: 다르마키르티, 유가행파, 공성, 瑜伽師地論, 간디)
- `authors.yml` — 현대 학자 (한국 + 일본 + 서구 인도학자: 정승석, 桂紹隆, Schmithausen, Olivelle 등)
- `journals.yml` — 인용 학술지 (印度学仏教学研究 표기 변형 통합 등)
- `institutions.yml` — 기관 예외 alias (정규식 `^.+?대학교\b` 가 못 잡는 약칭만)

**KCI 영문 저자명 보강 (선택)**: `kci_authors.parquet`에 영문 저자명이 90.2%(590/654) 있어, `authors.yml`의 surface_forms에 자동 추가 가능. 외국인 인용 측 매칭 정확도를 높이는 데 유용 (e.g., `이길산` ↔ `GIL-SAN LEE`).

### 사전 스키마 (YAML)

```yaml
- canonical_id: dharmakirti          # snake_case ASCII 안정 키
  canonical_kr: 다르마키르티           # 화면 디폴트
  canonical_iast: Dharmakīrti
  canonical_zh: 法稱
  type: 학자                          # 학자/학파/개념/원전/문헌/인물
  era: 7세기
  surface_forms:                      # 데이터에 등장 가능한 모든 변형
    - 다르마키르티
    - 다르마끼르띠
    - Dharmakīrti
    - 法稱
  verified: true                      # 수동 승인 = 분석에 사용
  notes: "..."                        # 콜론 들어가면 따옴표 필수
```

### 사용 흐름

```python
from ksip.normalize import add_canonical_column, coverage_report, resolve_person

# 사전별 정규화 적용
df_norm = add_canonical_column(df, "키워드_원본", "concepts")

# 인물 통합 해상도 (concepts.학자 + authors 모두 봄)
canonical_id, display = resolve_person("世親")  # → ("concepts:vasubandhu", "세친")

# 통합 vs 분리 집계
df_norm.groupby("canonical_id").size()        # 통합
df_norm.groupby("키워드_원본").size()          # 분리

# 미해상도 빈도 — 사전 보강 우선순위
report = coverage_report(df, "키워드_원본", "concepts")
report["unresolved_top"]
```

`load_authority(name, include_unverified=True)` 로 후보까지 로드 가능. `lru_cache` 메모리 캐시.

---

## 9. 명령어 참고

```bash
# ★ 마스터 빌드 — raw + KCI API 모두 일괄 (다른 환경에서도 이거 하나면 끝)
.venv/bin/python scripts/build_all.py
#   --skip-api       : KCI API 단계 건너뛰기 (캐시·기존 parquet만 사용)
#   --only 1 --only 4: 특정 단계만 실행

# 개별 단계
.venv/bin/python scripts/build_data.py             # xls → 4 parquet
.venv/bin/python scripts/fetch_journal_metrics.py  # KCI citationDetail (1 호출)
.venv/bin/python scripts/fetch_articles.py         # KCI articleDetail × 636 (캐시 시 즉시)
.venv/bin/python scripts/parse_articles.py         # cache → kci_*.parquet

# 데이터 품질 진단 (사전 보강 우선순위 확인)
.venv/bin/python scripts/diagnose_data.py

# Streamlit 실행
.venv/bin/python -m streamlit run app.py

# 패키지 설치 (pip 래퍼가 깨졌으니 python -m pip 사용)
.venv/bin/python -m pip install <pkg>

# 공인 IP 조회 (KCI API 키 IP 갱신 시)
curl -s https://api.ipify.org
```

---

## 10. 환경적 함정

### 10.1 venv 깨진 상태
폴더 이동 이력(`철학+디지털인문학` → `DigitalHumanities`, `인도철학_학회지분석` → `ksip_journal_analysis`) 으로 `.venv/bin/pip` 등 래퍼 스크립트가 옛 경로를 하드코딩. **`.venv/bin/python -m pip`** 로 우회. `streamlit` 도 마찬가지: `.venv/bin/python -m streamlit run app.py`.

깨끗한 정리:
```bash
rm -rf .venv && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
```

### 10.2 .gitignore
- 원본 데이터(`*.csv`, `*.xls(x)`)는 모두 git 제외
- `data/dictionaries/*.yml` 은 git 포함 (분석 결과물)
- `data/processed/*.parquet` 은 git 포함 (총 2.5MB, Streamlit Cloud 배포 시 raw 없이 cold start 가능)
- `.streamlit/config.toml` 은 git 포함, `secrets.toml` 만 제외

### 10.3 한글 폰트
시각화 시 macOS 는 `AppleGothic` / `AppleSDGothicNeo`, Linux 는 `NanumGothic` 등 명시 필요.

### 10.4 GitHub
리포 이름: `naspatterns/ksip_journal_analysis` (옛 이름 `-_-`에서 변경 완료).

### 10.5 Streamlit 자동 사이드바 네비
`.streamlit/config.toml`에 `showSidebarNavigation = false` 로 비활성화. 한글 페이지명 + 명시적 `st.page_link()` 가 자동 nav 보다 깔끔.

### 10.6 Plotly selection 잔존
Streamlit의 `st.plotly_chart(on_select="rerun")` 은 selection 상태가 리렌더 시 재트리거될 수 있음. `treemap_last_sig` 같은 시그니처 추적 + 초기화 시 chart key 정리 필요.

---

## 11. 인터랙션 디자인 컨벤션 (Plan A)

- **클릭 = 그 항목의 상세 화면으로 이동** (cross-filter 아님)
    - 기관 트리맵 셀 클릭 → 인용의 풍경(기관)
    - 저자 막대 클릭 → 인용의 풍경(저자)
    - 키워드 셀렉터 → 개념 탐험기
- **연도 슬라이더**: 지형도에서만 가역적 글로벌 필터
- **표기 토글**: 모든 집계는 `통합 (canonical)` / `표기별 분리 (surface)` 토글 (Authority Control 노출)
- **사이드바 패턴**: 서브 페이지는 "← 🗺️ 지형도로 돌아가기" 강조 + 자기 자신 제외한 다른 화면 링크
- **디폴트 엔터티**: 인용의 풍경 = 동국대학교, 개념 탐험기 = 다르마키르티
- **자기인용 강조**: 별 모양 마커 + 굵은 외곽선 + 빨강 채움 (ego-network)

---

## 12. 무엇을 하지 말 것

- ❌ 공저자 네트워크 (데이터에 거의 없음)
- ❌ 주제분야 분포 (단일값)
- ❌ surface form을 덮어쓰는 정규화 (canonical_id 컬럼만 추가)
- ❌ verified=false 사전을 분석에 자동 적용 (사용자 검증 후 승급)
- ❌ `.venv/bin/pip` / `.venv/bin/streamlit` 직접 호출 (깨짐, `python -m` 사용)
- ❌ 옛 `data_utils.py / visualize.py` 의 함수 import (폐기 코드, 어디서도 안 씀)
- ❌ `pages/__init__.py` 생성 (Streamlit 페이지 자동 디스커버리 깨짐)
- ❌ Crossref/OpenAlex/RISS/DBpia API 시도 (인도철학 커버리지 약함, 검증 완료)
- ❌ KCI `referenceSearch` endpoint 사용 (text-only, REFARTIID 없음 — `articleDetail`이 권위 source)
- ❌ KCI API 키 / `data/cache/` git 커밋 (.gitignore에 등록됨)
- ❌ Streamlit 페이지에서 KCI API 직접 호출 (CORS/키 노출 — 빌드 단계에서만 호출, parquet에 저장)
