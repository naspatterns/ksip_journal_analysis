"""「인도철학」 학술지 평가 프로젝트 — 별도 Streamlit 진입점.

기존 대시보드(`/app.py`)와 분리. 학술지 자체를 8개 축으로 평가하는 워크벤치.
실행: `.venv/bin/python -m streamlit run evaluation/app.py`
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

# ksip 패키지 import 가능하도록 프로젝트 루트를 path에 추가
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="「인도철학」 학술지 평가",
    page_icon="📐",
    layout="wide",
)

st.title("📐 「인도철학」 학술지 평가 워크벤치")
st.caption("1989–2025, 636편 · 8개 축으로 평가 — 디지털 인문학 2026-1")

st.markdown(
    """
이 워크벤치는 학술지 「인도철학」 자체를 **통합적으로 평가** 하는 별도 프로젝트입니다.
기존 대시보드(지형도·개념 탐험기·인용의 풍경) 와 데이터·코드를 공유하지만,
질문의 결이 다르므로 분리되어 있습니다.

### 평가 축

| # | 축 | 핵심 질문 | 단계 |
|---|---|---|---|
| 1 | **커버리지** | 인도철학 전 분야를 고루 다루는가, 편중되어 있는가 | 🔨 진행 중 |
| 6 | **학제 경계** | 인도철학 vs 동아시아 불교 vs 티베트 불교의 경계 | 🔨 진행 중 |
| 2 | 의존도 | 인용 연구의 권역·학파 분포 | ⏸ 다음 |
| 4 | 주도성 | 한국 학계 인도철학을 주도하는가 | ⏸ 후속 |
| 3 | 대표성 | 학자들이 한국 인도철학을 대표하는가 | ⏸ 후속 |
| 5 | 시간 진화 | 36년간 어떻게 변했는가 | ⏸ 종합 |
| 7 | 국제 좌표 | 국내 매체인가 국제 발신구인가 | ⏸ 후속 |
| 8 | 거버넌스 | 닫힌 클럽인가 광장인가 | ⏸ 후속 |

### 분류 체계 (논문당 다중 라벨)

논문 1편당 4개 변수로 라벨링 — 자세한 정의는 [`taxonomy/SCHEMA.md`](taxonomy/SCHEMA.md):

- **`primary_school`** — 다루는 사상의 학파 (유식·중관·베단타·화엄·겔룩 등 13~15개)
- **`era`** — 사상 시대 (베다·고전기·후고전기·근현대 등 6구간)
- **`tradition_language`** — 사상의 원천 언어 (sanskrit·pali·chinese·tibetan) — concept-level
- **`primary_source_basis`** — 일차문헌 기반 (paper-level, references 에서 계산)
- **`secondary_source_horizon`** — 이차문헌 학계 horizon (paper-level, references 에서 계산)
- **`reception_horizon`** — 사상 지평 (india·east_asia·tibet·korea·west)
    - 축 6 의 핵심 변수: `reception_horizon == 'india'` 가 인도철학

### 진행 단계

1. ✅ 폴더 스캐폴딩 + 분류 체계 문서화
2. 🔨 `concepts.yml` 메타필드 확장 + 기존 70+ 엔트리 라벨링
3. ⏸ 동아시아·티베트 종파 사전 신규 추가
4. ⏸ 라벨링 파이프라인 (사전 + BERTopic)
5. ⏸ 검수 표본 100편 추출
6. ⏸ 페이지 1 커버리지 / 페이지 2 학제 경계 시각화

좌측 사이드바에서 페이지를 선택하세요.
"""
)

with st.sidebar:
    st.header("운영 규칙")
    st.markdown(
        """
- 인접 학술지 비교 시 사용자 사전 확인 필수
- 라벨링 정확도 목표: 80%
- 검수 표본: 무작위 50 + 저신뢰 50
- 이 단계 KCI API 미사용
"""
    )
    st.divider()
    st.caption("기존 대시보드는 `streamlit run app.py`")
