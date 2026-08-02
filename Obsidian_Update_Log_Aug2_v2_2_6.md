# TLCS System Update - August 2, 2026 (v2.2.5 & v2.2.6 Hotfix)

## 1. TLCS Day Type Scanner (formerly PivotBoss Combined Scanner)
- **Engine Refactor**: Built `TLCS_PivotBoss_FNL_FNH_Dashboard.pine` supporting 40 symbols, 5 blueprint types (Rejection, FNL/FNH, Absorption, Outside, and Stop Run Days), and 5 market types.
- **Webhook Integration**: Established JSON array-based alerting in TradingView and backend JSONB Upsert logic in Supabase `pivotboss_scans` table (using `process-webhook-background.js`).
- **UI Renaming & Branding**: Renamed "PIVOTBOSS COMBINED SCANNER" strictly to **TLCS DAY TYPE SCANNER**.
- **Web Deployment (`dashboard.html`)**: Injected the dynamic grid into the web dashboard.
- **Mobile Deployment (`page.tsx`)**: Injected the scanner onto the **Analytics** tab of the mobile application.

## 2. V2.2.6 Hotfixes (Scanner Loading Bug & Tab Placement)
- **JSONB Payload Bug**: Addressed an edge-case in Supabase JS v1 where the `scan_data` JSONB column was being returned as a stringified payload on the front-end, crashing the `loadPivotBossScanner` loop (`scanData.forEach is not a function`).
  - *Fix*: Applied defensive JSON parsing logic (`typeof scanData === 'string' ? JSON.parse(scanData) : scanData`) in both `dashboard.html` and `page.tsx` to handle raw strings gracefully.
- **Mobile Tab Migration**: The scanner was originally erroneously placed in the **MARKETS** tab (`ANALYSIS`). It has been successfully migrated to sit permanently in the **ANALYTICS** tab (`ANALYTICS`).

## 3. UI Rebranding
- **"Weekly Expectancy" Label**: Corrected a misleading label on the frontend. The logic was already calculating today's expectancy, so the label was renamed from "WEEKLY EXPECTANCY" to "EXPECTANCY" across all UI tables.
- **Scanner Empty State**: Renamed the empty state message to "No active TLCS Day Type blueprints today."

## 4. AGENTS.md Single-Source-of-Truth Rules Update
- Documented the exact location and branding of the TLCS DAY TYPE SCANNER in the `Terminology & Page Name Mappings` section.
