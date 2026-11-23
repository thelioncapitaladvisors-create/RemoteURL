# Obsidian Document 117: Platform v5.0 Divergence 1.00x ATR Stop Loss & 1:1 Oscillator Replica Plotting Parity

**Status**: Implemented & Verified in Production  
**Date**: November 23, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Master Pine Script Indicators (`TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, `TLCS_Live_Pivot_Alerts.pine`), BlackBox Strategy Engine (`algo_engine/strategies.py`, `dhan-scanner-background.js`), Automated Unit Tests (`algo_engine/tests/test_phase1.py`), and Knowledge Base (`Obsidian/`).

---

## 1. Executive Summary & User Requirements

Per direct user instructions and reference code:
1. **Divergence Stop Loss**:
   - Baseline 1.00x ATR from Entry for all Divergence signals (D and H).
   - Dynamic SL computation in `initializeTradeSession` and `Fire_Alert`.
   - BlackBox engine (`algo_engine/strategies.py`) and background scanner (`dhan-scanner-background.js`) synchronized to 1.00x ATR SL.
2. **1:1 Oscillator Divergence Plot Replica**:
   - Restore native on-chart divergence labels (`pLabel = label.new(...)`) and price trendlines (`pLine = line.new(...)`) within `method divergence` at line 2904.
   - Match exact oscillator properties (`propLabel.color`, `propLabel.style`, `propLabel.yloc`, `priceLabelText` `[ D ]` / `[ H ]`, and formatted tooltips).
   - Disable/comment out legacy `plotshape(DivergenceBuy/Sell)` and `plotshape(HiddenDivBuy/Sell)` lines in Section 9 to eliminate conflicting, duplicate, or candle-shifted shapes.

---

## 2. Technical Implementation Details

### 2.1 Pine Script Indicator
- **Version 5.0 Header**:
  ```pine
  // TLCS PivotBoss Indicator — Version 5.0 (Master Release)
  indicator('TLCS PivotBoss Indicator v5.0', shorttitle = 'TLCS v5.0', overlay = true, max_lines_count = 500, max_labels_count = 500, max_bars_back = 500)
  ```
- **Native 1:1 Oscillator Divergence Labels & Lines (Line 2901-2905)**:
  ```pine
  pLine = line.new(lastPricePoint.time, lastPricePoint.price, pricePoint.time, pricePoint.price, xloc=xloc.bar_time, extend=propLine.extend, color=propLine.color, style=propLine.style, width=1, force_overlay=true)
  line oLine = na

  pLabel = label.new(pricePoint.time, pricePoint.price, text=priceLabelText, xloc=xloc.bar_time, yloc=propLabel.yloc, color=propLabel.color, style=propLabel.style, textcolor=propLabel.textcolor, size=propLabel.size, textalign=propLabel.textalign, tooltip=priceTooltipText, force_overlay=true)
  label oLabel = na
  ```
- **1.00x ATR Stop Loss Input & Dynamic Calculation (Lines 2961, 3506-3508, 4039-4045)**:
  ```pine
  float divSlAtrMultInput = input.float(title = 'Divergence SL ATR Mult', defval = 1.0, step = 0.1, group = 'STOP_LOSS')

  float currentSlMult = isDivTrade ? divSlAtrMultInput : slAtrMultInput
  trade.slLevel  := isLong ? math.round_to_mintick(trade.entryLevel - currentSlMult * atrValue)
                           : math.round_to_mintick(trade.entryLevel + currentSlMult * atrValue)
  ```
- **Legacy Plotshape Deactivation (Lines 3977-3984)**:
  ```pine
  // 🟢 / 🔴 1. REGULAR DIVERGENCE PLOTS (Legacy plotshapes disabled to prevent duplicate/conflicting shapes; rendered natively by Zigzag Divergence Screener label.new at line 2904 for 1:1 oscillator replica)
  // plotshape(DivergenceBuy,  title = "Bullish Regular Divergence (Confirmed)", style = shape.labelup,   location = location.belowbar, color = color.new(color.lime, 0), text = "D", textcolor = color.black, size = size.small)
  // plotshape(DivergenceSell, title = "Bearish Regular Divergence (Confirmed)", style = shape.labeldown, location = location.abovebar, color = color.new(color.maroon, 0), text = "D", textcolor = color.white, size = size.small)

  // 🔵 / 🟠 2. HIDDEN DIVERGENCE PLOTS (Legacy plotshapes disabled to prevent duplicate/conflicting shapes; rendered natively by Zigzag Divergence Screener label.new at line 2904 for 1:1 oscillator replica)
  // plotshape(HiddenDivBuy,   title = "Bullish Hidden Divergence (Confirmed)",  style = shape.labelup,   location = location.belowbar, color = color.teal,   text = "H", textcolor = color.white, size = size.small)
  // plotshape(HiddenDivSell,  title = "Bearish Hidden Divergence (Confirmed)",  style = shape.labeldown, location = location.abovebar, color = color.orange, text = "H", textcolor = color.black, size = size.small)
  ```

### 2.2 BlackBox Engine Parity
- `algo_engine/strategies.py`: `div_sl_atr_mult = 1.00` in `StrategyConfig`.
- `dhan-scanner-background.js`: `const slMult = isDivSignal ? 1.0 : 0.75`.
- `algo_engine/tests/test_phase1.py`: `test_divergence_initial_sl_is_1x_atr` (passed 9/9 divergence unit tests).

---

## 3. Checksum Parity Across All 4 Indicator Source Files

```
Algorithm: SHA-256
Hash: ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4

Files Verified:
1. TV Indicator/TLCS_Live_Pivot_Alerts.pine  [ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4]
2. TV_Indicator_Full_Code.txt               [ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4]
3. user_code.pine                           [ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4]
4. TLCS_Live_Pivot_Alerts.pine              [ac1911d7e2e92d37d9130a816420be305fd64b4784cf74bb17296ea0a98c50b4]

Status: 100% BYTE-FOR-BYTE IDENTICAL
```
