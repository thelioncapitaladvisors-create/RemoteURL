# Obsidian Update Log: September 14, 2026 (v1.1)
## Virtual Paper Portfolio Simulator, Filter Button Reactivity & KPI Heading Harmonization

---

### 1. Executive Summary
This update documents the resolution of filter button reactivity issues within the **Virtual Paper Portfolio Simulator** (SCREENER tab) and the complete visual harmonization of the 6-Metric KPI grid headers. It establishes the architectural principles distinguishing normalized strategy edge (`NET P&L`) from physical lot-sizing cash returns (`REALIZED P&L`).

---

### 2. Issues Addressed & Architectural Fixes

#### A. Simulator Reset Timestamp (`paperResetTs`) Defaulting Bug
* **Problem**: In `Tv-Alert-Mobile/src/app/page.tsx`, `paperResetTs` was previously auto-initialized to `Date.now()` on component mount if no prior reset was recorded in `localStorage`. This caused the trade filter (`sigTs < paperResetTs`) to inadvertently discard all historical and intraday signals generated before opening the tab, giving the appearance that market filter chips (`NIFTY 50`, `NYMEX`, `FOREX`, `WORLD`, etc.) and the `All Signals / Today Only` toggles were frozen or returning 0 trades.
* **Solution**:
  - `paperResetTs` now strictly defaults to `null` on mount and only receives a timestamp when the user explicitly clicks **"START AFRESH"** (`handleResetPaperPortfolio`).
  - Added a dedicated **`RESTORE`** button in the Paper Portfolio header (`handleRestorePaperPortfolio`) that allows users to instantly restore historical signals and clear the active reset timestamp.

#### B. Complete Multi-Asset Market Expansion
* Expanded the Paper Portfolio market grid from 6 to all 8 standard market groups:
  1. `ALL MARKETS` (`ALL`) — Multi-Asset Matrix
  2. `NIFTY 50` (`nifty`) — NIFTY1! 65 Qty / BANKNIFTY 15 Qty
  3. `STOCKS` (`stocks`) — Indian Equities 100 Shares
  4. `MCX COMMODITIES` (`mcx`) — Crude 100 / Gold 100 / NG 1250
  5. `NYMEX & COMEX` (`nymex`) — CL / NG / GC / SI 1 Lot (USD to ₹ @ live FX)
  6. `CRYPTO TOP 25` (`crypto`) — BTC 0.1 / ETH 1 / SOL 10 (USD to ₹ @ live FX)
  7. `FOREX PAIRS` (`forex`) — Major & Minor Pairs 10,00,00 Units (0.1 Mini Lot)
  8. `WORLD INDICES` (`world`) — US30 / NAS100 / SPX500 1 Contract

#### C. KPI Grid Heading Row Harmonization
* Harmonized both 3-tile heading rows in the Virtual Paper Portfolio 6-Metric grid:
  - **Row 1**: `NET WORTH`, `REALIZED P&L`, `WIN RATE`
  - **Row 2**: `EXPECTANCY`, `CALMAR`, `AVG WIN/LOSS`
* Standardized all tile headers to `text-blue-600 dark:text-blue-400 font-mono font-black uppercase` and wrapped all tiles in identical glassmorphic containers (`bg-gradient-to-br from-secondary/50 to-secondary/20 border border-primary/25`).

---

### 3. Dual P&L Engine Mathematical Reference

| Metric | View / Tab | Financial Formulation | Standard Allocation Base |
| :--- | :--- | :--- | :--- |
| **`NET P&L`** | **LOGS** *(Trade Distribution)* | $\sum \frac{\text{exact\_pct}_i}{100} \times ₹1,00,000$ | Normalized ₹1,00,000 notional per trade |
| **`REALIZED P&L`** | **SCREENER** *(Paper Simulator)* | $\sum (\Delta \text{Points}_i \times \text{Lot Size}_i \times \text{FX Rate})$ | Physical Contract Multipliers across ₹10,00,000 account |
