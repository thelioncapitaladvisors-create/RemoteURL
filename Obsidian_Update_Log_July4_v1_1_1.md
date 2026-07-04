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
- **Filter Matching**: Fixed composite filter matching bug in `matchFilter` by updating the evaluation logic. It now checks for partial matching, direct equivalence, and cleanses the `"DAY"` keyword during day type matching (e.g. mapping `"Sideways Day"` to `"SIDEWAYS"` accurately instead of failing index checks).

### 3. Website AI Scanner Loading and Date Formatter Safeguards
- **Files Modified**: [commodity-scanner.js](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js) and [scanner.js](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js)
- **Loader Robustness**: Wrapped `Promise.all` Supabase database queries in `commodity-scanner.js` with defensive `.catch()` error handlers returning empty datasets. This prevents the scanner page from hanging indefinitely on "Loading scanner data..." when a custom database view fails to load.
- **RangeError Safeguards**: In `scanner.js`, added invalid date verification (`isNaN(dateObj.getTime())`) in the weekly performance logs iteration loop to prevent execution halts due to corrupted date formats.
- **TypeError Bug Fix**: Fixed a critical loading state hang in `scanner.js` by initializing `window.tvFallbackCache` inside the `buildRows` function. Previously, attempting to read `window.tvFallbackCache[symKey]` when it was undefined threw a fatal TypeError, halting the rendering pipeline and leaving the UI stuck in the "Loading..." state indefinitely.
- **Fallback DOM Update Fix**: Resolved a silent bug in `scanner.js` and `commodity-scanner.js` where dynamic fallback data (Opening Bias and Day Type) fetched from the Yahoo Finance fallback script was never rendered in the UI. Added `.bias-val` and `.day-type-pill` classes to the dynamically generated table cells so the DOM selectors find and update them correctly.

### 4. Webhook Backend Sanitization & Normalization
- **Files Modified**: [route.ts](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/webhook/route.ts) and [process-webhook-background.js](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/process-webhook-background.js)
- **Sanitization Helper**: Implemented the `cleanBiasOrDayType` function on both the Next.js API route (mobile backend) and Netlify background functions (website backend).
- **Format Normalization**: Standardizes opening bias and day type strings upon ingestion before upserting into the Supabase database. Replaces literal `\\n` / `\n` characters with spaces, collapses multiple whitespace gaps, capitalizes all characters, maps `"Double Distribution"` to `"DD"`, and normalizes commas. This ensures clean, uniform data is stored directly in database columns and metadata objects.

### 5. Historical Trade Data Retroactive Population
- **Action Taken**: Ran a migration script (`populate_missing_stats.py`) to query all historical signals created today that were missing Bias or Day Type values (including `ETHUSDT`, `DOGEUSDT`, and `BTCUSDT`).
- **Pivots Computation**: Calculated CPR pivot data dynamically using Yahoo Finance historical daily chart parameters and successfully populated all today's historical signals in the database with their correct sanitized Opening Bias and Day Type metrics. This restores the missing stats across both the website and mobile platforms instantly.
