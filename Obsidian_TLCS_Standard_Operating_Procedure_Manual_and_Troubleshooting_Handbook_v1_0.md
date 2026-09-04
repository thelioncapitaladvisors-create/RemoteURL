# TLCS Engineering Standard Operating Procedure (SOP) & Manual Troubleshooting Handbook

**Document Version:** `v1.0.0` (Production Master)  
**System Scope:** TLCS Trading Terminal Ecosystem (TradingView Indicator, Netlify Serverless Backend, Supabase Database, Next.js Mobile Application, Web Dashboard)  
**Target Audience:** System Owner & Technical Operators (Designed for 100% autonomous, manual troubleshooting without reliance on AI tools)

---

# 1. System Architecture & End-to-End Data Pipeline

The entire system is hosted **EXCLUSIVELY on Netlify** with **Supabase (PostgreSQL)** as the single source of truth database.

```
┌────────────────────────────────────────────────────────┐
│             TradingView Pine Script Indicator          │
│  (Fires JSON Alert upon: Setup, Fill, TrailSL, Close)  │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP POST (within 3s timeout)
                           ▼
┌────────────────────────────────────────────────────────┐
│     Netlify Fast Relayer (netlify/functions/webhook.js) │
│  - Returns 200 OK to TradingView in < 100ms            │
│  - Asynchronously forwards payload to background Lambda│
└──────────────────────────┬─────────────────────────────┘
                           │ HTTP POST (Internal relay)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Netlify Worker (process-webhook-background.js)         │
│  - Validates WEBHOOK_SECRET                            │
│  - Performs Triple-Binding: Direction + Price + Time   │
│  - Injects canonical percentage: metadata.exact_pct    │
│  - Upserts into Supabase 'signals' table               │
│  - Dispatches Web Push & Telegram notifications        │
└──────────────────────────┬─────────────────────────────┘
                           │ TLS / REST API
                           ▼
┌────────────────────────────────────────────────────────┐
│               Supabase Database (PostgreSQL)           │
│  Tables:                                               │
│   - 'signals': Every active limit, live trade & exit   │
│   - 'pivotboss_scans': Day Type Blueprints & Sequences │
│   - 'weekly_performance_logs': Weekly aggregated stats │
└──────────────────────────┬─────────────────────────────┘
                           │ Realtime WebSocket + REST Fetch
              ┌────────────┴────────────┐
              ▼                         ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│  Next.js Mobile App       │ │  Production Web Engine   │
│  (Tv-Alert-Mobile)        │ │  (TLCS_Website_Deploy)   │
│  Tabs: HUB, LOGS, SCREENER│ │  Pages: index.html,      │
│  MARKETS, INSIGHTS,       │ │  scanner.html,           │
│  ANALYTICS                │ │  dashboard.html          │
└───────────────────────────┘ └──────────────────────────┘
```

---

# 2. Critical Configuration & Credential Registry

When troubleshooting without AI, use these exact files to find credentials and endpoints:

| Component | Location on Disk | Description |
| :--- | :--- | :--- |
| **Supabase REST URL** | `Tv-Alert-Mobile/.env.local` | `https://dwepduvhzuhzeehbeaaz.supabase.co` |
| **Service Role Key** | `Tv-Alert-Mobile/.env.local` (Line 8) | Service role key (bypasses Row-Level Security for background workers and scripts) |
| **Production Webhook Secret** | `user_code.pine` (Line 6) / Netlify Env | `675d6a25933d3fc1b78b45ba2d6b400c0d1598e6780e9b8ae4ea1b1f824d89eb` |
| **Production Webhook URL** | TradingView Alert Dialog | `https://thelioncapitalsolutions.com/.netlify/functions/webhook` |
| **Submodule 1 (Web)** | `TLCS_Website_Deploy/` | Static website and Netlify functions repository |
| **Submodule 2 (Mobile)**| `Tv-Alert-Mobile/` | Next.js 14 mobile terminal progressive web application |

---

# 3. Golden Architectural Rules (Never Violate)

1. **`metadata.exact_pct` is the Single Source of Truth**:
   - Exact mathematical formula: `((Exit - Entry) / Entry) * 100` (inverted for SHORTs: `((Entry - Exit) / Entry) * 100`).
   - Never rely on TradingView string outcomes alone. Outcome resolution must check `exact_pct > 0 => WIN`, `exact_pct < 0 => LOSS`, `exact_pct == 0 => BREAKEVEN`.
