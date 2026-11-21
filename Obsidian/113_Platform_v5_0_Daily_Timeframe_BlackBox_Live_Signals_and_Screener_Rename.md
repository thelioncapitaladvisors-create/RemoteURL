# Obsidian Document 113: Platform v5.0 Daily Timeframe (1D Swing) BlackBox Signals, Nil-Signal Gating & Screener Tab Header Standardization

**Status**: Implemented & Verified in Production  
**Date**: November 21, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Autonomous BlackBox Engine (`algo_engine/`), Supabase Ingestion (`shadow_signals`), Next.js Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, `RemoteURL/page.tsx`), and Knowledge Base (`Obsidian/`, `AGENTS.md`).

---

## 1. Executive Summary & User Requirements

Under Platform Version 5.0, three key directives have been fully executed:
1. **Daily Timeframe (1D Swing) Live Signals**: Enabled autonomous Daily Timeframe (1D Swing) execution signal generation via the Python BlackBox engine for approved universe markets (NIFTY Indices, NSE Top 100 Equities, and MCX Commodities), populating Supabase `shadow_signals` with genuine, mathematically verified limit orders and swing setups.
2. **Nil-Signal Clean Hiding**: On the INSIGHTS tab (`activeTab === 'INSIGHTS'`), gated `renderDhanLiveSignalsSection()` and `renderDhanUnifiedBiasScreener()` to return `null` when `liveSignalsStats.total === 0`, ensuring the section remains completely collapsed and hidden during zero-signal intervals (such as non-trading days or when no candidates qualify).
3. **Screener Tab Header Standardization**: Renamed the sticky header banner from `TLCS SIGNALS` to **`TLCS INTRADAY TRADE SIGNALS`** in the 7-Day Matrix inside the Screener tab, establishing unambiguous visual distinction between 15-minute intraday execution signals and 1D daily swing signals.

---

## 2. Core Architectural Implementation

### 2.1 Autonomous Daily Timeframe (1D Swing) Scanner Engine
- **Historical Daily Candle Ingestion**:
  - Implemented `fetch_daily_candles(symbol, days=60)` in `DhanFeed` (`algo_engine/feeds/dhan_feed.py` and `RemoteURL/algo_engine/feeds/dhan_feed.py`).
  - Calls DhanHQ's historical chart endpoint (`https://api.dhan.co/v2/charts/historical`) for equities (`NSE_EQ`) and commodities (`MCX_COMM`), converting responses into chronological OHLC candle sequences.
- **Dynamic MCX Front-Month Contract Resolution**:
  - Leveraged `ScripResolver` to resolve active front-month commodity futures (e.g. `CRUDEOIL` Dec FUT `576264`, `NATURALGAS` Nov FUT `574581`), preventing expired contract stalls.
- **Strategy Engine Evaluation**:
  - Created `algo_engine/run_daily_scanner.py` (and mirrored to `RemoteURL`).
  - Evaluates all approved universe assets against canonical `StrategyEngine`:
    - **Missile**: Bullish/Bearish trend expansion with EMA alignment.
    - **Scalp**: High-velocity momentum setups.
    - **Lightning**: Native Missile + Scalp confluence.
    - **Extreme Reversal**: Bollinger Band exhaustion reversals.
    - **Divergence**: RSI Regular and Hidden divergences with symmetrical DMI momentum gating.
    - **Virgin CPR**: Touch tests of unbreached CPR zones.
  - Strict $H_4/L_4$ limit touch-point gating: Long entries require `low < H4`; Short entries require `high > L4`.

### 2.2 Supabase Shadow Pipeline Ingestion Parity
- **Schema Alignment**:
  - Updated `ShadowPipeline.sync_signal` in `algo_engine/shadow_pipeline.py`.
  - Stored `timeframe: '1D'` and `interval: '1D'` inside JSONB `metadata` (conforming to Supabase `shadow_signals` table schema without unsupported root columns).
  - Preserved status as `ACTIVE LIMIT` with canonical fields (`entry`, `stop`, `target`, `tp2`, `tp3`, `tp4`).
