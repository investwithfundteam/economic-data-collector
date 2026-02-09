"""
경제 데이터 통합 대시보드 (멀티페이지)
==========================================

FRED, ECOS, BLS에서 수집한 경제 지표를 
인터랙티브하게 시각화하고 분석할 수 있는 통합 대시보드입니다.

📌 주요 기능:
1. 🏠 메인 화면: 저장된 차트 대시보드
2. 📈 지표별 비교: 크로스 소스 비교 + 세팅 저장
3. ⚙️ 설정: 저장된 세팅 관리

🔧 실행 방법:
streamlit run dashboard.py
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import json
import logging

# 지표 정의 임포트
from indicators.fred_indicators import (
    INDICATOR_CATEGORIES as FRED_CATEGORIES,
    ALL_INDICATORS as FRED_INDICATORS
)
from indicators.ecos_indicators import (
    INDICATOR_CATEGORIES as ECOS_CATEGORIES,
    ALL_INDICATORS as ECOS_INDICATORS
)
from indicators.bls_indicators import (
    INDICATOR_CATEGORIES as BLS_CATEGORIES,
    ALL_INDICATORS as BLS_INDICATORS
)

# 설정 및 유틸리티 임포트
import config
from utils.indicator_filter import (
    filter_hidden_indicators,
    filter_available_in_data,
    get_category_indicators
)
from utils.data_loader import SourceData

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ============================================================
# 🔧 유틸리티 함수
# ============================================================

def get_data_path(source: str) -> Path:
    """데이터 파일 경로를 반환합니다."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    filenames = {
        "FRED": "fred_data.xlsx",
        "ECOS": "ecos_data.xlsx",
        "BLS": "bls_data.xlsx",
    }
    
    return data_dir / filenames.get(source, "data.xlsx")


def get_settings_path() -> Path:
    """세팅 저장 파일 경로를 반환합니다."""
    script_dir = Path(__file__).parent
    return script_dir / "saved_settings.json"


def load_saved_settings() -> dict:
    """저장된 세팅을 불러옵니다."""
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 기본 분류 추가
                if "categories" not in data:
                    data["categories"] = config.DEFAULT_CATEGORIES
                return data
        except FileNotFoundError:
            logger.info(f"Settings file not found: {settings_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in settings file: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error loading settings: {e}")
    
    return {
        "saved_charts": [], 
        "main_layout": [],
        "categories": config.DEFAULT_CATEGORIES
    }


def save_settings(settings: dict):
    """세팅을 저장합니다."""
    settings_path = get_settings_path()
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_source_info():
    """각 소스의 정보를 반환합니다."""
    return {
        "FRED": {"emoji": "🇺🇸", "name": "FRED (미국 연준)", "categories": FRED_CATEGORIES, "indicators": FRED_INDICATORS},
        "ECOS": {"emoji": "🇰🇷", "name": "ECOS (한국은행)", "categories": ECOS_CATEGORIES, "indicators": ECOS_INDICATORS},
        "BLS": {"emoji": "📊", "name": "BLS (미국 노동통계)", "categories": BLS_CATEGORIES, "indicators": BLS_INDICATORS},
    }


def get_korean_name(indicator_code: str, all_indicators: dict) -> str:
    """지표 코드에서 한국어 이름(NSA/SA 포함)을 추출합니다.
    
    예: "CPI 전체 항목 (NSA) (CPI All Items) - 월별" 
        -> "CPI 전체 항목 (NSA)"
    """
    desc = all_indicators.get(indicator_code, indicator_code)
    
    # "(SA)" 또는 "(NSA)" 이후의 영어 부분과 주기 제거
    # 패턴: "한국어 이름 (SA/NSA) (영어 설명) - 주기"
    if "(SA)" in desc:
        # NSA/SA 포함해서 자르기
        idx = desc.find("(SA)") + 4
        return desc[:idx].strip()
    elif "(NSA)" in desc:
        idx = desc.find("(NSA)") + 5
        return desc[:idx].strip()
    elif " (" in desc:
        # SA/NSA 표시가 없으면 첫 괄호 전까지
        return desc.split(" (")[0]
    
    return desc


@st.cache_data(ttl=3600)
def load_all_data() -> dict[str, SourceData]:
    """모든 소스의 데이터를 로드합니다."""
    all_data = {}
    source_info = get_source_info()
    
    for source in config.DATA_SOURCES:
        data_path = get_data_path(source)
        
        if not data_path.exists():
            all_data[source] = SourceData(None, {}, [])
            continue
        
        try:
            xl = pd.ExcelFile(data_path)
            sheet_names = xl.sheet_names
            main_sheet = '전체' if '전체' in sheet_names else sheet_names[0]
            
            df_raw = pd.read_excel(data_path, sheet_name=main_sheet, header=None)
            
            series_ids = df_raw.iloc[0].tolist()
            korean_names = df_raw.iloc[1].tolist()
            
            id_to_name = {}
            for sid, kname in zip(series_ids, korean_names):
                if pd.notna(sid) and str(sid) != 'date':
                    if pd.notna(kname):
                        id_to_name[str(sid)] = str(kname)
            
            df = df_raw.iloc[3:].copy()
            df.columns = series_ids
            df = df.reset_index(drop=True)
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])
                df = df.sort_values('date')
            
            categories = [s for s in sheet_names if s != '전체']
            all_data[source] = SourceData(df, id_to_name, categories)
            
        except FileNotFoundError:
            logger.warning(f"Data file not found for {source}: {data_path}")
            all_data[source] = SourceData(None, {}, [])
        except Exception as e:
            logger.error(f"Error loading data for {source}: {e}")
            all_data[source] = SourceData(None, {}, [])
    
    return all_data


