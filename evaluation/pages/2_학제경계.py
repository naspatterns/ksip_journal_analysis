"""축 6 — 학제 경계: 인도철학 vs 동아시아 불교 vs 티베트 불교."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="학제 경계", page_icon="🧭", layout="wide")

st.title("🧭 축 6 — 학제 경계")
st.caption("인도철학 vs 동아시아 불교 vs 티베트 불교 — `reception_horizon` 으로 분리")

st.info(
    "🔨 **TODO** — 라벨링 파이프라인 완료 후 다음을 시각화:\n\n"
    "1. `reception_horizon` 도넛 (india / east_asia / tibet / korea / west)\n"
    "2. 시간 추이: 동아시아·티베트 비중 변화\n"
    "3. 인도(reception=india) 안에서 primary_source_basis 분포 — 한역·티베트역 자료 기반 인도 사상 연구의 비율 (Decision-18 후 paper-level)\n"
    "4. 경계 사례 표 — 인도/동아시아 모호 논문 수동 검토 대상"
)
