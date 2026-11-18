# Platform v4.0: Live Signals & Watchlist Separation, Zero-Truncation UI, and System-Wide Release Architecture

**Document ID**: 105  
**Effective Date**: November 18, 2026 (20:35 IST)  
**Classification**: Production Release Specification & System Architecture Sign-Off  
**Release Target**: TLCS Platform Version 4.0 (`v4.0`)  
**Status**: 🚀 PRODUCTION RELEASED & ACTIVE  

---

## 1. Executive Summary

TLCS Platform Version 4.0 (`v4.0`) is officially released and active across all terminal frontend components, configuration files, and documentation bases. Version 4.0 succeeds the locked Version 3.0 baseline, delivering two major usability and layout advancements:

1. **Dedicated Separation of Live Signals and Watchlist on the INSIGHTS Tab**: Slices the unified bias screener into two distinct, dedicated institutional sections:
   - `⚡ LIVE SIGNALS (INSTANT EXECUTION & LIMITS)`: Strictly isolates active live orders, limit touchpoints, and active trade executions (`liveActionOnly: true`).
   - `📋 WATCHLIST (DAY-TYPE CANDIDATES & SETUPS)`: Strictly isolates qualifying day-type candidate setups and watchlist opportunities (`watchlistOnly: true`).
   - Both sections adopt the exact 3-tier responsive filter architecture proven in the **LOGS** tab's `TRADE FILTERS` section.

2. **Universal Zero-Truncation Pill Geometry (Analytics Tearsheet Matrix)**:
   - Solved the mobile font elevation truncation issue where 4-column metric pills clipped text labels (e.g. `REALIZED CLOS...`) and streak statistics (e.g. `12 Consecut...`).
   - Completely eliminated rigid `whitespace-nowrap` and `overflow-hidden` constraints across all 22 metric pills in the Tearsheet card, enabling fluid vertical 2-line wrapping with `break-words`.
   - Elevated responsive container height to `min-h-[54px] sm:min-h-[58px]` with comfortable padding (`p-2 sm:p-2.5 rounded-xl`), guaranteeing 100% visible, unclipped metrics across all viewports (320px to 4K).

3. **System-Wide Version 4.0 Parity**:
   - `Tv-Alert-Mobile/package.json`: Upgraded to `"version": "4.0.0"`.
   - Terminal Main Header: Elevated to `TLCS TERMINAL v4.0`.
   - Health Sentinel & Verification Daemon: Elevated to `Active Daemon v4.0`.
   - Legal Compliance Footer: Elevated to `Store Ready v4.0`.
   - 100% byte-for-byte synchronization maintained between `Tv-Alert-Mobile/src/app/page.tsx` and root `page.tsx`.

---

## 2. Live Signals vs. Watchlist Decoupling Architecture

### 2.1 State Management & Dedicated Filtering Pipelines
In `Tv-Alert-Mobile/src/app/page.tsx` and root `page.tsx`, state variables are strictly segregated so user filter choices in Live Signals never contaminate Watchlist filters:

| Component | State Variables | Description |
| :--- | :--- | :--- |
| **Live Signals** | `isLiveSignalsMasterExpanded`<br>`liveSignalsActiveFilter`<br>`liveSignalsMarketFilter`<br>`liveSignalsDirectionFilter`<br>`liveSignalsSessionFilter` | Independent master toggle, status/setup filter (`ALL`, `LIVE`, `LIMIT`, `REGULAR`, etc.), 8-market category chip filter, direction toggle (`ALL`, `BULL`, `BEAR`), and session toggle (`ALL`, `REG`, `EXT`). |
| **Watchlist** | `isWatchlistMasterExpanded`<br>`watchlistActiveFilter`<br>`watchlistMarketFilter`<br>`watchlistDirectionFilter`<br>`watchlistSessionFilter` | Independent master toggle, setup category tab (`ALL`, `OOR`, `VCPR`, `NCPR`, etc.), 8-market category chip filter, direction toggle, and session toggle. |

