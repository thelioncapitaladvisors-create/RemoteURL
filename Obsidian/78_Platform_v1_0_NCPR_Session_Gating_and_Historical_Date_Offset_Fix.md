# Platform v1.0: Narrow CPR Session Gating Calibration & Historical Date Offset Architecture

**Status**: PRODUCTION VERIFIED & SYNCHRONIZED  
**Date**: October 26, 2026  
**Indicator Version**: v1.0 (Pine Script v6) & Python BlackBox Engine  
**Target Files**:
- `Tv-Alert-Mobile/src/app/page.tsx`
- `algo_engine/feeds/dhan_feed.py`
- `algo_engine/tests/test_phase2.py`

---

## 1. Executive Summary & Root Cause Analysis

On Monday, October 26, 2026, the user noted:
> *"There was NCPR yesterday not today."*
accompanied by a live 15-minute TradingView chart of ONGC showing Wide CPR on Monday (CPR ratio = 33.33%), while Friday, October 23, 2026 (yesterday's session) had a paper-thin Narrow CPR (CPR ratio = 3.03%).

In the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`), the DhanHQ BlackBox screener ("STOCKS WITH ACTION") displayed **ONGC (+0.24%)** and **LUPIN (+0.35%)** under the **"Narrow CPR"** tab on Monday, causing understandable confusion.

### 1.1 Mathematical Ground-Truth Verification
Under Frank Ochoa's Swing Trade Pro 2.0 / TLCS Indicator lines 731–733:
$$\text{CPR Ratio} = \frac{|\text{TC} - \text{BC}|}{\max(\text{DH} - \text{DL}, \text{mintick})} \times 100 < 5.0\%$$

- **Friday 23-Oct-2026 (Calculated from Thursday 22-Oct OHLC)**:
  - Thursday: H = 226.20, L = 224.00, C = 225.00 $\rightarrow$ Range = 2.20
  - Pivot = 225.07, BC = 225.10, TC = 225.03 $\rightarrow$ CPR Width = 0.0667
  - $\text{CPR Ratio} = \frac{0.0667}{2.20} \times 100 = \mathbf{3.03\%} < 5.0\% \implies \mathbf{NCPR = TRUE}$
- **Monday 26-Oct-2026 (Calculated from Friday 23-Oct OHLC)**:
  - Friday: H = 227.50, L = 223.69, C = 227.50 $\rightarrow$ Range = 3.81
  - Pivot = 226.23, BC = 225.60, TC = 226.86 $\rightarrow$ CPR Width = 1.27
  - $\text{CPR Ratio} = \frac{1.27}{3.81} \times 100 = \mathbf{33.33\%} \gg 5.0\% \implies \mathbf{NCPR = FALSE}$

### 1.2 Root Cause 1: Per-Setup Fallback Leak in `page.tsx`
In `extractDhanScreenerAssets`:
```typescript
// LEGACY FLAW: Checked only within the filtered setup category
const hasTodaySignals = eligibleSignals.some(s => ts >= startOfToday);
if (!hasTodaySignals && eligibleSignals.length > 0) {
  latestSessionDateStr = new Date(maxTs).toISOString().split('T')[0];
}
```
Because no stocks met the < 5% NCPR threshold on Monday, `hasTodaySignals` evaluated to `false` for NCPR. It then executed fallback logic, setting `latestSessionDateStr = '2026-10-23'`, which silently pulled Friday's ONGC and LUPIN while other tabs (like Outside Range & Value) displayed Monday's setups.

### 1.3 Root Cause 2: Historical Candle Indexing in `dhan_feed.py`
In `algo_engine/feeds/dhan_feed.py` line 404:
```python
# LEGACY FLAW: Unconditionally assumed highs[-1] was today
y_h = float(highs[-2])
```
When DhanHQ `/v2/charts/historical` returns only closed daily bars (where `highs[-1]` is Friday), taking `highs[-2]` took Thursday, calculating Friday's CPR instead of Monday's CPR.

---

## 2. Architecture & Calibration

### 2.1 System-Wide Active Session Principle (`page.tsx`)
1. **Engine-Wide Liveness**: Check whether ANY BlackBox signal exists for today across the entire system:
   ```typescript
   const hasAnyBlackboxToday = dhanBlackboxSignals.some(s => ts >= startOfToday);
   ```
2. **Strict Session Isolation**:
   - If `hasAnyBlackboxToday === true` and `sessionFilter === 'TODAY'`: strictly filter for `isToday === true`. If a category has 0 setups today, it returns 0 setups (`Screened: 0`). It never leaks an older session into today's view.
   - If `hasAnyBlackboxToday === false` (weekend/holiday): fallback to the latest market session, but with explicit session badges.
3. **Session Filter Controls**:
   - Added interactive `[TODAY]` (emerald) vs `[ALL]` (purple) session toggle buttons in the screener header.
   - Added date badges (`[TODAY]` or `[23-OCT]`) next to every symbol in the screener table.
   - Provided an intuitive empty state with a 1-click button to view historical sessions.

### 2.2 Historical Candle Timestamp Inspection (`dhan_feed.py`)
Inspecting the timestamp of the last bar in DhanHQ historical response:
```python
is_last_bar_today = False
if timestamps and len(timestamps) >= len(highs):
    last_bar_date = datetime.fromtimestamp(last_ts, tz=ist).date()
    if last_bar_date >= today_ist:
        is_last_bar_today = True

idx_y = -2 if is_last_bar_today else -1
idx_prev2 = -3 if (is_last_bar_today and len(highs) >= 3) else (-2 if (not is_last_bar_today and len(highs) >= 2) else None)
```

---

## 3. Verification & Test Suite

1. **Automated Unit Tests**:
   - Added `test_dhan_historical_daily_levels_indexing` in `algo_engine/tests/test_phase2.py`.
   - Comprehensive test suite: **114/114 passed** in 1.970s.
2. **Next.js Mobile Terminal Production Build**:
   - `npm run build` compiled cleanly with 8/8 static pages generated and 0 TypeScript errors.
