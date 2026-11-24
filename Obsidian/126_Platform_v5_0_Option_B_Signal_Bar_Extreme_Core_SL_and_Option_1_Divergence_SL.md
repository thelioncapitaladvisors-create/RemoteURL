# 126. Platform v5.0: Option B (Signal Bar Extreme) Core Trend SL & Option 1 Divergence SL Mandate

**Effective Date**: November 24, 2026  
**Status**: ACTIVE PRODUCTION MANDATE  
**Release Version**: v5.0 (`v5.0.0`)  
**Scope**: All Pine Script Indicators (`TLCS_Live_Pivot_Alerts.pine`, `TLCS_Daily_TF_Indicator.pine`), Python BlackBox Algorithm Engine (`algo_engine/strategies.py`), and Unit Test Suites (`algo_engine/tests/test_phase1.py`).

---

## 1. Executive Summary & Objective

Based on comprehensive **VectorBT backtesting and forward-walk analysis across 72,008 hourly candles (17 multi-asset symbols across Equities, Indices, Commodities, Forex, and Crypto)**, the trading framework was optimized to resolve false stop-outs while maximizing risk-adjusted return:
1. **Core Trend Signals (Option B: Structural Candle Extreme)**:
   - For Missile, Scalp, Lightning, and Extreme Reversal, initial Stop Loss is anchored strictly to the **Signal Bar Extreme** with an offset of 0.50 * ATR.
   - **Performance Impact**: Delivers the highest overall net profit (**+276.70%**), lowest drawdown (**88.28%** vs 96.67% baseline), and strongest future forward-walk gain (**+49.26%**).
2. **Divergence Signals (Option 1: D/H Extreme +/- 2.0 * AvgCandleSize10)**:
   - Initial Stop Loss is anchored to the swing extreme of the candle printing the Divergence (`D` or `H`) with an offset of 2.0 * AvgCandleSize10.
   - Entry remains strictly at the confirmation candle midpoint (high + low) / 2.0 on subsequent bar touch (`status: 'ACTIVE LIMIT'`, `hasHitEntry = false`).

---

## 2. Mathematical Formulations

### 2.1 Core Trend Strategies (Option B: Signal Bar Extreme)
For all non-divergence trend setups:
- **Long Trend Signals** (`LONG MISSILE`, `LONG SCALP`, `LONG LIGHTNING`, `LONG EXTREME REVERSAL`):
  25495\text{slLevel} = \text{Low}_{\text{signal}} - 0.50 \times \text{ATR}25495
- **Short Trend Signals** (`SHORT MISSILE`, `SHORT SCALP`, `SHORT LIGHTNING`, `SHORT EXTREME REVERSAL`):
  25495\text{slLevel} = \text{High}_{\text{signal}} + 0.50 \times \text{ATR}25495

### 2.2 Divergence Signals (Option 1: D/H Extreme)
- **Long Divergence** (`LONG DIVERGENCE`, `LONG HIDDEN DIVERGENCE`):
  25495\text{slLevel} = \text{divLow} - 2.0 \times \text{AvgCandleSize}_{10}25495
- **Short Divergence** (`SHORT DIVERGENCE`, `SHORT HIDDEN DIVERGENCE`):
  25495\text{slLevel} = \text{divHigh} + 2.0 \times \text{AvgCandleSize}_{10}25495
Where:
25495\text{AvgCandleSize}_{10} = \frac{1}{10} \sum_{k=0}^{9} (\text{High}_{i-k} - \text{Low}_{i-k})25495

---

## 3. Comprehensive VectorBT Analysis Results (72,008 Bars)

| SL Strategy / Regime | Total Trades | Win Rate (%) | Profit Factor | Net Return (%) | Max Drawdown (%) | In-Sample Past (%) | Out-of-Sample Future (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Option B (`CORE_SL_BAR_EXTREME`)** | **1,573** | **30.45%** | **1.10** | **+276.70%** | **88.28%** | **+227.44%** | **+49.26%** |
| Fixed 1.00x ATR (`CORE_SL_1.00_ATR`) | 1,607 | 25.02% | 0.99 | +161.53% | 96.67% | +115.35% | +46.18% |
| Fixed 0.75x ATR (`CORE_SL_0.75_ATR`) | 1,612 | 21.03% | 0.90 | +20.35% | 97.58% | +3.85% | +16.50% |
| Fixed 1.50x ATR (`CORE_SL_1.50_ATR`) | 1,595 | 30.60% | 1.02 | +139.12% | 93.88% | +135.21% | +3.91% |

---

## 4. Code Parity Implementation Summary

1. **Python BlackBox Engine (`algo_engine/strategies.py` & `RemoteURL/algo_engine/strategies.py`)**:
   - `_build_signal()` updated to accept `bar_high` and `bar_low`.
   - Core Long signals set `sl = round(bar_low - 0.50 * atr_val, 2)`.
   - Core Short signals set `sl = round(bar_high + 0.50 * atr_val, 2)`.
   - Divergence signals set `sl_dist = 2.0 * avg_candle_size_10`.
2. **TradingView 15m Alerts Indicator (`TLCS_Live_Pivot_Alerts.pine` & mirrors)**:
   - Lines 3538-3541: Non-divergence trades calculate SL as `low - 0.50 * atrValue` for Long, and `high + 0.50 * atrValue` for Short.
   - Line 4055: `Fire_Alert` payload non-divergence SL matches `low - 0.50 * atrValue` / `high + 0.50 * atrValue`.
   - Divergence SL distance set to `2.0 * avgCandleSize10`.
3. **TradingView Daily 1D Indicator (`TV Indicator/TLCS_Daily_TF_Indicator.pine` & `RemoteURL/TV Indicator/...`)**:
   - Core alert dispatches (Missile, Scalp, Lightning, Extreme Reversal) set initial SL to `low - 0.50 * atrValue` (Long) and `high + 0.50 * atrValue` (Short).
   - Divergence alerts set SL to `2.0 * avgCandleSize10` from D/H candle extreme.
4. **Automated Unit Tests (`algo_engine/tests/test_phase1.py` & `RemoteURL/...`)**:
   - Added `test_core_trend_signals_initial_sl_bar_extreme()` verifying exact Option B mathematics.
   - Updated Divergence SL test to expect `b1.low - 2.0 * avg_10`.
   - **100/100 tests passing**.
