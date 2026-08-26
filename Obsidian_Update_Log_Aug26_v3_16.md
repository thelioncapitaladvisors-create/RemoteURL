# TLCS Terminal & Mobile Suite — Version 3.16 Release Notes
**Release Date:** August 26, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 3.16)
Version 3.16 resolves the critical metrics mismatch between the Web Dashboard and the Mobile App by aligning Supabase query row limits and implementing the per-market session boundary today-filtering logic across both platforms. It also introduces a dedicated "Live Trades" card to the Mobile HUB layout to distinguish executed live positions from pending limit orders.

---

## Key Enhancements & Architectural Updates (V3.16)

### 1. Market-Specific Session Boundaries for "Today's Trades" (Option A)
- **Problem:** Simple midnight-based today boundaries caused closed trade counts, win rates, and profit factors to diverge between the Web Dashboard (10 closed) and the Mobile App (2 closed) due to timezone overlap and early-morning sessions.
- **Session-Aware Filtering:**
  - Added `getLastMarketCloseTs` and `isSignalActiveForMarket` functions in both `dashboard.html` and `trade-metrics.js` to replicate the mobile app's session calculation.
  - Aligned boundaries by market close schedules: NSE (15:30 IST), MCX (23:30 IST), NYMEX/Forex/World (02:30 IST), and Crypto (05:30 IST).
  - Web performance statistics and cumulative equity curves now cleanly filter out stale signals from previous sessions.

### 2. Database Queries & Row Limit Unification
- **Standardized Limits:** Increased signal fetch limits in the Next.js API route (`route.ts`) and `trade-metrics.js` from `500` to `2000` to prevent truncation discrepancies during weekly/monthly aggregation calculations.
- **Aligned Projections:** Standardized all queries to select all fields (`select('*')`), ensuring consistent metadata extraction across Web and Mobile.

### 3. Dedicated 'Live Trades' Card on Mobile HUB
- **Granular Open Tracking:** Added a new card `LIVE TRADES` next to `ACTIVE LIMITS` on the HUB tab.
- **Status Splitting:** Separated the open signals count:
  - `ACTIVE LIMITS` now strictly shows pending unexecuted limit orders (`!s.updated_at`).
  - `LIVE TRADES` strictly shows active, filled positions (`!!s.updated_at`).
- **Responsive Layout:** Upgraded Row 1 of the HUB grid to `grid-cols-5` and scaled typography parameters to maintain a clean display without overlap.

---

## Tagging & Git Version Control
- **Web App Repo (`TLCS_Website_Deploy`):** Git Tag `v3.16.0`.
- **Mobile App Repo (`Tv-Alert-Mobile`):** Git Tag `v3.16.0`.
- **Root Repository (`Project`):** Commit & Git Tag `v3.16.0`.

---
*Official Version 3.16 Sealed on August 26, 2026.*
