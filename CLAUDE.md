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
├── ksip/                             ★ 순수 Python 패키지 (Streamlit 의존 없음)
│   ├── __init__.py
│   ├── load.py                       papers/authors/keywords long-form 추출 + 클리닝/정규화 적용
│   ├── references.py                 12,887 참고문헌 유형별 슬래시 파서
│   ├── normalize.py                  Authority + load_authority + resolve_person (인물 통합)
│   ├── clean.py                      PUA 제거 / 트레일링 underscore / NFKC
│   ├── institutions.py               parent_institution() — 사전 + 정규식 하이브리드
│   ├── data.py                       parquet 로더 + Filter (Streamlit 페이지가 사용)
│   ├── citations.py                  ego-network 집계 + landscape_stats
│   └── concepts.py                   개념 탐험기 집계(시계열/공출현/저자/대표논문)
├── pages/
│   ├── 1_개념_탐험기.py
│   └── 2_인용의_풍경.py
├── data/
│   ├── raw/                          .xls 3개 + .csv 통합본 (.gitignore)
│   ├── processed/                    parquet 4개 (git 포함, build_data.py 산출물 — 배포용)
│   └── dictionaries/                 ★ Authority files (git 포함)
│       ├── concepts.yml              학자/학파/개념/원전/인물 (~70 entries)
│       ├── authors.yml               한국·일본·서구 학자 (~45 entries, 모두 verified)
│       ├── journals.yml              한·일·영문 인용 학술지 (~52 entries)
│       └── institutions.yml          기관 alias 예외 (정규식 미해결 케이스만)
├── scripts/
│   ├── build_data.py                 raw → processed 빌드 (재실행 가능)
│   └── diagnose_data.py              데이터 품질 진단 (어디 클리닝 필요한지 점검)
├── .streamlit/
│   └── config.toml                   showSidebarNavigation = false
├── .claude/
│   ├── settings.local.json
│   └── launch.json                   preview_start로 실행할 streamlit 설정
└── ksip_jouyrnal_analysis/           (오타 폴더, 빈 .git만 — 무시)
```

---

## 5. 구현 상황 (2026-04-27 기준)

### ✅ 완료
- **데이터 파이프라인** (`scripts/build_data.py`):
    - `papers.parquet` 636 rows + `기관_부모` 컬럼 + `논문명_원본` 백업
    - `authors.parquet` 654 rows (208 unique surface, canonical **266건/40.7%**)
    - `keywords.parquet` 3,089 rows (2,333 unique, canonical **384건/12.4%**)
    - `references.parquet` 12,887 rows (학술지 canonical **1,546건/53.9%**, 자기인용 312건/2.4%)
- **데이터 클리닝 (단계 0.5)**: 논문명 119편 / 키워드 PUA 14건 / 동국대 14변형 → 297편 통합
- **Authority Control**: YAML 사전 + surface 보존 + verified 토글 + `resolve_person()` (concepts.학자 + authors 통합)
- **사전 v3**: concepts.yml 70+, journals.yml 52+, authors.yml 45+(모두 verified), institutions.yml 예외만
- **3개 화면 Streamlit 대시보드** (Plan A: 클릭=이동):
    - 지형도(`app.py`) — 4분할 + 클릭으로 다른 화면 진입
    - 개념 탐험기(`pages/1_개념_탐험기.py`) — 4분할 + 통합/분리 토글
    - 인용의 풍경(`pages/2_인용의_풍경.py`) — ego-network 5탭 + 우측 정적 풍경
- **UI 개선**: 자기인용 별 모양 강조, http: 노이즈 제거, 도넛 라벨 자동, 사이드바 중복 제거

### ⏸ 진행 예정
1. **CLAUDE.md / README.md 마무리** (문서 정리)
2. **KCI Open API 키 신청** (사용자 액션, 안정 환경 이동 후 — 5분, 자동 승인): `https://www.kci.go.kr` 회원가입 → 데이터 → OPEN API → 인증키. 공인 IP 필요(`curl -s https://api.ipify.org`).
3. **단계 2: REFARTIID 보강** (API 키 도착 후): 482편 artiId로 `referenceSearch` 호출 → `REFARTIID` 추출 → 정확한 인용 그래프 엣지 patch.
4. **단계 3: 학술지 메타**: `citationDetail`로 IF/ZIF/자기인용비율 시계열 → 헤더 KPI.
5. **추가 사전 보강** (롱테일): 쫑카파, 하타 요가, Frauwallner, Mallinson, 眞諦 등 미해상도 빈도 높은 항목.

### 🚫 의도적 비범위
- 공저자 네트워크 (단독저자 97%)
- 주제분야 분포 (단일값 "철학")
- WoS / Crossref / OpenAlex 자료원 (인도철학 커버리지 약함, ROI 낮음)

---

## 6. KCI 데이터 수집 4단계 (요약)

| # | 내용 | 의존 | 상태 |
|---|---|---|---|
| 0 | 로컬 .xls 파싱 → references.parquet | 없음 | ✅ 완료 |
| 1 | KCI Open API 키 신청 (사용자) | kci.go.kr 회원가입, 공인 IP | ⏸ 대기 (1주일 ETA) |
| 2 | `referenceSearch` → REFARTIID 매칭 | 단계 1 키 | ⏸ |
| 3 | `citationDetail` → IF/ZIF 시계열 | 단계 1 키 | ⏸ |
| 4 (선택) | 피인용 데이터 (KCI 데이터 신청 또는 WoS KJD) | 별도 신청 | 우선순위 낮음 |

