# TLCS Terminal & Mobile Suite — Version 3.13 Release Notes
**Release Date:** August 9, 2026  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)

---

## Executive Summary (Version 3.13)
Version 3.13 delivers UI density optimizations, strict non-guesswork hold duration resolution on trade log cards, and full mobile viewport table responsiveness across the Web Dashboard and Mobile Application platforms.

---

## Key Enhancements & Architectural Updates

### 1. Web Dashboard — Compact Alert Signal Rankings Redesign (`trade-metrics.js`)
- **Padding & Whitespace Trimming:** Reduced internal card padding from `1.25rem` (20px) to `0.55rem 0.75rem` (8px–12px) and trimmed card bottom margins by over 60%.
- **Inline Header Layout:** Integrated the Rank Badge (`RANK #1`), Strategy Name (`BEARISH HIDDEN DIVERGENCE`), Trade Count (`TRADES: 7`), and Performance Metrics (`WR: 100% | NET: +0.42%`) into a single high-density header row.
- **Dense Symbol Chips:** Reduced padding and font size for market symbol chips, allowing users to view all 5 top-performing ranking cards simultaneously without scrolling.

### 2. Mobile Application — Strict Real Entry Hold Duration (`page.tsx`)
- **Zero-Guesswork Hold Resolution:** Updated hold duration logic across both **HUB** and **LOGS** tabs.
- **Strict `real_entry_time` Requirement:** `HELD:` and `ALIVE:` durations are calculated strictly when `metadata.real_entry_time` (the exact millisecond the limit order executed) is present in the trade log payload.
- **Explicit `HELD: --` Fallback:** When `real_entry_time` is absent (such as unexecuted limit orders or legacy signals), the UI strictly displays `HELD: --` to ensure no artificial or estimated hold times are presented to the user.

### 3. Mobile Application — Strategy Table Viewport Fit & Dark Grid Aesthetic (`page.tsx`)
- **100% Mobile Viewport Fit:** Removed hardcoded `min-w-[700px]` container boundaries that previously forced horizontal scrolling and truncated `PROFIT FACTOR` and `AVG PROFIT/LOSS` columns off-screen.
- **Responsive 5-Column Layout:** Applied `table-fixed w-full` column distribution (`SIGNAL TYPE`, `WIN RATE`, `EXPECTANCY`, `PROFIT FACTOR`, `AVG P/L`) fitting all 5 metrics cleanly within standard mobile screen widths.
- **Dark Grid Visual Styling:** Transformed the table theme to match the website's dark aesthetic (`#080c14` background, `#e2b33c` gold headers, `#141b29` grid borders, `#00e676` green / `#ff5f56` red performance values).

### 4. System Scanner Polling & Update Frequency
- **5-Second UI Refresh:** Mobile app polls Supabase `pivotboss_scans` table every 5 seconds.
- **Real-Time Webhook Push:** TradingView indicator pushes live scan payloads immediately upon market structure changes, dynamically refreshing the `LAST UPDATED:` timestamp.

---

## Verification & Deployment Log
- **Web Dashboard Repo (`TLCS_Website_Deploy`):** Committed `7117089` to `origin/main` (`TLCS_Website.git`). Deployed live on Netlify (`thelioncapitalsolutions.com`).
- **Mobile App Repo (`Tv-Alert-Mobile`):** Committed `c97c671` to `origin/main` (`thelioncapital-alerts.git`). Deployed live on Netlify (`market-store.online`).
- **Root Workspace Repo (`Project`):** Committed `9417486` to `origin/main` (`RemoteURL.git`).
- **Obsidian Vault:** Updated [`Obsidian_Update_Log_Aug9_v3_13.md`](file:///Users/vishant/Documents/Obsidian%20Vault/Obsidian_Update_Log_Aug9_v3_13.md).

---
*End of Version 3.13 Log.*
