# Obsidian Document 117: Platform v5.0 Divergence 1.00x ATR Stop Loss & Informational On-Chart Markers Parity

**Status**: Implemented & Verified in Production  
**Date**: November 23, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Master Pine Script Indicators (`TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, `TLCS_Live_Pivot_Alerts.pine`), BlackBox Strategy Engine (`algo_engine/strategies.py`, `dhan-scanner-background.js`), Automated Unit Tests (`algo_engine/tests/test_phase1.py`), and Knowledge Base (`Obsidian/`).

---

## 1. Executive Summary & User Requirements

Per direct user instructions:
> *"Use this SL logic (1.00x ATR from Entry) for our BlackBox engine logic and also for the tradingview indicator. Modify the tradingview indicator code accordingly and share for adding onto the chart for fresh signals."*
> *"Keep current signal gating, but plot informational markers: Keep the strict trade confirmation and CPR gating for trade execution, but display informational [ H ] / [ D ] markers whenever the oscillator detects them."*

### Key Implementation Deliverables:
1. **1.00x ATR Stop Loss for Divergence Signals Across All Indicators & Engines**:
   - Indicator input `divSlAtrMultInput = input.float(1.0, step = 0.1, group = 'STOP_LOSS')`.
   - Dynamic SL computation in `initializeTradeSession`:
     `float currentSlMult = isDivTrade ? divSlAtrMultInput : slAtrMultInput`
     `trade.slLevel := isLong ? trade.entryLevel - currentSlMult * atrValue : trade.entryLevel + currentSlMult * atrValue`
   - Confluence alert webhook payload `FireAlert` updated with `fireSlMult` (1.00x ATR for Divergence signals).
   - Python BlackBox (`algo_engine/strategies.py`): `div_sl_atr_mult = 1.00` in `StrategyConfig`.
   - Node.js Background Scanner (`dhan-scanner-background.js`): `const slMult = isDivSignal ? 1.0 : 0.75`.
2. **Informational On-Chart Divergence Markers (`[ H ]` and `[ D ]`)**:
   - The Zigzag divergence engine now checks oscillator validity (`validOscDivergence`) first.
   - When detected, informational markers (`pLabel = label.new(...)`) and connecting pivot lines (`pLine = line.new(...)`) are immediately plotted on the candle chart at the pivot bar:
     - Lime `[ H ]` below candle for Bullish Hidden Divergence.
     - Orange `[ H ]` above candle for Bearish Hidden Divergence.
     - Green `[ D ]` below candle for Bullish Regular Divergence.
     - Red `[ D ]` above candle for Bearish Regular Divergence.
3. **Strict Trade Execution CPR / VAH-VAL Gating Fully Preserved**:
   - For trade qualification (`currentDivergence`), the strict CPR / VAH-VAL filter remains active.
   - If a Hidden Divergence occurs outside CPR and outside VAH/VAL, the informational `[ H ]` label is displayed for chart parity with the oscillator, but `divergenceType` is set to `None` so no trade execution order or signal is created.
4. **Byte-for-Byte Checksum Parity Across All 4 Pine Script Indicator Files**:
   - Exact SHA-256 hash synchronization: `e0b38c7a78cbbd20c414c6d10d2a9ddccffabbf5b3be2ed325fd3d0e6d8e5df5`.

---

## 2. Technical Implementation Details

### 2.1 Pine Script Indicator (`method divergence`)
```pine
                    validOscDivergence = true
                    for bar = lastPricePoint.index + 1 to pricePoint.index - 1 by 1
                        priceAtBar = priceMap.get(bar)
                        oscillatorAtBar = oscillatorMap.get(bar)
                        
                        px1 = lastPricePoint.index
                        py1 = lastPricePoint.price
                        px2 = pricePoint.index
                        py2 = pricePoint.price
                        priceTheoPrice = py1 + ((py2 - py1) / (px2 - px1)) * (bar - px1)

                        x1 = llastOscillatorPoint.index
                        y1 = llastOscillatorPoint.price
                        x2 = oscillatorPoint.index
                        y2 = oscillatorPoint.price
                        oscTheoPrice = y1 + ((y2 - y1) / (x2 - x1)) * (bar - x1)

                        if priceAtBar * dir > priceTheoPrice * dir or oscillatorAtBar * dir > oscTheoPrice * dir
                            validOscDivergence := false
                            break

                    if validOscDivergence
                        priceLabelText = divergenceType == DivergenceType.BullishDivergence or divergenceType == DivergenceType.BearishDivergence ? 'D' : 'H'
                        priceTooltipText = str.tostring(divergenceType) + '
Price : ' + str.tostring(lastPrice) + ' ( ' + str.tostring(priceRatio) + ' ) - ' +
                                         str.tostring(priceDirection) + '
' + 'Oscillator :' + str.tostring(lastMa) + ' ( ' + str.tostring(oscRatio) + ' ) - ' + str.tostring(oscillatorDirection)
                        
                        propLine = linePropertiesMap.get(divergenceType)
                        propLabel = labelPropertiesMap.get(divergenceType)

                        pLine = line.new(lastPricePoint.time, lastPricePoint.price, pricePoint.time, pricePoint.price, xloc=xloc.bar_time, extend=propLine.extend, color=propLine.color, style=propLine.style, width=1, force_overlay=true)
                        line oLine = na

                        pLabel = label.new(pricePoint.time, pricePoint.price, text=priceLabelText, xloc=xloc.bar_time, yloc=propLabel.yloc, color=propLabel.color, style=propLabel.style, textcolor=propLabel.textcolor, size=propLabel.size, textalign=propLabel.textalign, tooltip=priceTooltipText, force_overlay=true)
                        label oLabel = na
                        
                        divergenceObject = DivergenceObject.new(pLine, oLine, pLabel, oLabel, lastPricePoint.index, pricePoint.index, pricePoint, divergenceType)
                        divergenceObjects.push(divergenceObject)

                        // Strict Gating for Trade Execution: Hidden Divergence must be formed with CPR or within VAH/VAL levels
                        bool isHidden = (divergenceType == DivergenceType.BullishHiddenDivergence or divergenceType == DivergenceType.BearishHiddenDivergence)
                        bool validTradeDivergence = true
                        if isHidden
                            float cprTop = math.max(DTc, DBc)
                            float cprBot = math.min(DTc, DBc)
                            float vahLvl = math.max(VAH, VAL)
                            float valLvl = math.min(VAH, VAL)
                            bool formedWithCPR = (pricePoint.price >= cprBot and pricePoint.price <= cprTop) or (lastPricePoint.price >= cprBot and lastPricePoint.price <= cprTop) or (high >= cprBot and low <= cprTop) or (close >= cprBot and close <= cprTop)
                            bool formedWithinVAHVAL = (pricePoint.price >= valLvl and pricePoint.price <= vahLvl) or (lastPricePoint.price >= valLvl and lastPricePoint.price <= vahLvl) or (high >= valLvl and low <= vahLvl) or (close >= valLvl and close <= vahLvl)
                            if not (formedWithCPR or formedWithinVAHVAL)
                                validTradeDivergence := false

                        if not validTradeDivergence
                            divergenceType := DivergenceType.None
                        true
                    else
                        divergenceType := DivergenceType.None
                        false
```

### 2.2 Python BlackBox Engine (`algo_engine/strategies.py`)
```python
@dataclass
class StrategyConfig:
    atr_length: int = 14
    sl_atr_mult: float = 0.75      # Generic SL = 0.75 * ATR from entry
    div_sl_atr_mult: float = 1.00  # Divergence SL = 1.00 * ATR from entry
...

    def _build_signal(self, ...):
        cfg = self.config
        direction = "LONG" if is_long else "SHORT"
        sl_mult = cfg.div_sl_atr_mult if "DIVERGENCE" in name else cfg.sl_atr_mult

        if is_long:
            sl  = entry_price - sl_mult * atr_val
...
```

---

## 3. Verification & Parity Audit

1. **Automated Unit Tests**:
   - `python3 -m unittest algo_engine.tests.test_phase1.TestV7IndicatorParity.test_divergence_initial_sl_is_1x_atr` -> `OK`.
2. **Checksum Parity Across 4 Files**:
   - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `e0b38c7a78cbbd20c414c6d10d2a9ddccffabbf5b3be2ed325fd3d0e6d8e5df5`
   - `TV_Indicator_Full_Code.txt`: `e0b38c7a78cbbd20c414c6d10d2a9ddccffabbf5b3be2ed325fd3d0e6d8e5df5`
   - `user_code.pine`: `e0b38c7a78cbbd20c414c6d10d2a9ddccffabbf5b3be2ed325fd3d0e6d8e5df5`
   - `TLCS_Live_Pivot_Alerts.pine`: `e0b38c7a78cbbd20c414c6d10d2a9ddccffabbf5b3be2ed325fd3d0e6d8e5df5`
