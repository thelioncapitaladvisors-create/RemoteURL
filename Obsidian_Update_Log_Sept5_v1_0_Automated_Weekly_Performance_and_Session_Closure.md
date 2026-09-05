# Version 1.0 Production Update: Automated Weekly Performance Edge Workflow & Zero-Trace Session Closure

**Release Date:** September 5, 2026  
**Milestone Version:** `v1.0.0` (Production Master)  
**System Components Affected:** `.github/workflows (weekly-performance-cron.yml)`, `algo_engine (sync_weekly_performance.py)`, `TLCS_Website_Deploy (sync_weekly_performance.py, scanner.js, trade-metrics.js, metrics.html, netlify/functions/cron-heal-outcomes.js, netlify/functions/cron-weekly-logs.js, netlify/functions/cron-eod-close.js)`, `Supabase (weekly_performance_logs, signals)`

---

## 1. System Overview & Problem Statement

### A. Weekly Performance Statistics Stalling
- **Issue**: Historical performance metrics in the **Weekly Performance Edge** table on both the website (`scanner.html`, `index.html`) and the mobile app (`page.tsx`, **ANALYTICS** tab) remained frozen at 70 trades across 6 rows from August 31, failing to automatically roll up the 15 new closed trades from September 1–4.
- **Root Cause 1**: In `TLCS_Website_Deploy/netlify/functions/cron-heal-outcomes.js`, line 38 queried `.select('id, outcome, status, metadata, exit_price')` while omitting `symbol`, `created_at`, `exit_at`, and `signal_ts`. When `syncWeeklyPerformanceLogs(signals)` executed, `s.symbol` and dates were undefined, causing the weekly aggregator to abort with 0 updates.
- **Root Cause 2**: In `cron-weekly-logs.js`, the schedule (`55 23 * * 0` UTC = Monday 05:25 AM IST) caused `getDay()` to resolve to Monday (`1`), shifting the weekly calculation to look forward from Monday onwards, missing the prior completed week entirely.
- **Root Cause 3**: No automated GitHub Actions cron workflow existed to ensure weekly rollups execute reliably with run logs.

### B. Lingering Traces of Closed Sessions on Weekends
- **Issue**: On Saturday evening (September 5, 2026), when NYMEX and all traditional markets were closed, the scanner displayed `CL1!` under NYMEX with `HOLD TIME: 21h 52m`, and the dashboard displayed `CL1!` with a pulsing green `LIVE NOW` badge.
- **Root Cause**: When `CL1!` exited on Friday night (`Exit: 91.22`, `Outcome: LOSS`), the webhook inserted a new row (`ID: 47198b94...`) rather than updating the pending row (`ID: 338f9a89...`), leaving the pending row in Supabase with `status: 'Active', exit_price: null`. The frontend evaluated `if (resolveOutcome(s) === 'OPEN') return true;` without checking if the market was closed on weekends.

---

## 2. Architectural Implementations & Fixes

