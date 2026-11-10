# 89. Platform v3.0: Confirmed Divergence Execution Gating & Collapsible Live Signals UI Standard (Effective November 10, 2026)

## Executive Summary
This production update resolves premature divergence entries by enforcing strict confirmation candle close execution across both TradingView indicator engines and Python BlackBox (`algo_engine`), ensuring divergence trades only execute upon valid directional candle confirmation. In parallel, the mobile terminal (`HUB` tab) introduces collapsible and toggleable Live Signals filter controls and updates the table header badge to `LIVE SIGNALS`.

---

## 1. Problem Statement & Root Cause Analysis

### RCA: Premature Short Entry on `BINANCE:DOGEUSDT 15m`
- **Observed Anomaly**: On November 10, 2026, `BINANCE:DOGEUSDT` fired a `SHORT HIDDEN DIVERGENCE` limit order at `0.07003` when `H` was detected.
- **Root Cause**:
  1. The indicator created an `ACTIVE LIMIT` order at `trendLine = 0.07003` without requiring a confirmed candle close on the subsequent bar.
  2. The candle after `H` rallied strongly (`close = 0.07003`), filling the short limit order while price was moving aggressively upward against the setup.
  3. The subsequent bar expanded bullishly through `0.07020`, immediately triggering Initial Stop Loss.
  4. The divergence was never directionally confirmed before trade entry.

---

## 2. Quantitative Architecture & Implementation Details

### A. Confirmed Divergence Execution Engine
Implemented symmetrically across all three Pine Script engines (`TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`) and `algo_engine/strategies.py`:

1. **Unconfirmed Bar 0**:
   - Detection of divergence (`ext_bullishDiv`, `ext_bearishDiv`, `ext_bullishHiddenDiv`, `ext_bearishHiddenDiv`) registers the detection bar index without opening trade sessions or transmitting webhooks.
2. **Directional Confirmation Candle Gating (Bars 1 to 5)**:
   - **Bullish Divergence** (`LONG DIVERGENCE` / `LONG HIDDEN DIVERGENCE`):
     - Requires: `(close > open) and (close > close[1])`.
   - **Bearish Divergence** (`SHORT DIVERGENCE` / `SHORT HIDDEN DIVERGENCE`):
     - Requires: `(close < open) and (close < close[1])`.
   - **Regular Divergence Parity**: Strictly preserves the requirement for Power Candle bounce (`GrS` for Longs, `ReS` for Shorts).
3. **Execution on Confirmation Close**:
   - For divergence setups, entry level snaps directly to the confirmation candle close (`trade.entryLevel := isDivTrade ? close : trendLine`, `trade.hasHitEntry := isDivTrade ? true : false`).
   - Dynamic ATR TP and SL levels are anchored directly to this confirmed entry price.
4. **Invalidation Guard**:
   - If price closes beyond the divergence bar's extreme (breaks above the high for bearish divergence, or breaks below the low for bullish divergence), the setup is immediately invalidated and cleared (`na`), preventing trades if a breakout occurs against the divergence.
5. **Single-Fire Memory**:
   - Guaranteed single execution per divergence setup via `lastFiredBar < lastDivBar` tracking.

---

## 3. Mobile Terminal Live Signals UI Enhancements (`Tv-Alert-Mobile/src/app/page.tsx`)
1. **Renamed Table Badge to `LIVE SIGNALS ⚡`**:
   - The badge on the `HUB` tab table header has been renamed from `CURRENT SIGNAL ⚡` to **`LIVE SIGNALS ⚡`** with animated gradients.
2. **Collapsible Filter Strip**:
   - Interactive `COLLAPSE` / `EXPAND` toggle button with `ChevronUp` / `ChevronDown` icons integrated into the top ticker strip.
3. **Toggleable Category Buttons**:
   - Clicking an active filter button toggles the state back to `'ALL'` for smooth single-tap resets.

---

## 4. Verification & Checksum Parity

1. **Pine Script Checksum Parity**:
   ```
   fadedf4b4376a84b0dd143b53b33f6165c3685aa43f93cebd4032e57085ee258  TV Indicator/TLCS_Live_Pivot_Alerts.pine
   fadedf4b4376a84b0dd143b53b33f6165c3685aa43f93cebd4032e57085ee258  TV_Indicator_Full_Code.txt
   fadedf4b4376a84b0dd143b53b33f6165c3685aa43f93cebd4032e57085ee258  user_code.pine
   ```
2. **Python Unit Tests**:
   - 94 unit tests in `algo_engine/tests/test_phase1.py` passing cleanly (0.011s).
3. **Next.js Production Build**:
   - `npm run build` compiled cleanly without type errors.
