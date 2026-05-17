"""축 1 — 커버리지: 인도철학 학술지가 인도철학 전 분야를 고루 다루는가."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="커버리지", page_icon="🗺️", layout="wide")

st.title("🗺️ 축 1 — 커버리지")
st.caption("인도철학 학술지가 인도철학 전 분야를 고루 다루는가, 편중되어 있는가")

st.info(
    "🔨 **TODO** — 라벨링 파이프라인 완료 후 다음을 시각화:\n\n"
    "1. 학파 × 시기 streamgraph (5년 버킷, 주 라벨 기준)\n"
    "2. Shannon entropy 시계열 — 학술지 다양성의 시간 추세\n"
    "3. Gini / HHI 부 지표\n"
    "4. 학파별 누적 논문 수 + TOP 키워드"
)
