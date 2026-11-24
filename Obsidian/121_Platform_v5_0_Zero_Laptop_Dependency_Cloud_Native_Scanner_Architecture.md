# 121_Platform_v5_0_Zero_Laptop_Dependency_Cloud_Native_Scanner_Architecture

**Document ID**: `121_Platform_v5_0_Zero_Laptop_Dependency_Cloud_Native_Scanner_Architecture`  
**Application Version**: `v5.0` (Institutional Build)  
**Effective Date**: November 24, 2026  
**Status**: ACTIVE / VERIFIED IN PRODUCTION  
**Impacted Files**:
- `~/Library/LaunchAgents/com.tlcs.nse100scanner.plist` (Decommissioned)
- `.github/workflows/dhan_scanner_cloud.yml` (New 24/7 Cloud Sentinel)
- `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js`
- `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js`
- `Tv-Alert-Mobile/src/app/api/cron/eod-close/route.ts`
- `Tv-Alert-Mobile/src/app/page.tsx`
- `AGENTS.md` & `.agents/AGENTS.md`

---

## 1. Executive Summary & Problem Resolution

### 1.1 The Incident & Root Cause
- **Old Static Snapshot Execution**:
  The background daemon was found executing from `/Users/vishant/Project/algo_engine` (a stale snapshot dated November 10), rather than `/Users/vishant/Documents/Project/algo_engine` (the active Git workspace).
- **macOS TCC Sandbox Access Blockade**:
  When launchd attempted to execute jobs targeting `/Users/vishant/Documents/Project`, macOS Full Disk Access / TCC blocked execution with `[Errno 1] Operation not permitted`.
- **Laptop Dependency Vulnerability**:
  Running background quantitative scanning on a personal laptop exposed the trading system to downtime whenever the machine slept, restarted, or disconnected from the network.

### 1.2 The Resolution
The local laptop background daemon has been **completely decommissioned and unloaded**. The quantitative scanning and trade lifecycle management have been transitioned to run **100% cloud-natively** across Netlify Serverless Background Functions and GitHub Actions Cloud Sentinel.

---

## 2. Cloud-Native Serverless Architecture

### 2.1 Complete Local Daemon Decommissioning
- Unloaded and disabled `~/Library/LaunchAgents/com.tlcs.nse100scanner.plist`.
- Terminated all local `run_nse100_scanner.py` daemon processes (PID 964).
- Confirmed zero local trading processes running on the host machine.

### 2.2 24/7 Cloud Sentinel via GitHub Actions (`dhan_scanner_cloud.yml`)
- **15-Minute Automated Cloud Cron**:
  Runs on Ubuntu container in GitHub Actions every 15 minutes (`*/15 3-18 * * 1-5`, 08:30 to 23:30 IST, Monday–Friday).
- **Autonomous Scanners**:
  - Executes `python algo_engine/run_nse100_scanner.py --once` during market hours.
  - At 15:30 IST (`mins >= 930`): executes `python algo_engine/run_daily_scanner.py --market nse` to evaluate Top 100 NSE stocks & NIFTY indices on 1D daily candles.
  - At 23:30 IST (`mins >= 1410`): executes `python algo_engine/run_daily_scanner.py --market mcx` to evaluate MCX commodities on 1D daily candles.
- **Redundancy Ping**:
  Dispatches a background ping to Netlify's `dhan-scanner-background` function for dual-engine fault tolerance.

### 2.3 1D Swing Multi-Day & Next-Week Persistence Mandate
- **EOD Sweeper Protection**:
  Across `cron-eod-close.js`, `dhan-scanner-background.js`, `nse100_scanner.py`, and `api/cron/eod-close/route.ts`:
  All signals with `timeframe in ('1D', 'DAILY', 'D')` or `is_swing === true` are strictly exempt from EOD cancellation, deletion, or premature closure.
- **Frontend Retention**:
  In `page.tsx` across `Tv-Alert-Mobile`, `RemoteURL`, and root, 1D swing signals are exempt from intraday session cutoff guards (`sessionFilter === 'TODAY'`), remaining visible on the INSIGHTS tab under **`SWING TRADING OPPORTUNITIES`** until next week or until authentically invalidated (reaching TP or SL).

---

## 3. Compliance & Verification
1. **Zero Laptop Dependency**: Verified `launchctl list` and process table contain zero local scanner processes.
2. **Deterministic Parity**: Pine Script indicator hash (`ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4`) preserved byte-for-byte.
3. **Application Version**: Formally designated Version 5.0 (`v5.0`).
