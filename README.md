# 인도철학 학술지 분석 대시보드

학술지 `<인도철학>`(KCI 등재, 인도철학회) 의 1989–2025년 서지 데이터 **636편** 을 분석하는 Streamlit 대시보드. 2026-1학기 디지털 인문학 수업 과제.

**목표는 *연구 영감*** — 사용자가 거시적 풍경 → 개념 탐험 → 인용 네트워크 순서로 들어가며 논문 주제를 발굴할 수 있는 도구.

---

## 3개 화면 (Plan A: 클릭 = 그 항목의 상세로 이동)

### 🗺️ [학술지 지형도](app.py) — 메인
- 연도 슬라이더 1개만 글로벌 필터.
- 4분할: 연도별 논문 수 라인 / 기관 트리맵(클릭→인용의 풍경) / 키워드 워드클라우드+셀렉터(→개념 탐험기) / 저자 TOP 20 막대(클릭→인용의 풍경).

### 🔍 [개념 탐험기](pages/1_개념_탐험기.py)
URL `?keyword=…` 진입. 시계열 빈도 / 공출현 키워드 TOP 10 / 저자 TOP 10 / 대표 논문 카드. **표기 변형 토글** 로 통합(canonical) ↔ 표기별 분리(surface) 비교.

### 📚 [인용의 풍경](pages/2_인용의_풍경.py)
URL `?entity=author|institution&id=…` 진입 (디폴트=동국대학교). 5개 탭(혼합/학술지/단행본/원전/학자) ego-network + 우측 학술지 전체 풍경. **자기인용은 별 모양 마커 + 빨강 외곽선** 으로 강조.

---

## 데이터

| 항목 | 값 |
|---|---|
| 논문 수 | 636편 (1989–2025, 37년) |
| 단독저자 비율 | 97.3% |
| 동국대 비율 | 44% (297편 family rollup) |
| 키워드 surface unique | 2,333개 |
| 참고문헌 (KCI 권위) | 12,357건 + REFARTIID 843건 |
| 학술지 IF/ZIF 시계열 | 17년 (2008–2024) |
| Authority canonical | 저자 40.7% / 키워드 12.4% / 학술지 53.9% |

**두 source 통합:**
- 로컬 .xls 3개 → 논문 메타·저자·키워드·참고문헌 fallback
- KCI Open API (`articleDetail`/`citationDetail`) → REFARTIID 정밀 인용 그래프, FWCI/피인용수, 영문 저자명, 학술지 시계열 + 등재 변천사

원본 .xls 는 `data/raw/` 에 (.gitignore). 빌드 산출물 parquet은 모두 `data/processed/` 에 git 포함 (배포용). KCI API 응답 raw XML 캐시는 `data/cache/` 에 (.gitignore).

자세한 데이터 노트와 의도적 비범위는 [CLAUDE.md](CLAUDE.md) 참조. KCI API 활용은 [docs/kci_api_overview.md](docs/kci_api_overview.md) + [docs/kci_api_workflow.md](docs/kci_api_workflow.md) 참조.

---

## 기술 스택

- **프레임워크**: Streamlit
- **분석**: pandas, pyarrow
- **시각화**: Plotly · WordCloud · NetworkX · matplotlib
- **데이터**: parquet (빌드 산출물), YAML (Authority 사전 4종)

---

## 로컬 실행

```bash
# 1. 가상환경 + 패키지
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2. (선택) 빌드 재실행 — raw .xls + KCI API 모두 일괄
.venv/bin/python scripts/build_all.py
#   --skip-api : KCI API 단계 건너뛰기 (캐시·기존 parquet만 사용)
#   --only 1   : 특정 단계만

# 3. 대시보드
.venv/bin/python -m streamlit run app.py
```

> ⚠️ `.venv/bin/pip` / `.venv/bin/streamlit` 직접 호출은 폴더 이동 이력으로 깨져 있을 수 있음. 항상 `python -m pip` / `python -m streamlit` 로.

`data/processed/*.parquet` 이 리포에 포함되어 있어 raw + API 키 없이도 대시보드 즉시 실행 가능.

KCI API 키가 있으면 `KCI_OpenAPI_Key.txt` 평문 파일로 루트에 저장 (.gitignore 처리됨). `scripts/build_all.py` 가 자동으로 감지해 단계 2-3을 실행. 키 없으면 자동 skip.

---

## 디렉토리 구조

```
ksip_journal_analysis/
├── app.py                       지형도 (Plan A 메인)
├── pages/                       개념 탐험기 + 인용의 풍경
├── ksip/                        순수 Python 패키지 (Streamlit 의존 X)
│   ├── load.py / clean.py
│   ├── normalize.py             Authority Control + resolve_person
│   ├── institutions.py          parent_institution() 사전+정규식
│   ├── citations.py / concepts.py
│   ├── references.py / data.py
├── data/
│   ├── raw/                     .xls + .csv (.gitignore)
│   ├── processed/               parquet 4종 (git 포함)
│   └── dictionaries/            YAML 4종 (git 포함)
├── scripts/
│   ├── build_data.py            raw → processed 빌드
│   └── diagnose_data.py         데이터 품질 진단
└── .streamlit/config.toml       사이드바 자동 nav 비활성화
```

---

## Authority Control

**원칙: 통일하지 않고 인식만 한다.** Surface form 은 절대 덮어쓰지 않고 `canonical_id` 컬럼만 추가. UI 토글로 통합/분리 모드 비교 가능.

사전 4종 (`data/dictionaries/`):
- `concepts.yml` (~70) — 학자/학파/개념/원전/인물 (다르마키르티, 유가행파, 공성, 瑜伽師地論…)
- `authors.yml` (~45, 모두 verified) — 한국·일본·서구 현대 학자
- `journals.yml` (~52) — 인용 학술지 표기 변형 통합
- `institutions.yml` — 정규식 미해상도 alias 예외만

자세한 스키마/사용 흐름은 [CLAUDE.md §8](CLAUDE.md) 참조.

---

## License & Credit

학술 과제용. 데이터 출처: KCI(Korea Citation Index) 반출본 · 인도철학회.