### A. Automated End-of-Week Statistics Workflow (`weekly-performance-cron.yml`)
- Created a dedicated GitHub Actions workflow: [`.github/workflows/weekly-performance-cron.yml`](file:///Users/vishant/Documents/Project/.github/workflows/weekly-performance-cron.yml).
- **Execution Schedules**:
  - `cron: '30 18 * * 0'` — Every Sunday at 18:30 UTC (which is **Monday 00:00:00 IST / Sunday 23:59:59 IST**, the exact end-of-week boundary).
  - `cron: '0 22 * * 5'` — Every Friday at 22:00 UTC (EOD weekly close for equities, commodities, and forex).
  - `workflow_dispatch` — Instant 1-click manual trigger from the GitHub Actions console.
- **Task Runner**: Runs `algo_engine/sync_weekly_performance.py` using Python 3.11 with pinned dependencies (`supabase==2.15.1`, `httpx==0.27.2`).

### B. High-Performance Weekly Aggregation Engine (`sync_weekly_performance.py`)
- Created [`algo_engine/sync_weekly_performance.py`](file:///Users/vishant/Documents/Project/algo_engine/sync_weekly_performance.py).
- **Strict Canonical Formulas Enforced**:
  - Exact percentage returns from `metadata.exact_pct`.
  - Canonical Win Rate Formula: `Wins / (Wins + Losses + Breakevens) * 100` (Breakevens strictly included in denominator).
  - Profit Factor (`Gross Profit / Gross Loss`) and Half-Kelly % risk edge (`0.5 * (WinRateDec - LossRateDec / RR) * 100`).
  - Monday week boundaries in `Asia/Kolkata` time (`Asia/Kolkata` / UTC+5:30).
  - Upsert into `weekly_performance_logs` on conflict `(market_type, week_start_date)`.

### C. Zero-Trace Market Closure Sweep
- **Orphaned Row Deleted**: Permanently purged the duplicate orphaned `CL1!` row (`ID: 338f9a89...`). The true closed trade was already recorded in `ID: 47198b94...` with `Exit: 91.22` and `Outcome: LOSS`.
- **Database Verified**: Confirmed **0 open signals** remain across closed markets in Supabase.
- **EOD Sweeper Hardened (`cron-eod-close.js`)**:
  - Added fallback service role key to guarantee execution on Netlify.
  - Traditional markets are recognized as unconditionally closed on weekends (Saturday and Sunday).
- **Frontend Safeguards**:
  - `scanner.js`: Added `isSignalEligibleAsActive(s)` check. Stale `OPEN` trades from closed markets cannot linger on weekends.
  - `trade-metrics.js`: Added market closure checks to `isSignalActiveForMarket` and `updateBlackBoxPanel`.
  - `metrics.html`: Suppressed the pulsing green `LIVE NOW` badge for closed markets, cleanly rendering `MARKET CLOSED`.

### D. Redundant Netlify Cron Healers
- Fixed `cron-heal-outcomes.js` to select `symbol, exit_at, created_at, updated_at, signal_ts`, enabling the 30-minute self-healing cron to continuously keep `weekly_performance_logs` up to date.
- Fixed `cron-weekly-logs.js` schedule to `30 18 * * 0` (Sunday 18:30 UTC) with full historical Monday grouping.

---

## 3. Production Verification

1. **Local & CI/CD Execution**:
   - Executed `algo_engine/sync_weekly_performance.py` against production Supabase.
   - Processed all **85 closed signals**:
     - **Week 2026-08-31** (82 trades):
       - `crypto`: 17 trades | WR: 52.94% | Net: +10.03% | PF: 2.94 | Half-Kelly: +17.46%
       - `forex`: 4 trades | WR: 75.00% | Net: +1.52% | PF: 51.67 | Half-Kelly: +36.77%
       - `mcx`: 19 trades | WR: 15.79% | Net: -0.31% | PF: 0.89 | Half-Kelly: +0.00%
       - `nifty`: 24 trades | WR: 25.00% | Net: -6.22% | PF: 0.22 | Half-Kelly: +0.00%
       - `nymex`: 18 trades | WR: 33.33% | Net: +7.33% | PF: 3.92 | Half-Kelly: +13.97%
     - **Week 2026-08-24**: 1 trade | WR: 0.00% | Net: -0.32% | PF: 0.00 | Half-Kelly: +0.00%
2. **Aggregated Edge Rollup (System-Wide All Markets)**:
   - Week 2026-08-31 Total Trades: 82 (27W / 47L / 8BE) | True Win Rate: 32.93% | Net Edge: +2.47% | Profit Factor: 11.93 | Half-Kelly: +13.64%
3. **Market Closure Cleanliness**:
   - Supabase query confirms 0 open signals remaining.
   - Weekend view shows 0 active signals for NYMEX/NIFTY/MCX/FOREX/WORLD, and 0 `LIVE NOW` badges for closed markets.
