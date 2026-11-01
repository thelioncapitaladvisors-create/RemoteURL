# 84. Platform v2.0 — Divergence Screener Filter, Confluence Pipeline Hardening, and VectorBT Standalone Benchmarks

## Executive Summary
**Release Date**: November 1, 2026 (22:15 IST)  
**Release Tag**: `v2.0` / `v2.0.0`  
**Components**: `Tv-Alert-Mobile` (Next.js 14 PWA), `TLCS_Website_Deploy` (Netlify Functions & Webhook Ingestion), `algo_engine` (Python BlackBox Scanner & Daemon), `TV Indicator` (Pine Script @v6 Indicator & Execution Wrapper), `Project Backup Mirrors`, `Obsidian Vault`  
**Status**: 100% Production Ready, Built, Verified, and Pushed  

This release implements the definitive **Platform Version 2.0 Divergence & Confluence Architecture Release**, introducing a dedicated **Divergence Screener Filter** on the Insights tab strictly restricted to key commodity contracts (**NG**, **CL**, **GC**, **SI** on MCX & NYMEX) and **GIFT NIFTY**, adding verified **Regular & Hidden Divergence Standalone Benchmark Rows** to the VectorBT tearsheet, resolving the root-cause bottlenecks that suppressed confluence signals over the preceding 48 hours across indicators, webhooks, and the Python BlackBox scanner, and synchronizing all project mirrors and local backup directories.

---

## 1. Divergence Screener Filter Architecture (`market-store.online`)

### 1.1 Motivation & Universe Gating
To give institutional traders rapid visibility into momentum exhaustion and trend continuation setups on primary commodity and macro index assets, a dedicated Divergence Screener filter was introduced to Section 4 of the Insights tab, mirroring the VCPR architecture.
- **Strictly Allowed Universe**:
  - MCX Commodities: `NATURALGAS` (`NG`), `CRUDEOIL` (`CL`), `GOLD` (`GC`), `SILVER` (`SI`) (including mini contracts).
  - NYMEX / COMEX Commodities: `NG1!`, `CL1!`, `GC1!`, `SI1!`.
  - Macro Index: `GIFTNIFTY` / `NSEIX:NIFTY1!`.
  - All standard equities, base metals (Copper, Zinc, Aluminium), and foreign forex/crypto pairs are strictly excluded from the Divergence filter.

### 1.2 Interactive Controls & Sub-Filters
- **Divergence Sub-Filter**: `[⚡ ALL DIVERGENCES]`, `[🎯 REGULAR]`, and `[🔍 HIDDEN]` with real-time asset count badges.
- **Market Chips**: `[🌐 ALL MARKETS]`, `[🛢️ MCX]`, `[🇺🇸 NYMEX]`, `[🇮🇳 GIFT NIFTY]`.
- **Session Filter**: `[TODAY]` (live intraday session signals) vs `[ALL]` (historical recent sessions).
- **Inspection Modal**: Integrated Momentum Divergence framework checklist with violet branding theme (`#9333ea`).

---

## 2. VectorBT Standalone Divergence Quantitative Benchmarks

The **VectorBT Confluence Quantitative Benchmark** table on the Insights tab was expanded to incorporate the baseline parameters for standalone divergence models:
1. **Regular Divergence (Standalone)**:
   - Standalone PF: `1.31`
   - Confluence PF: `1.31`
   - Edge Delta: `BASELINE`
   - Standalone MDD: `10.62%`
   - Confluence MDD: `6.23%` (`-41.3%`)
   - VBT Win Rate: `26.10%`
2. **Hidden Divergence (Standalone)**:
   - Standalone PF: `0.96`
   - Confluence PF: `1.18`
   - Edge Delta: `+22.9%`
   - Standalone MDD: `2.81%`
   - Confluence MDD: `1.85%` (`-34.2%`)
   - VBT Win Rate: `38.46%`

---

## 3. Confluence Signal Pipeline Resolution (Root Cause Audit & Fixes)

Over the preceding 2 days, zero confluence signals were recorded. Comprehensive cross-stack audit identified and fixed 4 compounding bottlenecks:

### 3.1 Pine Script Alert Payload Telemetry Omission
- **Root Cause**: `sendAlert` previously omitted `"is_confluence"` and `"confluence_type"` in the alert JSON payload string, emitting only raw `"LONG MISSILE"`.
- **Fix**: Updated `sendAlert` and `initializeAndPushTrade` across `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, and `user_code.pine` to emit `"is_confluence":{14},"confluence_type":"{15}"`. Expanded confirmation buffer from 2 bars to 6 bars (`regBullDiv[0..5]` / `hiddenBullishConfirmed[0..5]`).

### 3.2 DhanHQ Python BlackBox Scanner Omission
- **Root Cause**: In `algo_engine/nse100_scanner.py` and `engine_daemon.py`, `MarketContext` was instantiated without computing or passing `bull_regular_div`, `bear_regular_div`, `bull_hidden_div`, or `bear_hidden_div`. These fields defaulted to `False`, causing `is_confluence` to evaluate to `False` on 100% of scanned bars.
- **Fix**: Implemented `compute_rsi(bars, 14)` and `compute_divergences(bars, lookback=10)` in `algo_engine/pivots.py`. Wired divergence flags, `prev_cpr_top`, and `prev_cpr_bottom` directly into `MarketContext` in both scanner modules.

### 3.3 Backend Webhook Ingestion & 24x7 GIFT NIFTY Support
- **Root Cause**: Ingestion handlers dropped confluence metadata and suppressed after-hours GIFT NIFTY signals.
- **Fix**: In both `Tv-Alert-Mobile/src/app/api/webhook/route.ts` and `TLCS_Website_Deploy/netlify/functions/process-webhook-background.js`, added parsing for `is_confluence`, `confluence_type`, and `confluence_tag`, and exempted `GIFTNIFTY` from cash NSE market hours cutoff.

### 3.4 Frontend Confluence Evaluation
- **Fix**: In `Tv-Alert-Mobile/src/app/page.tsx`, updated `isConfluenceSignal` to normalize symbol prefixes with `cleanSym` and evaluate all active/recent signals.

---

## 4. Verification & Testing Results

- **Python Test Suite**: `python3 -m pytest algo_engine/tests` passed 115 / 115 tests (including new `test_divergence_confluence_qualification`).
- **Next.js Production Build**: `npm run build` compiled 100% cleanly with 8 static routes and 80.9 kB middleware bundle.
- **Netlify Deployments**: Deployed live across `market-store.online` and `thelioncapitalsolutions.com`.

---

## 5. Storage Hierarchy & Local Backup Synchronizations

### 5.1 Primary Project Mirror
- Path: `/Users/vishant/Documents/Project/Project Backup/`
- Mirrored via verified `rsync` with zero exclusions of active source code.

### 5.2 Secondary External Mirror
- Path: `/Users/vishant/Documents/Project Backup/`
- Full root mirror synchronized bit-for-bit.

### 5.3 Milestone Archive Distributions
- Path: `/Users/vishant/Documents/Backups/`
- `TLCS_Applications_v2.0_20261101.zip`
- `TLCS_v2.0_Complete_Backup_20261101.zip`
- `Backups/TLCS_v2.0_Complete_Backup_20261101/`
