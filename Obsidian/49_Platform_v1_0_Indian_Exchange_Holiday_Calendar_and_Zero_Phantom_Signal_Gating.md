# Platform Update Note: Version 1.0 Indian Exchange Holiday Calendar & Zero-Phantom Holiday Signal Gating
**Date**: October 20, 2026  
**Module**: Algo Engine (`algo_engine/nse100_scanner.py`), Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`), API Routes (`/api/option-chain`, `/api/fno-buildups`), Serverless Functions (`TLCS_Website_Deploy/netlify/functions/dhan-option-chain.js`, `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js`), Documentation (`AGENTS.md`)  
**Scope**: Implementation of the official 2026 NSE & MCX exchange trading holiday calendars, elimination of phantom active limit orders on market holidays, database purge of invalid signals, and universal holiday gating across scanners, APIs, and client-side market hours evaluators.

---

## 1. Executive Summary & Root-Cause Analysis

### A. The Incident: Phantom Active Limit Trades on Dussehra (Vijayadashami)
On **Tuesday, October 20, 2026** (an official NSE and BSE trading holiday for Dussehra / Vijayadashami), the mobile terminal HUB dashboard displayed:
- **`ACTIVE LIMITS: 10`**
- **`LIVE TRADES: 0`**
- **`CLOSED TRADES: 0`**

### B. Fact-Backed Root Cause Analysis
1. **Exchange Trading State**:
   - Today, October 20, 2026, is an official NSE trading holiday (closed all day).
   - MCX is closed for the morning session (09:00 to 17:00 IST) and open only for the evening session (17:00 to 23:30 IST).
2. **Scanner Daemon Behavior**:
   - The macOS background daemon (`com.tlcs.nse100scanner.plist` running `/Users/vishant/Project/algo_engine/run_nse100_scanner.py --interval 900`, PID 921) previously verified market hours solely via `weekday < 5` and clock time `09:15 <= mins < 15:30 IST`.
   - Lacking an exchange holiday calendar, the daemon assumed Tuesday October 20 was an active market session.
   - When the scanner queried DhanHQ for 15-minute equity candles, Dhan returned the latest available historical candles (Monday, October 19, 2026 EOD).
   - Because the daemon did not check candle dates against today's date or check whether today is a trading holiday, it evaluated those prior-day candles as live today, generating 10 limit entry signals (`ADANIPORTS LONG LIGHTNING` $\times 5$ and `SBIN LONG DIVERGENCE` $\times 5$) and inserting them into `public.shadow_signals` between 09:16 AM and 11:46 AM IST.
3. **Client-Side Market Hours & Limit Gating Gap**:
   - `isNseMarketHours()` in `page.tsx`, `/api/option-chain`, and `/api/fno-buildups` also relied solely on `day !== 0 && day !== 6` and `timeNum >= 9.25 && timeNum < 15.5`.
   - `isActiveLimit()` in `page.tsx` evaluated `market === 'NIFTY' && timeNum >= 15.5 ? false : true`, failing to verify whether the market was actively trading (`isNseMarketHours()`).
   - Consequently, unexecuted limit orders were evaluated as active limits during daytime hours on an exchange holiday.

---

## 2. Full Corrective Actions Implemented

### A. Database Cleanup (Zero Fictitious Data Mandate)
- Hard-deleted all 10 invalid phantom limit rows from Supabase `public.shadow_signals` (`outcome=eq.OPEN&created_at=gte.2026-10-20T00:00:00Z`).
- Verified with direct Supabase REST API queries that open trades for today dropped from 10 to **0**.

### B. Official Indian Exchange Holiday Calendar 2026 (NSE & MCX)
Integrated canonical 2026 holiday sets into all components:
- **NSE Equities & F&O (`NSE_HOLIDAYS_2026`)**:
  `"2026-01-15"` (Makar Sankranti), `"2026-01-26"` (Republic Day), `"2026-03-03"` (Holi), `"2026-03-26"` (Ram Navami), `"2026-03-31"` (Mahavir Jayanti), `"2026-04-03"` (Good Friday), `"2026-04-14"` (Dr. Ambedkar Jayanti), `"2026-05-01"` (Maharashtra Day), `"2026-05-28"` (Bakri Id), `"2026-06-26"` (Muharram), `"2026-09-14"` (Ganesh Chaturthi), `"2026-10-02"` (Mahatma Gandhi Jayanti), `"2026-10-20"` (Dussehra), `"2026-11-10"` (Diwali Balipratipada), `"2026-11-24"` (Gurunanak Jayanti), `"2026-12-25"` (Christmas).
- **MCX Full-Day Closed (`MCX_FULL_HOLIDAYS_2026`)**:
  `"2026-01-26"`, `"2026-04-03"`, `"2026-10-02"`, `"2026-12-25"`.
- **MCX Morning Closed (09:00–17:00 IST) / Evening Open (17:00–23:30 IST) (`MCX_MORNING_HOLIDAYS_2026`)**:
  `"2026-01-15"`, `"2026-03-03"`, `"2026-03-26"`, `"2026-03-31"`, `"2026-04-14"`, `"2026-05-01"`, `"2026-05-28"`, `"2026-06-26"`, `"2026-09-14"`, `"2026-10-20"` (Dussehra), `"2026-11-10"`, `"2026-11-24"`.

### C. Algo Engine Scanner Hardening (`algo_engine/nse100_scanner.py`)
- `is_trade_entry_allowed_for_bar(sym, timestamp)`: Validates candle timestamp date against holiday sets. For NSE equities, aborts immediately if date is in `NSE_HOLIDAYS_2026`. For MCX, checks full-day vs. morning-session closures.
- `is_nse_market_open_now()` and `is_nse_entry_allowed_now()`: Gated by `NSE_HOLIDAYS_2026`.
- `is_mcx_market_open_now()` and `is_mcx_entry_allowed_now()`: Gated by `MCX_FULL_HOLIDAYS_2026` and `MCX_MORNING_HOLIDAYS_2026`.
- Reloaded macOS background daemon (`launchctl kickstart -k gui/501/com.tlcs.nse100scanner`). Verified scanner log:
  `No markets open (12:15:03 IST). Status: NSE=False, MCX=False. Cycle completed. 0 signals generated.`

### D. Client Application & API Route Hardening (`page.tsx`, routes, and netlify functions)
1. **`isNseMarketHours()`**: Evaluates IST date string (`YYYY-MM-DD`) against `NSE_HOLIDAYS_2026`. Returns `false` on holidays regardless of time of day.
2. **`isMcxMarketHours()`**: Evaluates `MCX_FULL_HOLIDAYS_2026` (returns `false` all day) and `MCX_MORNING_HOLIDAYS_2026` (returns `false` before 17:00 IST; `true` between 17:00 and 23:30 IST).
3. **`isActiveLimit()`**: Evaluates `if (market === 'NIFTY') return isNseMarketHours();` and `if (market === 'MCX') return isMcxMarketHours();`. Unexecuted limit orders are strictly inactive when exchanges are closed.
4. **`getLastMarketCloseTs()`**: Dynamically steps backward day-by-day past weekends and exchange holidays to locate the true preceding trading session's close time.
5. **`/api/option-chain` & `/api/fno-buildups`**: Serve genuine EOD snapshots from Supabase on holidays with `marketStatus: 'EOD'`, avoiding unnecessary or failing calls to Dhan live quote feeds.

---

## 3. Verification & Operational Status
- **Next.js Typecheck & Production Build**: Verified with `npx tsc --noEmit` and `npm run build` (0 errors, 23/23 routes compiled successfully).
- **Scanner Daemon**: Running actively with PID 4927 under launchd supervisor; 0 signals generated on holiday.
- **Supabase State**: `public.shadow_signals` and `public.signals` contain 0 open trades for October 20, 2026.
- **HUB Terminal**: `ACTIVE LIMITS: 0`, `LIVE TRADES: 0`, `CLOSED TRADES: 0`.