def transform_series(series, transform_mode):
    """개별 시리즈에 변환을 적용합니다."""
    if transform_mode == "원 데이터":
        return series
    elif transform_mode == "지수화 (기준=100)":
        first_valid = series.dropna().iloc[0] if not series.dropna().empty else 1
        if first_valid != 0:
            return (series / first_valid) * 100
        return series
    elif transform_mode == "MoM (전월 대비)":
        return series.pct_change(periods=1) * 100
    elif transform_mode == "QoQ (전분기 대비)":
        return series.pct_change(periods=3) * 100
    elif transform_mode == "YoY (전년 동기 대비)":
        return series.pct_change(periods=12) * 100
    return series


def calculate_change(series):
    """전월 대비 변화율을 계산합니다."""
    if len(series.dropna()) < 2:
        return None
    
    valid_values = series.dropna().iloc[-2:]
    if len(valid_values) < 2:
        return None
    
    prev_val = valid_values.iloc[0]
    curr_val = valid_values.iloc[1]
    
    if prev_val == 0:
        return None
    
    return ((curr_val - prev_val) / abs(prev_val)) * 100


def calculate_correlation(series1, series2):
    """두 시계열 간의 상관계수를 계산합니다."""
    combined = pd.concat([series1, series2], axis=1).dropna()
    if len(combined) < 3:
        return None
    return combined.iloc[:, 0].corr(combined.iloc[:, 1])


def find_optimal_lag(series1, series2, max_lag=config.MAX_LAG_MONTHS):
    """최적의 시차를 찾습니다."""
    correlations = []
    
    for lag in range(-max_lag, max_lag + 1):
        shifted = series2.shift(lag)
        corr = calculate_correlation(series1, shifted)
        correlations.append({
            'lag': lag,
            'correlation': corr if corr is not None else 0
        })
    
    valid_corrs = [c for c in correlations if c['correlation'] is not None]
    if not valid_corrs:
        return correlations, 0, 0
    
    best = max(valid_corrs, key=lambda x: abs(x['correlation']))
    return correlations, best['lag'], best['correlation']


# ============================================================
# 📊 차트 생성 함수
# ============================================================

def create_chart(indicator_settings, merged_df, separate_yaxis=True, height=config.CHART_HEIGHT):
    """통합 차트를 생성합니다."""
    colors = config.CHART_COLORS
    
    fig = go.Figure()
    
    for i, (display_key, settings) in enumerate(indicator_settings.items()):
        if display_key not in merged_df.columns:
            continue
        
        source = settings['source']
        name = settings['name']
        shift_val = settings.get('shift', 0)
        chart_type = settings.get('chart_type', '라인')
        transform = settings.get('transform', '원 데이터')
        
        # 범례 이름 생성 (변환 유형 포함)
        legend_name = f"[{source}] {name}"
        
        # 변환 유형 추가
        if transform in config.TRANSFORM_LABELS:
            legend_name += f"({config.TRANSFORM_LABELS[transform]})"
        
        # 시차 추가
        if shift_val != 0:
            direction = "선행" if shift_val < 0 else "후행"
            legend_name += f" ({abs(shift_val)}개월 {direction})"
        
        color = colors[i % len(colors)]
        
        valid_data = merged_df[['date', display_key]].dropna()
        
        if valid_data.empty:
            continue
        
        plot_dates = valid_data['date']
        if shift_val != 0:
            plot_dates = valid_data['date'] + pd.DateOffset(months=shift_val)
        
        yaxis_name = f'y{i+1}' if separate_yaxis and i > 0 else 'y'
        
        if chart_type == "막대":
            fig.add_trace(go.Bar(
                x=plot_dates,
                y=valid_data[display_key],
                name=legend_name,
                marker=dict(color=color),
                hovertemplate=f"<b>{legend_name}</b><br>" +
                              "날짜: %{x|%Y-%m-%d}<br>" +
                              "값: %{y:,.2f}<extra></extra>"
            ))
        else:
            mode = 'lines+markers' if chart_type == "라인+마커" else 'lines'
            marker_cfg = dict(size=4, color=color) if chart_type == "라인+마커" else None
            fig.add_trace(go.Scatter(
                x=plot_dates,
                y=valid_data[display_key],
                mode=mode,
                name=legend_name,
                line=dict(width=2.5, color=color),
                marker=marker_cfg,
                yaxis=yaxis_name,
                hovertemplate=f"<b>{legend_name}</b><br>" +
                              "날짜: %{x|%Y-%m-%d}<br>" +
                              "값: %{y:,.2f}<extra></extra>"
            ))
    
    layout_config = dict(
        height=height,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=50, r=50, t=60, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            autorange=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        hovermode='x unified',
        dragmode='pan',  # 드래그로 팬, 스크롤로 줌
    )

    # 첫 번째 지표의 축 설정 적용 (단일 Y축 모드 포함)
    first_settings = next(iter(indicator_settings.values()), {})
    if first_settings.get('reverse'):
        layout_config['yaxis']['autorange'] = 'reversed'
    if first_settings.get('log_scale'):
        layout_config['yaxis']['type'] = 'log'

    # 다중 Y축 설정
    if separate_yaxis and len(indicator_settings) > 1:
        for i, (display_key, settings) in enumerate(indicator_settings.items()):
            if i == 0:
                layout_config['yaxis']['title'] = dict(
                    text=settings['name'][:15],
                    font=dict(color=colors[0])
                )
                layout_config['yaxis']['tickfont'] = dict(color=colors[0])
            else:
                axis_name = f'yaxis{i+1}'
                axis_config = dict(
                    title=dict(
                        text=settings['name'][:15],
                        font=dict(color=colors[i % len(colors)])
                    ),
                    tickfont=dict(color=colors[i % len(colors)]),
                    overlaying='y',
                    side='right' if i % 2 == 1 else 'left',
                    showgrid=False,
                )
                if settings.get('reverse'):
                    axis_config['autorange'] = 'reversed'
                if settings.get('log_scale'):
                    axis_config['type'] = 'log'
                layout_config[axis_name] = axis_config
    
    fig.update_layout(**layout_config)
    return fig