2. **Canonical Win Rate Formula**:
   - Denominator across all cards and tabs MUST be total closed trades: `wins / totalClosedTrades`.
   - Never use `wins / (wins + losses)`, which improperly omits breakeven trades.
3. **Session Day Boundaries (00:00 Local Time)**:
   - "Today's trades" always starts at 0 Hrs local time: `new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()`.
   - Never use UTC date splitting (`toISOString().split('T')[0]`), which misaligns during Indian Standard Time (IST) evening hours.
4. **Market Session Closing Times (IST)**:
   - **NIFTY / Domestic Equities**: 15:30 IST (3:30 PM)
   - **MCX Commodities**: 23:30 IST (11:30 PM)
   - **NYMEX / Forex / World Indices**: 04:00 IST (4:00 AM next morning)
   - **Cryptocurrency**: 05:30 IST (5:30 AM next morning)
5. **Git Submodule Deployment Requirement**:
   - When modifying files inside `TLCS_Website_Deploy` or `Tv-Alert-Mobile`, you must commit and push inside the submodule directory first, then update the parent git pointer (`git add TLCS_Website_Deploy && git commit`). Failing to update the parent pointer leaves production disconnected.

---

# 4. Step-by-Step Manual Troubleshooting Guides

---

## Guide 1: Signals Stopped Updating / Daily Counts Show 0

### Symptoms:
- Weekly metrics show past trades, but "Today's Trades", "Live Trades", or "Active Limits" show `0`.
- TradingView alerts are firing, but Supabase `signals` table has no new rows.

### Manual Diagnosis Steps:
1. **Check for JavaScript Syntax Errors in Netlify Functions**:
   Open Terminal, navigate to the repository, and run the Node syntax validator:
   ```bash
   for f in TLCS_Website_Deploy/netlify/functions/*.js; do
     node -c "$f"
   done
   ```
   *If any file outputs `SyntaxError: Identifier 'xyz' has already been declared`, fix the duplicated variable name.*

2. **Query the Latest Signals in Supabase via Terminal**:
   Run this command in terminal to see the 5 most recent signals in the database:
   ```bash
   python3 -c "
   import urllib.request, json
   url = 'https://dwepduvhzuhzeehbeaaz.supabase.co/rest/v1/signals?select=id,symbol,type,created_at,status,outcome&order=created_at.desc&limit=5'
   headers = {
       'apikey': 'YOUR_SUPABASE_SERVICE_ROLE_KEY',
       'Authorization': 'Bearer YOUR_SUPABASE_SERVICE_ROLE_KEY'
   }
   req = urllib.request.Request(url, headers=headers)
   with urllib.request.urlopen(req) as resp:
       for s in json.loads(resp.read().decode()):
           print(s['id'], s['symbol'], s.get('type'), s['created_at'], s['status'])
   "
   ```
   *If the newest timestamp is hours old, alerts are not entering the database.*

3. **Test the Live Netlify Webhook Relayer**:
   Send a test ping from your terminal:
   ```bash
   curl -X POST https://thelioncapitalsolutions.com/.netlify/functions/webhook \
     -H "Content-Type: application/json" \
     -d '{"secret":"675d6a25933d3fc1b78b45ba2d6b400c0d1598e6780e9b8ae4ea1b1f824d89eb","trigger":"PingTest","symbol":"PING"}'
   ```
   *Expected Response:* `{"ok":true,"status":"dispatched_to_background"}` (HTTP 200).  
   *If it returns 401 Unauthorized, verify that the `secret` matches.*

