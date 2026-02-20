"""Dashboard configuration constants."""
from typing import Final

# ============================================================
# Chart Configuration
# ============================================================

CHART_HEIGHT: Final[int] = 400

CHART_COLORS: Final[list[str]] = [
    '#F3A950',  # Orange (Primary)
    '#E25454',  # Red
    '#404040',  # Dark Gray
    '#FFD559',  # Gold
    '#240F33',  # Dark Purple
    '#EB8149',  # Deep Orange
    '#7F7F7F',  # Medium Gray
    '#0D0D0D',  # Near Black
    '#D9D9D9',  # Light Gray
    '#262626',  # Darker Gray
]

# ============================================================
# Analysis Configuration
# ============================================================

MAX_LAG_MONTHS: Final[int] = 24
MIN_SAMPLES_FOR_CORRELATION: Final[int] = 3

# ============================================================
# Data Transform Options
# ============================================================

TRANSFORM_OPTIONS: Final[list[str]] = [
    "Raw Data",
    "Indexed (Base=100)",
    "MoM",
    "QoQ",
    "YoY",
]

TRANSFORM_LABELS: Final[dict[str, str]] = {
    "MoM": "MoM",
    "QoQ": "QoQ",
    "YoY": "YoY",
    "Indexed (Base=100)": "Index",
}

# ============================================================
# Category Configuration
# ============================================================

DEFAULT_CATEGORIES: Final[list[str]] = [
    "Rates", "Inflation", "Employment", "Activity", "Other"
]

# ============================================================
# Data Source Information
# ============================================================

DATA_SOURCES: Final[list[str]] = ["FRED", "ECOS", "BLS"]

# ============================================================
# Chart Type & Layout Options
# ============================================================

CHART_TYPE_OPTIONS: Final[list[str]] = ["Line", "Line + Marker", "Bar"]

LAYOUT_OPTIONS: Final[list[str]] = ["1 Column", "2 Columns", "3 Columns"]

LAYOUT_COLS_MAP: Final[dict[str, int]] = {
    "1 Column": 1,
    "2 Columns": 2,
    "3 Columns": 3,
}

# ============================================================
# Migration Mappings (Korean -> English)
# ============================================================

KOREAN_TO_ENGLISH_TRANSFORMS: Final[dict[str, str]] = {
    "원 데이터": "Raw Data",
    "지수화 (기준=100)": "Indexed (Base=100)",
    "MoM (전월 대비)": "MoM",
    "QoQ (전분기 대비)": "QoQ",
    "YoY (전년 동기 대비)": "YoY",
}

KOREAN_TO_ENGLISH_CHART_TYPES: Final[dict[str, str]] = {
    "라인": "Line",
    "라인+마커": "Line + Marker",
    "막대": "Bar",
}

KOREAN_TO_ENGLISH_CATEGORIES: Final[dict[str, str]] = {
    "금리": "Rates",
    "물가": "Inflation",
    "고용": "Employment",
    "경기": "Activity",
    "기타": "Other",
    "심리": "Sentiment",
    "통화": "Money Supply",
    "환율": "FX",
    "무역": "Trade",
    "실업": "Unemployment",
    "JOLTS": "JOLTS",
    "임금": "Wages",
    "생산성": "Productivity",
    "생산자물가": "PPI",
}
