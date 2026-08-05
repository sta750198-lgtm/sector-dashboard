"""
Sector ETF Correlation & Rotation Dashboard - Interactive Version
--------------------------------------------------------------
Run with: streamlit run app.py

Author: Haseeb Ashraf
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import streamlit as st

# -----------------------------------------------------------------
# PAGE CONFIG - sets the browser tab title and a wide layout
# -----------------------------------------------------------------
st.set_page_config(page_title="Sector Rotation Dashboard", layout="wide")

SECTOR_ETFS = {
    "XLK": "Technology", "XLF": "Financials", "XLV": "Health Care",
    "XLY": "Cons. Discretionary", "XLP": "Cons. Staples", "XLE": "Energy",
    "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities",
    "XLRE": "Real Estate", "XLC": "Communication",
}
BENCHMARK = "SPY"

# -----------------------------------------------------------------
# CACHED DATA PULL
# @st.cache_data means: run this function once, save the result, and
# reuse it instead of re-downloading every time the page redraws.
# ttl=300 means "the cache expires after 300 seconds (5 min)" - so the
# app automatically pulls fresh data periodically without you doing
# anything, but doesn't hammer Yahoo Finance on every click.
# -----------------------------------------------------------------
@st.cache_data(ttl=300)
def pull_price_data(tickers, period):
    raw = yf.download(tickers, period=period, progress=False)
    return raw["Close"]


def compute_daily_returns(close_prices):
    return close_prices.pct_change().dropna()


# -----------------------------------------------------------------
# SIDEBAR - these become interactive controls in the browser.
# Every time the user changes one, Streamlit re-runs the script
# top to bottom automatically with the new value.
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
    "Data auto-refreshes every 5 minutes. Prices are end-of-day / delayed, "
    "not real-time streaming quotes."
)

# -----------------------------------------------------------------
# MAIN PAGE
# -----------------------------------------------------------------
st.title("Sector ETF Correlation & Rotation Dashboard")
st.caption("Tracking how S&P sector ETFs move relative to the broader market (SPY)")

all_tickers = list(SECTOR_ETFS.keys()) + [BENCHMARK]
labels = {**SECTOR_ETFS, BENCHMARK: "S&P 500 (SPY)"}

with st.spinner("Pulling market data..."):
    close_prices = pull_price_data(all_tickers, lookback)
    daily_returns = compute_daily_returns(close_prices)

st.success(f"Loaded {len(close_prices)} trading days through {close_prices.index[-1].date()}")

# --- Return ranking table ---
cumulative = (1 + daily_returns).cumprod() - 1
final_returns = cumulative.rename(columns=labels).iloc[-1].sort_values(ascending=False)

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Return Ranking")
    ranking_df = (final_returns * 100).round(1).reset_index()
    ranking_df.columns = ["Sector", "Return %"]
    st.dataframe(ranking_df, hide_index=True, use_container_width=True)

with col2:
    st.subheader("Relative Strength")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    renamed_cum = cumulative.rename(columns=labels)
    for col in renamed_cum.columns:
        if col == "S&P 500 (SPY)":
            ax.plot(renamed_cum.index, renamed_cum[col], label=col, color="black", linewidth=2.5, zorder=10)
        else:
            ax.plot(renamed_cum.index, renamed_cum[col], label=col, linewidth=1.2, alpha=0.85)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    ax.grid(alpha=0.25)
    st.pyplot(fig)
    plt.close(fig)

st.divider()

# --- Correlation heatmap ---
st.subheader("Correlation Matrix")
renamed_returns = daily_returns.rename(columns=labels)
corr_matrix = renamed_returns.corr()
fig2, ax2 = plt.subplots(figsize=(11, 8))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            square=True, linewidths=0.5, vmin=-1, vmax=1, ax=ax2)
st.pyplot(fig2)
plt.close(fig2)

st.divider()

# --- Rolling correlation + sign-flip table ---
st.subheader("Rolling Correlation to S&P 500")

rolling_corr = pd.DataFrame(index=daily_returns.index)
for ticker in daily_returns.columns:
    if ticker == BENCHMARK:
        continue
    rolling_corr[ticker] = daily_returns[ticker].rolling(rolling_window).corr(daily_returns[BENCHMARK])
rolling_corr = rolling_corr.dropna().rename(columns=labels)

if len(rolling_corr) > rolling_window and selected_sectors:
    fig3, ax3 = plt.subplots(figsize=(11, 5))
    for sector in selected_sectors:
        ax3.plot(rolling_corr.index, rolling_corr[sector], label=sector, linewidth=2)
    ax3.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax3.set_ylim(-1, 1)
    ax3.legend(loc="upper left", fontsize=9)
    ax3.grid(alpha=0.25)
    st.pyplot(fig3)
    plt.close(fig3)

    shifts = []
    for col in rolling_corr.columns:
        start_val = rolling_corr[col].iloc[-rolling_window] if len(rolling_corr) > rolling_window else rolling_corr[col].iloc[0]
        end_val = rolling_corr[col].iloc[-1]
        shifts.append({
            "Sector": col,
            f"Corr {rolling_window}d ago": round(start_val, 2),
            "Corr now": round(end_val, 2),
            "Sign Flip": (start_val > 0) != (end_val > 0),
        })
    shifts_df = pd.DataFrame(shifts).sort_values("Corr now")

    st.subheader("Correlation Regime Shifts")
    st.dataframe(shifts_df, hide_index=True, use_container_width=True)

    flipped = shifts_df[shifts_df["Sign Flip"]]
    if len(flipped) > 0:
        st.warning(f"⚠️ Sign flip detected: {', '.join(flipped['Sector'].tolist())}")
else:
    st.info("Select at least one sector in the sidebar to see the rolling correlation chart.")
