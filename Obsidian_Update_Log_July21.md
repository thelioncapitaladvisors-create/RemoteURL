# Version 1.2.3 Update Log - July 21, 2026

## 🔍 Live DB Audit — Today's Signal State (21:19 IST)

A live Supabase query was run against today's signals to confirm the root cause of "0 Closed Trades" on the web and "0% success" on mobile.

### Findings
| Metric | Count |
|--------|-------|
| Total signals with `created_at >= today` | 124 |
| Resolved as CLOSED (WIN/LOSS/BE) | 26 |
| Resolved as OPEN | 65 |
| Resolved as CANCELLED | 33 |
| Closed trades missing `exit_at` | 21 |
| Closed trades missing `updated_at` | 21 |
| Closed trades missing `exact_pct` | 21 |
| OPEN signals with no `updated_at` | 65 (ALL 65 = stale limits) |

### Key DB Discoveries

**Discovery 1 — 21 Phantom "Hit SL" Duplicate Rows:**
```
[LOSS] EURJPY | status="Hit SL" | outcome=null | exact_pct=null | exit_at=NULL | updated_at=NULL
[LOSS] NG1!   | status="Hit SL" | outcome=null | exact_pct=null | exit_at=NULL | updated_at=NULL
```
These are created when the `isOutcomeUpdate` detection fails (due to `signal_ts` precision mismatch — TradingView sends whole-second, Supabase stores sub-millisecond). Backend falls to INSERT instead of UPDATE → produces ghost row with only `status="Hit SL"` and nothing else.

**Discovery 2 — 65 OPEN Signals ALL Stale Limits:**
Every single OPEN record had `updated_at=NULL`, confirming they are all unexecuted limit orders. Zero live trailing trades.

**Discovery 3 — 10 Stale-Sweeper Closures Invisible to UI:**
Trades force-closed today by the sweeper cron (`Force Closed (Stale)`) have `created_at` from yesterday and `exit_at=NULL`. `getSignalTime` falls back to `created_at` (yesterday) → outside `startOfToday` → invisible to today's dashboard.
```
[GC1!]     status="Force Closed (Stale)" | outcome="WIN"  | created=2026-07-20 | updated=2026-07-21
[TATASTEEL] status="Force Closed (Stale)" | outcome="WIN" | created=2026-07-20 | updated=2026-07-21
```

### Follow-Up Fixes Applied
- **Fix A (Missing Data Root Cause)**: `st.includes('CLOSED')` was hijacking all executed closed trades (including `"Force Closed (Stale)"` and `"Trade Closed"`) and returning `'CANCELLED'` before checking `outcome` or `exact_pct`. Fixed across `trade-metrics.js`, `scanner.js`, `commodity-scanner.js`, and `page.tsx`. `loadPerformanceStats` status exclusion also unblocked.
- **Fix B (No Ghost Inserts on Exit)**: `process-webhook-background.js` previously inserted a brand-new signal row if `activeSignal` was not found on exit alerts. Removed ghost insert on exit; now logs warning and returns 200 OK without creating duplicate rows.
- **Fix C (Single Trade per Symbol at a Point in Time)**: Added `dedupeSignals` in `page.tsx` that collapses concurrent duplicate signal entries for the same symbol at the same entry point/time window.
- **Fix D (Stale-Sweeper Visibility)**: `getSignalTime` now includes `updated_at` fallback for closed trades so today's force-closed stale trades appear in today's performance stats.
- **Fix E (loadInsightsData NaN Fix)**: Added missing `lossCount: 0` initialization and increment in `loadInsightsData` to prevent NaN win rate calculation.
- **Fix F (Exit Lookup Engine Upgrade)**: Fixed 4 real bugs in webhook exit signal lookup (`process-webhook-background.js` and `route.ts`): (1) 10-digit Unix timestamp parsing on entry and exit (`ts > 1e9` -> `ts * 1000`) for 100% millisecond timestamp alignment, (2) `entryPrice` tolerance binder (0.1%), (3) ±60s window expansion, and (4) FIFO fallback (`created_at ASC`).
- **Fix G (Reverted Artificial `yfinance` Price Resolving)**: Reverted `close_stale_trades.py` to strictly target trades open for **more than 24 hours** (`if hours_open <= 24: continue`). Reaffirmed the rule: **Strict Reliance on Alert JSONs (No Artificial Intraday Price Resolving)**. Intraday trade resolution relies strictly and exclusively on TradingView webhook payloads.
# Version 1.0 Release Log — July 21, 2026

