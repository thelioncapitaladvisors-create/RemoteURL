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
   - Arranged rows in both the *Day Type & Market Regime* scorecard and the *Canonical Signal Family* scorecard in descending order of performance.
   - Deterministic sorting hierarchy: `hasTrades` -> `winCount` (desc) -> `winRate` (desc) -> `netReturn` (desc) -> `pfNum` (desc) -> `expectancy` (desc) -> `totalTrades` (desc).
   - Dynamic crown: The top-performing day type (`🏆 MAX WINS` with `TOP EDGE` badge) automatically heads Row #1 of the Day Type matrix.
   - Zero-trade categories remain neatly grouped at the bottom.

---

## 2. Verification & Commits

- **Tv-Alert-Mobile**: Commits `1694f33` and `74bb3dd` pushed to `origin/main`.
- **Root Repository**: Commits `de3b037` and `9feb0e3` pushed to `origin/main`.
- **TypeScript AST**: Validated with `npx tsc --noEmit` — 0 errors.
