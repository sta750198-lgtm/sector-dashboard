"""
Sector ETF Correlation & Rotation Dashboard
--------------------------------------------
Pulls sector ETF price data, computes correlations to the S&P 500,
and flags sectors whose relationship to the market is shifting.

Author: Haseeb Ashraf
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf

# ---------------------------------------------------------------
# CONFIG - change these to adjust the analysis without touching
# the logic below
# ---------------------------------------------------------------
SECTOR_ETFS = {
    "XLK": "Technology", "XLF": "Financials", "XLV": "Health Care",
    "XLY": "Cons. Discretionary", "XLP": "Cons. Staples", "XLE": "Energy",
    "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities",
    "XLRE": "Real Estate", "XLC": "Communication",
}
BENCHMARK = "SPY"
LOOKBACK_PERIOD = "6mo"     # how much history to pull
ROLLING_WINDOW = 30          # trading days for rolling correlation
HIGHLIGHT_SECTORS = ["Energy", "Technology", "Utilities", "Real Estate"]


# ---------------------------------------------------------------
# FUNCTIONS - each one does exactly one job. This makes the code
# reusable and easy to test/debug piece by piece.
# ---------------------------------------------------------------

def pull_price_data(tickers, period):
    """Download close prices for a list of tickers."""
    raw = yf.download(tickers, period=period, progress=False)
    return raw["Close"]


def compute_daily_returns(close_prices):
    """Convert price levels into daily percent returns."""
    return close_prices.pct_change().dropna()


def plot_correlation_heatmap(daily_returns, labels, save_path):
    renamed = daily_returns.rename(columns=labels)
    corr = renamed.corr()
    plt.figure(figsize=(11, 9))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                square=True, linewidths=0.5, vmin=-1, vmax=1)
    plt.title("Sector ETF Correlation Matrix (6-Month Daily Returns)", fontsize=13, pad=15)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    return corr


def plot_relative_strength(daily_returns, labels, benchmark_label, save_path):
    cumulative = (1 + daily_returns).cumprod() - 1
    cumulative = cumulative.rename(columns=labels)
    plt.figure(figsize=(12, 7))
    for col in cumulative.columns:
        if col == benchmark_label:
            plt.plot(cumulative.index, cumulative[col], label=col,
                      color="black", linewidth=2.5, zorder=10)
        else:
            plt.plot(cumulative.index, cumulative[col], label=col,
                      linewidth=1.3, alpha=0.85)
    plt.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    plt.title("Sector Relative Strength — Cumulative Return", fontsize=13)
    plt.ylabel("Cumulative Return")
    plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
    plt.legend(loc="upper left", fontsize=8, ncol=2)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    return cumulative.iloc[-1].sort_values(ascending=False)


def compute_rolling_correlation(daily_returns, benchmark, window):
    rolling_corr = pd.DataFrame(index=daily_returns.index)
    for ticker in daily_returns.columns:
        if ticker == benchmark:
            continue
        rolling_corr[ticker] = daily_returns[ticker].rolling(window).corr(daily_returns[benchmark])
    return rolling_corr.dropna()


def plot_rolling_correlation(rolling_corr, labels, highlight, window, save_path):
    renamed = rolling_corr.rename(columns=labels)
    plt.figure(figsize=(12, 6))
    for col in highlight:
        plt.plot(renamed.index, renamed[col], label=col, linewidth=2)
    plt.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    plt.title(f"{window}-Day Rolling Correlation to {BENCHMARK}", fontsize=13)
    plt.ylabel("Correlation")
    plt.ylim(-1, 1)
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()


def flag_correlation_shifts(rolling_corr, labels, lookback_days=30):
    """Identify sectors whose correlation to the benchmark flipped sign."""
    renamed = rolling_corr.rename(columns=labels)
    shifts = []
    for col in renamed.columns:
        start_val = renamed[col].iloc[-lookback_days]
        end_val = renamed[col].iloc[-1]
        flipped = (start_val > 0) != (end_val > 0)
        shifts.append({
            "Sector": col,
            f"Corr {lookback_days}d ago": round(start_val, 2),
            "Corr now": round(end_val, 2),
            "Sign Flip": flipped,
        })
    return pd.DataFrame(shifts).sort_values("Corr now")


# ---------------------------------------------------------------
# MAIN - runs the full pipeline start to finish
# ---------------------------------------------------------------

def main():
    all_tickers = list(SECTOR_ETFS.keys()) + [BENCHMARK]
    labels = {**SECTOR_ETFS, BENCHMARK: "S&P 500 (SPY)"}

    print(f"Pulling {LOOKBACK_PERIOD} of data for {len(all_tickers)} tickers...")
    close_prices = pull_price_data(all_tickers, LOOKBACK_PERIOD)
    close_prices.to_csv("sector_close_prices.csv")

    daily_returns = compute_daily_returns(close_prices)

    print("Building correlation heatmap...")
    plot_correlation_heatmap(daily_returns, labels, "sector_correlation_heatmap.png")

    print("Building relative strength chart...")
    final_returns = plot_relative_strength(daily_returns, labels, "S&P 500 (SPY)",
                                            "sector_relative_strength.png")

    print("Computing rolling correlation...")
    rolling_corr = compute_rolling_correlation(daily_returns, BENCHMARK, ROLLING_WINDOW)
    plot_rolling_correlation(rolling_corr, SECTOR_ETFS, HIGHLIGHT_SECTORS,
                              ROLLING_WINDOW, "rolling_correlation.png")

    shifts = flag_correlation_shifts(rolling_corr, SECTOR_ETFS, ROLLING_WINDOW)

    print("\n=== 6-Month Return Ranking ===")
    print((final_returns * 100).round(1).astype(str) + "%")

    print(f"\n=== Correlation Shift Check ({ROLLING_WINDOW}d ago -> now) ===")
    print(shifts.to_string(index=False))

    print("\nDone. Charts saved: sector_correlation_heatmap.png, "
          "sector_relative_strength.png, rolling_correlation.png")


if __name__ == "__main__":
    main()
