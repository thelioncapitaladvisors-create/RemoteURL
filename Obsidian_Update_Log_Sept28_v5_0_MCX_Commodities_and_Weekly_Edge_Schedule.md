# Obsidian Operational Update Log: September 28, 2026 (v5.0)
## MCX Commodities Black Box Engine, DhanHQ FUTCOM Binding, Weekly Performance Edge Sunday Boundary & Pine Script Zero Exit Invariance

---

### 1. Executive Summary & Context
* **Platform Baseline**: Version `v5.0` / `5.0.0`
* **Release Date**: September 28, 2026
* **Target Repositories & Subsystems**:
  - `algo_engine/` (Python Black Box Engine, `dhan_scanner.py`, `dhan_auth.py`, `sync_weekly_performance.py`)
  - `TLCS_Website_Deploy/` (Netlify background workers, `dhan-auth.js`, `cron-heal-outcomes.js`, `cron-weekly-logs.js`, `system-audit.js`)
  - `Tv-Alert-Mobile/` (Next.js PWA terminal, `page.tsx`, `api/system-audit/route.ts`)
  - Indicator Codebases (`TV_Indicator_Full_Code.txt`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `Project Backup/TV_Indicator_Full_Code.txt`)
  - Database: Supabase PostgreSQL (`signals`, `shadow_signals`, `weekly_performance_edge`)
  - Knowledge Base: `.agents/AGENTS.md` and Obsidian Vault (`/Users/vishant/Documents/Obsidian Vault/`)
* **Primary Scope**:
  1. **Pine Script Zero Exit Price Elimination**: Guaranteed that any intraday expired trade or force-closed trade records the actual candle close price instead of `0.00`, preserving exact percentage math integrity across the entire platform.
  2. **Weekly Performance Edge Schedule & Sunday 00:00 IST Boundary**: Aligned weekly performance aggregation crons to Sunday midnight (`30 18 * * 0` UTC / Monday 00:00 IST) and strictly excluded the ongoing, active current week from premature database insertion and UI display.
  3. **MCX Commodities Ingestion via DhanHQ Black Box Engine**: Resolved DhanHQ API binding errors for commodities by establishing the mandatory `instrument: 'FUTCOM'` and `exchangeSegment: 'MCX_COMM'` protocol, mapped active Scrip Master contract security IDs, and activated dual-market operating hours (NSE until 15:30 IST, MCX until 23:30 IST).
  4. **Multi-Runtime Dhan Token Sharing**: Implemented shared file-based token caching (`/tmp/dhan_token_cache.json`) across Python and Node.js serverless runtimes, completely bypassing Dhan's strict 2-minute token regeneration rate limit (`DH-901`).
  5. **Supabase `shadow_signals` Schema Integrity**: Standardized the market filtering column to `exchange` (preventing PostgREST 42703 schema errors) and satisfied the `updated_at` NOT NULL constraint.

---

### 2. Pine Script Zero Exit Price Elimination & Mathematical Invariance

#### A. Problem Analysis
* When intraday trades remained open into the subsequent session, the Pine Script indicator's `isPastDay` logic forcibly closed the trade. However, it set `trade.isClosed := true` without assigning `trade.closeLevel := close`.
* This caused `exit_price: 0.00` to be dispatched in the webhook payload, leading the backend and UI to calculate:
  $$\text{exact\_pct} = \frac{0.00 - \text{Entry}}{\text{Entry}} \times 100 = -100\%$$
* This severe anomaly polluted Win Rate, Profit Factor, Expectancy, and Drawdown analytics.

#### B. Architectural Solution & Code Hardening
* Patched `terminateTrade`, `finalizeTrade`, and `processTradeArray` across all indicator files:
  ```pinescript
  bool isPastDay = timeframe.isintraday and (time - trade.entryTime) >= 86400000
  if isPastDay
      trade.isClosed    := true
      trade.forceClosed := true
      trade.closeLevel  := close  // Guaranteed candle close capture
  ```
* Enforced safe non-zero fallbacks before payload construction:
  ```pinescript
  if trade.closeLevel == 0.0 or na(trade.closeLevel)
      trade.closeLevel := close
  ```
* Synchronized `TV_Indicator_Full_Code.txt`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, and `Project Backup/TV_Indicator_Full_Code.txt` byte-for-byte.

---

### 3. Weekly Performance Edge Calendar Re-Alignment & Sunday Boundary

#### A. Premature Current Week Row Elimination
* **Root Cause**: On Monday mornings (e.g., 28 September), cron jobs and audit scripts evaluated the newly started week and prematurely inserted a row into `weekly_performance_edge` with partial/zero trades.
* **Architectural Mandate**:
  - The weekly edge reflects **completed historical weekly performance**. The ongoing current week must NEVER be inserted into `weekly_performance_edge` until the weekly session has officially terminated on Sunday at 23:59:59 IST.
  - Netlify scheduled cron expression anchored strictly to: `30 18 * * 0` (Sunday 18:30 UTC = Monday 00:00:00 IST).

