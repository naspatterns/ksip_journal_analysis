# GEMINI.md

## 1. Project Overview
- **Project Name:** 인도철학 학술지 데이터 분석 대시보드 구축
- **Objective:** KCI에서 추출한 `<인도철학>` 잡지 논문 데이터를 바탕으로 연구 경향성, 인물망, 주제 변화를 분석하는 인터랙티브 대시보드 제작.
- **Environment:** Python 3.x, Streamlit (Dashboard), Pandas (Data Analysis), Plotly/Seaborn (Visualization).

## 2. Data Source Context
- **Primary Data:** `인도철학_1_300.xls - 논문목록.csv` (KCI 반출 데이터)
- **Key Columns:** `발행연도`, `저자명`, `저자키워드`, `주저자 소속기관`, `논문명`, `인용된 총 횟수` 등.
- **Constraints:**
    - 저자명은 `,` 또는 `;`로 구분된 다중 저자 케이스가 존재함.
    - 데이터 시작 연도(1989년)의 모든 저자는 '신규 저자'로 간주함(주석 표기 필수).
    - 키워드 분석 시 국문/영문/산스크리트어(IAST)가 혼재됨을 고려함.

## 3. Dashboard Structure (Tabs)
### Group 1: 연구 활성도 및 시계열 지표 (Tab 1)
- **Line Charts (Toggle/Tab):**
    - 연도별 논문 게재 수
    - 연도별 총 참여 저자 수
    - **신규 저자 유입 지표:** 신규 저자 수(Bar) + 신규 저자 비율(Line)

### Group 2: 키워드 및 주제 분석 (Tab 2)
- 핵심 키워드 빈도 분석 (Top N Word Cloud & Bar Chart)
- 주요 학파/개념별 시계열 트렌드 변화 (Moving Average 적용)
- 학파별 비중 분류 (Treemap 또는 Pie Chart)

### Group 3: 연구 네트워크 및 영향력 (Tab 3)
- 소속 기관별 연구 분포 (Treemap)
- 공저자 네트워크 (Co-authorship Network)
- 저자-키워드 연결망 (Author-Topic Mapping)

## 4. Technical Instructions
- **Visualization Style:** 깔끔하고 학술적인 스타일 지향 (Seaborn whitegrid 또는 Plotly template).
- **Korean Support:** 시각화 시 한글 폰트(NanumGothic 등) 설정 필수.
- **Code Philosophy:** 함수형 모듈 구조, 데이터 클렌징 로직 포함.

## 5. Specific Rules
- 모든 라인 그래프는 동일 영역 내에서 탭(st.tabs)이나 드롭다운으로 전환 가능하도록 설계.
- 신규 저자 분석 시 `set()` 자료형을 활용하여 연도별 누적 저자 리스트를 관리할 것.