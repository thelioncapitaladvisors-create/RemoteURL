# TLCS Terminal & Mobile Suite — Version 3.20 Release Notes
**Release Date:** August 30, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)  
**GitHub Version Tag:** `v3.20.0` / `v3.20`

---

## Executive Summary (Version 3.20)
Version 3.20 delivers a comprehensive architectural fix for the **Performance Analytics Statistics Engine** across the Web Platform (`dashboard.html`) and Mobile Application (`ANALYTICS` tab). It resolves Numba bytecode cache incompatibilities, eliminates empty statistical dataframe fallbacks, institutes an automated resilient direct-calculation math fallback, introduces clean matrix value sanitization (`NaN`/`NaT`/`inf` -> `-`), and resolves Pine Script v5 global-scope compilation formatting.

---

## Key Enhancements & Architectural Updates (V3.20)

### 1. Performance Analytics Statistics Engine Restoration (`strategy_tearsheet.html`)
- **Numba JIT Cache Isolation**: Enforced `NUMBA_DISABLE_CACHING=1` at the top of the tearsheet generation pipeline and purged corrupted bytecode cache files (`*.nbc` / `*.nbi`) that caused unpickling failures (`ValueError: incorrect value for flags variable`).
- **Resilient Statistical Math Fallback**:
  - Replaced the vulnerable `try...except -> pd.DataFrame(columns=markets)` empty-table failure mode with a robust mathematical fallback engine.
  - If VectorBT's aggregated `.stats()` throws an exception, the system automatically computes complete statistical metrics (`Total Return [%]`, `Annualized Return [%]`, `Annualized Volatility [%]`, `Max Drawdown [%]`, `Sharpe Ratio`, `Calmar Ratio`, `Sortino Ratio`, `Skew`, `Kurtosis`, etc.) directly from historical returns.
- **Polished Matrix Sanitization**:
  - Automatically formats float returns and percentages to 2 decimal places (`f'{val:.2f}%'`).
  - Safely converts unpopulated asset classes, invalid metrics, `NaN`, `NaT`, and infinite ratios (`inf`, `-inf`) into clean, consistent `-` placeholders.
- **Immediate Deployment**: Regenerated `strategy_tearsheet.html` populated with all 175 closed historical trades across all 6 core markets (`NIFTY`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`, `WORLD`).

### 2. Multi-Path Environment Configuration
- Updated `TLCS_Website_Deploy/generate_tearsheet.py` and `algo_engine/backtest_edge.py` with multi-path `.env` resolution (`.env`, `.env.local`, `algo_engine/.env`, `Tv-Alert-Mobile/.env.local`) to ensure local execution, CI/CD runners, and scheduled cron workflows seamlessly locate Supabase credentials regardless of the current working directory.

### 3. Pine Script v5 Indicator Syntax Optimization
- Diagnosed and resolved TradingView compilation error `Mismatched input {unexpectedToken} expecting set {expecting} (CE10013)` caused by unintended leading indentation on global variable declarations.
- Standardized multi-line condition continuation formatting for `dX` and `mX` day type and bias evaluation.

---

## Files Modified & Created

### Algorithmic Engine & Generators
- `TLCS_Website_Deploy/generate_tearsheet.py`: Added resilient statistical calculation, clean value formatting, multi-path `.env` loading, and Numba cache disable flags.
- `algo_engine/backtest_edge.py`: Updated with matching resilient statistical calculation, formatting, and environment resolution.
- `TLCS_Website_Deploy/strategy_tearsheet.html`: Regenerated with complete, populated statistical matrices across all markets.

### Documentation & Logs
- `Obsidian_Update_Log_Aug30_v3_20.md` *(NEW)*: Release documentation for Version 3.20.

---

## Git Tagging & Version Control
- **Tag:** `v3.20.0` / `v3.20`
- **Repos:**
  - `Tv-Alert-Mobile` → `v3.20.0`
  - `TLCS_Website_Deploy` → `v3.20.0`
  - `Project` (Root) → `v3.20.0`

---
*Official Version 3.20 Sealed on August 30, 2026.*