#### B. Cross-Platform Guard Implementation
* **Backend Functions** (`cron-heal-outcomes.js`, `cron-weekly-logs.js`, `system-audit.js`):
  ```javascript
  const currentWeekStartISO = getStartOfWeekISO(now);
  if (weekStartISO === currentWeekStartISO) {
      // Skip ongoing active week - only process completed historical weeks
      return;
  }
  ```
* **Mobile Terminal** (`page.tsx`, `api/system-audit/route.ts`): Filtered out any in-progress current week from weekly analytics cards and tables.
* **Python Aggregator** (`algo_engine/sync_weekly_performance.py`): Enforced the same boundary guard.
* **Database Cleanup**: Purged invalid premature `2026-09-28` rows and legacy `market_type: 'stocks'` records from Supabase, restoring mathematical parity with daily trade counts.

---

### 4. MCX Commodities Ingestion via DhanHQ Black Box Architecture

#### A. DhanHQ API Protocol Resolution (`FUTCOM`)
* When querying MCX commodity contracts, passing `instrument: 'COMMODITY'` triggered Dhan HTTP 400 `DH-905 Input_Exception` because Dhan categorizes commodity futures as `FUTCOM` under `exchangeSegment: 'MCX_COMM'`.
* Standardized `instrument: 'FUTCOM'` and `exchangeSegment: 'MCX_COMM'` across both the Python black box engine and the Netlify options proxy.

#### B. Verified Scrip Master Security IDs for MCX Futures
Extracted directly from DhanHQ's live daily scrip master:
| Commodity Underlying | Scrip Security ID | Exchange Segment | Instrument Type |
| :--- | :--- | :--- | :--- |
| **GOLD** | `483079` | `MCX_COMM` | `FUTCOM` |
| **GOLDM** (Mini) | `569003` | `MCX_COMM` | `FUTCOM` |
| **SILVER** | `495214` | `MCX_COMM` | `FUTCOM` |
| **SILVERM** (Mini) | `483080` | `MCX_COMM` | `FUTCOM` |
| **CRUDEOIL** | `569900` | `MCX_COMM` | `FUTCOM` |
| **CRUDEOILM** (Mini) | `569901` | `MCX_COMM` | `FUTCOM` |
| **NATURALGAS** | `570750` | `MCX_COMM` | `FUTCOM` |
| **COPPER** | `571298` | `MCX_COMM` | `FUTCOM` |
| **ZINC** | `571303` | `MCX_COMM` | `FUTCOM` |
| **ALUMINIUM** | `571297` | `MCX_COMM` | `FUTCOM` |
| **ALUMINI** (Mini) | `571296` | `MCX_COMM` | `FUTCOM` |

#### C. Dual-Market Operating Sessions & Sweeps
* **NSE Equities**:
  - Scanning & Execution: `09:15` to `15:30 IST`.
  - New Entry Order Cutoff: Strictly `14:00 IST` (`mins < 840`).
  - Session Close Sweep: `15:30 IST`.
* **MCX Commodities**:
  - Scanning & Execution: `09:00` to `23:30 IST`.
  - New Entry Order Cutoff: Strictly `22:00 IST` (`mins < 1320`).
  - Session Close Sweep: `23:30 IST`.

---

### 5. Multi-Runtime Dhan Token Sharing (`/tmp/dhan_token_cache.json`)

* **Rate-Limit Constraint**: Dhan imposes a strict 2-minute cooldown on generating access tokens via TOTP (`DH-901 Multiple IP or Rapid Auth`). When both Python (`algo_engine`) and Node.js (`netlify/functions`) independently attempted TOTP generation, auth requests collided.
* **Shared Persistent Disk Cache**:
  - Location: `/tmp/dhan_token_cache.json`.
  - Stores: `{ "token": "...", "expires_at": "...", "created_at": "..." }`.
  - Both `dhan_auth.py` and `dhan-auth.js` check this file before initiating an RFC 6238 TOTP handshake. If a valid token exists with >5 minutes remaining, it is immediately reused.
  - Generates seamless single-token 24-hour lifecycle across independent processes.

---

### 6. Supabase `shadow_signals` Schema Integrity Mandate

* **Column Naming**:
  - In `shadow_signals`, the market category column is strictly named **`exchange`** (values: `'nifty'`, `'mcx'`).
  - Attempting to filter or write using `.eq('market', ...)` or `market: ...` causes PostgREST error `42703: column shadow_signals.market does not exist`. All queries and inserts must use `exchange`.
* **Timestamp Constraints**:
  - Column `updated_at` has a `NOT NULL` database constraint. Every row write must supply `updated_at: new Date().toISOString()`.

---

### 7. Verification & Platform State
* **Indicator Code**: 0 compilation errors across 3,282 lines.
* **Next.js Mobile PWA**: Build passing with 0 errors (`npm run build` completed cleanly).
* **Netlify Backend Functions**: Syntax verified; all endpoints running on Node 20 runtime.
* **Git Repository**: All changes committed and pushed to `origin/main`.
* **Zero Speculation Guarantee**: Every architectural resolution backed by live Dhan API contracts, PostgREST schema verification, and exact mathematical execution proofs.
