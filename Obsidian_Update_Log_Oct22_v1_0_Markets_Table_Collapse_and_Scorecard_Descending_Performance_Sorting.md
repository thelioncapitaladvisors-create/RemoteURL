# TLCS Architecture Audit Log: Markets Table Trade Collapse & Scorecard Descending Performance Sorting
**Release Tag**: Version 1.0 (Production Release)  
**Date**: October 22, 2026  
**Auditor**: Antigravity Quantitative AI Team  

---

## 1. Scope & Execution Overview

1. **Markets Consolidated Table Trade Outcome Folding**:
   - Integrated an interactive `EXPAND` / `COLLAPSE` toggle defaulting to collapsed (`isTodayTradesExpanded = false`) in `Tv-Alert-Mobile/src/app/page.tsx`.
   - Header action pill and dividing table strip allow instant toggling of individual trade outcome rows under the Intraday Trajectory curve.
   - Prevents table height blowout and allows instant access to lower market sections (e.g., `MCX COMMODITIES`).
   - Bottom collapse button provided for ergonomic folding on long trade lists.

2. **Descending Order of Performance Arrangement**:
   - Arranged rows across all 3 performance scorecards (*Day Type & Market Regime*, *Canonical Signal Family*, and *Market-Wise Execution Breakdown*) in descending order of performance.
   - Deterministic sorting hierarchy: `hasTrades` -> `winCount` / `wr` (desc) -> `netReturn` (desc) -> `pfNum` (desc) -> `expectancy` (desc) -> `totalTrades` (desc).
   - Dynamic crowns & leaders:
     - Day Type: `🎯 IN RANGE / IN VALUE (CONSOLIDATION)` heads row #1 (`🏆 MAX WINS` with `TOP EDGE` badge).
     - Signal Family: `🚀 MISSILE` (28 trades, 4 wins) heads row #1.
     - Market-Wise Execution: `🌍 World Indices` (25.0% WR, positive net return) heads row #1, followed by `💱 Forex Pairs` (2 wins), `₿ Crypto Top 25` (1 win), `⛽ MCX Commodities`, and 0-trade segments.
   - Zero-trade categories remain neatly grouped at the bottom, and pinned sticky columns are 100% preserved.

---

## 2. Verification & Commits

- **Tv-Alert-Mobile**: Commits `1694f33`, `74bb3dd`, and `ae8b6c3` pushed to `origin/main`.
- **Root Repository**: Pushed to `origin/main`.
- **TypeScript AST**: Validated with `npx tsc --noEmit` — 0 errors.
