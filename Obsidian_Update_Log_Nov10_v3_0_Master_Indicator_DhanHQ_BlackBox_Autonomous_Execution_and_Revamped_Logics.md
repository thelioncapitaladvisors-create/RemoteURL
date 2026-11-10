# Platform v3.0: Master Indicator Release, DhanHQ BlackBox Autonomous Execution & Revamped Trade Logics

**Effective Date:** November 10, 2026  
**Release Tag:** `v3.0`  
**Components:** `TV Indicator` (Pine Script v6 / v3.0), `algo_engine` (Python BlackBox Daemon), `Tv-Alert-Mobile` (Next.js PWA Terminal), `Telegram Dispatcher`  
**Status:** Complete, Verified & Production Locked  

---

## 1. Executive Summary

Platform Version 3.0 establishes the canonical release of the **TLCS PivotBoss Indicator v3.0** in full parity with the standalone **DhanHQ Python BlackBox Execution Engine**. Approved Indian markets (**NIFTY Top 100 Equities** and **MCX Commodities**) operate autonomously through the DhanHQ BlackBox daemon, evaluating real-time market data, generating signals, managing orders, and dispatching live trade alerts to the mobile application and Telegram channels without relying on external TradingView webhook triggers.

---

## 2. Revamped Trade Logics & Technical Specifications

### 2.1 Symmetrical Neutral Zone Fire_Alert Confluence Gate
In accordance with user directives, `Fire_Alert` confluence dots on the chart, mobile terminal, and Telegram dispatches are strictly restricted to the **Neutral Zone**:
- **Zone Definitions**:
  - `Redzcol = ((minus > plus) and (fShortEMA < fMedEMA) and (fPivotPDEMAF < fPivotPDEMAS))`
  - `Greenzcol = ((plus > minus) and (fShortEMA > fMedEMA) and (fPivotPDEMAF > fPivotPDEMAS))`
- **Symmetrical Blocking**:
  - Long trades and short trades are **BOTH BLOCKED** inside Greenzone and Redzone.
  - `Fire_Alert` triggers exclusively in the Neutral zone:
    ```pine
    Fire_Alert = Anysignal and not (Greenzcol or Redzcol)
    ```
- **Directional Coloring in Neutral Zone**:
  - Dots render with clear directional signaling:
    ```pine
    plotshape(Fire_Alert, title = 'Fire Alert Confluence', style = shape.circle, location = location.top, color = isFireLong ? color.green : color.red, size = size.tiny)
    ```

### 2.2 Complete Elimination of Engulfing Trend Limit Candles
- Bearish Engulfing at Top (`highTrendLimitLevel = bool(bearpower)`) and Bullish Engulfing at Bottom (`lowTrendLimitLevel = bool(bullpower)`) have been permanently excised from:
  1. Variable assignments (`bool highTrendLimitLevel = false`, `bool lowTrendLimitLevel = false`).
  2. `Fire_Alert` candidate lists (`isFireLong`, `isFireShort`, `Anysignal`).
  3. Active signal labels and trade triggers.
- Under zero circumstances will engulfing candle limit levels generate trade signals or chart labels.

### 2.3 Standalone Divergences (Regular `D` & Hidden `H`)
- **Regular Divergence (`D`)**:
  - The trend-direction ternary condition (`isBullCandle ? bullCond : ...`) has been removed, restoring pure momentum oscillator divergences.
  - Exclusively operates with a sliding 6-bar lookback buffer paired with `GrS` / `ReS` Power Candle bounces off S&R levels.
  - Fully exempt from H4/L4 Camarilla limits and Narrow CPR restrictions.
- **Hidden Divergence (`H`)**:
  - Plotted and evaluated as an oscillator confirmation signal.
  - Gated to formations within the Central Pivot Range (`cpr_top` / `cpr_bottom`) or Value Area (`VAH` / `VAL`).
  - Exempt from H4/L4 limit gating.

### 2.4 Standalone DhanHQ BlackBox Autonomous Execution
The Python BlackBox daemon (`algo_engine/`) runs continuously for approved Indian markets:
- **Approved Market Universe**:
  - `NIFTY`: NSE Top 100 liquid equities (`RELIANCE`, `HDFCBANK`, `INFY`, `TCS`, `ICICIBANK`, `SBIN`, etc.).
  - `MCX`: MCX front-month commodity futures (`CRUDEOIL`, `CRUDEOILM`, `NATURALGAS`, `NATURALGASM`, `GOLD`, `GOLDM`, `SILVER`, `SILVERM`, `COPPER`, `ZINC`, `ALUMINIUM`).
- **Autonomous Lifecycle**:
  1. Live market feed ingestion via DhanHQ WebSocket (`dhan_feed.py`).
  2. In-memory candle aggregation into 15m and Daily OHLC (`aggregator.py`).
  3. Deterministic calculation of CPR, Camarilla, ATR, DMI, and triple-smoothed EMAs (`pivots.py`).
  4. Execution of Version 3.0 gated strategy triggers (`strategies.py`).
  5. Order lifecycle management (`trade_manager.py`):
     - Midpoint limit order placement (`(session_high + session_low) / 2.0`).
     - Strict `low < H4` (Long) and `high > L4` (Short) wick touch-point qualification.
     - Target calculation: TP1, TP2, TP3, TP4.
     - **Pre-TP1 Midpoint Breakeven**: SL snaps to entry when price travels 50% towards TP1.
     - Exact percentage return tracking: `((Exit - Entry) / Entry) * 100`.
  6. Database & UI synchronization (`shadow_pipeline.py`):
     - Publishes directly to Supabase `public.shadow_signals` with `source = 'blackbox_dhan'` and `meta.source_feed = 'DhanHQ'`.
     - Powers the mobile terminal's **DhanHQ Screener** (`DHAN_SCREENER`) and **DhanHQ Virtual Paper Portfolio** (`DHAN_PAPER`).
  7. Telegram Alert Dispatch (`telegram_dispatcher.py`):
     - Market-routed alerts dispatched immediately upon order fill (`⚡ TRADE ACTIVE`), trailing SL movement (`🎯 TRAILING STOP UPDATE`), and trade closure (`🛑 TRADE CLOSED`).

---

## 3. Triple-File Source Code Parity & Checksums

All three master Pine Script indicator source files declare Version 3.0 with shorttitle `TLCS v3.0` and possess identical SHA256 checksums:

```
TV Indicator/TLCS_Live_Pivot_Alerts.pine: 06bdeb6ba1468126cff17e708df591c71cc5c610ae2d1b3c833e7c87189ac9d4
TV_Indicator_Full_Code.txt:               06bdeb6ba1468126cff17e708df591c71cc5c610ae2d1b3c833e7c87189ac9d4
user_code.pine:                           06bdeb6ba1468126cff17e708df591c71cc5c610ae2d1b3c833e7c87189ac9d4
```

---

## 4. Test Suite & Verification Results

Automated unit tests in `algo_engine/tests` confirm 100% deterministic parity:
```bash
python3 -m unittest discover -s algo_engine/tests
----------------------------------------------------------------------
Ran 128 tests in 1.807s

OK (skipped=1)
```
- `TestVersion30BlackBoxParity`:
  - `test_version_30_engulfing_limits_excluded_from_fire_alert` — Verified engulfing candles never produce trade signals.
  - `test_version_30_fire_alert_neutral_zone_symmetrical` — Verified `Fire_Alert` is blocked in Greenzone and Redzone, triggering only in Neutral Zone.
  - `test_version_30_dhan_approved_markets_autonomous_routing` — Verified autonomous routing of `NIFTY` equities and `MCX` commodities.
