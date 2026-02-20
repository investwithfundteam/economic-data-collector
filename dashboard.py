"""
INVESTWITH Macro Data System
==========================================

Integrated dashboard for visualizing and analyzing economic indicators
collected from FRED, ECOS, and BLS data sources.

Usage:
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

import config
from utils.indicator_filter import (
    filter_hidden_indicators,
    filter_available_in_data,
    get_category_indicators
)
from utils.data_loader import SourceData

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ============================================================
# Utility Functions
# ============================================================

def get_data_path(source: str) -> Path:
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    filenames = {
        "FRED": "fred_data.xlsx",
        "ECOS": "ecos_data.xlsx",
        "BLS": "bls_data.xlsx",
    }
    return data_dir / filenames.get(source, "data.xlsx")


def get_settings_path() -> Path:
    script_dir = Path(__file__).parent
    return script_dir / "saved_settings.json"


def migrate_settings_to_english(settings: dict) -> dict:
    """One-time migration of Korean values to English in saved settings."""
    if settings.get("migrated_to_english"):
        return settings

    kr_to_en_transform = config.KOREAN_TO_ENGLISH_TRANSFORMS
    kr_to_en_chart = config.KOREAN_TO_ENGLISH_CHART_TYPES
    kr_to_en_cat = config.KOREAN_TO_ENGLISH_CATEGORIES

    # Migrate categories list
    old_cats = settings.get("categories", [])
    settings["categories"] = [kr_to_en_cat.get(c, c) for c in old_cats]

    # Migrate each saved chart
    for chart in settings.get("saved_charts", []):
        chart["category"] = kr_to_en_cat.get(
            chart.get("category", ""), chart.get("category", "Other")
        )
        for ind in chart.get("indicators", []):
            ind["transform"] = kr_to_en_transform.get(
                ind.get("transform", ""), ind.get("transform", "Raw Data")
            )
            ind["chart_type"] = kr_to_en_chart.get(
                ind.get("chart_type", ""), ind.get("chart_type", "Line")
            )

    settings["migrated_to_english"] = True
    return settings


def load_saved_settings() -> dict:
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "categories" not in data:
                    data["categories"] = config.DEFAULT_CATEGORIES
                data = migrate_settings_to_english(data)
                save_settings(data)
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
    settings_path = get_settings_path()
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_source_info():
    return {
        "FRED": {"name": "FRED (Federal Reserve)", "categories": FRED_CATEGORIES, "indicators": FRED_INDICATORS},
        "ECOS": {"name": "ECOS (Bank of Korea)", "categories": ECOS_CATEGORIES, "indicators": ECOS_INDICATORS},
        "BLS": {"name": "BLS (Bureau of Labor Statistics)", "categories": BLS_CATEGORIES, "indicators": BLS_INDICATORS},
    }


def get_korean_name(indicator_code: str, all_indicators: dict) -> str:
    desc = all_indicators.get(indicator_code, indicator_code)
    if "(SA)" in desc:
        idx = desc.find("(SA)") + 4
        return desc[:idx].strip()
    elif "(NSA)" in desc:
        idx = desc.find("(NSA)") + 5
        return desc[:idx].strip()
    elif " (" in desc:
        return desc.split(" (")[0]
    return desc


@st.cache_data(ttl=3600)
def load_all_data() -> dict[str, SourceData]:
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
    if transform_mode == "Raw Data":
        return series
    elif transform_mode == "Indexed (Base=100)":
        first_valid = series.dropna().iloc[0] if not series.dropna().empty else 1
        if first_valid != 0:
            return (series / first_valid) * 100
        return series
    elif transform_mode == "MoM":
        return series.pct_change(periods=1) * 100
    elif transform_mode == "QoQ":
        return series.pct_change(periods=3) * 100
    elif transform_mode == "YoY":
        return series.pct_change(periods=12) * 100
    return series


def calculate_change(series):
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
    combined = pd.concat([series1, series2], axis=1).dropna()
    if len(combined) < 3:
        return None
    return combined.iloc[:, 0].corr(combined.iloc[:, 1])


def find_optimal_lag(series1, series2, max_lag=config.MAX_LAG_MONTHS):
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
# Chart Creation
# ============================================================

def create_chart(indicator_settings, merged_df, separate_yaxis=True, height=config.CHART_HEIGHT):
    colors = config.CHART_COLORS
    fig = go.Figure()

    for i, (display_key, settings) in enumerate(indicator_settings.items()):
        if display_key not in merged_df.columns:
            continue

        source = settings['source']
        name = settings['name']
        shift_val = settings.get('shift', 0)
        chart_type = settings.get('chart_type', 'Line')
        transform = settings.get('transform', 'Raw Data')

        legend_name = f"[{source}] {name}"

        if transform in config.TRANSFORM_LABELS:
            legend_name += f" ({config.TRANSFORM_LABELS[transform]})"

        if shift_val != 0:
            direction = "lead" if shift_val < 0 else "lag"
            legend_name += f" ({abs(shift_val)}mo {direction})"

        color = colors[i % len(colors)]

        valid_data = merged_df[['date', display_key]].dropna()
        if valid_data.empty:
            continue

        plot_dates = valid_data['date']
        if shift_val != 0:
            plot_dates = valid_data['date'] + pd.DateOffset(months=shift_val)

        yaxis_name = f'y{i+1}' if separate_yaxis and i > 0 else 'y'

        hover_tpl = (
            f"<b>{legend_name}</b><br>"
            "Date: %{x|%Y-%m-%d}<br>"
            "Value: %{y:,.2f}<extra></extra>"
        )

        if chart_type == "Bar":
            fig.add_trace(go.Bar(
                x=plot_dates,
                y=valid_data[display_key],
                name=legend_name,
                marker=dict(color=color),
                hovertemplate=hover_tpl,
            ))
        else:
            mode = 'lines+markers' if chart_type == "Line + Marker" else 'lines'
            marker_cfg = dict(size=4, color=color) if chart_type == "Line + Marker" else None
            fig.add_trace(go.Scatter(
                x=plot_dates,
                y=valid_data[display_key],
                mode=mode,
                name=legend_name,
                line=dict(width=2, color=color),
                marker=marker_cfg,
                yaxis=yaxis_name,
                hovertemplate=hover_tpl,
            ))

    layout_config = dict(
        height=height,
        template="plotly_white",
        font=dict(
            family="Helvetica, 'Helvetica Neue', Arial, sans-serif",
            size=12,
            color="#404040",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#404040"),
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
        ),
        margin=dict(l=50, r=50, t=60, b=50),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(217, 217, 217, 0.5)",
            gridwidth=0.5,
            linecolor="#D9D9D9",
            linewidth=1,
            tickfont=dict(size=10, color="#7F7F7F"),
            autorange=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(217, 217, 217, 0.5)",
            gridwidth=0.5,
            linecolor="#D9D9D9",
            linewidth=1,
            tickfont=dict(size=10, color="#7F7F7F"),
            zeroline=True,
            zerolinecolor="#D9D9D9",
            zerolinewidth=1,
        ),
        plot_bgcolor="rgba(255, 255, 255, 1)",
        paper_bgcolor="rgba(255, 255, 255, 1)",
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#D9D9D9",
            font=dict(size=11, color="#0D0D0D"),
        ),
        dragmode='pan',
    )

    first_settings = next(iter(indicator_settings.values()), {})
    if first_settings.get('reverse'):
        layout_config['yaxis']['autorange'] = 'reversed'
    if first_settings.get('log_scale'):
        layout_config['yaxis']['type'] = 'log'

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
# Dashboard Page
# ============================================================

def render_main_page(all_data, source_info):
    st.header("Dashboard")

    settings = load_saved_settings()
    saved_charts = settings.get("saved_charts", [])
    main_layout = settings.get("main_layout", [])

    if not saved_charts:
        st.info("""
        **No saved charts yet.**

        1. Select **Compare** from the sidebar menu
        2. Choose indicators and analyze them
        3. Click **Save Chart** to save your configuration
        4. View saved charts on the Dashboard
        """)
        return

    all_categories = list(set(c.get("category", "Other") for c in saved_charts))
    all_categories = ["All"] + sorted([c for c in all_categories if c])

    col_cat, col_layout, col_refresh = st.columns([2, 2, 1], vertical_alignment="bottom")
    with col_cat:
        selected_category = st.selectbox("Category", all_categories, index=0, key="main_category_filter")
    with col_layout:
        layout_cols = st.selectbox("Layout", config.LAYOUT_OPTIONS, index=1, key="main_layout_cols")
    with col_refresh:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if selected_category != "All":
        filtered_charts = [c for c in saved_charts if c.get("category", "Other") == selected_category]
    else:
        filtered_charts = saved_charts

    if not filtered_charts:
        st.info(f"No saved charts in '{selected_category}' category.")
        return

    num_cols = config.LAYOUT_COLS_MAP.get(layout_cols, 2)

    for idx, chart_config in enumerate(filtered_charts):
        if not chart_config:
            continue

        if num_cols > 1:
            if idx % num_cols == 0:
                cols = st.columns(num_cols)
            col = cols[idx % num_cols]
        else:
            col = None

        with col if col is not None else st.container():
            with st.expander(f"{chart_config['name']}", expanded=True):
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

                    date_range = chart_config.get("date_range", [None, None])
                    if date_range[0] and date_range[1]:
                        mask = (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
                        df_filtered = df[mask][['date', sid]].copy()
                    else:
                        df_filtered = df[['date', sid]].copy()

                    df_filtered = df_filtered.dropna(subset=[sid])

                    transform = ind.get("transform", "Raw Data")
                    df_filtered[display_key] = transform_series(df_filtered[sid], transform)

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
                        'chart_type': ind.get("chart_type", "Line"),
                        'transform': transform,
                        'shift': shift,
                        'reverse': ind.get("reverse", False),
                        'log_scale': ind.get("log_scale", False)
                    }

                if merged_df is not None and not merged_df.empty:
                    merged_df = merged_df.sort_values('date')

                    fig = create_chart(
                        indicator_settings,
                        merged_df,
                        separate_yaxis=chart_config.get("separate_yaxis", True),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

                    metric_cols = st.columns(min(len(indicator_settings), 4))
                    for i, (key, s) in enumerate(indicator_settings.items()):
                        if key in merged_df.columns:
                            recent = merged_df[key].dropna()
                            if len(recent) > 0:
                                with metric_cols[i % 4]:
                                    unit = "%" if s.get('transform', 'Raw Data') in ("MoM", "QoQ", "YoY") else ""
                                    st.metric(
                                        label=f"{s['name'][:15]}",
                                        value=f"{recent.iloc[-1]:,.2f}{unit}",
                                        delta=f"{calculate_change(merged_df[key]):+.2f}%" if calculate_change(merged_df[key]) else None
                                    )
                else:
                    st.warning("Unable to load data.")


# ============================================================
# Compare Page
# ============================================================

def render_comparison_page(all_data, source_info):
    st.header("Compare Indicators")

    settings = load_saved_settings()

    available_sources = [s for s in ["FRED", "ECOS", "BLS"] if all_data[s].has_data]

    if not available_sources:
        st.error("Data files not found. Run collect_all.py first.")
        return

    st.sidebar.subheader("Select Indicators")

    selected_indicators = []

    for source in available_sources:
        info = source_info[source]
        source_data = all_data[source]

        with st.sidebar.expander(f"{source}", expanded=(source == "FRED")):
            category = st.selectbox(
                "Category",
                options=["All"] + source_data.categories,
                key=f"{source}_category"
            )

            if category == "All":
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

            hidden_indicators = settings.get("hidden_indicators", [])
            available_in_data = {
                k: v for k, v in available_in_data.items()
                if f"{source}:{k}" not in hidden_indicators
            }

            if available_in_data:
                selected_names = st.multiselect(
                    "Indicators",
                    options=list(available_in_data.values()),
                    key=f"{source}_indicators"
                )

                name_to_id = {v: k for k, v in available_in_data.items()}
                for name in selected_names:
                    if name in name_to_id:
                        sid = name_to_id[name]
                        proper_name = get_korean_name(sid, info['indicators'])
                        selected_indicators.append((source, sid, proper_name))

    if not selected_indicators:
        st.info("Select indicators from the sidebar to begin.")
        return

    st.sidebar.divider()
    st.sidebar.subheader("Analysis Settings")

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
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM"
    )

    default_transform = st.sidebar.selectbox("Default Transform", options=config.TRANSFORM_OPTIONS, index=0)

    separate_yaxis = st.sidebar.checkbox("Separate Y-Axes", value=len(selected_indicators) > 1)

    st.sidebar.divider()
    st.sidebar.subheader("Per-Indicator Settings")

    indicator_settings = {}

    for source, sid, name in selected_indicators:
        display_key = f"{source}_{sid}"
        display_name = f"[{source}] {name[:15]}..." if len(name) > 15 else f"[{source}] {name}"

        with st.sidebar.expander(display_name, expanded=False):
            chart_type_ind = st.selectbox("Chart Type", options=config.CHART_TYPE_OPTIONS, index=0, key=f"charttype_{display_key}")
            transform = st.selectbox("Transform", options=config.TRANSFORM_OPTIONS, index=config.TRANSFORM_OPTIONS.index(default_transform), key=f"transform_{display_key}")
            shift = st.slider("Lag Adjustment (months)", min_value=-24, max_value=24, value=0, key=f"shift_{display_key}")

            if shift != 0:
                direction = "lead" if shift < 0 else "lag"
                st.caption(f"{abs(shift)} month(s) {direction}")

            col_rev, col_log = st.columns(2)
            with col_rev:
                reverse = st.checkbox("Reverse", value=False, key=f"reverse_{display_key}")
            with col_log:
                log_scale = st.checkbox("Log Scale", value=False, key=f"log_{display_key}")

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

    # Save Settings
    st.sidebar.divider()

    with st.sidebar.expander("Save Chart", expanded=False):
        chart_name = st.text_input("Chart Name", value=f"Comparison {datetime.now().strftime('%m/%d %H:%M')}")

        available_categories = settings.get("categories", config.DEFAULT_CATEGORIES)

        col_cat, col_new = st.columns([2, 1])
        with col_cat:
            selected_cat = st.selectbox("Category", available_categories, key="save_category")
        with col_new:
            new_cat = st.text_input("New Category", key="new_category", label_visibility="collapsed", placeholder="New category...")

        chart_category = new_cat if new_cat else selected_cat

        if st.button("Save", use_container_width=True):
            settings = load_saved_settings()

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

            st.success(f"'{chart_name}' saved successfully! (Category: {chart_category})")

    # ========================================
    # Data Preparation & Chart Display
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
        st.warning("No data available for the selected indicators.")
        return

    merged_df = merged_df.sort_values('date')

    # Key Metrics
    st.subheader("Key Metrics")
    cols = st.columns(min(len(indicator_settings), 4))

    for i, (display_key, s) in enumerate(indicator_settings.items()):
        with cols[i % 4]:
            if display_key in merged_df.columns:
                recent = merged_df[display_key].dropna()
                if len(recent) > 0:
                    change = calculate_change(merged_df[display_key])
                    unit = "%" if s.get('transform', 'Raw Data') in ("MoM", "QoQ", "YoY") else ""
                    st.metric(
                        label=f"[{s['source']}] {s['name'][:15]}",
                        value=f"{recent.iloc[-1]:,.2f}{unit}",
                        delta=f"{change:+.2f}%" if change else None
                    )

    st.divider()

    # Chart
    st.subheader("Time Series Comparison")
    fig = create_chart(indicator_settings, merged_df, separate_yaxis, height=500)
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    # Correlation Analysis
    if len(indicator_settings) >= 2:
        with st.expander("Correlation Analysis", expanded=False):
            indicator_options = list(indicator_settings.keys())
            indicator_labels = {k: f"[{v['source']}] {v['name']}" for k, v in indicator_settings.items()}

            base_key = st.selectbox("Base Indicator", options=indicator_options, format_func=lambda x: indicator_labels[x])
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
                        'Indicator': indicator_labels[other_key],
                        'Correlation': f"{current_corr:.3f}" if current_corr else "N/A",
                        'Optimal Lag': f"{optimal_lag} mo",
                        'Max Correlation': f"{max_corr:.3f}"
                    })

                if results:
                    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

    # Data Table
    with st.expander("Raw Data", expanded=False):
        df_show = merged_df.copy()
        rename_map = {'date': 'Date'}
        for k, s in indicator_settings.items():
            if k in df_show.columns:
                rename_map[k] = f"[{s['source']}] {s['name']}"
        df_show = df_show.rename(columns=rename_map)

        st.dataframe(df_show.sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

        csv = df_show.to_csv(index=False).encode('utf-8-sig')
        st.download_button("Download CSV", data=csv, file_name="economic_data.csv", mime="text/csv")


# ============================================================
# Settings Page
# ============================================================

def render_settings_page():
    st.header("Settings")

    settings = load_saved_settings()
    saved_charts = settings.get("saved_charts", [])

    st.subheader("Saved Charts")

    if not saved_charts:
        st.info("No saved charts.")
    else:
        available_categories = settings.get("categories", config.DEFAULT_CATEGORIES)
        all_chart_categories = list(set([c.get("category", "Other") for c in saved_charts]))
        filter_categories = ["All"] + [cat for cat in available_categories if cat in all_chart_categories]

        selected_filter = st.selectbox("Category Filter", filter_categories, key="chart_filter")

        if selected_filter == "All":
            filtered_charts = saved_charts
        else:
            filtered_charts = [c for c in saved_charts if c.get("category", "Other") == selected_filter]

        if not filtered_charts:
            st.info(f"No saved charts in '{selected_filter}' category.")
        else:
            chart_list = list(enumerate(saved_charts))
            filtered_indices = [i for i, c in chart_list if (selected_filter == "All" or c.get("category", "Other") == selected_filter)]

            for row_start in range(0, len(filtered_indices), 2):
                cols = st.columns(2)

                for col_idx, col in enumerate(cols):
                    if row_start + col_idx >= len(filtered_indices):
                        break

                    i = filtered_indices[row_start + col_idx]
                    chart = saved_charts[i]

                    with col:
                        st.markdown(f"**{chart['name']}**")
                        category_label = chart.get("category", "Other")
                        indicators_str = ", ".join([f"{ind['source']}/{ind['id']}" for ind in chart.get('indicators', [])])
                        st.caption(f"[{category_label}] {indicators_str[:40]}...")

                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("Edit", key=f"edit_{i}", use_container_width=True):
                                st.session_state[f"editing_{i}"] = True
                        with btn_col2:
                            if st.button("Delete", key=f"delete_{i}", use_container_width=True):
                                settings["saved_charts"].pop(i)
                                settings["main_layout"] = [l for l in settings.get("main_layout", []) if l.get("chart_id") != chart["id"]]
                                save_settings(settings)
                                st.rerun()

            # Edit mode
            for i, chart in enumerate(saved_charts):
                if st.session_state.get(f"editing_{i}", False):
                    st.divider()
                    st.markdown(f"**Edit: {chart['name']}**")

                    with st.container():
                        new_name = st.text_input("Chart Name", value=chart['name'], key=f"name_{i}")

                        edit_categories = settings.get("categories", config.DEFAULT_CATEGORIES)
                        current_category = chart.get("category", "Other")
                        cat_index = edit_categories.index(current_category) if current_category in edit_categories else 0
                        new_category = st.selectbox("Category", edit_categories, index=cat_index, key=f"cat_{i}")

                        new_separate_yaxis = st.checkbox("Separate Y-Axes", value=chart.get("separate_yaxis", True), key=f"yaxis_{i}")

                        st.write("**Per-Indicator Settings:**")

                        new_indicators = []
                        for j, ind in enumerate(chart.get('indicators', [])):
                            ind_id = ind.get('id', '')
                            ind_source = ind.get('source', '')

                            with st.expander(f"{ind_source}/{ind_id}", expanded=False):
                                current_transform = ind.get('transform', 'Raw Data')
                                transform_idx = config.TRANSFORM_OPTIONS.index(current_transform) if current_transform in config.TRANSFORM_OPTIONS else 0
                                new_transform = st.selectbox(
                                    "Transform", config.TRANSFORM_OPTIONS, index=transform_idx,
                                    key=f"transform_{i}_{j}"
                                )

                                current_shift = ind.get('shift', 0)
                                new_shift = st.slider(
                                    "Lag (months)", -24, 24, current_shift,
                                    key=f"shift_{i}_{j}"
                                )

                                current_chart_type = ind.get('chart_type', 'Line')
                                chart_type_idx = config.CHART_TYPE_OPTIONS.index(current_chart_type) if current_chart_type in config.CHART_TYPE_OPTIONS else 0
                                new_chart_type = st.selectbox(
                                    "Chart Type", config.CHART_TYPE_OPTIONS, index=chart_type_idx,
                                    key=f"charttype_{i}_{j}"
                                )

                                col_rev, col_log = st.columns(2)
                                with col_rev:
                                    new_reverse = st.checkbox("Reverse", value=ind.get('reverse', False), key=f"reverse_{i}_{j}")
                                with col_log:
                                    new_log_scale = st.checkbox("Log Scale", value=ind.get('log_scale', False), key=f"log_{i}_{j}")

                            new_indicators.append({
                                'source': ind_source,
                                'id': ind_id,
                                'transform': new_transform,
                                'shift': new_shift,
                                'chart_type': new_chart_type,
                                'reverse': new_reverse,
                                'log_scale': new_log_scale
                            })

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("Save", key=f"save_{i}", use_container_width=True):
                                settings["saved_charts"][i]["name"] = new_name
                                settings["saved_charts"][i]["category"] = new_category
                                settings["saved_charts"][i]["separate_yaxis"] = new_separate_yaxis
                                settings["saved_charts"][i]["indicators"] = new_indicators
                                save_settings(settings)
                                st.session_state[f"editing_{i}"] = False
                                st.success("Saved successfully!")
                                st.rerun()
                        with col_cancel:
                            if st.button("Cancel", key=f"cancel_{i}", use_container_width=True):
                                st.session_state[f"editing_{i}"] = False
                                st.rerun()

    # Reset
    st.subheader("Reset")
    if st.button("Delete All Settings", type="secondary"):
        save_settings({"saved_charts": [], "main_layout": []})
        st.success("All settings have been deleted.")
        st.rerun()


def render_indicator_management_page(all_data: dict, source_info: dict):
    st.header("Indicator Management")
    st.caption("View collected indicators and configure visibility.")

    settings = load_saved_settings()
    hidden_indicators = settings.get("hidden_indicators", [])

    tabs = st.tabs(["FRED", "ECOS", "BLS"])
    sources = ["FRED", "ECOS", "BLS"]
    countries = {"FRED": "US", "ECOS": "KR", "BLS": "US"}

    for tab, source in zip(tabs, sources):
        with tab:
            info = source_info.get(source, {})
            indicators = info.get("indicators", {})
            categories = info.get("categories", {})

            source_data = all_data.get(source)
            if source_data is None or not source_data.has_data:
                st.info(f"No data collected for {source}.")
                continue
            df_data = source_data.df
            available_indicators = source_data.id_to_name

            indicator_to_category = {}
            for cat_name, cat_list in categories.items():
                for ind_id in cat_list:
                    indicator_to_category[ind_id] = cat_name

            col_save, col_select_all, col_deselect_all = st.columns([2, 1, 1])
            with col_save:
                save_clicked = st.button("Save Changes", key=f"save_{source}", use_container_width=True)
            with col_select_all:
                if st.button("Select All", key=f"all_{source}", use_container_width=True):
                    for ind_id in available_indicators.keys():
                        key = f"{source}:{ind_id}"
                        if key in hidden_indicators:
                            hidden_indicators.remove(key)
                    settings["hidden_indicators"] = hidden_indicators
                    save_settings(settings)
                    st.rerun()
            with col_deselect_all:
                if st.button("Deselect All", key=f"none_{source}", use_container_width=True):
                    for ind_id in available_indicators.keys():
                        key = f"{source}:{ind_id}"
                        if key not in hidden_indicators:
                            hidden_indicators.append(key)
                    settings["hidden_indicators"] = hidden_indicators
                    save_settings(settings)
                    st.rerun()

            st.divider()

            new_hidden = list(hidden_indicators)
            indicator_list = list(available_indicators.items())

            for i in range(0, len(indicator_list), 2):
                cols = st.columns(2)

                for j, col in enumerate(cols):
                    if i + j >= len(indicator_list):
                        break

                    ind_id, ind_name = indicator_list[i + j]
                    key = f"{source}:{ind_id}"
                    is_visible = key not in hidden_indicators

                    category = indicator_to_category.get(ind_id, "Other")

                    date_range = "N/A"
                    if df_data is not None and ind_id in df_data.columns:
                        valid_dates = df_data[df_data[ind_id].notna()]['date']
                        if len(valid_dates) > 0:
                            start = valid_dates.min().strftime('%Y.%m')
                            end = valid_dates.max().strftime('%Y.%m')
                            date_range = f"{start} ~ {end}"

                    with col:
                        korean_name = get_korean_name(ind_id, indicators)
                        short_name = korean_name[:20] + "..." if len(korean_name) > 20 else korean_name

                        new_visible = st.checkbox(
                            f"**{short_name}**",
                            value=is_visible,
                            key=f"vis_{source}_{ind_id}"
                        )

                        if new_visible and key in new_hidden:
                            new_hidden.remove(key)
                        elif not new_visible and key not in new_hidden:
                            new_hidden.append(key)

                        st.caption(f"`{ind_id}` | {category} | {date_range} | Monthly | {countries[source]}")

            if save_clicked:
                settings["hidden_indicators"] = new_hidden
                save_settings(settings)
                st.success("Saved successfully!")
                st.rerun()


# ============================================================
# Main App
# ============================================================

def main():
    st.set_page_config(
        page_title="INVESTWITH Macro Data System",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Premium Light Theme CSS
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: Helvetica, "Helvetica Neue", Arial, sans-serif !important;
    }
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
        width: 72px;
        margin: 0 auto;
        display: block;
    }
    .brand-title {
        text-align: center;
        font-size: 13px;
        font-weight: 600;
        color: #240F33;
        margin-top: 8px;
        margin-bottom: 24px;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }
    h1, h2, h3 {
        color: #0D0D0D !important;
        font-weight: 600;
    }
    [data-testid="stMetric"] {
        background-color: #FAFAF8;
        border: 1px solid #E8E8E4;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .stDownloadButton > button {
        background-color: #FFD559 !important;
        color: #0D0D0D !important;
        border: none !important;
        font-weight: 600;
    }
    .stDownloadButton > button:hover {
        background-color: #F3A950 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    all_data = load_all_data()
    source_info = get_source_info()

    # Sidebar
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
        "Navigation",
        ["Dashboard", "Compare", "Indicators", "Settings"],
        label_visibility="collapsed"
    )

    st.sidebar.divider()

    if page == "Dashboard":
        render_main_page(all_data, source_info)
    elif page == "Compare":
        render_comparison_page(all_data, source_info)
    elif page == "Indicators":
        render_indicator_management_page(all_data, source_info)
    elif page == "Settings":
        render_settings_page()

    # Footer
    st.sidebar.divider()
    st.sidebar.caption("Collapse sidebar with the arrow at top-left")
    st.sidebar.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
