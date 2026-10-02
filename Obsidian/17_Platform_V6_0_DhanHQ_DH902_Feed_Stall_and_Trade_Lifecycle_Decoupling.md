# Platform Architecture Log — October 2, 2026: DhanHQ DH-902 Feed Restriction & Trade Lifecycle Decoupling

**Baseline Standard**: Platform v6.0 Production Baseline  
**Date**: October 2, 2026  
**Status**: ACTIVE DEPLOYED  

---

## 1. Executive Summary & Core Mandate

When DhanHQ API returns HTTP 451 (`DH-902: Unsubscribed Data API`), rate limits, or session cutoffs (14:00 IST for NSE, 22:00 IST for MCX):
1. **NEW TRADE GATING ONLY**: The restriction applies **strictly and exclusively** to considering and generating **NEW trades**. Candidate scanning and new limit order creation are paused.
2. **EXISTING TRADE LIFECYCLE PRESERVATION**: Existing trades that are already opened / filled (`status = '⚡ TRADE ACTIVE'`, `real_entry_time` populated) **MUST continue their journey without interruption** until their natural, verified exits:
   - **`Hit Initial SL`** (Stop Loss hit)
   - **`Trailing SL`** (`Hit B/E`, `Hit TP1 Trailing`, `Hit TP2 Trailing`, `Hit TP3 Trailing`)
   - **`Hit EMA`** (Post-TP4 Dynamic Medium EMA cross)
   - **`EOD Exit`** (Market session close force-close with exact percentage)
   - Or Take Profit target tiers (`TP1-TP4`)
3. **ZERO UNEXECUTED LIMIT ORDERS IN ACTIVE FEED**: Unexecuted pending limit orders (`ACTIVE LIMIT`) must NEVER be displayed in the HUB Alerts Dashboard as live active trades or decorated with `⚡`.

---

## 2. Root Cause Analysis (RCA)

### Issue A: Position Management Coupled to Candle Ingestion
- In `dhan-scanner-background.js`, `processOpenTradesAndFills` was positioned **inside** the new candidate scan loop, executed only **after** `fetchIntradayCandles(sym, info)` successfully returned at least 3 completed 15-minute bars.
- When DhanHQ Charts API returned HTTP 451 (`DH-902`), `fetchIntradayCandles` returned `null`, immediately returning `null` from the batch promise.
- Consequently, open trades (such as the `NATURALGAS` Divergence position) were completely bypassed during post-22:00 IST bars, preventing `Hit Initial SL` from executing.

### Issue B: Mobile HUB Dashboard Pending Limit Order Leakage
- In `Tv-Alert-Mobile/src/app/page.tsx` line 5950, `activeBlackboxSigs` checked:
  ```typescript
  if (!isLiveTrade && !isActiveLimit(s, isToday)) return false;
  ```
  Because `isActiveLimit` treats any MCX order created today before 23:30 IST as active, pending limit orders passed the filter.
- Lines 6023–6025 unconditionally appended `⚡` to any signal where `b.source === 'blackbox_dhan'`:
  ```typescript
  const isBB = (b.source || '').toLowerCase().includes('blackbox');
  return isBB ? `${sClean}⚡` : sClean;
  ```
  This falsely tagged unexecuted 9-hour-old limit orders (such as `ALUMINIUM` SHORT SCALP) with `⚡`, displaying them as live active trades.

### Issue C: EOD Cron Calendar-Day Gap
- In `cron-eod-close.js`, MCX trades created on a previous day were checked against `hoursAgo > 14`. If the cron ran during morning hours before 14 hours had elapsed, trades were not swept until midday.

---

## 3. Implemented Architectural Remediation

### A. Decoupled Position Manager (`sweepAllOpenTradesAndFills`)
- `dhan-scanner-background.js` now executes `sweepAllOpenTradesAndFills(symbolsMap)` **FIRST**, at the very start of `runDhanScan`, before any candidate scanning.
- Evaluates all active and pending rows in `shadow_signals`:
  - **Market Session Closed**: Immediately hard-deletes unexecuted limits (Zero-Ghost policy) and force-closes live active positions as `EOD Exit` (`exact_pct`).
  - **Market Session Open**: Evaluates price touch-points for SL, TP, trailing stop, and limit fill.

### B. DhanHQ Market Quote / LTP Fallback (`fetchDhanLtpOrQuote`)
- Added `fetchDhanLtpOrQuote(symbol, info)` to query DhanHQ Marketfeed APIs (`/v2/marketfeed/quote` or `/v2/marketfeed/ltp`), which are standard Trading API endpoints that remain fully functional without the Charts Data API subscription.
- If `/v2/charts/intraday` returns 451 `DH-902`, the scanner falls back to live Quote/LTP (`last_price`, `high`, `low`) to evaluate active trades and execute `Hit Initial SL` or targets.

### C. Gating New Trades on DH-902 & Session Cutoffs
- When `fetchIntradayCandles` receives 451 `DH-902` or returns `null`, the scanner logs:
  `[DhanScanner] ${sym} intraday candles unavailable (DH-902 subscription requirement / feed restriction). Gating NEW trade consideration. Existing trades preserved.`
- Candidate generation is skipped cleanly, ensuring no synthetic or fictitious limit orders are spawned.

### D. Frontend HUB Alerts Dashboard Strict Live Enforcement
- In `Tv-Alert-Mobile/src/app/page.tsx`:
  - `activeBlackboxSigs` strictly requires `if (!isLiveTrade) return false;`.
  - `hubSigsToFilter` strictly uses `activeSignals.filter(s => isExecutedTrade(s))`.
  - Symbol rendering strictly requires `(isBB && isExecutedTrade(b)) ? `${sClean}⚡` : sClean`.
  - Unexecuted limits will NEVER appear in the HUB Alerts Dashboard or receive `⚡`.

### E. EOD Market Close Sweep Resilience
- In `cron-eod-close.js`, any intraday trade from a previous calendar day (`!isCreatedToday`) immediately evaluates as `isMarketClosed = true`, guaranteeing instantaneous closure at EOD without arbitrary hour thresholds.

---

## 4. Verification & Audit Trail

| File | Change | Verification |
| :--- | :--- | :--- |
| [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md) | Added `DhanHQ Data Restriction & Feed Stall Mandate` section. | Verified |
| [`dhan-scanner-background.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js) | Decoupled open trade sweep, added `fetchDhanLtpOrQuote`, gated new trades on DH-902. | Verified |
| [`cron-eod-close.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-eod-close.js) | Fixed previous day session close evaluation for NSE and MCX. | Verified |
| [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) | Enforced `isLiveTrade` on HUB Alerts Dashboard and removed unconditional `⚡` on pending limits. Added DH-902 Parity Audit verification pill. | Verified |
| [`dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html) | Added DH-902 decoupled lifecycle telemetry tooltip. | Verified |
