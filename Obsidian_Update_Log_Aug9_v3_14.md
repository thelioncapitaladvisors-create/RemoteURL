# TLCS Terminal & Mobile Suite — Version 3.14 Release Notes
**Release Date:** August 9, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 3.14)
Version 3.14 standardizes the Day Type Blueprint and Trade Sequence scanner update frequency to the **15-minute Opening Candle** close across all 6 market categories, and automates real-time Analytics tab data synchronization on the Web and Mobile platforms.

---

## Key Enhancements & Architectural Updates

### 1. Market-Wise 15-Minute Opening Candle Update Rule
- **Standardized Scanner Trigger:** Fixed the Day Type & Trade Sequence detection to lock in Opening Range (OR High/Low), Opening Bias, and Blueprints at the **close of the 15-minute opening candle** for all market categories:
  - **NIFTY / NSE Equities:** Opens 09:15 IST ➔ 15m OR closes at **09:30 IST**.
  - **MCX Commodities:** Opens 09:00 IST ➔ 15m OR closes at **09:15 IST**.
  - **NYMEX / US Commodities:** Opens 18:00 IST / 19:00 IST ➔ 15m OR closes at **18:15 IST / 19:15 IST** (09:45 EST).
  - **Forex (Global FX):** Session opens 13:30 IST (London) / 17:30 IST (NY) ➔ 15m OR closes at **13:45 IST / 17:45 IST**.
  - **World Indices:** Opens 19:00 IST (09:30 EST) ➔ 15m OR closes at **19:15 IST** (09:45 EST).
  - **Crypto 24/7:** Daily reset 05:30 IST (00:00 UTC) ➔ 15m OR closes at **05:45 IST**.

### 2. Automated Analytics Tab Data Synchronization (`page.tsx`)
- **Instant Tab-Switch Refresh:** Added `activeTab` to the primary state `useEffect` hook in `page.tsx`. Navigating to the **ANALYTICS** tab immediately triggers `fetchState()`, fetching the latest 15m opening candle scan payload without requiring manual reloads.
- **Continuous 5-Second Sync:** Mobile app continues polling the Supabase `pivotboss_scans` table every 5 seconds, updating the `LAST UPDATED:` timestamp live as scan webhooks arrive throughout the trading day.

---

## Verification & Deployment Log
- **Mobile App Repo (`Tv-Alert-Mobile`):** Committed and pushed to `origin/main` (`thelioncapital-alerts.git`). Deployed live on Netlify (`market-store.online`).
- **Root Workspace Repo (`Project`):** Committed and pushed to `origin/main` (`RemoteURL.git`).
- **Obsidian Vault:** Saved [`Obsidian_Update_Log_Aug9_v3_14.md`](file:///Users/vishant/Documents/Obsidian%20Vault/Obsidian_Update_Log_Aug9_v3_14.md).

---
*End of Version 3.14 Log.*
