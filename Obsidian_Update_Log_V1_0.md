# TLCS Platform Release Notes - Version 1.0
**Date**: June 28, 2026

## Core Architectural Shift: Exact Percentage Math & R-Multiple Deprecation

### 1. Database Schema & Views Rebuild
- **Table Modification**: Executed SQL cleanup schema migrations to permanently drop `r_multiple` and `outcome_pct` columns from the primary `signals` table, and dropped `avg_r_multiple` and `net_r_multiple` from `weekly_performance_logs`.
- **Database Views Re-creation**: Recreated `signal_stats` and `signal_stats_by_symbol` database views to compute metrics strictly and dynamically from the `metadata.exact_pct` JSONB field.
- **Single Source of Truth**: Standardized `((Exit - Entry) / Entry) * 100` as the absolute mathematical source of truth.

### 2. Backend & API Standardization
- **Netlify Webhooks & Crons**: Updated Netlify webhook listeners and cron jobs (`cron-weekly-logs.js`) to parse and aggregate outcomes directly using `metadata.exact_pct` instead of fallback R-multiple string parsers.
- **Mobile Next.js API Routes**: Redesigned Next.js endpoints (`webhook/route.ts`, `outcome/route.ts`, and `fix-db/route.ts`) to compute and inject exact percentage returns directly into the `metadata.exact_pct` column upon signal closure.

### 3. Website Dashboard UI Updates
- **R-to-Percent Transition**: Removed all remaining `R` suffixes on the main dashboard cards and charts, replacing them with standard `%` labels.
- **Novice Mode Points Math**: Fixed a bug where `cumulativeReturnPts` remained at 0 by restoring the raw exit-entry price difference calculation (`getRawPts`) for Novice Mode's `TOTAL EARNED (POINTS)` metric.
- **Weekly Card Headers**: Replaced `Pure R-Math` with `Ratio` under the Profit Factor cell in weekly scanner logs.

### 4. Mobile App UI Updates
- **Column Header Renaming**: Renamed all `AVG R-MULT` table headers to `Avg Profit`.
- **Value Formatting**: Swapped out the `R` suffix on all signal logs, Today's Best Markets tables, and Rank highlight cards to show exact percentage returns (`%`).
- **TypeScript Compilation Failsafe**: Resolved all compiler type check errors (e.g. `Object is possibly 'null'` or type mismatches) within `page.tsx` on Netlify by implementing solid conditional fallback handlers on `getExactPct(s)`.

### 5. Pivot Metadata & Data Integrity Fix
- **Bias & Day Type Resolution**: Fixed a critical issue on the website scanner tables (`scanner.js` and `commodity-scanner.js`) where the `BIAS` and `DAY TYPE` columns rendered empty `--` placeholders because they queried flat database columns that are `null`. Added a robust fallback to look inside `p.metadata.opening_bias` and `p.metadata.day_type` where TV webhook updates are persistently saved.