- **Fix H (Universal Web & Mobile Metric Synchronization)**: Fixed `resolveOutcome` in `dashboard.html` by removing `st.includes('CLOSED')` from early CANCELLED return (unblocking 35 executed trades). Fixed `getSignalTime` in `dashboard.html` by adding `s.updated_at` check for closed trades. Added `isRealTrade` pre-filtering before `dedupeSignals`. Updated chronological sorting for sequential metrics (`maxDrawdown`, `consecLosses`) to use `getSignalTime(a).getTime() - getSignalTime(b).getTime()`. Web and Mobile dashboards now yield **100% identical metrics down to the second decimal place** (Closed Trades: 186, Win Rate: 45.2%, Profit Factor: 1.07, Realized R:R: 1.30, Avg Winner: +0.54%, Avg Loser: -0.41%, Max Drawdown: -11.58%, Consec Losses: 7 trades, Equity Curve: +4.76%).
- **Fix I (Repaired Corrupted Stale MCX Outliers in DB)**: Repaired 5 corrupted stale rows in `signals` table (`CRUDEOIL1!` and `NATURALGAS1!`) where NYMEX USD prices ($84.41) were inserted into MCX INR trades (₹7,933.50). Set exit prices back to actual Stop Loss levels (₹7,881.00 and ₹279.00), removing the artificial -205% drawdown distortion.

---

## 🔧 Structural Bug Elimination (Stop Fixing the Same Problems Every Day)

### 1. Canonical `resolveOutcome` — Single Source of Truth (trade-metrics.js)
- **Root cause**: `resolveOutcome` was copy-pasted **4 times** inside `trade-metrics.js`. Every patch session applied the fix to one copy but not the others, guaranteeing regression.
- **Fix**: Extracted a single `window.resolveOutcome` at the top of the file. All 4 local redefinitions replaced with one-liner delegates (`const resolveOutcome = window.resolveOutcome;`).
- **CANCELLED check hardened**: Changed `o === 'CANCELLED'` to `o.includes('CANCEL')` in the canonical, catching `'CANCEL'` status strings that previously slipped through.

### 2. Weekly Boundary UTC Leak Fixed (trade-metrics.js)
- **Root cause**: `globalStartOfWeekISO` was computed with `setHours(0,0,0,0)` (local midnight) then `toISOString()` (UTC conversion), which for IST (+5:30) pushed the boundary back by ~5.5 hours, leaking trades from the previous week into weekly metrics.
- **Fix**: Now builds `globalStartOfWeekMS` using `new Date(year, month, date + dist).getTime()` (strict local midnight ms), then converts to ISO only for Supabase query compatibility.

### 3. `window.todayClosedSignals` Mislabeling Fixed (trade-metrics.js)
- **Root cause**: `window.todayClosedSignals` (used by `renderTodayMarkets`) was assigned `todaySignals` which includes OPEN trades, causing the markets grid to render active trades as closed.
- **Fix**: `window.todayClosedSignals` now correctly assigned from `todayClosed` (closed-only array).

### 4. `loadAllActiveTrades` Ghost Trades Fixed (trade-metrics.js)
- **Root cause**: Active signals filter used raw `!s.outcome || s.outcome === 'OPEN'` — EXPIRED/COMPLETED/CANCELLED trades with `outcome=null` passed through and showed as active in the BlackBox panel.
- **Fix**: Filter now delegates to `window.resolveOutcome(s) === 'OPEN'`.

