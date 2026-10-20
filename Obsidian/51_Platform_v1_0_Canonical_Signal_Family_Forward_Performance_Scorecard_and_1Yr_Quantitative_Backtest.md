# 51: Platform v1.0 Canonical Signal Family Forward-Performance Scorecard & 1-Year Quantitative Backtest

**Date**: October 20, 2026 (16:45 IST)  
**Version**: `v1.0` / `v1.0.0` Production  
**Scope**: Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`), Algorithmic Signal Engine (`algo_engine/backtest_all_signals_1yr.py`), Quantitative Research (`tlcs_1yr_backtest_all_signals_results.json`), System Documentation (`AGENTS.md`, `.agents/AGENTS.md`)

---

## 1. Executive Summary

This release implements two institutional quantitative milestones for The Lion Capital Solutions platform:
1. **Live Forward-Performance Scorecard on Mobile INSIGHTS Tab**: A dedicated real-time performance breakdown table tracking all 6 canonical signal families (`DIVERGENCE`, `SCALP`, `MISSILE`, `EXTREME REVERSAL`, `HIDDEN DIVERGENCE`, `LIGHTNING`) strictly starting from **October 20, 2026 00:00:00 IST** onwards into the future.
2. **1-Year Multi-Asset Quantitative Backtest Across All 6 Signal Types & 12 Directional Triggers**: Rigorous 1-year backtest (October 20, 2025 to October 20, 2026) across 8,866 closed trades spanning 17 institutional instruments across Indian Equities, MCX/NYMEX Commodities, Global Indices, Forex, and Crypto.

---

## 2. INSIGHTS Tab Forward Scorecard Implementation

### Real-Time Live Forward Tracking Standard
* **Baseline Anchor**: Fixed strictly to `1792434600000` ms (`2026-10-20T00:00:00+05:30` IST). Any trade completed prior to October 20, 2026 is filtered out, ensuring zero legacy distortion.
* **Continuous Real-Time Accumulation**: As trades complete today and in all future market sessions, they automatically accumulate into this scorecard.
* **Deterministic Family Mapping**:
  * `🎯 DIVERGENCE`: Combines `LONG DIVERGENCE` & `SHORT DIVERGENCE`.
  * `⚡ SCALP`: Combines `LONG SCALP` & `SHORT SCALP`.
  * `🚀 MISSILE`: Combines `LONG MISSILE` & `SHORT MISSILE`.
  * `🔄 EXTREME REVERSAL`: Combines `LONG EXTREME REVERSAL` & `SHORT EXTREME REVERSAL`.
  * `🔍 HIDDEN DIVERGENCE`: Combines `LONG HIDDEN DIVERGENCE` & `SHORT HIDDEN DIVERGENCE`.
  * `🌩️ LIGHTNING`: Combines `LONG LIGHTNING` & `SHORT LIGHTNING`.
* **8 Core Metrics**:
  * `Total Trades`
  * `Wins / Losses / BE`
  * `Win Rate` ($\frac{\text{Wins}}{\text{Total Closed Trades}} \times 100$ — breakevens strictly included in denominator)
  * `Profit Factor` ($\frac{\text{Gross Profit}}{\text{Gross Loss}}$, displays `MAX` if gross loss is zero)
  * `Net Return` ($\sum \text{exact\_pct}$)
  * `Expectancy` ($\frac{\text{Net Return}}{\text{Total Trades}}$)
  * `Avg Win / Loss` (`+Avg Win% / -Avg Loss%`)
  * `Composite Total Footer`: Bottom aggregate row summing performance across all active families.
* **Mobile Responsive Styling**:
  * Contained within an `overflow-x-auto hide-scrollbar custom-horizontal-scrollbar rounded-2xl wc-table-card border border-black/10 dark:border-white/10 shadow-sm`.
  * Min-width of `620px` guarantees zero text clipping or ellipses across all smartphone viewports (< 560px).

---

## 3. 1-Year Multi-Asset Quantitative Backtest Summary

### Global Portfolio Performance (8,866 Trades)
* **Evaluation Period**: October 20, 2025 to October 20, 2026 (1 Full Year).
* **Timeframe**: 1-Hour continuous historical bars with prior-day completed Daily Camarilla (H1–H5, L1–L5) and Daily CPR (Pivot, TC, BC, NCPR).
* **Execution Standard**: Strict H4/L4 touch-point gating (`low < H4` for Longs, `high > L4` for Shorts), limit order fill verification (`low <= entry <= high`), dynamic TP1->Breakeven and trailing stop progression.
* **Core Macro Stats**:
  * **Total Trades**: 8,866 (2,214 Wins / 5,343 Losses / 1,309 Breakevens)
  * **Canonical Win Rate**: **24.97%**
  * **Profit Factor**: **1.16**
  * **Net Cumulative Return**: **+511.64%**
  * **Expectancy (Mean Trade)**: **+0.058% / trade**
  * **Realized Risk-to-Reward**: **2.80:1 R:R** (Average Win: $+1.68\%$, Average Loss: $-0.60\%$)
  * **Max Drawdown**: **-18.53%**
  * **Annualized Sharpe / Sortino**: **0.70 / 1.92**

### Signal Family Breakdown
| Signal Family | Total Trades | Win Rate | Profit Factor | Net Return | Realized R:R | Max Drawdown | Sharpe | Sortino |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🎯 **DIVERGENCE** | 2,379 | 26.1% | **1.31** | **+252.73%** | **2.97 R** | **-10.62%** | **1.22** | **3.80** |
| ⚡ **SCALP** | 3,248 | 24.5% | **1.15** | **+173.76%** | **2.86 R** | -24.62% | **0.67** | **1.78** |
| 🚀 **MISSILE** | 2,869 | 24.9% | **1.11** | **+115.52%** | **2.66 R** | -24.35% | **0.48** | **1.30** |
| 🔄 **EXTREME REVERSAL** | 29 | **31.0%** | **1.49** | **+5.04%** | **2.82 R** | **-4.88%** | **2.32** | **7.50** |
| 🔍 **HIDDEN DIVERGENCE** | 13 | 38.5% | 0.96 | -0.14% | 1.34 R | -2.81% | -0.30 | -0.52 |
| 🌩️ **LIGHTNING** | 328 | 20.4% | 0.74 | -35.27% | 2.30 R | -38.25% | -1.60 | -3.03 |

---

## 4. Verification & Build Integrity

* **Next.js Production Build**: Compiled cleanly with zero errors (`next build`).
* **All Signal Execution Log**: Saved at `algo_engine/tlcs_1yr_backtest_all_signals_results.json`.
* **Reproducible Test Script**: Saved at `algo_engine/backtest_all_signals_1yr.py`.
