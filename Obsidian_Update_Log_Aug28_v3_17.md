# TLCS Terminal & Mobile Suite — Version 3.17 Release Notes
**Release Date:** August 28, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 3.17)
Version 3.17 hardens the end-of-day (EOD) and stale trade closer cron jobs against API changes, schema changes, and query volume limits. It also resolves a visual floating-point precision bug on the Mobile App's Insights tab.

---

## Key Enhancements & Architectural Updates (V3.17)

### 1. Resilient EOD Closer & Database Synchronization
- **Schema Alignment:** Removed deprecated database columns (`outcome_pct`, `r_multiple`) from `eod_closer.py` updates. The script now correctly writes the mathematically exact percentage to `metadata.exact_pct` to comply with Version 1.0 rules.
- **Query Row Limit Safeguard:** Added `.order('created_at', desc=True)` ordering to `eod_closer.py` signals queries. This ensures that the PostgREST 1000-row limit returns the most recent active signals instead of being saturated by old historical rows.
- **Limit Order Expiry Resolution:** Implemented `is_unexecuted_limit` logic to differentiate between filled trades and pending limit orders. The EOD closer now correctly expires unexecuted limit orders as `CANCELLED` (with `exit_reason: EXPIRED_LIMIT`) instead of force-closing them with mock win/loss outcomes.

### 2. Symbol Normalization & Ticker Mapping
- **US Nasdaq Index (`NDQ` / `NDQ1!`):** Added explicit mappings to the Nasdaq 100 index (`^IXIC`) in both `close_stale_trades.py` and `eod_closer.py`. This prevents Nasdaq trades from defaulting to Indian stocks (`.NS`) and skipping price updates.
- **Continuous Contract Suffix Stripping:** Updated `eod_closer.py` to strip the continuous contract suffix (`1!`) from symbol strings so contracts like `GOLD1!` map correctly to their MCX database category.
- **Domestic Equities Memory:** Integrated the canonical list of 50 `NIFTY` stock symbols to ensure equity signals (like `ULTRACEMCO`) map correctly to the `IN` market group.

### 3. Execution Performance & API Rate-Limit Protection
- **Debug Signal Filter:** Updated `close_stale_trades.py` to instantly bypass any signals starting with `DEBUG_`. This prevents sequential HTTP query timeouts against Yahoo Finance and protects the cron runner from getting rate-limited.

### 4. Mobile UI Floating-Point Generalization
- **Rounded average P/L:** Fixed a string interpolation issue in `Tv-Alert-Mobile/src/app/page.tsx` where positive average profit/loss values were displayed as unformatted floats. Applied `.toFixed(2)` consistently so positive values cleanly display as `+0.35%` instead of `+0.3499999999999999%`.

---

## Tagging & Git Version Control
- **Web App Repo (`TLCS_Website_Deploy`):** Pushed to `main`.
- **Mobile App Repo (`Tv-Alert-Mobile`):** Pushed to `main`.
- **Root Repository (`Project`):** Pushed to `main`.

---
*Official Version 3.17 Sealed on August 28, 2026.*
