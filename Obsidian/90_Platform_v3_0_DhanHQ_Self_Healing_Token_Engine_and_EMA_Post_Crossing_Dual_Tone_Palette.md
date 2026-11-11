# 90. Platform v3.0: DhanHQ BlackBox Self-Healing Token Engine & EMA Post-Crossing Dual-Tone Palette

**Date:** November 11, 2026  
**Release:** Version 3.0 Production Maintenance Release  
**Components:**
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine` (Pine Script v6)
- `algo_engine/feeds/dhan_feed.py` (DhanHQ WebSocket & REST Data Feed)
- `algo_engine/nse100_scanner.py` (Top 100 NSE & MCX Autonomous Scanner)
- `algo_engine/strategies.py` (Strategy Trigger Evaluation Engine)
- `Tv-Alert-Mobile/src/app/page.tsx` (Mobile Terminal HUB & Markets Header)

---

## 1. Executive Summary

This production release resolves the two-week DhanHQ BlackBox operational silence, restores 100% autonomous execution across NSE Top 100 Equities and MCX Front-Month Commodities, implements strict subsequent confirmation candle close gating for all divergence signals, and updates on-chart EMA crossing visuals to an institutional dual-tone palette (**Green & Teal** for Bullish, **Red & Maroon** for Bearish).

---

## 2. DhanHQ BlackBox Self-Healing Engine & Forensic Root-Cause Resolution

### Forensic Analysis of Two-Week Silence
1. **Silent Token Expiration in Background Daemon**:
   - The LaunchAgent `com.tlcs.nse100scanner` cached the Dhan access token at daemon start.
   - Upon 24h expiration, the Dhan REST API returned `HTTP 401 (DH-901: Invalid_Authentication)`.
   - Without an in-cycle retry or dynamic TOTP trigger, `fetch_intraday_candles` and `fetch_daily_levels` silently fell back to empty responses, logging 0 signals every cycle in ~9 seconds.
2. **Premature Wall-Clock Cutoff Gating (Line 273)**:
   - `nse100_scanner.py` line 273 tested `is_trade_entry_allowed_for_bar(clean)` against `datetime.now()` (current system time) instead of candle timestamps.
   - For NSE equities (cutoff 14:00 IST), afternoon cycles (e.g. 14:46 IST) discarded all 100 NSE symbols immediately before evaluating any completed candles.
3. **Sequential Scan Duration & Evaluation Window**:
   - Sequential scans across 113 symbols with rate-limiting sleeps took 3,400s to 6,370s (1 to 1.75 hours).
   - Evaluating only the last 10 bars meant formed bars were missed before the runner could complete a cycle.
4. **Expired MCX Contract Scrips**:
   - `CRUDEOIL` in `DEFAULT_SYMBOL_MAP` was mapped to expired security ID `569900` (`HTTP 400`). Active front-month contract is `573422`.

### Architectural Fixes
- **Dynamic 401 Auto-Recovery**: `DhanFeed` intercepts `HTTP 401`, triggers `get_valid_dhan_token(force_refresh=True)` using dynamic TOTP, updates headers, and retries seamlessly.
- **Daily Levels Caching**: `self._daily_levels_cache` caches previous day H/L/C per symbol per calendar day, eliminating 113 redundant HTTP requests per cycle and cutting network overhead by 50%.
- **Active MCX Mapping**: `DEFAULT_SYMBOL_MAP` updated with front-month contract `573422` for `CRUDEOIL`.
- **Session Bar Evaluation & Engine Isolation**:
  - Line 273 wall-clock check removed.
  - Fresh `StrategyEngine()` instantiated per symbol, running all completed session bars from 09:15 open onward to maintain full divergence memory and 6-bar sliding windows.
  - Active signal recording restricted to recent evaluation window and valid candle timestamp entry hours (`is_trade_entry_allowed_for_bar(clean, cur_bar.timestamp)`).
- **Live Empirical Proof**:
  - Daemon restarted under PID `10512`.
  - First cycle completed in **17.62 seconds**, detecting and syncing **7 live signals** to `shadow_signals`: `CRUDEOIL` (SHORT VIRGIN CPR), `GOLD` (SHORT MISSILE, LONG HIDDEN DIVERGENCE), `SILVER` (LONG HIDDEN DIVERGENCE), and `CRUDEOILM`.

---

## 3. Strict Subsequent Confirmation Candle Close Gating (Version 3.0)

- **Unconfirmed Bar 0 Guarantee**: Zero trades, limit orders, or webhooks fire on Bar 0 (divergence formation candle).
- **Directional Confirmation Close (Bars 1 to 5)**:
  - Longs strictly require: `(close > open) and (close > close[1])`.
  - Shorts strictly require: `(close < open) and (close < close[1])`.
  - All legacy bypasses (`or GrS` / `or ReS`) permanently excised.
- **Structural Invalidation**: Penetration of divergence candle extreme (`low < lastBullDivLow` for Long, `high > lastBearDivHigh` for Short) immediately resets state (`lastDivBar := na`).
- **Entry Snap**: Snaps directly to confirmation candle close (`trade.entryLevel := isDivTrade ? close : trendLine`).

---

## 4. EMA Post-Crossing Dual-Tone Palette

In `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, and `user_code.pine`:
- **Fast EMA (`fShortEMA` / `PEMASlow`)**: Colored via `AdxCol`.
  - Bullish: **`color.green`**
  - Bearish: **`color.red`**
- **Medium EMA (`fMedEMA` / `PEMAMed`)**: Colored via `AdxCol1`.
  - Bullish: **`color.teal`**
  - Bearish: **`color.maroon`**
- **Combined Dual-Tone Standard**:
  - **Bullish Post-Crossing**: Fast = Green, Medium = Teal (**Green & Teal**).
  - **Bearish Post-Crossing**: Fast = Red, Medium = Maroon (**Red & Maroon**).
- **Post-Crossing Continuity**: Fallback embeds `(fShortEMA >= fMedEMA ? color.green/teal : color.red/maroon)` so lines never drop back to olive brown (`#887c12`), purple, or invisible white on light chart backgrounds.
- Fixed typo in `spanColor2A` (`m0 <= m0` -> `m0 <= m10`) and `twilight1` (`AdxCol` -> `AdxCol1`).

---

## 5. Verification & Parity Standards

- **100% SHA256 Parity**:
  - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `6f4878d217b4b0cfae70c7da6ee75eeb43bc45e03a58efc71580e1ac22dbddb5`
  - `TV_Indicator_Full_Code.txt`: `6f4878d217b4b0cfae70c7da6ee75eeb43bc45e03a58efc71580e1ac22dbddb5`
  - `user_code.pine`: `6f4878d217b4b0cfae70c7da6ee75eeb43bc45e03a58efc71580e1ac22dbddb5`
- **Unit Test Suite**: All 94 unit tests in `algo_engine/tests/test_phase1.py` passed cleanly (0.009s).
- **Mobile UI**: Header line 13944 in `Tv-Alert-Mobile/src/app/page.tsx` updated to `Markets Today`.