### 5. Scanner CANCELLED Active Filter Fixed (scanner.js)
- **Root cause**: `buildRows` used `!sig.outcome || sig.outcome === 'OPEN'` — CANCELLED trades with `outcome=null` showed as active signals in the scanner.
- **Fix**: Now uses `resolveOutcome(sig) === 'OPEN'`.

### 6. TRAIL → WIN Blind Fallback Removed (scanner.js, commodity-scanner.js, page.tsx)
- **Root cause**: The last-resort fallback `if (TRAIL) return 'WIN'` was firing when `exact_pct` was null, incorrectly classifying trail-stopped losses as wins.
- **Fix**: TRAIL status alone now returns `'OPEN'` (deferred) instead of `'WIN'`. The authoritative `exact_pct` fallback above it already handles all resolvable TRAIL outcomes.

### 7. `isRealTrade` Missing Status Guards Fixed (page.tsx)
- **Root cause**: `isRealTrade` didn't check for `expired`, `completed`, or `closed` in the status field, so limit orders cancelled/expired by TradingView passed all metric filters.
- **Fix**: Added `expired`, `completed`, `closed` to the exclusion check.

### 8. Profit Factor Raw Sign Bug Fixed (page.tsx — 2 locations)
- **Root cause**: PF was computed by grouping trades on raw `getExactPct(s) > 0` (profit) vs `< 0` (loss). A SHORT trade hitting SL produces positive `exact_pct` (since exit < entry), inflating PF to 14+.
- **Fix**: Both global PF and `marketsStats` useMemo now use `resolveOutcome(s) === 'WIN'` / `'LOSS'` for grouping, then `Math.abs(getExactPct(s))` for magnitude.
- **Cascading effect**: Today's Success % of 0% was caused by this — all 25 trades were being bucketed as BREAKEVEN/OPEN because wins and losses cancelled out in the signed math.

### 9. NYMEX/Forex Market Close Pruning Added (page.tsx)
- **Root cause**: `activeSignals` only pruned stale Indian (15:30 IST) and MCX (23:30 IST) limit orders after market close. NYMEX and Forex limit orders were never auto-hidden.
- **Fix**: Added NYMEX pruning at 23:30 IST. Added Forex pruning on Friday nights (weekend gap risk). Crypto remains 24/7.

### 10. Deprecated `outcome_pct`/`profit_pct` Reads Removed (page.tsx — 2 locations)
- **Root cause**: Two `useMemo` blocks (`marketCategoryStats`, `strategyInsights`) were reading deprecated `s.outcome_pct` and `s.profit_pct` fields, violating the V1.0 architectural rule.
- **Fix**: Both now use `Math.abs(getExactPct(s) || 0)` exclusively.

### 11. Terminal UI Loader Freeze Fix (trade-metrics.js)
- **Root cause**: `window.renderTodayMarkets` was defined without `async`, but contained an `await client.from('pivots')` call inside. This caused a fatal JS `SyntaxError: await is only valid in async functions`, completely halting script execution and leaving "Analyzing strategies..." and "Analyzing today's market performance..." loaders hanging indefinitely.
- **Fix**: Declared `window.renderTodayMarkets = async function(...)`. Wrapped `DOMContentLoaded` with a `document.readyState` check (`startMetricsEngine()`). Updated `loadInsightsData` catch block to safely clear loading states if Supabase calls fail. Removed single-symbol restriction in `loadAllActiveTrades` so performance cards remain MARKET-WIDE.

### 12. Original Entry Baseline & Trailing SL Principles Audit
- **Audit**: Verified database signals for today (297 trades: 55 TP1 hits, 100 SL hits, 10 active, 123 stale limit closes).
- **Confirmation**: Verified that ALL P&L calculations (`exact_pct`) across backend webhooks (`process-webhook-background.js`) and frontend UIs (`trade-metrics.js`, `dashboard.html`, `page.tsx`) strictly compute returns using the **Original Entry Price** (`((Exit - Entry) / Entry) * 100` for Long, `((Entry - Exit) / Entry) * 100` for Short). Trailed levels (`trail_sl`) are strictly trigger boundaries and are NEVER used as baseline price denominators.

