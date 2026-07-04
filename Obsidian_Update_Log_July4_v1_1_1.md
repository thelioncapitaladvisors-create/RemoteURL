# TLCS Platform Updates - July 4, 2026 (v1.1.1 — Mobile INSIGHTS Scope & Filter Hotfixes)

## Summary
Updates targeting mobile UI scopes, filter logic discrepancies, and defensive data loading configurations across the dashboard ecosystem. Scoped the mobile INSIGHTS tab strictly to today's activity and patched a silent JSONB parsing bug affecting filters.

## Modifications Made

### 1. Scoped INSIGHTS Tab to Today's Trades (Mobile v1.1.1)
- **Files Modified**: [page.tsx](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)
- **Logic Scoping**: Reconfigured `marketCategoryStats`, `strategyCategoryStats`, and `strategyInsights` to compute metrics by iterating over `todayClosedSignals` instead of the global `closedSignals` array.
- **Filter scoping**: Updated strategy filter lists dynamically to render only strategy buttons that generated signals today, preventing UI clutter from inactive assets.
- **Labels**: Adjusted the UI labels from "based on all closed signals" to "based on today's closed signals" to align user expectation with the new strict time filter.

### 2. Fixed MARKETS Tab Filters & Metadata Parsing (Mobile v1.1.1)
- **Files Modified**: [page.tsx](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)
- **Type Safety**: Extended `Signal` interface definition with `exchange?: string;` field to match Supabase's query response.
- **Defensive Parsing**: Applied defensive JSON string parsing for the `metadata` column in `getMarket`, `marketsClosedSignals` filter, and signal detail views to resolve silent crashes and blank Day Type / Bias filters.

### 3. Website AI Scanner Loading and Date Formatter Safeguards
- **Files Modified**: [commodity-scanner.js](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js) and [scanner.js](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js)
- **Loader Robustness**: Wrapped `Promise.all` Supabase database queries in `commodity-scanner.js` with defensive `.catch()` error handlers returning empty datasets. This prevents the scanner page from hanging indefinitely on "Loading scanner data..." when a custom database view fails to load.
- **RangeError Safeguards**: In `scanner.js`, added invalid date verification (`isNaN(dateObj.getTime())`) in the weekly performance logs iteration loop to prevent execution halts due to corrupted date formats.
