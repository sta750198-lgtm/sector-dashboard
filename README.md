# Sector ETF Correlation & Rotation Dashboard

An interactive web app (built with Streamlit) that pulls sector ETF price
data and analyzes how correlated each sector is to the broader market —
both right now and how that relationship has shifted over time. Change
settings in the sidebar and the whole dashboard updates live.

There are two versions in this project:
- **`app.py`** — the interactive Streamlit dashboard (recommended)
- **`sector_dashboard.py`** — the original static-chart script, still
  useful for quickly generating PNGs to drop into an email or slide

## A note on "live" data

This pulls end-of-day / lightly-delayed prices from Yahoo Finance, not
real-time tick-by-tick streaming quotes — true intraday streaming data
is institutional-grade infrastructure (Bloomberg, Refinitiv) that isn't
publicly available for free. The app re-pulls fresh data automatically
every 5 minutes, and has a manual "force refresh" button, so it always
reflects current market conditions even if it's not a live tick feed.

## Why this matters for sales & trading

Sector correlation to the benchmark is something a trading desk watches
constantly. When a sector's correlation to SPY drifts or flips sign, it
signals a rotation — money moving out of one part of the market and into
another — which is exactly the kind of color a salesperson uses in client
conversations. This tool automates that observation instead of eyeballing
it.

## What it produces

Running the script generates three charts and two summary tables:

1. **`sector_correlation_heatmap.png`** — full correlation matrix across
   all 11 sectors + SPY, over the last 6 months of daily returns.
2. **`sector_relative_strength.png`** — cumulative return per sector over
   6 months, so you can see which sectors have led/lagged the index.
3. **`rolling_correlation.png`** — 30-day rolling correlation to SPY for
   4 key sectors (Energy, Technology, Utilities, Real Estate), showing how
   the relationship moves over time rather than a single static number.
4. **Return ranking** (printed to console) — every sector's 6-month
   cumulative return, sorted best to worst.
5. **Correlation shift table** (printed to console) — each sector's
   correlation to SPY 30 days ago vs. now, flagging any sign flips
   (a sector that went from moving *with* the market to moving *against*
   it, or vice versa).

## Setup

```bash
# 1. Create a virtual environment (keeps this project's packages separate
#    from anything else on your machine)
python3 -m venv venv

# 2. Activate it
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the interactive dashboard

```bash
streamlit run app.py
```

This opens automatically in your browser (usually `http://localhost:8501`).
From there you can:
- Change the lookback period (3mo / 6mo / 1y / 2y)
- Adjust the rolling correlation window
- Pick which sectors to highlight
- Hit "Force refresh data now" to pull the latest prices on demand

Leave the terminal window running while you use the app — closing it
shuts the app down. To stop it, go back to the terminal and press Ctrl+C.

## Running the static-chart version

```bash
python3 sector_dashboard.py
```

This regenerates the three PNG charts and prints both summary tables to
the console — useful if you just want images to paste into an email.

## Configuration

All the adjustable settings live at the top of `sector_dashboard.py`:

- `LOOKBACK_PERIOD` — how much price history to pull (default `"6mo"`)
- `ROLLING_WINDOW` — the window size for rolling correlation, in trading
  days (default `30`)
- `HIGHLIGHT_SECTORS` — which sectors appear on the rolling correlation
  chart (default: Energy, Technology, Utilities, Real Estate)

## Sample findings (as of Aug 5, 2026)

- **Technology** has been the standout leader, up ~38% over 6 months —
  and its correlation to SPY sits consistently around 0.8–0.9, reflecting
  how much weight tech carries in the index.
- **Energy** has traded with a persistently *negative* correlation to
  SPY (-0.35 to -0.45) for most of the period — moving opposite the
  broader market rather than with it.
- **Utilities** is the notable rotation story: its correlation to SPY
  flipped from slightly positive (+0.03) to negative (-0.23) over the
  most recent 30-day window — a clear regime shift worth flagging.

## Possible extensions

- Add a premium/discount vs. NAV tracker for the ETFs themselves
- Extend beyond sectors to factor ETFs (value, growth, momentum, low-vol)
- Automate a daily email/Slack summary when a sign flip is detected
- Add international sector ETFs for a global rotation view
