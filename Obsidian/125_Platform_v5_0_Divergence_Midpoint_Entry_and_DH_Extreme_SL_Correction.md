# 125: Version 5.0 Divergence Confirmation Candle Midpoint Entry & D/H Candle Extreme SL Correction

**Date**: November 24, 2026  
**Status**: APPROVED & INSTITUTIONALIZED (v5.0)  
**Modules**: `TLCS_Live_Pivot_Alerts.pine`, `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV Indicator/TLCS_Daily_TF_Indicator.pine`, `algo_engine/strategies.py`, `algo_engine/tests/test_phase1.py`, `AGENTS.md`

---

## 1. Executive Summary & Root Cause Analysis (RCA)

### 1.1 The Problem
In live trading and chart replay on 15m intraday sessions (e.g. NIFTY `SHORT HIDDEN DIVERGENCE` trade `ac26b908-dbe2-4ce9-8ebb-c59e10aeb7b2`), users observed that trade levels (Entry, SL, TP lines) were failing to persist or display cleanly on charts following divergence detection badges (`D` / `H`).

### 1.2 Root Cause Analysis (RCA)
1. **Flawed Stop Loss Anchor**:
   - In earlier versions, divergence signals erroneously applied a tight initial SL offset derived directly from the entry candle (`entryLevel ± 1.00 * atrValue`), rather than anchoring the SL to the actual swing extreme of the candle that printed the Divergence (`D` or `H`).
   - Consequently, normal intraday price oscillation immediately touched the tight SL level on or right after the confirmation candle, causing an immediate false stop-out (`Hit Initial SL`).
   - In Pine Script, when a trade stops out, `deleteTradeVisuals(vis)` cleanly unplots the trade levels to prevent visual clutter, making it appear as though trade levels were never plotted for the divergence signal.
2. **Flawed Entry Anchor**:
   - The entry price was set to the confirmation candle `close`, rather than the **midpoint of the confirmation candle** (`(high + low) / 2.0`), which provides an institutional limit equilibrium price.

---

## 2. Institutional Directive & Exact Rulebook

Per user instructions:
> *"When we worked on the initial SL logic yesterday, it was instructed to keep the initial SL above or below the candle printing the D or H after confirmed by the confirmation candle, but we are mistakenly kep the SL level near to the entry level which always hits and we never get desired outputs from such divergence signals. Make necessary corrections to the BlackBox and the Indicator codes without touching any other elements of the code."*
> *"Ensure to keep the divergence signal entry level as mid of the confirmation candle. Extend other profit and trailing SL levels from this entry level. Keep entry SL as informed above. Revise the logic at all codes and BlackBox and come up with the modification done."*

### 2.1 The 4 Mathematical Mandates
1. **Confirmation Candle Midpoint Entry**:
   $$\text{entryLevel} = \text{round\_to\_mintick}\left(\frac{\text{high} + \text{low}}{2.0}\right)$$
   - Trade enters immediately upon confirmation candle close at this equilibrium midpoint price.
2. **Stop Loss (SL) Anchored to D/H Swing Extreme**:
   - **Long Divergence (Regular & Hidden)**:
     $$\text{slLevel} = \text{divLow} - \text{mintick} \quad (\text{Python BlackBox: } \text{div\_low} - 0.05)$$
   - **Short Divergence (Regular & Hidden)**:
     $$\text{slLevel} = \text{divHigh} + \text{mintick} \quad (\text{Python BlackBox: } \text{div\_high} + 0.05)$$
   - **Fallback**: If divergence extreme is unavailable, default safely to $\text{entryLevel} \pm 1.00 \times \text{ATR}$.
3. **Profit Targets (TP1–TP4) & Trailing SL Extension**:
   - All TP targets extend mathematically from the new confirmation candle midpoint `entryLevel`:
     $$\text{TP}_1 = \text{entryLevel} \pm 1.00 \times \text{ATR}$$
     $$\text{TP}_2 = \text{entryLevel} \pm 2.00 \times \text{ATR}$$
     $$\text{TP}_3 = \text{entryLevel} \pm 3.00 \times \text{ATR}$$
     $$\text{TP}_4 = \text{entryLevel} \pm 4.00 \times \text{ATR}$$
   - **Midpoint TP1-TP2 Breakeven**: When price reaches the 50% midpoint between $\text{TP}_1$ and $\text{TP}_2$, SL automatically advances to `entryLevel`.
   - **Trailing SL**: Continues trailing behind EMA / ATR steps beyond $\text{TP}_2$.
4. **Zero Side Modifications**:
   - Missile, Scalp, Lightning, and Extreme Reversal entry, stop, and target rules remain 100% untouched.

---

## 3. Implementation Details

