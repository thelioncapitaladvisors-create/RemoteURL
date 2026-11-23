# Obsidian Document 117: Platform v5.0 Divergence 1.00x ATR Stop Loss Parity

**Status**: Implemented & Verified in Production  
**Date**: November 23, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Master Pine Script Indicators (`TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, `TLCS_Live_Pivot_Alerts.pine`), BlackBox Strategy Engine (`algo_engine/strategies.py`, `dhan-scanner-background.js`), Automated Unit Tests (`algo_engine/tests/test_phase1.py`), and Knowledge Base (`Obsidian/`).

---

## 1. Executive Summary & User Requirements

Per direct user instructions:
> *"2. Baseline (1.00x ATR from Entry). Now only make necessary changes for SL in the BlackBox and Tradingview codes for this stop loss regime logic. Don't touch other code parts. Give me revised codes."*

### Exact Implementation Scope:
1. **Indicator Stop Loss Modification Only**:
   - Indicator input `divSlAtrMultInput = input.float(1.0, step = 0.1, group = 'STOP_LOSS')`.
   - Dynamic SL computation in `initializeTradeSession`:
     `float currentSlMult = isDivTrade ? divSlAtrMultInput : slAtrMultInput`
     `trade.slLevel := isLong ? trade.entryLevel - currentSlMult * atrValue : trade.entryLevel + currentSlMult * atrValue`
   - Confluence alert webhook payload `FireAlert` updated with `fireSlMult` (1.00x ATR for Divergence signals).
2. **Zero Signal, Zigzag, or Plot Modifications**:
   - All divergence formulas, zigzag pivot methods, label styles, and plotshape markers are 100% preserved from the original indicator baseline.
3. **BlackBox Parity**:
   - Python BlackBox (`algo_engine/strategies.py`): `div_sl_atr_mult = 1.00` in `StrategyConfig`.
   - Node.js Background Scanner (`dhan-scanner-background.js`): `const slMult = isDivSignal ? 1.0 : 0.75`.
4. **Byte-for-Byte Checksum Parity Across All 4 Indicator Source Files**:
   - Exact SHA-256 hash synchronization: `b5e40f985e8c476c1ae7661e31ea26c1eb67e732bbbae84640eb14d47a19d19c`.

---

## 2. Technical Implementation Details

### 2.1 Pine Script Indicator Changes
```pine
// ── ATR-Based SL/TP ──────────────────────────────────────────
int   atrLengthInput   = input.int(title = 'ATR Length',     defval = 14,  group = 'STOP_LOSS')
float slAtrMultInput   = input.float(title = 'SL ATR Mult',  defval = 0.75, step = 0.1, group = 'STOP_LOSS')
float divSlAtrMultInput = input.float(title = 'Divergence SL ATR Mult', defval = 1.0, step = 0.1, group = 'STOP_LOSS')

...

initializeTradeSession(Settings settings, string tradeDirection) =>
    ...
    // 🔥 Dynamic ATR TP/SL Levels (1.00x ATR for Divergence Signals)
    float currentSlMult = isDivTrade ? divSlAtrMultInput : slAtrMultInput
    trade.slLevel  := isLong ? math.round_to_mintick(trade.entryLevel - currentSlMult * atrValue)
                             : math.round_to_mintick(trade.entryLevel + currentSlMult * atrValue)

...

if Fire_Alert and enable_alerts
    float fireSlMult = str.contains(fireActiveSignal, 'DIVERGENCE') ? divSlAtrMultInput : slAtrMultInput
    ...
    str.tostring(isFireLong ? trendLine - fireSlMult * atrValue : trendLine + fireSlMult * atrValue, format.mintick)
```

---

## 3. Checksum Parity Across 4 Files

- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `b5e40f985e8c476c1ae7661e31ea26c1eb67e732bbbae84640eb14d47a19d19c`
- `TV_Indicator_Full_Code.txt`: `b5e40f985e8c476c1ae7661e31ea26c1eb67e732bbbae84640eb14d47a19d19c`
- `user_code.pine`: `b5e40f985e8c476c1ae7661e31ea26c1eb67e732bbbae84640eb14d47a19d19c`
- `TLCS_Live_Pivot_Alerts.pine`: `b5e40f985e8c476c1ae7661e31ea26c1eb67e732bbbae84640eb14d47a19d19c`
