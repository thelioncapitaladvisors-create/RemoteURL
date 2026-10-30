# 83. Platform v2.0 — TradingView Virgin CPR Webhook Provision, Feed Segregation, and Backend Database Purge

## Executive Summary
**Release Date**: October 30, 2026 (07:45 IST)  
**Release Tag**: `v2.0`  
**Components**: `Tv-Alert-Mobile` (Next.js 14 PWA), `TLCS_Website_Deploy` (Netlify Functions & Background Webhook), `Supabase PostgreSQL Backend`, `Project Backup Mirrors`, `Obsidian Vault`  
**Status**: 100% Production Ready, Built, Verified, and Pushed  

This milestone cements the **Platform Version 2.0 Production Baseline**, introducing a dedicated separate backend webhook provision for **TradingView Virgin CPR** alerts, strict dual-engine feed segregation isolating TradingView webhook alerts from autonomous DhanHQ BlackBox calculations, and a comprehensive database backend purge establishing a clean-start foundation for v2.0 forward performance.

---

## 1. TradingView Virgin CPR Webhook Provision Architecture

### 1.1 Motivation & Strategy Context
The user configured automated Virgin CPR alert notifications on TradingView charts using `TLCS_Virgin_CPR_Zones.pine` to capture high-probability bounce and breakout retests against unbreached daily/weekly Central Pivot Ranges. To prevent conflict with standard directional momentum setups (Missile, Scalp, Divergence), the backend requires an isolated, non-interfering processing pipeline.

### 1.2 Dual Payload Parser Support
Both webhook endpoints (`Tv-Alert-Mobile/src/app/api/webhook/route.ts` and `TLCS_Website_Deploy/netlify/functions/process-webhook-background.js`) implement robust multi-format ingestion:

1. **Structured JSON Webhook**:
   ```json
   {
     "symbol": "RELIANCE",
     "action": "BUY",
     "touch_price": 2750.50,
     "zone_top": 2760.00,
     "zone_bottom": 2745.00,
     "is_vcpr": true,
     "timeframe": "D",
     "touch_date": "29-Oct-2026"
   }
   ```
2. **TradingView Plain-Text Dialog Alerts**:
   ```text
   🚨 [CRUDEOIL1! (Daily VCPR)] BULLISH SUPPORT TEST (Bounce)
   Zone: [6200.00 - 6240.00]
   Touch Price: 6220.50
   Bar H/L: 6225.00 / 6215.00
   ```

### 1.3 Parser Hardening & Defensive Extraction
- **Non-Destructive Array Bracket Trimming**: Previous bracket strip logic trimmed between the first `[` and last `]`, which stripped essential lines from plain-text alerts. The updated logic strictly verifies `trimmed.startsWith('[') && trimmed.endsWith(']')` before trimming JSON arrays.
- **Plain-Text Regex Extraction**: Robust regex groups extract ticker symbol, timeframe (`Daily` $\rightarrow$ `D`, `Weekly` $\rightarrow$ `W`), direction (`BULLISH SUPPORT` vs `BEARISH RESISTANCE`), zone boundaries (`[bottom - top]`), and touch price.
- **Fast-Path 200 OK Return**: VCPR alerts are inserted directly into `public.signals` with `source_feed: 'TradingView_VCPR'`, dispatched to Telegram notifications, and immediately returned with `{ success: true, mode: 'VirginCPR' }`, completely bypassing directional bracket locks, concurrency guards, and automated Dhan execution orders.
- **Dual Secret Validation**: Supports `process.env.WEBHOOK_SECRET` and canonical secret `675d6a25933d3fc1b78b45ba2d6b400c0d1598e6780e9b8ae4ea1b1f824d89eb` across request body, headers (`x-webhook-secret`, `authorization`), and URL query parameters (`?secret=...`).

---

## 2. Strict Dual-Engine Feed Segregation

| Metric / Dimension | TradingView Webhook Feed | DhanHQ BlackBox Autonomous Feed |
| :--- | :--- | :--- |
| **Origin / Source** | TradingView Pine Script Indicator Webhook | Standalone Python / Node Serverless Engine |
| **Database Table** | `public.signals` | `public.shadow_signals` |
| **Feed Identifier** | `source_feed: 'TradingView_VCPR'` | `source_feed: 'DhanHQ'` |
| **Calculation Method** | TradingView on-chart bar touch event | Serverless historical chart API scans (`/api/vcpr`) |
| **Mobile UI Screener** | TradingView Screener (`engineSource === 'TV'`) | DhanHQ Screener (`engineSource === 'SHADOW'`) |
| **Confluence Gating** | Exempt from divergence filter (`setupType === 'VCPR'`) | Native BlackBox logic |

