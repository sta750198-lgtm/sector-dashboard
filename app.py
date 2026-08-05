"""
Sector ETF Correlation & Rotation Dashboard - Interactive Version
--------------------------------------------------------------
Run with: streamlit run app.py

Author: Haseeb Ashraf
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# -----------------------------------------------------------------
# CONFIG - all the "knobs" for this dashboard live here, not buried
# in the middle of the code, so they're easy to find and change.
# -----------------------------------------------------------------
SECTOR_ETFS = {
    "XLK": "Technology", "XLF": "Financials", "XLV": "Health Care",
    "XLY": "Cons. Discretionary", "XLP": "Cons. Staples", "XLE": "Energy",
    "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities",
    "XLRE": "Real Estate", "XLC": "Communication",
}
BENCHMARK = "SPY"

# How often (in seconds) the app both re-pulls data AND redraws itself.
# 45s keeps the dashboard feeling "alive" without hammering Yahoo
# Finance's free endpoint - going much lower (e.g. every few seconds)
# risks getting the app rate-limited/blocked, and the underlying daily
# return data doesn't actually change that fast anyway.
DATA_REFRESH_SECONDS = 45

# A small, consistent color per sector so the same sector always shows
# up in the same color across every chart (easier to read at a glance).
SECTOR_COLORS = px.colors.qualitative.Vivid
BENCHMARK_COLOR = "#FFFFFF"

# -----------------------------------------------------------------
# PAGE CONFIG + DARK, "FINTECH" STYLED CSS
# The .streamlit/config.toml file sets the base dark theme; this CSS
# on top of it is just polish - card backgrounds, spacing, a subtle
# accent glow on the title - purely cosmetic, no logic here.
# -----------------------------------------------------------------
st.set_page_config(
    page_title="Sector Rotation Dashboard",
    page_icon="\U0001F4C8",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }

    h1 {
        background: linear-gradient(90deg, #3DDC97, #4FA8FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #2A2F3A;
        border-radius: 12px;
        padding: 1rem 1rem 0.5rem 1rem;
    }

    div[data-testid="stMetricLabel"] { color: #9AA4B2; }

    .live-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background-color: rgba(61, 220, 151, 0.15);
        color: #3DDC97;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(61, 220, 151, 0.4);
    }

    .live-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        background-color: #3DDC97;
        margin-right: 6px;
        box-shadow: 0 0 6px 2px rgba(61, 220, 151, 0.7);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------
# AUTO-REFRESH
# st_autorefresh silently re-runs this whole script on a timer, the
# same way clicking "Rerun" would. Combined with the cache ttl below
# (same interval), that's what makes the page feel live: every
# DATA_REFRESH_SECONDS it wakes up, checks Yahoo Finance for new
# prices, and redraws.
# -----------------------------------------------------------------
st_autorefresh(interval=DATA_REFRESH_SECONDS * 1000, key="auto_refresh_timer")


# -----------------------------------------------------------------
# DATA PULL + CALCULATIONS
# Each function does exactly one thing, so it's easy to test/read in
# isolation - pull data, turn prices into returns, turn returns into
# cumulative performance, turn returns into rolling correlation.
# -----------------------------------------------------------------
@st.cache_data(ttl=DATA_REFRESH_SECONDS)
def pull_price_data(tickers, period):
    raw = yf.download(tickers, period=period, progress=False)
    return raw["Close"]


def compute_daily_returns(close_prices):
    return close_prices.pct_change().dropna()


def compute_cumulative_returns(daily_returns):
    return (1 + daily_returns).cumprod() - 1


def compute_rolling_correlation(daily_returns, window, benchmark):
    rolling_corr = pd.DataFrame(index=daily_returns.index)
    for ticker in daily_returns.columns:
        if ticker == benchmark:
            continue
        rolling_corr[ticker] = (
            daily_returns[ticker].rolling(window).corr(daily_returns[benchmark])
        )
    return rolling_corr.dropna()


def compute_correlation_shifts(rolling_corr, window):
    shifts = []
    for col in rolling_corr.columns:
        start_val = (
            rolling_corr[col].iloc[-window]
            if len(rolling_corr) > window
            else rolling_corr[col].iloc[0]
        )
        end_val = rolling_corr[col].iloc[-1]
        shifts.append({
            "Sector": col,
            f"Corr {window}d ago": round(start_val, 2),
            "Corr now": round(end_val, 2),
            "Sign Flip": (start_val > 0) != (end_val > 0),
        })
    return pd.DataFrame(shifts).sort_values("Corr now")


# -----------------------------------------------------------------
# CHART BUILDERS (Plotly, not matplotlib)
# Plotly charts render as interactive widgets in the browser - hover
# for exact values, click-drag to zoom, click a legend entry to
# hide/show that sector, double-click to reset. matplotlib's st.pyplot
# only ever produced a static image, so this is the actual "make it
# interactive" swap.
# -----------------------------------------------------------------
def build_heatmap_figure(corr_matrix):
    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        aspect="auto",
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=560,
    )
    fig.update_xaxes(side="bottom")
    return fig


def build_relative_strength_figure(cumulative_returns):
    fig = go.Figure()
    sector_cols = [c for c in cumulative_returns.columns if c != "S&P 500 (SPY)"]

    for i, col in enumerate(sector_cols):
        fig.add_trace(go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns[col],
            name=col,
            mode="lines",
            line=dict(width=1.8, color=SECTOR_COLORS[i % len(SECTOR_COLORS)]),
            hovertemplate="%{y:.1%}<extra>" + col + "</extra>",
        ))

    # Benchmark drawn last (on top) and thicker so it's always visible
    # as the reference line the sectors are being compared against.
    fig.add_trace(go.Scatter(
        x=cumulative_returns.index,
        y=cumulative_returns["S&P 500 (SPY)"],
        name="S&P 500 (SPY)",
        mode="lines",
        line=dict(width=3.5, color=BENCHMARK_COLOR, dash="dot"),
        hovertemplate="%{y:.1%}<extra>S&P 500 (SPY)</extra>",
    ))

    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#555")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_tickformat=".0%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        height=460,
        hovermode="x unified",
    )
    return fig


def build_rolling_corr_figure(rolling_corr, selected_sectors):
    fig = go.Figure()
    for i, sector in enumerate(selected_sectors):
        fig.add_trace(go.Scatter(
            x=rolling_corr.index,
            y=rolling_corr[sector],
            name=sector,
            mode="lines",
            line=dict(width=2.2, color=SECTOR_COLORS[i % len(SECTOR_COLORS)]),
            hovertemplate="%{y:.2f}<extra>" + sector + "</extra>",
        ))
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#555")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[-1, 1]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=10, r=10, t=40, b=10),
        height=420,
        hovermode="x unified",
    )
    return fig


# -----------------------------------------------------------------
# SIDEBAR - interactive controls. Every time the user changes one,
# Streamlit re-runs the script top to bottom automatically with the
# new value.
# -----------------------------------------------------------------
st.sidebar.header("Settings")

lookback = st.sidebar.selectbox(
    "Lookback period", options=["3mo", "6mo", "1y", "2y"], index=1
)

rolling_window = st.sidebar.slider(
    "Rolling correlation window (trading days)", min_value=10, max_value=90, value=30, step=5
)

all_sector_names = list(SECTOR_ETFS.values())
selected_sectors = st.sidebar.multiselect(
    "Sectors to highlight in rolling correlation chart",
    options=all_sector_names,
    default=["Energy", "Technology", "Utilities", "Real Estate"],
)

if st.sidebar.button("Force refresh data now"):
    st.cache_data.clear()  # wipes the cache so the next pull is guaranteed fresh
    st.rerun()

st.sidebar.caption(
    f"Auto-refreshes every {DATA_REFRESH_SECONDS} seconds. Prices are "
    "end-of-day / lightly delayed (Yahoo Finance), not real-time "
    "streaming quotes - true tick-by-tick data is institutional "
    "infrastructure (Bloomberg/Refinitiv), not something free tools "
    "have access to."
)

# -----------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------
header_col, badge_col = st.columns([5, 1])
with header_col:
    st.title("Sector ETF Correlation & Rotation Dashboard")
    st.caption("Tracking how S&P sector ETFs move relative to the broader market (SPY)")
with badge_col:
    st.markdown(
        f'<div style="text-align:right; padding-top: 1.6rem;">'
        f'<span class="live-badge"><span class="live-dot"></span>LIVE '
        f'&middot; every {DATA_REFRESH_SECONDS}s</span></div>',
        unsafe_allow_html=True,
    )

all_tickers = list(SECTOR_ETFS.keys()) + [BENCHMARK]
labels = {**SECTOR_ETFS, BENCHMARK: "S&P 500 (SPY)"}

with st.spinner("Pulling market data..."):
    close_prices = pull_price_data(all_tickers, lookback)
    daily_returns = compute_daily_returns(close_prices)

last_update = pd.Timestamp.now().strftime("%H:%M:%S")
st.caption(
    f"Loaded {len(close_prices)} trading days through "
    f"{close_prices.index[-1].date()} &nbsp;|&nbsp; last checked {last_update}"
)

# -----------------------------------------------------------------
# KPI ROW - the headline numbers, before anyone even looks at a chart.
# -----------------------------------------------------------------
cumulative = compute_cumulative_returns(daily_returns)
renamed_cumulative = cumulative.rename(columns=labels)
final_returns = renamed_cumulative.iloc[-1].sort_values(ascending=False)

sector_only_returns = final_returns.drop("S&P 500 (SPY)")
top_sector = sector_only_returns.index[0]
bottom_sector = sector_only_returns.index[-1]

renamed_returns = daily_returns.rename(columns=labels)
corr_matrix = renamed_returns.corr()

rolling_corr_raw = compute_rolling_correlation(daily_returns, rolling_window, BENCHMARK)
rolling_corr = rolling_corr_raw.rename(columns=labels)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Leading Sector", top_sector, f"{sector_only_returns.iloc[0]:+.1%}")
kpi2.metric("Lagging Sector", bottom_sector, f"{sector_only_returns.iloc[-1]:+.1%}")
kpi3.metric("S&P 500 (SPY)", f"{final_returns['S&P 500 (SPY)']:+.1%}", "benchmark")

if len(rolling_corr) > rolling_window and selected_sectors:
    shifts_df = compute_correlation_shifts(rolling_corr, rolling_window)
    n_flips = int(shifts_df["Sign Flip"].sum())
    kpi4.metric("Correlation Sign Flips", n_flips, "vs SPY" if n_flips else "none")
else:
    shifts_df = None
    kpi4.metric("Correlation Sign Flips", "-")

st.divider()

# -----------------------------------------------------------------
# RELATIVE STRENGTH (interactive)
# -----------------------------------------------------------------
st.subheader("Relative Strength")
st.plotly_chart(build_relative_strength_figure(renamed_cumulative), width='stretch')

st.divider()

# -----------------------------------------------------------------
# CORRELATION HEATMAP (interactive)
# -----------------------------------------------------------------
st.subheader("Correlation Matrix")
st.plotly_chart(build_heatmap_figure(corr_matrix), width='stretch')

st.divider()

# -----------------------------------------------------------------
# ROLLING CORRELATION + SIGN-FLIP TABLE (interactive)
# -----------------------------------------------------------------
st.subheader("Rolling Correlation to S&P 500")

if shifts_df is not None:
    st.plotly_chart(
        build_rolling_corr_figure(rolling_corr, selected_sectors), width='stretch'
    )

    st.subheader("Correlation Regime Shifts")
    st.dataframe(shifts_df, hide_index=True, width='stretch')

    flipped = shifts_df[shifts_df["Sign Flip"]]
    if len(flipped) > 0:
        st.warning(f"⚠️ Sign flip detected: {', '.join(flipped['Sector'].tolist())}")
else:
    st.info("Select at least one sector in the sidebar to see the rolling correlation chart.")
