# Update Log - July 18 (Active Limits & EOD Close)

## 1. Web Dashboard (metrics.html & trade-metrics.js)
- Fixed the `loadPerformanceStats` function that was failing to render UI elements because it crashed when elements were missing or when parsing cancelled trades. 
- Added a strict check to ensure that trades tagged as `CANCELLED`, `UNKNOWN`, or `CANCEL` in status are unconditionally skipped from metric arrays.
- Handled DOM properties correctly by checking if elements exist before assigning `.innerText` values (dashboard vs. AI research pages).

## 2. Mobile App (page.tsx)
- Modified `isRealTrade` and `resolveOutcome` to explicitly exclude trades with a `CANCELLED` outcome string.
- This prevents `CANCELLED` trades from bypassing the valid-trade filters and showing up as `ACTIVE LIMITS` on the HUB tab.

## 3. Webhook / Cron Job (eod-close/route.ts)
- Upgraded the EOD-closer API to forcefully fetch trades with `Limit Order Placed` status (previously it was only querying `Active` and `Open`). This fixes the bug where Forex active limits were not being processed by the Yahoo helper function.
- Added a strict **24-hour enforcement window** for FOREX and CRYPTO markets. The cron job will skip closing FOREX and CRYPTO active trades unless they have been open for over 24 hours, ensuring they aren't prematurely closed during the standard 15:30 IST Nifty/MCX batch.
