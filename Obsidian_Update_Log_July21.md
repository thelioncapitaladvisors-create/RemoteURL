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
- **Fix F (CL1! Profitable Trade Resolution)**: `close_stale_trades.py` upgraded to fetch 1-day `high`/`low` session price ranges via `yfinance` for all open signals. Evaluated `CL1!` (entry 83.695, target 84.12) against session high (85.03), automatically resolving `CL1!` as `WIN` (`TP1 Hit`, `Exit: 84.12`, `P&L: +0.51%`, `updated_at: NOW`) and sweeping 115 other open signals with missed TradingView exit webhooks.

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
