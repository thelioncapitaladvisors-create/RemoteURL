# TLCS Platform Architecture Note: Full 6-Tab DhanHQ Black Box Parity (v7.0)

**Document ID**: `TLCS-DOC-20261002-V7-FULL-6-TAB-DHANHQ-PARITY`  
**Date**: October 2, 2026  
**Platform Version**: `v7.0` (`7.0.0`)  
**Target Applications**: `Tv-Alert-Mobile` (Next.js PWA), `.agents/AGENTS.md`  

---

## 1. Executive Summary

To enable complete institutional comparative analysis between TradingView production alerts (`TV PROD`) and the autonomous algorithmic execution engine (`BLACK BOX LIVE`), the DhanHQ Black Box data pipeline has been extended across all six operational tabs of the mobile application:

1. **`HUB`** (`DASHBOARD`): Parameter Matrix, Trade Sequences, Extreme Reversal, and Normalized Trade Performance (Histogram, Bell Curve, 8 KPIs).
2. **`LOGS`** (`ALERTS`): Signal performance metrics grid and unified chronological trade audit feed.
3. **`SCREENER`** (`SCREENER`): Screener Matrix (`DHAN_SCREENER`) and Paper Portfolio (`DHAN_PAPER`).
4. **`MARKETS`** (`ANALYSIS`): Today's Signal Performance table, sticky `∑ CONSOLIDATED` row, Intraday Trajectory equity curve, and market audit feeds.
5. **`INSIGHTS`** (`INSIGHTS`): Opening prints (`IN RANGE IN VALUE`, `IN RANGE OUT OF VALUE`), day types, and Strategy Trigger performance matrix.
6. **`ANALYTICS`** (`ANALYTICS`): Macro institutional KPIs, 7-day day-wise volume/returns, and the Weekly Performance Edge table (with CAGR and Kelly criterion).

---

## 2. Zero-Load Architecture Proof

Extending the DhanHQ pipeline across all 6 tabs introduces **zero additional load** on both the backend and frontend:

### 2.1 Backend Load: 0% Increase
- **Pre-Existing Cache**: `shadow_signals` is already fetched once per polling cycle (`limit(500)`) in `page.tsx` for the Screener and Parity Audit screens.
- **Zero Extra Queries**: Switching tabs does not issue any new REST requests, database queries, or websocket listeners. The data is pulled directly from the in-memory React state (`dhanBlackboxSignals`).
- **Autonomous Scanners Decoupled**: Netlify background workers (`dhan-scanner-background.js`, `cron-eod-close.js`) run on isolated scheduled cron jobs independent of client tab views.

### 2.2 Frontend Runtime Overhead: 0% Overhead
- **Smaller Array Size ($O(N)$ Complexity)**:
  - `uniqueSignals` (TradingView Webhook): ~1,500 – 2,000 signals.
  - `dhanBlackboxSignals` (DhanHQ Black Box): ~100 – 500 signals (top 100 NSE equities + MCX commodities).
  - Array iterations (`.filter()`, `.reduce()`, `.map()`) over DhanHQ data process significantly fewer elements, reducing client CPU consumption.
- **Virtual DOM Isolation**: Only the active tab is mounted in the DOM (`{activeTab === 'ANALYSIS' && ...}`); all other 5 tabs remain completely unmounted.

---

## 3. Tab-by-Tab Data Pipeline Specification

| Tab | State Trigger | Data Source (`engineSource === 'SHADOW'`) | Telemetry Badge |
| :--- | :--- | :--- | :--- |
| **`HUB`** | `hubDataSource === 'DHAN'` | `dhanBlackboxSignals` (Active executed trades) | `⚡ DHANHQ 100 (BLACK BOX)` |
| **`LOGS`** | `engineSource === 'SHADOW'` | `dhanBlackboxSignals` (Filtered today & active) | `⚡ Standalone 15m Mini-Project` |
| **`SCREENER`** | `screenerViewTab === 'DHAN_*'` | `dhanBlackboxSignals` (Historical & live) | `DHANHQ 100 ⚡` |
| **`MARKETS`** | `engineSource === 'SHADOW'` | `dhanBlackboxSignals` (Today's closed & live) | `⚡ DHANHQ 100 (BLACK BOX)` |
| **`INSIGHTS`** | `engineSource === 'SHADOW'` | `dhanTodaySignals` (Opening bias & day types) | `⚡ DHANHQ 100 (BLACK BOX)` |
| **`ANALYTICS`** | `engineSource === 'SHADOW'` | `dhanBlackboxSignals` (Macro & weekly CAGR) | `⚡ DHANHQ 100 (BLACK BOX)` |

---

## 4. Verification & Build Confirmation

- **TypeScript Typecheck**: Verified via `./node_modules/.bin/tsc --noEmit` $\rightarrow$ **PASS (0 errors)**.
- **Admin Control**: Centralized switching in the **Terminal Menu** (`TERMINAL MENU`) uniformly drives all 6 tabs with zero fragmentation.
