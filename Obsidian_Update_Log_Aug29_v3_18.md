# TLCS Terminal & Mobile Suite — Version 3.18 Release Notes
**Release Date:** August 29, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 3.18)
Version 3.18 resolves an intraday session boundary and weekend rollover issue where late-session / EOD closing prints (e.g. trades completing at 03:32 IST on Friday night / early Saturday morning) were mistakenly treated as starting a new Saturday session rather than concluding Friday's session. It extends the NYMEX, Forex, and World indices close window to 04:00 IST and unifies the Mobile LOGS tab filtering with the dynamic session engine (`isSignalActiveForMarket`).

---

## Key Enhancements & Architectural Updates (V3.18)

### 1. Market Session Close Time Calibration (NYMEX, World Indices, Forex)
- **EOD Print Buffer:** Extended the daily session close boundary (`closeMins`) for NYMEX, Forex, and World indices from **02:30 IST** (`150m`) to **04:00 IST** (`240m`).
- **Late-Fill & Settlement Encompassment:** Accommodates EOD closing bars, 1-hour candle completions, and late settlement prints (which finalize around 03:30–03:35 IST) inside Friday's trading session.
- **Weekend Stale Trade Elimination:** Prevents closed Friday trades (such as `NG1!` and `BTCUSDT` closing at 03:32 IST) from rolling over as active trades on Saturday and Sunday.

### 2. Mobile App LOGS Tab Dynamic Session Filtering
- **Unified Session Resolution:** Updated `activeAlertLogs` in `Tv-Alert-Mobile/src/app/page.tsx` from raw calendar-day boundary matching (`getSignalTime >= startOfToday`) to the canonical `isSignalActiveForMarket(s, now)` dynamic session evaluator.
- **Consistency Across Hub and Logs:** Ensures that both the **HUB** (Dashboard) and **LOGS** (Alerts) tabs adhere to the exact same market session life cycle and clear closed session trades in lockstep.

### 3. Real Weekly Calmar Ratio Metric Integration
- **Chronological Equity & Drawdown Engine**: Implemented empirical Weekly Calmar Ratio calculation ($\text{Weekly Cumulative Return \%} / \text{Weekly Max Drawdown \%}$) sorted chronologically with tie-breaker timestamps (`exit_at` / `created_at`).
- **Mobile 5-Column Grid Alignment**: Upgraded Row 2 on the **HUB** tab to a 5-column grid layout matching Row 1.
- **Space Optimization**: Renamed `WEEKLY PROFIT FACTOR` to `WEEKLY PR` and `WEEKLY EXPECTANCY` to `WEEKLY EXP` so all 5 metric cards render with balanced spacing.
- **Universal Synchronization**: Added `WEEKLY CALMAR` to the Web Dashboard (`dashboard.html`) performance pills grid.

### 4. Active Limit Order Threshold Alignment
- **Limit Expiry Boundary:** Aligned `isActiveLimit` across both Web and Mobile suites to recognize pending limit orders up to `4.0` hours (04:00 IST) for NYMEX, Forex, and World markets.

---

## Files Modified
1. `Tv-Alert-Mobile/src/app/page.tsx`
2. `TLCS_Website_Deploy/dashboard.html`
3. `TLCS_Website_Deploy/trade-metrics.js`

---

## Tagging & Git Version Control
- **Web App Repo (`TLCS_Website_Deploy`):** Pushed to `main`.
- **Mobile App Repo (`Tv-Alert-Mobile`):** Pushed to `main`.
- **Root Repository (`Project`):** Pushed to `main`.

---
*Official Version 3.18 Sealed on August 29, 2026.*