4. **Inspect Live Netlify Function Logs**:
   - Log in to your [Netlify Dashboard](https://app.netlify.com).
   - Go to **Sites** > `thelioncapitalsolutions.com` > **Functions** > `process-webhook-background`.
   - Look at the live log stream. If the function crashed, the exact error stack trace with line number will be printed in red.

---

## Guide 2: Stale Trades Lingering as "Active" or "Open" on the Mobile App

### Symptoms:
- A trade from yesterday (e.g., `NG1!` with hold duration of 25h+) shows as `Active` on the LOGS tab or in Intraday Signals on SCREENER.
- The trade should have closed at market close or hit its target hours ago.

### Why This Happens:
TradingView alerts fire on bar conditions. If a trade opened yesterday but its exit alert was dropped (e.g., due to an indicator refresh, chart gap, or server downtime), the row in Supabase remains `status: 'Active'` and `exit_price: null`.

### Automated Safeguards Now in Place:
- Both `activeAlertLogs` and `INTRADAY SIGNALS` now check `isSignalActiveForMarket(s, now)`. As soon as a market crosses its official close time (e.g., 04:00 IST for NYMEX), the frontend hides the trade automatically.

### Manual Database Cleanup Steps:

#### Option A: Run the Cleanup Query in Supabase SQL Editor (Fastest)
1. Log in to [Supabase Dashboard](https://supabase.com/dashboard) > Project `dwepduvhzuhzeehbeaaz` > **SQL Editor**.
2. Run this query to inspect any stale open trades:
   ```sql
   SELECT id, symbol, type, created_at, status, entry, target, stop 
   FROM signals 
   WHERE outcome IS NULL OR outcome = 'OPEN' OR status ILIKE '%active%';
   ```
3. To safely close a stale trade at its target (WIN):
   ```sql
   UPDATE signals 
   SET 
     status = 'Completed TP1',
     outcome = 'WIN',
     exit_price = target,
     exit_at = NOW(),
     updated_at = NOW(),
     metadata = jsonb_set(COALESCE(metadata, '{}'::jsonb), '{exact_pct}', '1.25'::jsonb)
   WHERE id = 'PASTE_SIGNAL_ID_HERE';
   ```
4. To safely delete an unexecuted ghost limit order:
   ```sql
   DELETE FROM signals 
   WHERE id = 'PASTE_SIGNAL_ID_HERE';
   ```

#### Option B: Run the Emergency EOD Sweep Script
From your local terminal, execute the automated sweeper to close all trades open past market hours:
```bash
NODE_PATH=./Tv-Alert-Mobile/node_modules node -e "
const { sweepEODTrades } = require('./TLCS_Website_Deploy/netlify/functions/cron-eod-close.js');
sweepEODTrades().then(console.log);
"
```

---

## Guide 3: Paper Portfolio P&L Showing Unrealistic Numbers (e.g., ₹13 Lakhs in 2 Days)

### Symptoms:
- Virtual Net Worth or Realized Paper P&L shows hundreds of percent ROI in a few days.
- Average Win shows ₹1,00,000+ while individual stock/commodity trades only move a few thousand rupees.

### Root Cause & Currency Quotation Mechanics:
- When trading **JPY currency pairs** (`USDJPY`, `EURJPY`, `GBPJPY`), price points are in **Japanese Yen (¥)**, NOT US Dollars ($).
  - 1 Yen is roughly `$0.0064 USD` (or `~₹0.56 INR`).
  - If a 1.50 point move in USDJPY is multiplied by 10,000 units without dividing by the USD/JPY rate (~156.0), it creates an artificial **156x profit inflation**.
- When trading **INR currency pairs** (`USDINR`, `EURINR`), points are ALREADY in Rupees. If multiplied by `usdInrRate` (87.0), the profit is inflated by 87x.

### Code Location & Formula Audit:
The position sizing logic lives inside `Tv-Alert-Mobile/src/app/page.tsx` under `paperSimulatedTrades` (~Line 750–825). Ensure the conversion formulas remain intact:
```typescript
// 1. JPY Pairs (divide by exchange rate to get USD, then multiply by USD/INR)
if (cleanS.endsWith('JPY')) {
  const usdVal = (ptsDiff * mult) / (entry > 0 ? entry : 155.0);
  tradePnL = usdVal * usdInrRate;
}
// 2. INR Pairs (already in Rupees, do NOT multiply by usdInrRate)
else if (cleanS.endsWith('INR')) {
  tradePnL = ptsDiff * mult;
}
// 3. USD-base pairs (USDCAD, USDCHF)
else if (cleanS.startsWith('USD')) {
  const usdVal = (ptsDiff * mult) / (entry > 0 ? entry : 1.0);
  tradePnL = usdVal * usdInrRate;
}
// 4. Nikkei 225 (Index points are in Yen)
else if (cleanS === 'NI225' || cleanS === 'JP225') {
  tradePnL = (ptsDiff * 1 / 155.0) * usdInrRate;
}
```

---

## Guide 4: Day Type Blueprints / Screener Matrices Show "No active in last 7 days"

### Symptoms:
- Day Type Blueprints and Trade Sequences show empty or "No active Day Type Blueprints in the last 7 days."
- TradingView chart shows active blueprints for the day.

### Diagnosis Steps:
1. Day Type Scanner row data is stored in the Supabase table `pivotboss_scans` under `id = 1`.
2. Inspect the table in Supabase SQL Editor:
   ```sql
   SELECT id, updated_at, jsonb_array_length(scan_data) FROM pivotboss_scans WHERE id = 1;
   ```
3. If `jsonb_array_length` is 0 or `updated_at` is older than 24 hours:
   - In TradingView, open the chart with `TLCS_Intraday_Dashboards` or `TLCS_Sequence_Dashboard`.
   - Check if the alert is active: Alert action must be set to `alert() function calls only` pointing to `https://thelioncapitalsolutions.com/.netlify/functions/webhook`.
   - Verify that the alert fires on candle close (`alert.freq_once_per_bar_close`).

---

## Guide 5: Deploying Changes to Production Manually

Whenever you make any manual changes to the codebase, follow this exact sequence to deploy without AI:

### 1. If modifying Website / Netlify Functions (`TLCS_Website_Deploy`):
```bash
git -C TLCS_Website_Deploy add -A
git -C TLCS_Website_Deploy commit -m "fix: manual production update"
git -C TLCS_Website_Deploy push origin main
```

### 2. If modifying Mobile App (`Tv-Alert-Mobile`):
```bash
# Step A: Verify build locally first to catch any TypeScript errors
npm --prefix Tv-Alert-Mobile run build

# Step B: Commit and push
git -C Tv-Alert-Mobile add -A
git -C Tv-Alert-Mobile commit -m "fix: manual mobile app update"
git -C Tv-Alert-Mobile push origin main
```

### 3. Synchronize Root Workspace:
```bash
git add TLCS_Website_Deploy Tv-Alert-Mobile
git commit -m "chore: sync production submodules"
git push origin main
```
*Netlify will automatically detect the push and trigger an instantaneous production deployment.*

---

# 5. Emergency SQL Diagnostic & Healing Toolkit

Keep these SQL snippets handy. You can run them directly in the [Supabase SQL Editor](https://supabase.com/dashboard) at any time.

### Query 1: Find Any Outcome Mismatch (Math vs Label)
```sql
SELECT id, symbol, status, outcome, metadata->>'exact_pct' AS exact_pct
FROM signals
WHERE exit_price IS NOT NULL
  AND metadata->>'exact_pct' IS NOT NULL
  AND (
    ((metadata->>'exact_pct')::numeric > 0 AND outcome != 'WIN') OR
    ((metadata->>'exact_pct')::numeric < 0 AND outcome != 'LOSS') OR
    ((metadata->>'exact_pct')::numeric = 0 AND outcome != 'BREAKEVEN')
  );
```

### Query 2: Auto-Heal All Outcome Mismatches
```sql
UPDATE signals
SET outcome = CASE 
  WHEN (metadata->>'exact_pct')::numeric > 0 THEN 'WIN'
  WHEN (metadata->>'exact_pct')::numeric < 0 THEN 'LOSS'
  ELSE 'BREAKEVEN'
END
WHERE exit_price IS NOT NULL
  AND metadata->>'exact_pct' IS NOT NULL
  AND outcome IN ('WIN', 'LOSS', 'BREAKEVEN', 'OPEN');
```

### Query 3: Auto-Expire Trades Older Than 24 Hours
```sql
UPDATE signals
SET 
  status = 'EOD Exit',
  outcome = 'BREAKEVEN',
  exit_price = entry,
  exit_at = NOW(),
  updated_at = NOW(),
  metadata = jsonb_set(COALESCE(metadata, '{}'::jsonb), '{exit_reason}', '"STALE_MANUAL_SWEEP"'::jsonb)
WHERE (outcome IS NULL OR outcome = 'OPEN' OR status ILIKE '%active%')
  AND created_at < (NOW() - INTERVAL '24 HOURS');
```

---

*This document is permanently preserved in the repository root as `Obsidian_TLCS_Standard_Operating_Procedure_Manual_and_Troubleshooting_Handbook_v1_0.md`.*
