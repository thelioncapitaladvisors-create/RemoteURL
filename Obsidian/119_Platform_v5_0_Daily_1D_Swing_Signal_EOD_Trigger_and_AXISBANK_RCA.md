# Obsidian Document 119: Platform v5.0 Daily (1D Swing) Signal Autonomous Market Close Trigger and AXISBANK RCA

**Status**: Implemented & Verified in Production  
**Date**: November 23, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Autonomous BlackBox Engine (`algo_engine/`), Scanner Daemons (`nse100_scanner.py`, `run_daily_scanner.py`, `engine_daemon.py`), Supabase Ingestion (`shadow_signals`), Next.js Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`), and Knowledge Base (`Obsidian/`, `AGENTS.md`).

---

## 1. Executive Summary & Problem Statement

### 1.1 User Inquiries:
1. **Signal Eligibility Verification**: Determine whether the `AXISBANK` Daily (1D) timeframe signal observed on the chart is a valid Swing Trading signal eligible for the application's filter.
2. **Root Cause Analysis (RCA)**: Investigate why this signal was not triggered on market close today (Nov 23, 2026) or yesterday in the application, leaving `SWING TRADING OPPORTUNITIES` -> `DAILY TF SIGNALS ( '1D' TIME FRAME)` completely collapsed/empty.
3. **Automated Market Close Execution Mandate**: Ensure that all eligible signals on the 1D timeframe trigger on a real-time basis at the close of market hours automatically (15:30 IST for NSE Equities & Indices; 23:30 IST for MCX Commodities).

---

## 2. Fact-Backed Signal Eligibility Proof (AXISBANK 1D Swing)

### 2.1 Pine Script Indicator Mathematical Qualification:
On the Daily (1D) chart for `AXISBANK`, the daily candle closing Nov 20, 2026 generated green upward triangles below the candle body.
In `TLCS v5.0` (line 1445):
$$\text{JustMissileBuy} = \text{buySignal} \land \text{Trendbuy} \land \text{CanBuy} \land \text{dayAllowed} \land \text{longAllowed} \land \lnot \text{ScalpBuy}$$
This mathematically triggered the canonical `Long Missile` signal.

### 2.2 Standalone Python BlackBox Parity Execution:
Direct live execution of `DailyBlackboxScanner(market='nse').scan_symbol('AXISBANK')` against DhanHQ daily OHLC historical candles deterministically confirmed the signal:
```json
{
  "symbol": "AXISBANK",
  "type": "LONG MISSILE",
  "trigger": "LONG MISSILE Trigger",
  "entry": 1312.50,
  "stop": 1287.81,
  "target": 1394.79,
  "tp2": 1444.16,
  "tp3": 1526.44,
  "tp4": 1575.81,
  "timeframe": "1D",
  "status": "ACTIVE LIMIT",
  "outcome": "OPEN",
  "source": "blackbox_dhan",
  "exchange": "NSE",
  "metadata": {
    "trade_id": "DHAN_STOCKS_AXISBANK_2026-11-20_LONG_MISSILE_1D",
    "timeframe": "1D",
    "interval": "1D",
    "day_type": "BIG MOVE",
    "opening_bias": "BULLISH",
    "market_category": "STOCKS",
    "cmp": 1446.00
  }
}
```

### 2.3 Frontend INSIGHTS Tab Filter Matching:
In `Tv-Alert-Mobile/src/app/page.tsx` (lines 7182–7230), the 6 approved Swing Trading execution strategies are:
1. Confluence (`FIRE`)
2. Lightning (`LIGHTNING`)
3. Extreme Reversal (`EXT_REV`)
4. Missile (`MISSILE`) $\leftarrow$ **AXISBANK qualifies under MISSILE**
5. Scalp (`SCALP`)
6. Divergence (`DIV`)

AXISBANK matches `MISSILE`, possesses `timeframe === '1D'`, and is strictly excluded from VCPR. Hence, **AXISBANK is 100% eligible for display on the INSIGHTS tab**.

---

## 3. Root Cause Analysis (RCA)

### 3.1 RCA Finding 1: Absence of an Automated Market Close Scheduler for 1D Daily Scans
- **Analysis**: In production, the active background process was `python3 algo_engine/run_nse100_scanner.py --interval 900`.
- **Finding**: `run_nse100_scanner.py` runs `NSE100Scanner`, which scans **only 15-minute intraday candles** (`fetch_intraday_candles(..., interval=15)`). The dedicated 1D Swing scanner (`algo_engine/run_daily_scanner.py` / `DailyBlackboxScanner`) was implemented as a manual on-demand CLI script without an automated cron job or market-close scheduler hook.
- **Consequence**: At 15:30 IST on Friday and Monday, no process invoked `DailyBlackboxScanner`. Consequently, zero daily candles were fetched, zero 1D signals were evaluated, and zero records were inserted into Supabase `shadow_signals`.

### 3.2 RCA Finding 2: Nil-Signal Clean Hiding
- In `Tv-Alert-Mobile/src/app/page.tsx`:
  ```typescript
  if (liveSignalsStats.total === 0) return null;
  ```
- Because `shadow_signals` contained 0 records with `timeframe === '1D'`, `liveSignalsStats.total` evaluated to `0`, causing the entire `DAILY TF SIGNALS ( '1D' TIME FRAME)` card to be collapsed and hidden ab-initio.

### 3.3 RCA Finding 3: Intraday Market Close Sweeper Missing 1D Multi-Day Swing Order Protection
- In `algo_engine/nse100_scanner.py`, `exit_all_live_trades_at_market_close()` runs at 15:30 IST to sweep intraday trades.
- Prior to this release, the sweeper lacked an explicit filter for `timeframe == '1D'`, risking unexecuted multi-day swing limits being deleted or closed prematurely.

---

## 4. Architectural Resolution & Code Changes

### 4.1 Automated Market Close Trigger Integration (`algo_engine/nse100_scanner.py`)
In `run_scan_cycle()`:
- **NSE Market Close (15:30 IST)**:
  When `mins >= 930 and mins < 960` on trading days, if `_last_nse_daily_scan_date != today_str`:
  ```python
  from .run_daily_scanner import DailyBlackboxScanner
  daily_nse_scanner = DailyBlackboxScanner(dhan_feed=self.dhan_feed, shadow_pipeline=self.shadow_pipeline, mock_mode=self.mock_mode, market="nse")
  daily_nse_signals = daily_nse_scanner.scan_all()
  self._last_nse_daily_scan_date = today_date_str
  ```
- **MCX Market Close (23:30 IST)**:
  When `mins >= 1410 and mins < 1440` on trading days, if `_last_mcx_daily_scan_date != today_str`:
  ```python
  from .run_daily_scanner import DailyBlackboxScanner
  daily_mcx_scanner = DailyBlackboxScanner(dhan_feed=self.dhan_feed, shadow_pipeline=self.shadow_pipeline, mock_mode=self.mock_mode, market="mcx")
  daily_mcx_signals = daily_mcx_scanner.scan_all()
  self._last_mcx_daily_scan_date = today_date_str
  ```

### 4.2 Multi-Day Swing Trade Protection in Market Close Sweeper (`algo_engine/nse100_scanner.py`)
In `exit_all_live_trades_at_market_close()`:
```python
tf = (r.get("timeframe") or meta.get("timeframe") or meta.get("interval") or "").upper()
if tf in ("1D", "DAILY", "D"):
    continue  # Strictly preserve multi-day swing orders across sessions
