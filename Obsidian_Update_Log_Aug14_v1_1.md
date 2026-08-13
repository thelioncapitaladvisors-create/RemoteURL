# TLCS Terminal & Mobile Suite — Version 1.1 Production Release Notes
**Release Date:** August 14, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 1.1)
Version 1.1 delivers crucial architectural fixes to trade processing lifecycles, database querying resilience, indicator repainting defenses, and mobile analytics dashboard expansions.

---

## Key Updates & System Hardening (V1.1)

### 1. TradeFill Webhook Pipeline & Hold Duration Calibration
- **Real Entry Time Recording:** Captures the exact limit order fill event (`trigger: "TradeFill"`) via webhook, updating the DB status to `Active` and logging `metadata.real_entry_time`.
- **UI Duration Parsing:** The frontend dashboards (`scanner.js`, `commodity-scanner.js`) and mobile app (`page.tsx`) now prioritize `real_entry_time` for hold duration calculations to reflect actual live held times instead of limit-order latency.

### 2. Failproof Trade Identity Binding & Dedup Guards
- **Direct trade_id Query Binders:** Standardized all state-updating webhooks (`TradeFill`, `TradeClose`, `TrailingSLUpdate`, `TradeUpdate`) to target active signals strictly via `trade_id` (`SYMBOL_TIMESTAMP_DIRECTION`) to prevent bulk-updating bugs.
- **Bulk Update Guard:** Aborts the webhook lifecycle if no unique identifiers are present in the TV payload.
- **New Signal Dedup Guard:** Queries Supabase before new signal inserts to skip duplicate TV webhook retries (matching same `trade_id` or `signal_ts` within ±5s).

### 3. 2-Candle confirmed Divergence Exit
- **Anti-Repainting Exit Logic:** Modified the divergence exit logic in `TLCS_Live_Pivot_Alerts.pine` to ignore the live candle (`[0]`). Exits now require a divergence signal at least 1 or 2 bars old (`[1]` or `[2]`) **and** 2 consecutive closed candles moving against the trade direction to confirm the exit.
- **Multi-Trade Stacking:** Maintained dynamic multi-trade stacking logic so trending assets can scale multiple divergence trades simultaneously without restriction.

### 4. Mobile Analytics Multi-Dashboard Matrix
- **Daily Signal Dashboard Matrix:** Integrated a 7-day parameter performance matrix onto the Analytics tab.
- **Weekly Signal Performance & Achievement Table:** Added a secondary 7-day analytics matrix table mapping day-wise targets achieved (TP1-TP4), win rates, net edge, and average percentage returns.

---

## Tagging & Git Version Control
- **Web App Repo (`TLCS_Website_Deploy`):** Version `1.1.0` package, Git Tag `v1.1.0`.
- **Mobile App Repo (`Tv-Alert-Mobile`):** Version `1.1.0` package, Git Tag `v1.1.0`.
- **Root Repository (`Project`):** Version `1.1.0` commit & Git Tag `v1.1.0`.

---
*Official Version 1.1 Sealed on August 14, 2026.*
