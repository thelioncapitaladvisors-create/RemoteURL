# Obsidian Document 117: Platform v5.0 Divergence 1.00x ATR Stop Loss & 1:1 Oscillator Plot Replication Parity

**Status**: Implemented & Verified in Production  
**Date**: November 23, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Master Pine Script Indicators (`TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, `TLCS_Live_Pivot_Alerts.pine`), BlackBox Strategy Engine (`algo_engine/strategies.py`, `dhan-scanner-background.js`), Automated Unit Tests (`algo_engine/tests/test_phase1.py`), and Knowledge Base (`Obsidian/`).

---

## 1. Executive Summary & User Requirements

Per direct user instructions:
> *"Use this SL logic (1.00x ATR from Entry) for our BlackBox engine logic and also for the tradingview indicator. Modify the tradingview indicator code accordingly and share for adding onto the chart for fresh signals."*
> *"Why we are getting plots like this. I want exact replica of the oscillator code's plots on the chart."*

### Key Implementation Deliverables:
1. **1.00x ATR Stop Loss for Divergence Signals Across All Indicators & Engines**:
   - Indicator input `divSlAtrMultInput = input.float(1.0, step = 0.1, group = 'STOP_LOSS')`.
   - Dynamic SL computation in `initializeTradeSession`:
     `float currentSlMult = isDivTrade ? divSlAtrMultInput : slAtrMultInput`
     `trade.slLevel := isLong ? trade.entryLevel - currentSlMult * atrValue : trade.entryLevel + currentSlMult * atrValue`
   - Confluence alert webhook payload `FireAlert` updated with `fireSlMult` (1.00x ATR for Divergence signals).
   - Python BlackBox (`algo_engine/strategies.py`): `div_sl_atr_mult = 1.00` in `StrategyConfig`.
   - Node.js Background Scanner (`dhan-scanner-background.js`): `const slMult = isDivSignal ? 1.0 : 0.75`.
2. **Exact 1:1 Replica of Standalone Oscillator Plots on Candle Chart**:
   - Synchronized divergence formula at line 2854 with standalone oscillator (`TLCS_Native_Oscillator.pine: line 421`):
     `divergence = trend == dir and sentiment < 0 ? 1 : trend != dir and sentiment > 0 ? -1 : 0`
     (Restoring `trend == dir` ensures zero spurious divergence triggers on mismatched trend-pivot directions).
   - Excised duplicate `plotshape` calls for `DivergenceBuy/Sell` and `HiddenDivBuy/Sell` at lines 3978–3986 so only the native `pLabel` renders on the chart, eliminating duplicate/double-stacked markers and phantom maroon labels.
3. **Strict Trade Execution CPR / VAH-VAL Gating Fully Preserved**:
   - For trade qualification (`currentDivergence`), the strict CPR / VAH-VAL filter remains active.
   - If a Hidden Divergence occurs outside CPR and outside VAH/VAL, the informational `[ H ]` label is displayed on the chart matching the oscillator, but `divergenceType` is set to `None` so no trade execution order or signal is created.
4. **Byte-for-Byte Checksum Parity Across All 4 Pine Script Indicator Files**:
   - Exact SHA-256 hash synchronization: `1b1df4cdd4f6b1a5854ba86e4dac75eb7125143104d115a6ad3415337fc6e23c`.

---

## 2. Technical Implementation Details

### 2.1 Pine Script Indicator (`method divergence`)
```pine
                sentiment = math.sign(oscRatio - priceRatio)
                trend = properties.trendMethod == 3 ? math.sign(lastTrend) : properties.trendMethod == 1 ? math.sign(dir * (llastRatio - 1)) : math.sign(llastMa - lastMa)
                divergence = trend == dir and sentiment < 0 ? 1 : trend != dir and sentiment > 0 ? -1 : 0
                
                if divergence != 0
                    divergenceType := getDivergenceType(dir, divergence)

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

---

## 3. Verification & Parity Audit

1. **Checksum Parity Across 4 Files**:
   - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `1b1df4cdd4f6b1a5854ba86e4dac75eb7125143104d115a6ad3415337fc6e23c`
   - `TV_Indicator_Full_Code.txt`: `1b1df4cdd4f6b1a5854ba86e4dac75eb7125143104d115a6ad3415337fc6e23c`
   - `user_code.pine`: `1b1df4cdd4f6b1a5854ba86e4dac75eb7125143104d115a6ad3415337fc6e23c`
   - `TLCS_Live_Pivot_Alerts.pine`: `1b1df4cdd4f6b1a5854ba86e4dac75eb7125143104d115a6ad3415337fc6e23c`
