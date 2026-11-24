# 127. Platform v5.0: VectorBT Confluence Benchmark Metrics Refresh Post Initial SL & Divergence Midpoint Entry Optimization

**Effective Date**: November 24, 2026  
**Status**: ACTIVE PRODUCTION MANDATE  
**Release Version**: v5.0 (`v5.0.0`)  
**Scope**: Frontend Insights Tab (`Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, `page.tsx`), TradingView Pine Script Indicators, and Python BlackBox Algorithmic Engine.

---

## 1. Executive Summary & Objective

Following the institutional implementation of:
1. **Divergence Signals (`DIV_SL_0.5_AVG10`)**: Confirmation candle midpoint touch entry level ($\\text{entryLevel} = \\frac{\\text{high} + \\text{low}}{2.0}$) with initial Stop Loss anchored to the swing extreme of the candle printing the Divergence (`D` or `H`) with an offset of $0.5 \\times \\text{AvgCandleSize}_{10}$ (verified delivering Profit Factor **1.36**, Net Return **+194.39%**, and Max Drawdown **25.45%**).
2. **Core Trend Signals (`CORE_SL_BAR_EXTREME` / Option B)**: Initial Stop Loss anchored strictly to the Signal Bar Extreme with a $0.50 \\times \\text{ATR}$ buffer (verified delivering Profit Factor **1.10**, Net Return **+276.70%**, and Max Drawdown **88.28%**).

All quantitative benchmark metrics displayed under **🔥 VectorBT Confluence Quantitative Benchmark vs Live System** on the INSIGHTS tab (`activeTab === 'INSIGHTS'`) were re-simulated across **72,008 hourly candles** across 17 multi-asset instruments.

---

## 2. Deterministic VectorBT Backtest Benchmark Results (72,008 Bars)

### 2.1 Confluence Models Matrix (`MODELS`)

| Confluence Model | Setup Description | Standalone PF | Confluence PF | Edge Delta | Standalone MDD | Confluence MDD | MDD Reduction | VBT Win Rate (excl. BE) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MISSILE + DIVERGENCE** | Breakout confirmed by RSI Divergence | `1.12` | **`1.22`** | `+8.9%` | `40.53%` | **`35.35%`** | `-12.8%` | **`42.06%`** |
| **SCALP + DIVERGENCE** | S&R Retest confirmed by Divergence | `1.11` | **`1.44`** | `+29.7%` | `48.21%` | **`6.98%`** | `-85.5%` | **`40.91%`** |
| **LIGHTNING + DIVERGENCE (TRIPLE)** | Missile + Scalp + Divergence | `0.95` | **`1.29`** | `+35.8%` | `39.96%` | **`7.68%`** | `-80.8%` | **`66.67%`** |
| **REGULAR DIVERGENCE (STANDALONE)** | Mean Reversion RSI Divergence | `1.36` | **`1.36`** | `BASELINE` | `25.45%` | **`25.45%`** | `BASELINE` | **`30.20%`** |
| **HIDDEN DIVERGENCE (STANDALONE)** | Trend Continuation RSI Divergence | `0.96` | **`1.18`** | `+22.9%` | `2.81%` | **`1.85%`** | `-34.2%` | **`41.67%`** |

### 2.2 Comparison Summary Cards

#### Card 1: 📊 VectorBT Confluence Benchmark (72,000 BARS)
- **Sample Size Badge**: `72,000 BARS` (empirical 72,008 bars across 17 institutional instruments).
- **Profit Factor Range**: **`1.22 - 1.44`** (Subtitle: `+9% to +36% Edge`).
- **Win Rate Range**: **`30.2% - 66.7%`** (Subtitle: `Asymmetric 1:3 RR`).
- **Max Drawdown Range**: **`1.9% - 35.4%`** (Subtitle: `-13% to -86% Cut`).

#### Table Composite Footer Row:
- **Composite Benchmark PF**: **`1.30 Avg`** (was `1.27 Avg`).
- **Composite Benchmark Win Rate**: **`44.3% Avg`** (was `33.9% Avg`).
- **Composite Confluence Max Drawdown**: **`15.5% Avg`** (was `3.72% Avg`).
- **Composite Edge Delta**: **`+19.5% Avg`** (was `+20.2% Avg`).
- **Composite Drawdown Comparison Threshold**: `cMaxDD <= 15.5%`.

---

## 3. Mathematical Consistency & Methodology

1. **Breakeven Trade Exclusion**:
   - In alignment with the Version 5.0 mandate, all breakeven trades are strictly excluded from the win rate denominator ($\\text{Win Rate} = \\frac{\\text{Wins}}{\\text{Wins} + \\text{Losses}} \\times 100$).
   - Dilution is prevented, providing pure directional edge comparison against actual live trading.
2. **Confluence Filter Logic**:
   - Evaluated across rolling 5-bar confluence windows where a Core signal (Missile, Scalp, Lightning) occurs within 5 candles of an active Divergence signal.
3. **Execution Gating**:
   - Divergence signals utilize confirmation bar midpoint touch entries.
   - Core Trend signals utilize signal bar extreme initial stop loss buffers.

---

## 4. Full Parity Deployment Summary

The revised benchmarks were updated and verified across:
1. `Tv-Alert-Mobile/src/app/page.tsx`
2. `RemoteURL/page.tsx`
3. `page.tsx`
4. Institutional system guides: `AGENTS.md` and `.agents/AGENTS.md`.
5. Git repository `RemoteURL` commit `main` and production release tags `v5.0` and `v5.0.0`.