### 3.1 Python BlackBox (`algo_engine/strategies.py`)
```python
# Entry Midpoint
elif "DIVERGENCE" in name:
    sig_entry = round((bar.high + bar.low) / 2.0, 2)

# Stop Loss & Targets
if "DIVERGENCE" in name:
    if is_long:
        div_low = self._last_hidden_bull_div_low if "HIDDEN" in name else self._last_reg_bull_div_low
        sl = round(div_low - 0.05, 2) if div_low is not None else round(entry_price - cfg.sl_atr_mult * atr_val, 2)
        tp1 = round(entry_price + cfg.tp1_atr_mult * atr_val, 2)
        tp2 = round(entry_price + cfg.tp2_atr_mult * atr_val, 2)
        tp3 = round(entry_price + cfg.tp3_atr_mult * atr_val, 2)
        tp4 = round(entry_price + cfg.tp4_atr_mult * atr_val, 2)
    else:
        div_high = self._last_hidden_bear_div_high if "HIDDEN" in name else self._last_reg_bear_div_high
        sl = round(div_high + 0.05, 2) if div_high is not None else round(entry_price + cfg.sl_atr_mult * atr_val, 2)
        tp1 = round(entry_price - cfg.tp1_atr_mult * atr_val, 2)
        tp2 = round(entry_price - cfg.tp2_atr_mult * atr_val, 2)
        tp3 = round(entry_price - cfg.tp3_atr_mult * atr_val, 2)
        tp4 = round(entry_price - cfg.tp4_atr_mult * atr_val, 2)
```

### 3.2 TradingView Pine Script Indicators (`TLCS_Live_Pivot_Alerts.pine` & `TLCS_Daily_TF_Indicator.pine`)
```pine
// Global tracking variables declared above initializeTradeSession:
var float lastRegBullDivLow      = na
var float lastRegBearDivHigh     = na
var float lastHiddenBullDivLow   = na
var float lastHiddenBearDivHigh  = na

// Inside initializeTradeSession():
bool isDivTrade        = str.contains(tradeDirection, 'DIVERGENCE')
float confirmCandleMid = math.round_to_mintick((high + low) / 2.0)
trade.entryLevel       := isDivTrade ? confirmCandleMid : trendLine
trade.hasHitEntry      := isDivTrade ? true : false
bool isLong            = str.contains(str.upper(tradeDirection), 'LONG')

if isDivTrade
    if isLong
        float divLow = str.contains(tradeDirection, 'HIDDEN') ? lastHiddenBullDivLow : lastRegBullDivLow
        trade.slLevel := not na(divLow) ? math.round_to_mintick(divLow - syminfo.mintick) : math.round_to_mintick(trade.entryLevel - slAtrMultInput * atrValue)
    else
        float divHigh = str.contains(tradeDirection, 'HIDDEN') ? lastHiddenBearDivHigh : lastRegBearDivHigh
        trade.slLevel := not na(divHigh) ? math.round_to_mintick(divHigh + syminfo.mintick) : math.round_to_mintick(trade.entryLevel + slAtrMultInput * atrValue)
else
    trade.slLevel := isLong ? math.round_to_mintick(trade.entryLevel - slAtrMultInput * atrValue)
                            : math.round_to_mintick(trade.entryLevel + slAtrMultInput * atrValue)

trade.tp1Level := isLong ? math.round_to_mintick(trade.entryLevel + tp1AtrMultInput * atrValue)
                         : math.round_to_mintick(trade.entryLevel - tp1AtrMultInput * atrValue)
trade.tp2Level := isLong ? math.round_to_mintick(trade.entryLevel + tp2AtrMultInput * atrValue)
                         : math.round_to_mintick(trade.entryLevel - tp2AtrMultInput * atrValue)
trade.tp3Level := isLong ? math.round_to_mintick(trade.entryLevel + tp3AtrMultInput * atrValue)
                         : math.round_to_mintick(trade.entryLevel - tp3AtrMultInput * atrValue)
trade.tp4Level := isLong ? math.round_to_mintick(trade.entryLevel + tp4AtrMultInput * atrValue)
                         : math.round_to_mintick(trade.entryLevel - tp4AtrMultInput * atrValue)
```

---

## 4. Verification & Testing

1. **Automated Unit Tests**:
   - `algo_engine/tests/test_phase1.py`: All 98 unit tests passed with 100% success rate (`98 passed in 0.12s`).
   - `test_divergence_initial_sl_is_1x_atr` successfully updated and verified:
     - Confirmation candle midpoint entry: `102.75`
     - Divergence swing candle low SL: `97.95` (`div_low - 0.05`)
2. **Mirror Parity**:
   - 100% byte-for-byte synchronization across all repository copies (`RemoteURL`, `Project Backup`, `TV Indicator/`).
3. **Version 5.0 Release**:
   - Committed and tagged with `v5.0` and `v5.0.0`.
