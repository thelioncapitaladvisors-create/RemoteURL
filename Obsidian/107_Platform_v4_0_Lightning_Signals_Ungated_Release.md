# Platform v4.0: Lightning Signals Ungated Release & Multi-Engine Parity Specification

**Document ID**: 107  
**Effective Date**: November 19, 2026 (20:55 IST)  
**Classification**: Production Release Specification & Strategy Logic Sign-Off  
**Release Target**: TLCS Platform Version 4.0 (`v4.0`)  
**Status**: 🚀 PRODUCTION RELEASED & ACTIVE  

---

## 1. Executive Summary

Per direct user instruction and mandate, this release officially removes the `dayAllowed` (day-type filter) and `longAllowed`/`shortAllowed` (Camarilla $H_4/L_4$ touch-point gating) restrictions from **Lightning signals** (`LightningBuy` and `LightningSell`) across the entire trading ecosystem:
1. **TradingView Master Indicators**: `TV Indicator/TLCS_Live_Pivot_Alerts.pine`, `TV_Indicator_Full_Code.txt`, `user_code.pine`, and `TLCS_Live_Pivot_Alerts.pine`.
2. **Python BlackBox Algorithmic Engines**: `algo_engine/strategies.py` and `RemoteURL/algo_engine/strategies.py`.
3. **Autonomous DhanHQ Background Scanners**: `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js` and `dhan-scanner-background.js`.

---

## 2. Rationale & Structural Decoupling

### 2.1 The Nature of Lightning Signals
- Lightning signals represent the pure confluence of **Missile** (EMA 13/32 trend crossover or directional thrust) and **Scalp** (candle step-up / step-down bouncing from power candle midpoints):
  - `CanBuy && ScalpBuy`
  - `CanSell && ScalpSell`
- In legacy versions, Lightning signals inherited the restrictive baseline filters:
  - `dayAllowed`: Required market conditions to not be a sideways/in-range day (unless a Rejection Day).
  - `longAllowed` ($low < H_4$) / `shortAllowed` ($high > L_4$): Required the candle's touch-point to reach inside or beyond the Camarilla breakout boundaries.
- **Problem**: When strong momentum or trending moves occur in explosive market conditions, the confluence of Missile + Scalp frequently occurs while price has already broken beyond $H_4$ or without touching $H_4$, or on days classified as typical/sideways by early session ADR metrics. The legacy gates suppressed these high-velocity momentum continuation setups.

### 2.2 Symmetrical Ungated Architecture
- Following the precedent set for Divergences (Regular $D$ and Hidden $H$), Lightning signals are now treated as an **independent high-conviction breakout/continuation signal**, executing strictly upon dual Missile + Scalp confluence:
  $$\text{LightningBuy} = CanBuy \land ScalpBuy$$
  $$\text{LightningSell} = CanSell \land ScalpSell$$

---

## 3. Implementation Details Across All Engines

### 3.1 Pine Script Master Indicators (v4.0 Parity)

#### 1. Limit Touch-Point Exemption in `initializeAndPushTrade`:
```pine
// ── H4/L4 HARD GATE (Exempt for Divergence and Lightning signals per user mandate) ──
bool isGatingExempt = str.contains(longName, 'DIVERGENCE') or str.contains(longName, 'LIGHTNING')
bool _buy  = isGatingExempt ? buyCond  : (buyCond  and low < H4)
bool _sell = isGatingExempt ? sellCond : (sellCond and high > L4)
```

#### 2. Trigger Gating Removal:
```pine
// 1. Standard Lightning (Pure Native Missile + Scalp Confluence - Ungated per v4.0 mandate)
bool standardLightningBuy  = (CanBuy and ScalpBuy)
bool standardLightningSell = (CanSell and ScalpSell)
```

#### 3. On-Chart Visual Plotchar Parity:
```pine
// ⚡ 3. LIGHTNING PLOTS
plotchar(LightningBuy,  title = "Lightning Buy (Star)",  char = '★', location = location.belowbar, color = color.teal,   size = size.normal)
plotchar(LightningSell, title = "Lightning Sell (Star)", char = '★', location = location.abovebar, color = color.maroon, size = size.normal)
plotchar(LightningBuy,  title = "Lightning Buy (Bolt)",  char = '⚡', location = location.belowbar, color = color.lime,   size = size.normal)
plotchar(LightningSell, title = "Lightning Sell (Bolt)", char = '⚡', location = location.abovebar, color = color.lime,   size = size.normal)
```

### 3.2 Python BlackBox Engine (`algo_engine/strategies.py`)
```python
# 1. Standard Lightning (Pure Native Missile + Scalp Confluence - Ungated per v4.0 mandate)
standard_lightning_buy = can_buy and scalp_buy
standard_lightning_sell = can_sell and scalp_sell
lightning_buy = standard_lightning_buy
lightning_sell = standard_lightning_sell
```

### 3.3 DhanHQ Background Scanner (`dhan-scanner-background.js`)
```javascript
// 4. Strategy Triggers (Lines 3139-3166 - Ungated per v4.0 mandate)
const standardLightningBuy = (CanBuy && ScalpBuy);
const standardLightningSell = (CanSell && ScalpSell);
const LightningBuy = standardLightningBuy;
const LightningSell = standardLightningSell;
```

---

## 4. Verification & Parity Audit

### 4.1 SHA256 Checksum Parity Across Master Pine Script Indicators
All 4 indicator files maintain 100% byte-for-byte SHA256 parity:
- `TV Indicator/TLCS_Live_Pivot_Alerts.pine`: `120af02c7b4b2ac5f97ac204ce2023698462042aebdd6baa4de4dda7c04b5735`
- `TV_Indicator_Full_Code.txt`: `120af02c7b4b2ac5f97ac204ce2023698462042aebdd6baa4de4dda7c04b5735`
- `user_code.pine`: `120af02c7b4b2ac5f97ac204ce2023698462042aebdd6baa4de4dda7c04b5735`
- `TLCS_Live_Pivot_Alerts.pine`: `120af02c7b4b2ac5f97ac204ce2023698462042aebdd6baa4de4dda7c04b5735`

### 4.2 SHA256 Checksum Parity Across Python BlackBox Engines
Both Python strategy modules maintain 100% byte-for-byte SHA256 parity:
- `algo_engine/strategies.py`: `573259e6b2550d7a2e2ae4b64efa7c78085c917b441e371d4c8c8109c4b57fca`
- `RemoteURL/algo_engine/strategies.py`: `573259e6b2550d7a2e2ae4b64efa7c78085c917b441e371d4c8c8109c4b57fca`

### 4.3 SHA256 Checksum Parity Across DhanHQ Scanners
Both JavaScript scanner engines maintain 100% byte-for-byte SHA256 parity:
- `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js`: `1047c1d83d22c77c48176a95ee467127954d976b3a109546a3801d5c1592c460`
- `dhan-scanner-background.js`: `1047c1d83d22c77c48176a95ee467127954d976b3a109546a3801d5c1592c460`

### 4.4 Automated Test Suite
- Ran full unit test suite: `python3 -m unittest discover algo_engine/tests`
- **Result**: `Ran 136 tests ... OK (skipped=1)`

### 4.5 Production Frontend Build
- Executed Next.js compilation: `npm run build --prefix Tv-Alert-Mobile`
- **Result**: `✓ Compiled successfully`, `✓ Generating static pages (8/8)`, zero lint/type errors.

---

## 5. Sign-Off & Platform Status

The ungated Lightning signal release is fully verified, synchronized, and deployed on **Version 4.0 (`v4.0`)**.