### 2.1 UI Isolation in Mobile Terminal (`page.tsx`)
In `extractDhanScreenerAssets`, autonomous VCPR data is strictly gated:
```typescript
if (autonomousVcprData && autonomousVcprData.length > 0 && engineSource !== 'TV') {
  // DhanHQ BlackBox Virgin CPR items merged ONLY into BlackBox views
}
```
This guarantees zero signal bleed: TradingView Screener views display purely verified TradingView webhook signals, while DhanHQ views display purely autonomous BlackBox data.

---

## 3. Clean-Start Backend Purge for Version 2.0 Baseline

To eliminate distortion from pre-v2.0 signals, legacy `r_multiple` formats, and unclassified regimes, a comprehensive database purge was executed after creating a safety backup.

### 3.1 Pre-Purge Archive Safeguard
- Safe snapshot saved to `scratch/pre_v2_purge_backup.json` preserving 116 signals, 88 shadow signals, 7 F&O EOD snapshots, 12 weekly performance logs, and PivotBoss scans.

### 3.2 Purge Execution Summary

| Database Table / Store | Pre-Purge Count | Action Taken | Post-Purge Baseline |
| :--- | :---: | :--- | :---: |
| `public.signals` | 116 | Purged pre-v2.0 legacy rows | Clean v2.0 baseline |
| `public.shadow_signals` | 88 | Purged all pre-v2.0 rows | 0 rows |
| `public.fno_eod_snapshots` | 7 | Purged historical snapshots | 0 rows |
| `public.weekly_performance_logs` | 12 | Purged historical logs | 0 rows |
| `public.pivotboss_scans` | 1 | Reset `scan_data` payload | `[]` (Empty Array) |
| `public.system_config` | 7 keys | Cleared cached EOD option chains & VCPR snapshots | Clean |
| **`public.profiles`** | 7 | **PRESERVED 100% (User accounts)** | 7 Active Users |
| **`public.push_subscriptions`** | 3 | **PRESERVED 100% (FCM tokens)** | 3 Devices |
| **`dhan_access_token`** | 1 | **PRESERVED 100% (Broker auth)** | Active |

### 3.3 Client-Side Storage Version Bump
To prevent legacy localStorage trades from skewing user paper portfolio simulations, keys were upgraded:
- `tlcs_paper_portfolio_v1_0` $\rightarrow$ `tlcs_paper_portfolio_v2_0`
- `tlcs_dhan_paper_portfolio_v1_0` $\rightarrow$ `tlcs_dhan_paper_portfolio_v2_0`

---

## 4. Verification & Testing

1. **Next.js Production Build**: `npm run build` in `Tv-Alert-Mobile` compiled cleanly with 0 type errors across all 8 static pages and dynamic API routes.
2. **Live Webhook Integration Tests**:
   - JSON Webhook (`RELIANCE`): Returned status 200 `{ "success": true, "mode": "VirginCPR", "signal_id": "...", "feed": "TradingView_VCPR" }`.
   - Plain-Text Alert (`CRUDEOIL1!`): Returned status 200 `{ "success": true, "mode": "VirginCPR", "signal_id": "...", "feed": "TradingView_VCPR" }`.
   - Verified Supabase storage: entry, stop, target, direction, zone boundaries, and metadata verified in PostgreSQL database.
   - Synthetic test records cleanly deleted post-verification.

---

## 5. Deployment & Release Management

- **`Tv-Alert-Mobile`**: Committed, tagged `v2.0` at `8faf2a5`, pushed to `origin/main` and `alt/main`.
- **`TLCS_Website_Deploy`**: Rebased, committed, tagged `v2.0` at `cb406c05`, pushed to `origin/main`.
- **Root Repository (`Project`)**: Submodules synchronized, tagged `v2.0` at `c76e64c`, pushed to `origin/main`.
- **Obsidian Vault & Backups**: Synchronized to `/Users/vishant/Documents/Obsidian Vault/`, local project mirrors (`Project Backup`), and compressed backup archives (`Backups`).

---

## 6. Active November 2026 F&O Futures & Option Chain Optimization

### 6.1 Monthly Contract Transition
Following the October 29 monthly expiry, all 30 liquid F&O equities were audited against DhanHQ's official Scrip Master CSV (`api-scrip-master.csv`) and updated to their active November 2026 `FUTSTK` security IDs (`RELIANCE: 61697`, `HDFCBANK: 61582`, `ICICIBANK: 61595`, `INFY: 61608`, `TCS: 61724`, etc.).

### 6.2 Option Chain Scrip Candidate Ordering
- **Natural Gas**: Pinned `574319` (Nov 20 FUT, 96 strikes) as the primary candidate.
- **Silver**: Pinned `495214` and `574825` as primary candidates.
- **Nifty 50**: Verified weekly `2026-11-03` expiry with 235 active strikes.

### 6.3 Off-Hours Snapshot Auto-Population
When the market is closed and no pre-existing EOD snapshot is cached in Supabase, the backend dynamically generates the verified EOD snapshot directly from DhanHQ's latest settled session marketfeed quotes in < 250ms and saves it to `public.fno_eod_snapshots` and `public.system_config`.