# ============================================================
# 🏠 메인 화면
# ============================================================

def render_main_page(all_data, source_info):
    """메인 화면을 렌더링합니다."""
    st.header("메인 대시보드")
    
    settings = load_saved_settings()
    saved_charts = settings.get("saved_charts", [])
    main_layout = settings.get("main_layout", [])
    
    if not saved_charts:
        st.info("""
        📌 **저장된 차트가 없습니다.**
        
        1. 왼쪽 메뉴에서 **📈 지표별 비교**를 선택하세요
        2. 원하는 지표를 선택하고 분석하세요
        3. **📌 세팅 저장** 버튼을 클릭하여 저장하세요
        4. 메인 화면에서 저장된 차트를 확인하세요
        """)
        return
    
    # 분류 및 레이아웃 옵션
    # 사용 가능한 분류 목록
    all_categories = list(set(c.get("category", "기타") for c in saved_charts))
    all_categories = ["전체"] + sorted([c for c in all_categories if c])

    col_cat, col_layout, col_refresh = st.columns([2, 2, 1], vertical_alignment="bottom")
    with col_cat:
        selected_category = st.selectbox("분류", all_categories, index=0, key="main_category_filter")
    with col_layout:
        layout_cols = st.selectbox("레이아웃", ["1열", "2열", "3열"], index=1, key="main_layout_cols")
    with col_refresh:
        if st.button("🔄 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # 분류별 필터링
    if selected_category != "전체":
        filtered_charts = [c for c in saved_charts if c.get("category", "기타") == selected_category]
    else:
        filtered_charts = saved_charts
    
    if not filtered_charts:
        st.info(f"📌 '{selected_category}' 분류에 저장된 차트가 없습니다.")
        return
    
    num_cols = {"1열": 1, "2열": 2, "3열": 3}.get(layout_cols, 2)
    
    # 차트 표시 (필터링된 차트 사용)
    for idx, chart_config in enumerate(filtered_charts):
        if not chart_config:
            continue
        
        # 컬럼 레이아웃
        if num_cols > 1:
            if idx % num_cols == 0:
                cols = st.columns(num_cols)
            col = cols[idx % num_cols]
        else:
            col = None

        with col if col is not None else st.container():
            # 차트 카드
            with st.expander(f"📊 {chart_config['name']}", expanded=True):
                # 데이터 준비
                indicator_settings = {}
                merged_df = None
                
                for ind in chart_config.get("indicators", []):
                    source = ind["source"]
                    sid = ind["id"]
                    source_data = all_data.get(source)
                    
                    if source_data is None or not source_data.has_data or sid not in source_data.df.columns:
                        continue
                    
                    df = source_data.df
                    display_key = f"{source}_{sid}"
                    name = source_data.id_to_name.get(sid, sid)
                    
                    # 데이터 필터링
                    date_range = chart_config.get("date_range", [None, None])
                    if date_range[0] and date_range[1]:
                        mask = (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
                        df_filtered = df[mask][['date', sid]].copy()
                    else:
                        df_filtered = df[['date', sid]].copy()
                    
                    df_filtered = df_filtered.dropna(subset=[sid])
                    
                    # 변환 적용
                    transform = ind.get("transform", "원 데이터")
                    df_filtered[display_key] = transform_series(df_filtered[sid], transform)
                    
                    # 시차 적용
                    shift = ind.get("shift", 0)
                    if shift != 0:
                        df_filtered[display_key] = df_filtered[display_key].shift(shift)
                    
                    df_filtered = df_filtered[['date', display_key]]
                    
                    if merged_df is None:
                        merged_df = df_filtered
                    else:
                        merged_df = pd.merge(merged_df, df_filtered, on='date', how='outer')
                    
                    indicator_settings[display_key] = {
                        'source': source,
                        'sid': sid,
                        'name': name,
                        'chart_type': ind.get("chart_type", "라인"),
                        'transform': transform,
                        'shift': shift,
                        'reverse': ind.get("reverse", False),
                        'log_scale': ind.get("log_scale", False)
                    }
                
                if merged_df is not None and not merged_df.empty:
                    merged_df = merged_df.sort_values('date')
                    
                    # 차트 표시
                    fig = create_chart(
                        indicator_settings, 
                        merged_df, 
                        separate_yaxis=chart_config.get("separate_yaxis", True),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
                    
                    # 최신 값 표시
                    metric_cols = st.columns(min(len(indicator_settings), 4))
                    for i, (key, s) in enumerate(indicator_settings.items()):
                        if key in merged_df.columns:
                            recent = merged_df[key].dropna()
                            if len(recent) > 0:
                                with metric_cols[i % 4]:
                                    st.metric(
                                        label=f"{s['name'][:15]}",
                                        value=f"{recent.iloc[-1]:,.2f}",
                                        delta=f"{calculate_change(merged_df[key]):+.2f}%" if calculate_change(merged_df[key]) else None
                                    )
                else:
                    st.warning("데이터를 불러올 수 없습니다.")


# ============================================================
# 📈 지표별 비교 페이지
# ============================================================

def render_comparison_page(all_data, source_info):
    """지표별 비교 페이지를 렌더링합니다."""
    st.header("📈 지표별 비교")
    
    available_sources = [s for s in ["FRED", "ECOS", "BLS"] if all_data[s].has_data]
    
    if not available_sources:
        st.error("⚠️ 데이터 파일을 찾을 수 없습니다. 먼저 collect_all.py를 실행하세요.")
        return
    
    # 지표 선택
    st.sidebar.subheader("📋 지표 선택")
    
    selected_indicators = []
    
    for source in available_sources:
        info =source_info[source]
        source_data = all_data[source]
        
        with st.sidebar.expander(f"{info['emoji']} {source}", expanded=(source == "FRED")):
            category = st.selectbox(
                "카테고리",
                options=["전체"] + source_data.categories,
                key=f"{source}_category"
            )
            
            if category == "전체":
                available_indicators = source_data.id_to_name
            else:
                category_indicators = info['categories'].get(category, {})
                available_indicators = {
                    k: source_data.id_to_name.get(k, v) 
                    for k, v in category_indicators.items() 
                    if k in source_data.df.columns
                }
            
            available_in_data = {
                k: v for k, v in available_indicators.items() 
                if k in source_data.df.columns
            }
            
            # 숨김 처리된 지표 필터링
            settings = load_saved_settings()
            hidden_indicators = settings.get("hidden_indicators", [])
            available_in_data = {
                k: v for k, v in available_in_data.items()
                if f"{source}:{k}" not in hidden_indicators
            }
            
            if available_in_data:
                selected_names = st.multiselect(
                    "지표 선택",
                    options=list(available_in_data.values()),
                    key=f"{source}_indicators"
                )
                
                name_to_id = {v: k for k, v in available_in_data.items()}
                for name in selected_names:
                    if name in name_to_id:
                        sid = name_to_id[name]
                        # 지표 정의에서 NSA/SA 포함 이름 가져오기
                        proper_name = get_korean_name(sid, info['indicators'])
                        selected_indicators.append((source, sid, proper_name))
    
    if not selected_indicators:
        st.info("👈 사이드바에서 비교할 지표를 선택하세요.")
        return
    
    # 분석 설정
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ 분석 설정")
    
    # 기간 선택
    all_dates = []
    for source, sid, name in selected_indicators:
        df = all_data[source].df
        if df is not None and 'date' in df.columns:
            all_dates.extend(df['date'].dropna().tolist())
    
    if all_dates:
        min_date = min(all_dates).date()
        max_date = max(all_dates).date()
    else:
        min_date = datetime(2000, 1, 1).date()
        max_date = datetime.now().date()
    
    date_range = st.sidebar.slider(
        "📅 기간 선택",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM"
    )
    
    # 전역 설정
    default_transform = st.sidebar.selectbox("기본 변환", options=config.TRANSFORM_OPTIONS, index=0)
    
    # 차트 옵션
    separate_yaxis = st.sidebar.checkbox("Y축 분리 (다중 축)", value=len(selected_indicators) > 1)
    
    # 지표별 설정
    st.sidebar.divider()
    st.sidebar.subheader("📈 지표별 설정")
    
    indicator_settings = {}
    
    for source, sid, name in selected_indicators:
        display_key = f"{source}_{sid}"
        display_name = f"[{source}] {name[:15]}..." if len(name) > 15 else f"[{source}] {name}"
        
        with st.sidebar.expander(display_name, expanded=False):
            chart_type_ind = st.selectbox("차트 유형", options=["라인", "라인+마커", "막대"], index=0, key=f"charttype_{display_key}")
            transform = st.selectbox("변환", options=config.TRANSFORM_OPTIONS, index=config.TRANSFORM_OPTIONS.index(default_transform), key=f"transform_{display_key}")
            shift = st.slider("시차 조정 (개월)", min_value=-24, max_value=24, value=0, key=f"shift_{display_key}")
            
            if shift != 0:
                direction = "선행" if shift < 0 else "후행"
                st.caption(f"📊 {abs(shift)}개월 {direction}")

            col_rev, col_log = st.columns(2)
            with col_rev:
                reverse = st.checkbox("역축", value=False, key=f"reverse_{display_key}")
            with col_log:
                log_scale = st.checkbox("로그 축", value=False, key=f"log_{display_key}")

        indicator_settings[display_key] = {
            'source': source,
            'sid': sid,
            'name': name,
            'chart_type': chart_type_ind,
            'transform': transform,
            'shift': shift,
            'reverse': reverse,
            'log_scale': log_scale
        }
    
    # ========================================
    # 📌 세팅 저장 버튼
    # ========================================
    st.sidebar.divider()
    
    with st.sidebar.expander("📌 세팅 저장", expanded=False):
        chart_name = st.text_input("차트 이름", value=f"비교 차트 {datetime.now().strftime('%m/%d %H:%M')}")
        
        # 분류 선택
        settings = load_saved_settings()
        available_categories = settings.get("categories", ["금리", "물가", "고용", "경기", "기타"])
        
        col_cat, col_new = st.columns([2, 1])
        with col_cat:
            selected_cat = st.selectbox("분류", available_categories, key="save_category")
        with col_new:
            new_cat = st.text_input("새 분류", key="new_category", label_visibility="collapsed", placeholder="새 분류...")
        
        chart_category = new_cat if new_cat else selected_cat
        
        if st.button("💾 저장", use_container_width=True):
            settings = load_saved_settings()
            
            # 새 분류 추가
            if new_cat and new_cat not in settings.get("categories", []):
                settings["categories"] = settings.get("categories", []) + [new_cat]
            
            new_chart = {
                "id": f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "name": chart_name,
                "category": chart_category,
                "indicators": [
                    {
                        "source": s["source"],
                        "id": s["sid"],
                        "chart_type": s["chart_type"],
                        "transform": s["transform"],
                        "shift": s["shift"],
                        "reverse": s.get("reverse", False),
                        "log_scale": s.get("log_scale", False)
                    }
                    for s in indicator_settings.values()
                ],
                "date_range": [str(date_range[0]), str(date_range[1])],
                "separate_yaxis": separate_yaxis
            }
            
            settings["saved_charts"].append(new_chart)
            settings["main_layout"].append({"chart_id": new_chart["id"]})
            save_settings(settings)
            
            st.success(f"✅ '{chart_name}' 저장 완료! (분류: {chart_category})")
    
    # ========================================
    # 📊 데이터 준비 및 차트 표시
    # ========================================
    
    merged_df = None
    
    for display_key, s in indicator_settings.items():
        source = s['source']
        sid = s['sid']
        df = all_data[source].df
        
        if df is None or sid not in df.columns:
            continue
        
        mask = (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
        df_filtered = df[mask][['date', sid]].copy()
        df_filtered = df_filtered.dropna(subset=[sid])
        
        df_filtered[display_key] = transform_series(df_filtered[sid], s['transform'])
        
        if s['shift'] != 0:
            df_filtered[display_key] = df_filtered[display_key].shift(s['shift'])
        
        df_filtered = df_filtered[['date', display_key]]
        
        if merged_df is None:
            merged_df = df_filtered
        else:
            merged_df = pd.merge(merged_df, df_filtered, on='date', how='outer')
    
    if merged_df is None or merged_df.empty:
        st.warning("선택한 지표에 대한 데이터가 없습니다.")
        return
    
    merged_df = merged_df.sort_values('date')
    
    # 통계 요약
    st.subheader("📊 주요 지표 요약")
    cols = st.columns(min(len(indicator_settings), 4))
    
    for i, (display_key, s) in enumerate(indicator_settings.items()):
        with cols[i % 4]:
            if display_key in merged_df.columns:
                recent = merged_df[display_key].dropna()
                if len(recent) > 0:
                    change = calculate_change(merged_df[display_key])
                    st.metric(
                        label=f"[{s['source']}] {s['name'][:15]}",
                        value=f"{recent.iloc[-1]:,.2f}",
                        delta=f"{change:+.2f}%" if change else None
                    )
    
    st.divider()
    
    # 차트
    st.subheader("📈 시계열 비교 차트")
    fig = create_chart(indicator_settings, merged_df, separate_yaxis, height=500)
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    
    # 상관관계 분석
    if len(indicator_settings) >= 2:
        with st.expander("🔬 상관관계 분석", expanded=False):
            indicator_options = list(indicator_settings.keys())
            indicator_labels = {k: f"[{v['source']}] {v['name']}" for k, v in indicator_settings.items()}
            
            base_key = st.selectbox("기준 지표", options=indicator_options, format_func=lambda x: indicator_labels[x])
            other_keys = [k for k in indicator_options if k != base_key]
            
            if other_keys and base_key in merged_df.columns:
                base_series = merged_df[base_key].dropna()
                
                results = []
                for other_key in other_keys:
                    if other_key not in merged_df.columns:
                        continue
                    
                    other_series = merged_df[other_key].dropna()
                    current_corr = calculate_correlation(base_series, other_series)
                    _, optimal_lag, max_corr = find_optimal_lag(base_series, other_series)
                    
                    results.append({
                        '지표': indicator_labels[other_key],
                        '상관계수': f"{current_corr:.3f}" if current_corr else "N/A",
                        '최적 시차': f"{optimal_lag}개월",
                        '최적 상관계수': f"{max_corr:.3f}"
                    })
                
                if results:
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
    
    # 데이터 테이블
    with st.expander("📋 원시 데이터", expanded=False):
        df_show = merged_df.copy()
        rename_map = {'date': '날짜'}
        for k, s in indicator_settings.items():
            if k in df_show.columns:
                rename_map[k] = f"[{s['source']}] {s['name']}"
        df_show = df_show.rename(columns=rename_map)
        
        st.dataframe(df_show.sort_values('날짜', ascending=False), use_container_width=True, hide_index=True)
        
        csv = df_show.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 CSV 다운로드", data=csv, file_name="economic_data.csv", mime="text/csv")


# ============================================================
# ⚙️ 설정 페이지
# ============================================================

def render_settings_page():
    """설정 페이지를 렌더링합니다."""
    st.header("⚙️ 설정")
    
    settings = load_saved_settings()
    saved_charts = settings.get("saved_charts", [])
    
    st.subheader("저장된 차트 관리")
    
    if not saved_charts:
        st.info("저장된 차트가 없습니다.")
    else:
        # 분류 필터
        available_categories = settings.get("categories", ["금리", "물가", "고용", "경기", "기타"])
        all_chart_categories = list(set([c.get("category", "기타") for c in saved_charts]))
        filter_categories = ["전체"] + [cat for cat in available_categories if cat in all_chart_categories]
        
        selected_filter = st.selectbox("분류 필터", filter_categories, key="chart_filter")
        
        # 필터링된 차트
        if selected_filter == "전체":
            filtered_charts = saved_charts
        else:
            filtered_charts = [c for c in saved_charts if c.get("category", "기타") == selected_filter]
        
        if not filtered_charts:
            st.info(f"'{selected_filter}' 분류에 저장된 차트가 없습니다.")
        else:
            # 2열 레이아웃
            chart_list = list(enumerate(saved_charts))
            filtered_indices = [i for i, c in chart_list if (selected_filter == "전체" or c.get("category", "기타") == selected_filter)]
            
            for row_start in range(0, len(filtered_indices), 2):
                cols = st.columns(2)
                
                for col_idx, col in enumerate(cols):
                    if row_start + col_idx >= len(filtered_indices):
                        break
                    
                    i = filtered_indices[row_start + col_idx]
                    chart = saved_charts[i]
                    
                    with col:
                        # 차트 카드
                        st.markdown(f"**{chart['name']}**")
                        category_label = chart.get("category", "기타")
                        indicators_str = ", ".join([f"{ind['source']}/{ind['id']}" for ind in chart.get('indicators', [])])
                        st.caption(f"[{category_label}] {indicators_str[:40]}...")
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("편집", key=f"edit_{i}", use_container_width=True):
                                st.session_state[f"editing_{i}"] = True
                        with btn_col2:
                            if st.button("삭제", key=f"delete_{i}", use_container_width=True):
                                settings["saved_charts"].pop(i)
                                settings["main_layout"] = [l for l in settings.get("main_layout", []) if l.get("chart_id") != chart["id"]]
                                save_settings(settings)
                                st.rerun()
            
            # 편집 모드 (별도 섹션)
            for i, chart in enumerate(saved_charts):
                if st.session_state.get(f"editing_{i}", False):
                    st.divider()
                    st.markdown(f"**{chart['name']} 편집**")
                    
                    with st.container():
                        # 차트 이름
                        new_name = st.text_input("차트 이름", value=chart['name'], key=f"name_{i}")
                        
                        # 분류 변경
                        edit_categories = settings.get("categories", ["금리", "물가", "고용", "경기", "기타"])
                        current_category = chart.get("category", "기타")
                        cat_index = edit_categories.index(current_category) if current_category in edit_categories else 0
                        new_category = st.selectbox("분류", edit_categories, index=cat_index, key=f"cat_{i}")
                        
                        # Y축 분리
                        new_separate_yaxis = st.checkbox("Y축 분리", value=chart.get("separate_yaxis", True), key=f"yaxis_{i}")
                        
                        # 지표별 세팅
                        st.write("**지표별 세팅:**")
                        transform_options = ["원 데이터", "지수화 (기준=100)", "MoM (전월 대비)", "QoQ (전분기 대비)", "YoY (전년 동기 대비)"]
                        
                        new_indicators = []
                        for j, ind in enumerate(chart.get('indicators', [])):
                            ind_id = ind.get('id', '')
                            ind_source = ind.get('source', '')
                            
                            with st.expander(f"{ind_source}/{ind_id}", expanded=False):
                                # 변환 유형
                                current_transform = ind.get('transform', '원 데이터')
                                transform_idx = transform_options.index(current_transform) if current_transform in transform_options else 0
                                new_transform = st.selectbox(
                                    "변환", transform_options, index=transform_idx, 
                                    key=f"transform_{i}_{j}"
                                )
                                
                                # 시차
                                current_shift = ind.get('shift', 0)
                                new_shift = st.slider(
                                    "시차 (개월)", -24, 24, current_shift,
                                    key=f"shift_{i}_{j}"
                                )
                                
                                # 차트 유형
                                chart_type_options = ["라인", "라인+마커", "막대"]
                                current_chart_type = ind.get('chart_type', '라인')
                                chart_type_idx = chart_type_options.index(current_chart_type) if current_chart_type in chart_type_options else 0
                                new_chart_type = st.selectbox(
                                    "차트 유형", chart_type_options, index=chart_type_idx,
                                    key=f"charttype_{i}_{j}"
                                )

                                col_rev, col_log = st.columns(2)
                                with col_rev:
                                    new_reverse = st.checkbox("역축", value=ind.get('reverse', False), key=f"reverse_{i}_{j}")
                                with col_log:
                                    new_log_scale = st.checkbox("로그 축", value=ind.get('log_scale', False), key=f"log_{i}_{j}")

                            new_indicators.append({
                                'source': ind_source,
                                'id': ind_id,
                                'transform': new_transform,
                                'shift': new_shift,
                                'chart_type': new_chart_type,
                                'reverse': new_reverse,
                                'log_scale': new_log_scale
                            })
                        
                        # 저장/취소 버튼
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("저장", key=f"save_{i}", use_container_width=True):
                                settings["saved_charts"][i]["name"] = new_name
                                settings["saved_charts"][i]["category"] = new_category
                                settings["saved_charts"][i]["separate_yaxis"] = new_separate_yaxis
                                settings["saved_charts"][i]["indicators"] = new_indicators
                                save_settings(settings)
                                st.session_state[f"editing_{i}"] = False
                                st.success("저장 완료!")
                                st.rerun()
                        with col_cancel:
                            if st.button("취소", key=f"cancel_{i}", use_container_width=True):
                                st.session_state[f"editing_{i}"] = False
                                st.rerun()
    
    # 모든 세팅 초기화
    st.subheader("🔄 초기화")
    if st.button("🗑️ 모든 세팅 삭제", type="secondary"):
        save_settings({"saved_charts": [], "main_layout": []})
        st.success("모든 세팅이 삭제되었습니다.")
        st.rerun()


def render_indicator_management_page(all_data: dict, source_info: dict):
    """지표 관리 페이지를 렌더링합니다."""
    
    st.header("📋 지표 관리")
    st.caption("수집된 지표 정보를 확인하고 표시 여부를 설정합니다.")
    
    settings = load_saved_settings()
    hidden_indicators = settings.get("hidden_indicators", [])
    
    # 출처별 탭
    tabs = st.tabs(["🇺🇸 FRED", "🇰🇷 ECOS", "📊 BLS"])
    sources = ["FRED", "ECOS", "BLS"]
    countries = {"FRED": "🇺🇸 미국", "ECOS": "🇰🇷 한국", "BLS": "🇺🇸 미국"}
    
    for tab, source in zip(tabs, sources):
        with tab:
            info = source_info.get(source, {})
            indicators = info.get("indicators", {})
            categories = info.get("categories", {})
            
            # 데이터에서 실제 수집된 지표 정보 가져오기
            source_data = all_data.get(source)
            if source_data is None or not source_data.has_data:
                st.info(f"{source} 데이터가 수집되지 않았습니다.")
                continue
            df_data = source_data.df
            available_indicators = source_data.id_to_name
            
            # 카테고리별 역매핑
            indicator_to_category = {}
            for cat_name, cat_list in categories.items():
                for ind_id in cat_list:
                    indicator_to_category[ind_id] = cat_name
            
            # 저장 버튼
            col_save, col_select_all, col_deselect_all = st.columns([2, 1, 1])
            with col_save:
                save_clicked = st.button("💾 변경사항 저장", key=f"save_{source}", use_container_width=True)
            with col_select_all:
                if st.button("✅ 전체 선택", key=f"all_{source}", use_container_width=True):
                    for ind_id in available_indicators.keys():
                        key = f"{source}:{ind_id}"
                        if key in hidden_indicators:
                            hidden_indicators.remove(key)
                    settings["hidden_indicators"] = hidden_indicators
                    save_settings(settings)
                    st.rerun()
            with col_deselect_all:
                if st.button("☐ 전체 해제", key=f"none_{source}", use_container_width=True):
                    for ind_id in available_indicators.keys():
                        key = f"{source}:{ind_id}"
                        if key not in hidden_indicators:
                            hidden_indicators.append(key)
                    settings["hidden_indicators"] = hidden_indicators
                    save_settings(settings)
                    st.rerun()
            
            st.divider()
            
            # 지표 목록 - 2열 레이아웃
            new_hidden = list(hidden_indicators)  # 복사본 생성
            indicator_list = list(available_indicators.items())
            
            for i in range(0, len(indicator_list), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    if i + j >= len(indicator_list):
                        break
                    
                    ind_id, ind_name = indicator_list[i + j]
                    key = f"{source}:{ind_id}"
                    is_visible = key not in hidden_indicators
                    
                    # 지표 정보 가져오기
                    category = indicator_to_category.get(ind_id, "기타")
                    
                    # 시계열 정보 수집
                    date_range = "N/A"
                    if df_data is not None and ind_id in df_data.columns:
                        valid_dates = df_data[df_data[ind_id].notna()]['date']
                        if len(valid_dates) > 0:
                            start = valid_dates.min().strftime('%y.%m')
                            end = valid_dates.max().strftime('%y.%m')
                            date_range = f"{start}~{end}"
                    
                    with col:
                        # 체크박스와 정보를 한 줄에
                        korean_name = get_korean_name(ind_id, indicators)
                        short_name = korean_name[:20] + "..." if len(korean_name) > 20 else korean_name
                        
                        new_visible = st.checkbox(
                            f"**{short_name}**", 
                            value=is_visible, 
                            key=f"vis_{source}_{ind_id}"
                        )
                        
                        # 상태 변경 추적
                        if new_visible and key in new_hidden:
                            new_hidden.remove(key)
                        elif not new_visible and key not in new_hidden:
                            new_hidden.append(key)
                        
                        # 상세 정보
                        st.caption(f"`{ind_id}` | 📁{category} | 📅{date_range} | ⏱️월별 | {countries[source]}")
            
            # 저장 처리
            if save_clicked:
                settings["hidden_indicators"] = new_hidden
                save_settings(settings)
                st.success("✅ 저장되었습니다!")
                st.rerun()


# ============================================================
# 🎨 메인 앱
# ============================================================

def main():
    """메인 대시보드 함수"""
    
    # 페이지 설정
    st.set_page_config(
        page_title="경제 데이터 통합 대시보드",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS 스타일
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 350px;
    }
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }
    .sidebar-logo {
        filter: brightness(0) invert(1);
        width: 80px;
        margin: 0 auto;
        display: block;
    }
    .brand-title {
        text-align: center;
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        margin-top: 8px;
        margin-bottom: 20px;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 모든 데이터 로드
    all_data = load_all_data()
    source_info = get_source_info()
    
    # ========================================
    # 사이드바 메뉴
    # ========================================
    
    # 로고 표시
    import base64
    logo_path = Path(__file__).parent / "assets" / "logo.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{logo_data}" class="sidebar-logo">',
            unsafe_allow_html=True
        )
        st.sidebar.markdown(
            '<div class="brand-title">INVESTWITH<br>Macro Data System</div>',
            unsafe_allow_html=True
        )
    
    page = st.sidebar.radio(
        "메뉴",
        ["메인 화면", "지표별 비교", "지표 관리", "설정"],
        label_visibility="collapsed"
    )
    
    st.sidebar.divider()
    
    # ========================================
    # 페이지 렌더링
    # ========================================
    if page == "메인 화면":
        render_main_page(all_data, source_info)
    elif page == "지표별 비교":
        render_comparison_page(all_data, source_info)
    elif page == "지표 관리":
        render_indicator_management_page(all_data, source_info)
    elif page == "설정":
        render_settings_page()
    
    # 푸터
    st.sidebar.divider()
    st.sidebar.caption("💡 사이드바 접기: 왼쪽 상단 ◀ 클릭")
    st.sidebar.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
