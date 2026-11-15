# Version 3.0 Production Log: Root Cause Analysis (RCA) on Divergence Plotting, Maroon "D" Elimination, and BlackBox Dual Slope Barrier Parity

**Date**: November 15, 2026  
**Release Tag**: `v3.0`  
**Checksum Parity**: `88dcdb039553f03803d5bd6f60b3791483ce663f905098956855e8b58c87d286`  

---

## 1. Executive Summary & Root Cause Analysis (RCA)

### Issue 1: Sudden Long Trade Level Plot at ~19:30
- **Observation**: A Long trade level projection (Entry, SL, and TP levels with green/red boxes) suddenly appeared on the chart at ~19:30.
- **RCA**:
  1. Earlier at 18:45, a Bullish Divergence setup was forming, but execution was blocked by the Symmetrical DMI Directional Momentum Filter because $DI^- > DI^+$ (`minus > plus`).
  2. At ~19:30, a **Bullish Hidden Divergence (`HiddenDivBuy`)** formed within CPR / Value Area.
  3. At that candle, DMI momentum shifted positive (`not (minus > plus)` became true).
  4. With directional confirmation satisfied, `HiddenDivBuy` confirmed and triggered `initializeAndPushTrade(settings, HiddenDivBuy, ...)`.
  5. `generateTradeVisuals` immediately rendered the active trade lines and risk-reward projections.

### Issue 2: Unconfirmed "D with Maroon Background" Appearing on Chart
- **Observation**: A maroon box with text "D" appeared above the candle at ~19:15-19:30, while no matching "D" appeared in the oscillator pane below.
- **RCA**:
  1. In the previous turn's optimization, legacy `plotshape(DivergenceSell, color=color.maroon, text="D")` at line 3935 was uncommented.
  2. In the original code, this `plotshape` was explicitly disabled (`// Legacy plotshapes disabled to prevent duplicate/phantom labels; rendered natively by Zigzag Divergence Screener label.new at line 2890`).
  3. Because `confirmedRegBear` looks back across a 5-bar window (`barsSinceRegBear >= 1 and barsSinceRegBear <= 5`), any candle that closed red within 5 bars of a prior bearish divergence pivot triggered `DivergenceSell`, causing a maroon "D" to paint on the post-pivot confirmation candle.
  4. Simultaneously, inside `zigzag.divergence()`, `oLabel` (oscillator label) and `pLabel` had been set to `na`, which suppressed the native oscillator labels.
  5. The combination of a maroon "D" painting on a confirmation candle without an accompanying oscillator label created visual confusion and made the signal look like an unconfirmed rogue trade.

---

## 2. Code Corrections & Permanent Anchors

### A. Master Pine Script v3.0
1. **Restored Native Oscillator Labels & Lines (`oLine` and `oLabel`)**:
   - Inside `zigzag.divergence()` (lines 2899-2904), `oLine` and `oLabel` are rendered with `force_overlay=false` so the oscillator pane always shows the exact matching "D" and "H" labels and trendlines at the divergence pivot.
   - `pLine` and `pLabel` are rendered with `force_overlay=true` on the price chart.
2. **Re-Disabled Legacy Redundant `plotshape` on Candles**:
   - Re-commented `plotshape(DivergenceBuy)`, `plotshape(DivergenceSell)`, `plotshape(HiddenDivBuy)`, and `plotshape(HiddenDivSell)` (lines 3934-3939).
   - Completely eliminates the stray maroon "D" and phantom post-pivot shapes.
3. **Preserved Dual Price & Oscillator Slope Line Validation**:
   - Theoretical slope check `priceAtBar * dir > priceTheoPrice * dir or oscillatorAtBar * dir > oscTheoPrice * dir` remains 100% intact.
4. **Maintained 100% Byte-for-Byte Checksum Parity**:
   - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, and `user_code.pine`:
     `SHA256: 88dcdb039553f03803d5bd6f60b3791483ce663f905098956855e8b58c87d286`.

### B. Python BlackBox & Background Scanner Parity
1. **`algo_engine/pivots.py` & `RemoteURL/algo_engine/pivots.py`**:
   - Implemented `check_trendline_barrier()` verifying theoretical trendlines for both price and oscillator across all intermediate bars between swing pivots.
   - Divergence is invalidated if either price or oscillator breaches the trendline.
2. **`algo_engine/strategies.py` & `RemoteURL/algo_engine/strategies.py`**:
   - Symmetrical DMI Directional Filter enforced across all divergence triggers.
   - Decoupled confirmation candle close gating.
3. **`algo_engine/trade_manager.py` & `RemoteURL/algo_engine/trade_manager.py`**:
   - Confirmed-only divergence exits (`is_confirmed_div_exit`), zero premature Bar 0 exits.
4. **`dhan-scanner-background.js`**:
   - Added theoretical trendline slope check for intermediate bars between j and i for both price and oscillator.
