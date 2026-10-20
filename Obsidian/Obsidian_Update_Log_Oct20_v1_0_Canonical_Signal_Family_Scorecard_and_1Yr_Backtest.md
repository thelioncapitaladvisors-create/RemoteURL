# Obsidian Update Log — October 20, 2026 (v1.0 Production)

**Scope**: Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`), Algorithmic Signal Engine (`algo_engine/backtest_all_signals_1yr.py`), Quantitative Research (`tlcs_1yr_backtest_all_signals_results.json`), System Documentation (`AGENTS.md`, `.agents/AGENTS.md`)

---

### 1. Canonical Signal Family Forward Scorecard (INSIGHTS Tab)
- Added the **Performance Breakdown by Canonical Signal Family** table at the bottom of the **INSIGHTS** tab on the mobile application (`Tv-Alert-Mobile/src/app/page.tsx`).
- **Baseline Date**: Strictly filters all closed signals starting from today (**October 20, 2026 00:00:00 IST**, `1792434600000` ms) onwards into the future.
- **6 Canonical Families**: 
  - `🎯 DIVERGENCE` (Long & Short Divergence)
  - `⚡ SCALP` (Long & Short Scalp)
  - `🚀 MISSILE` (Long & Short Missile)
  - `🔄 EXTREME REVERSAL` (Long & Short Extreme Reversal)
  - `🔍 HIDDEN DIVERGENCE` (Long & Short Hidden Divergence)
  - `🌩️ LIGHTNING` (Long & Short Lightning)
- **Metrics Tracked**: Total Trades, Wins / Losses / BE, Win Rate (canonical formula: `wins / totalClosed * 100`), Profit Factor, Net Return, Expectancy, and Avg Win / Loss.
- **Composite Total Footer**: Summary row aggregating all closed trades from October 20, 2026 onwards.

---

### 2. 1-Year Multi-Asset Quantitative Backtest Across All 6 Signal Types
- Created and executed [algo_engine/backtest_all_signals_1yr.py](file:///Users/vishant/Documents/Project/algo_engine/backtest_all_signals_1yr.py) across 17 multi-asset instruments for a full 1-year historical period (Oct 20, 2025 to Oct 20, 2026).
- **Core Results (8,866 Trades)**:
  - **Net Cumulative Return**: **+511.64%**
  - **Canonical Win Rate**: **24.97%** (2,214 W / 5,343 L / 1,309 BE)
  - **Profit Factor**: **1.16**
  - **Expectancy**: **+0.058% / trade**
  - **Realized R:R**: **2.80:1** (Avg Win: +1.68%, Avg Loss: -0.60%)
  - **Max Drawdown**: **-18.53%**
  - **Sharpe / Sortino**: **0.70 / 1.92**
- **Top Performing Family**: `DIVERGENCE` (+252.73% Net, 1.31 PF, 2.97 R:R, 1.22 Sharpe, 3.80 Sortino).
- **Highest Trade Expectancy**: `EXTREME REVERSAL` (+0.174% / trade, 1.49 PF, 2.32 Sharpe, 7.50 Sortino) with zero phantom gap signals.

---

### 3. Verification & Build
- Next.js production build (`next build`) in `Tv-Alert-Mobile` compiled successfully with 0 errors.
- Saved full dataset to [algo_engine/tlcs_1yr_backtest_all_signals_results.json](file:///Users/vishant/Documents/Project/algo_engine/tlcs_1yr_backtest_all_signals_results.json).
