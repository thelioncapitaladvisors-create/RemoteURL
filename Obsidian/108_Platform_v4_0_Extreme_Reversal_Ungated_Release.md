# Platform v4.0: Extreme Reversal Signals Ungated Release & Multi-Engine Parity Specification

**Document ID**: 108  
**Effective Date**: November 19, 2026 (21:05 IST)  
**Classification**: Production Release Specification & Strategy Logic Sign-Off  
**Release Target**: TLCS Platform Version 4.0 (`v4.0`)  
**Status**: 🚀 PRODUCTION RELEASED & ACTIVE  

---

## 1. Executive Summary

Per direct user instruction and mandate, this release officially removes the `dayAllowed` (day-type gate) and `longAllowed`/`shortAllowed` (Camarilla $H_4/L_4$ touch-point gating) restrictions from **Extreme Reversal signals** (`ExtremeReversalBuy` and `ExtremeReversalSell`) across the entire trading ecosystem:
1. **TradingView Master Indicators**: `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, and `TLCS_Live_Pivot_Alerts.pine`.
2. **Python BlackBox Algorithmic Engines**: `algo_engine/strategies.py` and `RemoteURL/algo_engine/strategies.py`.
3. **Autonomous DhanHQ Background Scanners**: `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js` and `dhan-scanner-background.js`.

---

## 2. Technical Rationale & Structural Decoupling

### 2.1 The Nature of Extreme Reversal
- Extreme Reversal identifies exhaustion climax moves where price extends dramatically beyond statistical mean levels:
  - Requires a massive candle whose range exceeds $2\times$ the 50-period SMA candle range (`ta.tr > 2.0 * ta.sma(ta.tr, 50)`).
  - Requires decisive directional commitment where the candle body constitutes at least $75\%$ of the total candle range (`bodyPct >= 0.75`).
- **The Gating Problem**:
  - Climax exhaustion bars by definition occur during rapid, vertical thrusts that push prices well into the extremes of the session.
  - When a bullish exhaustion climax bar occurs, price has already expanded upward, frequently meaning its $low$ does not reach below $H_4$ (`low < H4`).
  - When early session ADR calculations categorize a day as typical or in-range, `dayAllowed` evaluates to `false`.
  - Under legacy gating (`Elongsignal and longAllowed and dayAllowed`), valid climax reversal entries were systematically suppressed by $H_4/L_4$ touch gating and sideways filters.

### 2.2 Symmetrical Ungated Architecture
- Mirroring the proven ungated structure of Divergence ($D, H$) and Lightning ($★, ⚡$) setups, Extreme Reversal is now treated as an **independent standalone exhaustion reversal signal**:
  $$\text{ExtremeReversalBuy} = Elongsignal$$
  $$\text{ExtremeReversalSell} = Eshortsignal$$
- Gating inside `initializeAndPushTrade` has been updated to explicitly exempt Extreme Reversal from $H_4/L_4$ touch requirements.

---

## 3. Implementation Details Across All Engines

### 3.1 Pine Script Master Indicators (v4.0 Parity)

#### 1. Limit Touch-Point Exemption in `initializeAndPushTrade`:
```pine
// ── H4/L4 HARD GATE (Exempt for Divergence, Lightning, and Extreme Reversal signals per user mandate) ──
bool isGatingExempt = str.contains(longName, 'DIVERGENCE') or str.contains(longName, 'LIGHTNING') or str.contains(longName, 'EXTREME REVERSAL')
bool _buy  = isGatingExempt ? buyCond  : (buyCond  and low < H4)
bool _sell = isGatingExempt ? sellCond : (sellCond and high > L4)
```

#### 2. Trigger Gating Removal:
```pine
// 4. Extreme Reversal (Independent signal, ungated per v4.0 mandate)
bool ExtremeReversalBuy  = Elongsignal
bool ExtremeReversalSell = Eshortsignal
```

#### 3. On-Chart Visual Plot Parity:
```pine
// 🔥 4. EXTREME REVERSAL PLOTS
plotshape(ExtremeReversalBuy,  title = "Bullish Extreme Reversal", style = shape.arrowup,   location = location.belowbar, color = color.aqua,    size = size.normal, text = "EXT REV", textcolor = color.aqua)
plotshape(ExtremeReversalSell, title = "Bearish Extreme Reversal", style = shape.arrowdown, location = location.abovebar, color = color.fuchsia, size = size.normal, text = "EXT REV", textcolor = color.fuchsia)
```

### 3.2 Python BlackBox Engine (`algo_engine/strategies.py`)
```python
# 4. Extreme Reversal (Independent signal, ungated per v4.0 mandate)
extreme_rev_buy = ctx.extreme_long_signal
extreme_rev_sell = ctx.extreme_short_signal
```

### 3.3 DhanHQ Background Scanner (`dhan-scanner-background.js`)
```javascript
// Extreme Reversal strategies are exempt from dayAllowed and H4/L4 gating per v4.0 mandate
const ExtremeReversalBuy = Elongsignal;
const ExtremeReversalSell = Eshortsignal;
```

### 3.4 Pine Script Screener Payload Scope Parity Fix
In TradingView, Pine Script v6 enforces strict local variable scoping. The 12 screener string formatting variables (`isNcprStr`, `isInsideStr`, `isNvaStr`, `isRejStr`, `isContStr`, `dtcStr`, `dbcStr`, `prevRangeStr`, `cprWidthStr`, `vahStr`, `valStr`, `vaWidthStr`) were previously declared indented inside `if Fire_Alert and enable_alerts`. When referenced by `if isNewDaySession or isNewRejectionSetup`, TradingView threw compiler error `CE10272: Undeclared identifier "isNcprStr"`. These declarations have been lifted to the global script scope immediately before `if Fire_Alert and enable_alerts`, ensuring zero compile errors and full availability across all alert branches.

---

## 4. Verification & Parity Audit

### 4.1 SHA256 Checksum Parity Across Master Pine Script Indicators
All 4 indicator files maintain 100% byte-for-byte SHA256 parity:
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `39c54b890337c5766297c9f955a43fc60380a6c76f34c4ccdf704dea88525f15`
- `TV_Indicator_Full_Code.txt`: `39c54b890337c5766297c9f955a43fc60380a6c76f34c4ccdf704dea88525f15`
- `user_code.pine`: `39c54b890337c5766297c9f955a43fc60380a6c76f34c4ccdf704dea88525f15`
- `TLCS_Live_Pivot_Alerts.pine`: `39c54b890337c5766297c9f955a43fc60380a6c76f34c4ccdf704dea88525f15`

### 4.2 SHA256 Checksum Parity Across Python BlackBox Engines
Both Python strategy modules maintain 100% byte-for-byte SHA256 parity:
- `algo_engine/strategies.py`: `dd30699e2eabef0c7d3fd117ee5f5f36fcf3212025c714c7f45e92000a22e424`
- `RemoteURL/algo_engine/strategies.py`: `dd30699e2eabef0c7d3fd117ee5f5f36fcf3212025c714c7f45e92000a22e424`

### 4.3 SHA256 Checksum Parity Across DhanHQ Scanners
Both JavaScript scanner engines maintain 100% byte-for-byte SHA256 parity:
- `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js`: `1081cff0d572087e32a2b538c0bbee6ebc91792cfbfa2ecef8b77a50540d539e`
- `dhan-scanner-background.js`: `1081cff0d572087e32a2b538c0bbee6ebc91792cfbfa2ecef8b77a50540d539e`

### 4.4 Automated Test Suite
- Ran full unit test suite: `python3 -m unittest discover algo_engine/tests`
- **Result**: `Ran 136 tests ... OK (skipped=1)`

### 4.5 Production Frontend Build
- Executed Next.js compilation: `npm run build --prefix Tv-Alert-Mobile`
- **Result**: `✓ Compiled successfully`, `✓ Generating static pages (8/8)`, zero lint/type errors.

---

## 5. Sign-Off & Platform Status

The ungated Extreme Reversal signal release is fully verified, synchronized, and deployed on **Version 4.0 (`v4.0`)**.