- **Initial Scan Results**:
  - Scanned all 115 approved symbols across NIFTY, STOCKS, and MCX.
  - Generated and inserted **29 authentic Daily 1D Swing execution signals** directly into Supabase `shadow_signals` (`HTTP/2 201 Created`), including `CRUDEOIL` Short Missile, `NATURALGAS` Long Missile, `RELIANCE` Long Missile, `IOC` Long Missile & Short Virgin CPR, and `INDIGO` Long Virgin CPR.

### 2.3 Frontend INSIGHTS Tab & Session-Resilient Swing Order Retention
- **Active Limit & Live Swing Protection**:
  - In `extractDhanScreenerAssets`:
    - Fixed `hasEntered` check: `(Boolean(s.updated_at) && !stUpper.includes('LIMIT') && stUpper !== 'OPEN')` ensures newly inserted limit orders remain classified as `ACTIVE LIMIT` rather than prematurely elevated to `LIVE`.
    - Session Filter update: When `liveActionOnly` is true and `tradeLifecycle === 'ACTIVE LIMIT' | 'LIVE'`, active swing orders are preserved across calendar days and non-trading days under `sessionFilter === 'TODAY'`.
    - Enabled Virgin CPR touch recognition in `ALL_LIVE` pass-through (`⚡ VCPR TOUCH`).
    - Decoupled `assetMap` key: `${cSym}_${s.id || s.type || relBadge}` ensures individual distinct execution signals for the same symbol render as separate rows.
- **Dynamic Nil-Signal Hiding**:
  - In `renderDhanLiveSignalsSection`: Returns `null` when `(liveSignalsStats?.total || 0) === 0`.
  - In `renderDhanUnifiedBiasScreener`: Returns `null` if `liveSection` is empty on the INSIGHTS tab.

### 2.4 Screener Tab Banner Renaming
- In `renderDhanUnifiedBiasScreener()` (7-Day Matrix sticky header):
  - Renamed `TLCS SIGNALS` to **`TLCS INTRADAY TRADE SIGNALS`** with `7-DAY MATRIX` badge.
  - Synchronized across `Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, and root `page.tsx`.

---

## 3. Verification & Compliance Matrix

| Component | Status | Verification Detail |
| :--- | :---: | :--- |
| `Daily BlackBox Scanner` | ✅ Verified | `python3 algo_engine/run_daily_scanner.py --market all` generated 29 authentic 1D signals |
| `Supabase Ingestion` | ✅ Verified | `shadow_signals` populated with `timeframe: '1D'`, `status: 'ACTIVE LIMIT'`, HTTP 201 Created |
| `INSIGHTS Live Matrix` | ✅ Verified | Displays active 1D limit orders and swing trades with setup pills and category chips |
| `Nil-Signal Hiding` | ✅ Verified | `renderDhanLiveSignalsSection` returns `null` when total signals === 0 |
| `Screener Renaming` | ✅ Verified | `TLCS INTRADAY TRADE SIGNALS` rendered in 7-Day Matrix |
| `Next.js Production Build` | ✅ Verified | `npm run build` passed with exit code `0` (8/8 static routes) |
| `Multi-Repository Parity` | ✅ Verified | `Tv-Alert-Mobile`, `RemoteURL`, and root `Project` synchronized under `v5.0` |

---

## 4. Commits Pushed (v5.0)

- **`Tv-Alert-Mobile`**: Commit `2c9df3d` (`feat(v5.0): enable Daily 1D Swing BlackBox live signals on INSIGHTS tab`)
- **`RemoteURL`**: Commit `bbccefb` (`feat(v5.0): enable Daily 1D Swing BlackBox live signals on INSIGHTS tab`)
- **Root `Project`**: Commit `559c0a3` (`feat(v5.0): enable Daily 1D Swing BlackBox live signals on INSIGHTS tab`)
