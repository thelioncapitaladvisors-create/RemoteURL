# Version 1.2.1 Update Log - July 19, 2026

## 🚀 Enhancements & Features

### 1. Stale Active Limits Sweep (24-Hour EOD Closer)
- **Engine Logic Enhancement:** Added a new background cron script (`close_stale_trades.py`) that forcefully sweeps the database for any trades sitting as `OPEN` or `Active` for more than 24 hours.
- **Global Markets Fallback:** Extended the yfinance EOD fetching logic to fully support Crypto (`BTCUSDT` -> `BTC-USD`) and Forex (`NZDUSD` -> `NZDUSD=X`), which previously bypassed the legacy EOD closer.
- **Automated Execution:** The database sweep is now automatically orchestrated by a newly implemented GitHub Actions workflow (`stale_trades_cron.yml`) that triggers every 6 hours.

### 2. Exact Percentage Rule Compliance
- Strictly enforced the Version 1.1 architectural mandate where mathematically guessing logic (like `r_multiple` or `outcome_pct`) is bypassed. The script derives the `exact_pct` directly from the current yfinance price versus the trade's entry.
- Trades successfully categorized under Win, Loss, or Breakeven now contribute cleanly to the Dashboard and AI Research statistics instead of permanently polluting the Active Limits count. Limit orders missing prices are safely cleaned up and flagged as `CANCELLED`.