```

### 4.3 Standalone Daemon Mode (`algo_engine/run_daily_scanner.py`)
Added `--daemon` flag to `run_daily_scanner.py`. When launched with `--daemon`, the scanner continuously monitors IST time, triggering `scan_all()` automatically at 15:30 IST (for NSE) and 23:30 IST (for MCX) once per trading session.

### 4.4 Multi-Timeframe Engine Daemon Hook (`algo_engine/engine_daemon.py`)
Updated `_handle_daily_bar_close()` to evaluate `DailyBlackboxScanner.scan_symbol(symbol)` and synchronize authentic 1D swing execution signals to `shadow_signals`.

---

## 5. Verification Proof & Empirical Results

1. **AXISBANK & ADANIPORTS Live Sync**:
   - `AXISBANK`: `LONG MISSILE @ 1312.50` (Target: 1394.79, Stop: 1287.81). Successfully synced to Supabase `shadow_signals` with `id: 14e2cc7c-6915-4db7-b86c-31a035165026`.
   - `ADANIPORTS`: `LONG MISSILE @ 1786.05` (Target: 1892.85, Stop: 1754.01). Successfully synced to Supabase `shadow_signals`.
2. **Multi-Day Swing Order Protection**:
   - Market close sweep verified: 1D records are strictly bypassed and preserved as `ACTIVE LIMIT`.
3. **Checksum & Pine Script Integrity**:
   - Indicator files remain 100% byte-for-byte intact with SHA-256 checksum parity.
