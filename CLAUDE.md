# Project Context for Claude Code

## Who this is for
Haseeb Ashraf, Finance student at Schulich School of Business (York University),
building this project after a coffee chat with a contact on the ETF sales &
trading desk at Scotiabank. The contact asked him to learn some Python and
build something relevant to sales & trading, with an update due **September 3,
2026**. No prior coding experience — this project is also how he's learning
Python, so favor clear, well-commented code over clever/terse code.

## What this project is
A Sector ETF Correlation & Rotation Dashboard. It pulls price data for the
11 S&P sector ETFs + SPY, and analyzes:
- How correlated each sector is to the broader market (SPY)
- How that correlation shifts over time (rolling correlation)
- Which sectors are leading/lagging (relative strength / cumulative return)
- Flags "sign flips" — sectors whose correlation to SPY changed direction
  recently, which signals a sector rotation

This is genuinely relevant to an ETF sales & trading desk: correlation shifts
are exactly the kind of market color a salesperson would reference with
clients.

## Current state
- `sector_dashboard.py` — original static-chart version (saves PNGs, prints
  tables to console). Simpler, still useful for generating images for slides
  or an email.
- `app.py` — interactive Streamlit web app version (recommended). Sidebar
  controls for lookback period, rolling window, and sector selection. Data
  cached for 5 min with a manual refresh button. **This has been tested and
  runs cleanly** as of the last session.
- `requirements.txt` — yfinance, pandas, matplotlib, seaborn, streamlit
- `README.md` — full documentation, setup instructions, sample findings

## Important framing note
Be accurate about data limitations: yfinance provides end-of-day / lightly
delayed prices, NOT real-time streaming quotes. Real-time streaming is
institutional infrastructure (Bloomberg/Refinitiv) not available for free.
Don't oversell this as "real-time" — a desk professional will notice
immediately and it undermines credibility. "Auto-refreshes every 5 minutes"
is accurate; "real-time" is not.

## Coding conventions established so far
- Heavy inline comments explaining *why*, not just what (Haseeb is learning
  Python through this code)
- Functions broken into single-responsibility pieces (pull data / compute
  returns / plot / etc.) rather than one long script
- Config values (tickers, lookback period, window size) live in named
  constants at the top of the file, not hardcoded inline
- No unnecessary complexity — this should stay readable by a beginner

## Possible next steps (not yet started)
- Premium/discount vs NAV tracker for the ETFs themselves
- Extend to factor ETFs (value, growth, momentum, low-vol)
- Automated alert (email/Slack) when a correlation sign-flip is detected
- Deploy the Streamlit app somewhere it's accessible via a link (e.g.
  Streamlit Community Cloud) rather than only running locally
- Push to GitHub so it can be shared as a link

## Deadline
September 3, 2026 update to the Scotiabank contact. Prioritize a working,
demonstrable deliverable over feature completeness.
