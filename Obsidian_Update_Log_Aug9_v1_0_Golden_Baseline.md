# TLCS Terminal & Mobile Suite — Version 1.0 Production Freeze & Golden Baseline Release Notes
**Release Date:** August 9, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 1.0 Golden Baseline)
Version 1.0 represents the **official production freeze and canonical baseline** for the entire TLCS Trading Terminal suite. All systems — including Pine Script indicator algorithms, Netlify backend webhooks and background workers, Supabase database schemas and triggers, the Web Dashboard, and the Mobile Application — are locked into a rock-solid, production-hardened release state.

---

## Golden Baseline Architecture & System Contract (V1.0)

### 1. Single Source of Truth for Trade Metrics (`exact_pct`)
- Deprecated all R-multiple and TradingView `outcome_pct` parsing.
- Performance metrics (Win Rate, Profit Factor, Expectancy, Best Trade, Max Drawdown) across both Web and Mobile platforms strictly calculate off the exact percentage formula: `((Exit - Entry) / Entry) * 100`.
- Mathematical outcome resolution (`resolveOutcome`): `exact_pct > 0` = `WIN`, `exact_pct < 0` = `LOSS`, `exact_pct === 0` = `BREAKEVEN`. `exact_pct` is evaluated BEFORE keyword status strings.

### 2. Exclusive Netlify Infrastructure
- Entire system operates **EXCLUSIVELY on Netlify** (`thelioncapitalsolutions.com` web client & backend serverless functions, `market-store.online` mobile client). Zero Vercel dependencies exist.

### 3. Market-Wise Telegram Alert Routing
- Telegram alerts route dynamically based on symbol market category (`TELEGRAM_CHAT_ID_NIFTY`, `TELEGRAM_CHAT_ID_MCX`, `TELEGRAM_CHAT_ID_NYMEX`, `TELEGRAM_CHAT_ID_CRYPTO`, `TELEGRAM_CHAT_ID_FOREX`, `TELEGRAM_CHAT_ID_WORLD`).
- Telegram alerts fire **ONLY** for executed active trades (`⚡ TRADE ACTIVE`) or trailing SL / closing fills (`TARGET` / `SL`). Alerts NEVER fire for unexecuted limit orders (`ACTIVE LIMIT`).

### 4. Zero-Guesswork Real Trade Entry & Hold Duration
- Trade cards strictly display **SIGNAL TIME** (limit order placement time) in the top-right header, and **REAL ENTRY TIME** (`metadata.real_entry_time`, exact fill millisecond) inside the ENTRY card block.
- Hold duration (`HELD:` / `ALIVE:`) is computed strictly when `real_entry_time` is present. If `real_entry_time` is absent, the UI strictly presents `HELD: --` to prevent artificial guesswork.

### 5. Standardized 15-Minute Opening Range Scanner Trigger
- Day Type Blueprints (Rejection, Absorption, Failed New Low, Outside Day, Stop Run Day) and Trade Sequences lock in at the **15-minute Opening Candle** close across all 6 market categories.
- UI automatically synchronizes scanner state every 5 seconds and instantly upon switching to the ANALYTICS tab.

### 6. High-Density UI & Responsive Viewport Design
- **Web Dashboard:** Compact Alert Signal Rankings cards with high-density inline header rows (`RANK #1`, strategy title, trade count, WR, Net Profit).
- **Mobile Application:** Responsive 5-column strategy table (`table-fixed w-full`) fitting mobile screens 100% cleanly with dark grid aesthetics (`#080c14` background, `#e2b33c` gold headers).

---

## Tagging & Git Version Control
- **Web App Repo (`TLCS_Website_Deploy`):** Version `1.0.0` package, Git Tag `v1.0`.
- **Mobile App Repo (`Tv-Alert-Mobile`):** Version `1.0.0` package, Header `TLCS TERMINAL v1.0`, Git Tag `v1.0`.
- **Root Repository (`Project`):** Version `1.0.0` Golden Baseline commit & Git Tag `v1.0`.

---
*Official Version 1.0 Production Freeze Sealed on August 9, 2026.*