### 2.2 Sliced Memoization with Zero Business Logic Duplication
Signals are derived using the canonical `extractDhanScreenerAssets()` engine with boolean isolation flags:
```typescript
// Live Signals Pipeline: strictly isolates active limit orders and live execution trades
const liveSignalsAssets = useMemo(() => {
  return extractDhanScreenerAssets(
    'LIVE_SIGNALS',
    dhanOorData,
    liveSignalsMarketFilter,
    liveSignalsDirectionFilter,
    liveSignalsSessionFilter,
    liveSignalsActiveFilter,
    true,  // liveActionOnly = true
    false  // watchlistOnly = false
  );
}, [dhanOorData, liveSignalsMarketFilter, liveSignalsDirectionFilter, liveSignalsSessionFilter, liveSignalsActiveFilter]);

// Watchlist Pipeline: strictly isolates day-type candidate setups
const watchlistAssets = useMemo(() => {
  return extractDhanScreenerAssets(
    'WATCHLIST',
    dhanOorData,
    watchlistMarketFilter,
    watchlistDirectionFilter,
    watchlistSessionFilter,
    watchlistActiveFilter,
    false, // liveActionOnly = false
    true   // watchlistOnly = true
  );
}, [dhanOorData, watchlistMarketFilter, watchlistDirectionFilter, watchlistSessionFilter, watchlistActiveFilter]);
```

### 2.3 Exact 3-Tier LOGS Tab Design Rhythm
Both sections implement the uniform 3-tier header rhythm:
1. **Tier 1 (Status & Setup Tabs)**: Pill selectors with counts (`ALL`, `LIVE EXECUTIONS`, `ACTIVE LIMITS`, `REGULAR`, `HIDDEN`, etc.) and right-aligned total badges (`TOTAL: X`).
2. **Tier 2 (Market Category Chips)**: Horizontal scrollable chips (`ALL`, `NIFTY`, `STOCKS`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`, `WORLD`) with live category asset counts.
3. **Tier 3 (Direction & Session Filter Toggles)**: Independent direction (`ALL`, `BULL`, `BEAR`) and session filters (`ALL`, `REG`, `EXT`).
4. **Summary KPI Strip**: 1-row metric strip showing Total Assets, Active Count, Outcomes (Wins/Losses), and Average Return %.
5. **3-Column Intuitive Responsive Grid**: Streamlined table (`SYMBOL & TIME` | `SETUP & STATUS` | `RETURN (%)`), eliminating horizontal scroll friction and preventing the 48px sticky column collapse bug.

---

## 3. Zero-Truncation Pill Redesign (Analytics Tearsheet Matrix)

### 3.1 Problem Diagnosis & Root Cause
Under dynamic mobile font elevation rules in `globals.css`, micro-fonts (`text-[9px]`, `text-[10px]`) are elevated to `11.5px !important;` on viewports under 640px. The previous Analytics Tearsheet cards utilized:
```html
<!-- LEGACY: Caused truncation on mobile -->
<div className="flex flex-col items-center justify-center p-1.5 rounded-lg border min-h-[48px] overflow-hidden whitespace-nowrap">
  <span className="text-[9px] uppercase tracking-wider text-slate-500 truncate">REALIZED CLOSED TRADES</span>
  <span className="text-xs font-black truncate">{stats.closedTrades}</span>
</div>
```
This forced longer strings like `REALIZED CLOSED TRADES` to render as `REALIZED CLOS...` and `12 Consecutive` to render as `12 Consecut...`.

### 3.2 Solution Architecture
The 22 metric pills in the Tearsheet Matrix were refactored to allow natural multi-line vertical wrapping:
- **Removed Constraints**: Stripped `whitespace-nowrap` and `overflow-hidden`.
- **Added Dynamic Flow**: Introduced `break-words leading-tight tracking-tight` on all label elements.
- **Elevated Height**: Increased minimum height to `min-h-[54px] sm:min-h-[58px]` with comfortable padding (`p-2 sm:p-2.5 rounded-xl`).
- **Streamlined Metric Strings**: Format strings for streak counts and date spans were streamlined (`{stats.maxWinStreak} Cons.`, `{stats.currentStreak} Wins/Losses`) to maintain clear typography alongside high-density mobile font elevation.

---

## 4. System-Wide Version 4.0 Parity & Checksums

- **`Tv-Alert-Mobile/package.json`**: `"version": "4.0.0"`
- **`Tv-Alert-Mobile/src/app/page.tsx`**: Updated to `v4.0` across branding, daemons, and footers.
- **Root `page.tsx`**: 100% byte-for-byte identical mirror (`diff -q page.tsx Tv-Alert-Mobile/src/app/page.tsx` return code 0; 6,119 curly braces, 3,372 square brackets).
- **Core Indicators & Strategy Engine**: 100% frozen and untouched, preserving canonical mathematical integrity and zero unilateral alterations.