**핵심 발견:** `referenceSearch` 응답에 `REFARTIID` 필드가 있어, 인용된 논문이 KCI 등재면 텍스트 매칭 없이 정확한 그래프 엣지 구축 가능. 엔드포인트: `https://open.kci.go.kr/po/openapi/openApiSearch.kci?apiCode=referenceSearch&key={KEY}&id={artiId}`. 인도철학 학술지 식별자: sereId=001529, ISSN 1226-3230.

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

---

## 8. Authority Control (정규화) 시스템

**원칙: 통일하지 않고 인식만 한다.** Surface form은 절대 덮어쓰지 않고, `canonical_id` 컬럼을 별도로 추가해 그루핑 키로 사용. UI는 토글로 통합/분리 모드를 선택할 수 있게 함.

### 사전 4종
- `concepts.yml` — 학자(고전), 학파, 개념, 원전, 인물 (예: 다르마키르티, 유가행파, 공성, 瑜伽師地論, 간디)
- `authors.yml` — 현대 학자 (한국 + 일본 + 서구 인도학자: 정승석, 桂紹隆, Schmithausen, Olivelle 등)
- `journals.yml` — 인용 학술지 (印度学仏教学研究 표기 변형 통합 등)
- `institutions.yml` — 기관 예외 alias (정규식 `^.+?대학교\b` 가 못 잡는 약칭만)

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
# 데이터 빌드 (raw → processed parquet 재생성)
.venv/bin/python scripts/build_data.py

# 데이터 품질 진단 (사전 보강 우선순위 확인)
.venv/bin/python scripts/diagnose_data.py

# Streamlit 실행
.venv/bin/python -m streamlit run app.py

# 패키지 설치 (pip 래퍼가 깨졌으니 python -m pip 사용)
.venv/bin/python -m pip install <pkg>

# 공인 IP 조회 (KCI API 키 신청 시)
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
- ❌ 인접 학술지를 자의적으로 선정 (반드시 사용자 사전 문의 — 평가 프로젝트 운영 규칙)

---

## 13. evaluation/ — 학술지 평가 서브프로젝트

기존 대시보드와 분리된 별도 Streamlit 프로젝트 (`evaluation/`). 학술지를 8개 축으로 통합 평가. **이 폴더에 처음 들어오면 `evaluation/README.md` → `evaluation/docs/PIPELINE.md` 순서로 읽을 것.**

### 13.1 진행 단계

| Phase | 내용 | 상태 |
|---|---|---|
| 0. 분류 체계 설계 | 8축 합의 + 17개 세부 결정 (다중라벨, 4축 직교: school × era × source_language × reception_horizon) | ✅ |
| 1. 사전 스키마 확장 | `concepts.yml` 의 69 entry 에 신규 4필드 backfill. 옛 free-form `era` → `century` rename | ✅ |
| 2. 키워드 등장 빈도 감사 | 후보 ~85개를 keywords/제목에서 substring 매칭 → INCLUDE/MARGINAL/SKIP 판정 | ✅ |
| 3. 신규 27 entry 추가 (Q1c·Q2c·Q3 contextual). entry 69 → 96, 커버리지 12.4% → 14.3% | ✅ |
| 4. 라벨링 파이프라인 (사전 1차 → BERTopic → contextual disambiguation → 다수결 집계) | 🚫 |
| 5. 검수 표본 (랜덤 50 + 신뢰도 하위 50) | 🚫 |
| 6. Streamlit 시각화 (커버리지 streamgraph + entropy / 학제경계 reception 비율) | 🚫 |

### 13.2 핵심 결정 (전체는 `evaluation/docs/DECISIONS.md`)

- **4축 직교 라벨**: `school` (사상 학파) × `era` (시대 bucket) × `source_language` (자료 언어) × `reception_horizon` (다뤄진 지평).
- **축 6 측정 정의**: `reception_horizon == "india"` 비율 = "인도철학 비중". 한역·티베트역 자료라도 사상 *원천* 이 인도면 india.
- **다중 라벨**: 주 1 + 부 N.
- **yoga era 필수**: classical / post_classical (하타) / modern.
- **chan 3국 통합** (지역은 reception 으로 구분), **nyaya/vaisheshika/pramana 별도**, **vedanta 단일**.
- **Q1 (구마라집)**: `school=madhyamaka, reception=east_asia`.
- **Q2 (대승기신론)**: `school=east_asian_other`.
- **Q3 (법화경류 모호 텍스트)**: 사전 단정 회피 → 공출현 키워드 contextual rule 로 Phase 4 에서 처리.
- **신규 entry 추가 원칙**: 키워드 감사에서 빈도 ≥ 1 인 것만. 親鸞·道元·空海·법장·혜능 등 빈도 0 후보는 제외.

### 13.3 산출 데이터

- `data/dictionaries/concepts.yml` — 신규 4필드 (school/era/source_language/reception_horizon) + 옛 era → century rename. (전체 본 프로젝트가 공유)
- `evaluation/output/keyword_audit.csv` — 키워드 등장 빈도 감사 결과 (멱등 재실행 가능)

### 13.4 운영 규칙

- 인접 학술지 비교 시 **반드시 사용자 사전 문의**. 자의적 선정 금지.
- 라벨링 정확도 목표 80% → 시각화 → 시간 남으면 환류.
- 모호 텍스트의 학파는 사전이 아닌 라벨링 파이프라인에서 contextual 결정.
- ruamel.yaml 의존 (`backfill_concepts_metadata.py`).
- evaluation/ 의 변경이 기존 대시보드 코드를 깨지 않음 (사전 신규 필드는 `extras` 로 흘러들어가 무시됨).
