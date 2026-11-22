# Obsidian Document 116: Platform v5.0 VectorBT Comparative Analysis Breakeven Trades Exclusion & Actual Drawdown Metric Integration

**Status**: Implemented & Verified in Production  
**Date**: November 22, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Next.js Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, `RemoteURL/page.tsx`), Knowledge Base (`Obsidian/`, `AGENTS.md`, `.agents/AGENTS.md`).

---

## 1. Executive Summary & User Mandate

Under Platform Version 5.0, user-directed quantitative methodology and visualization refinements were executed across the **INSIGHTS** tab under `🔥 VectorBT Confluence Quantitative Benchmark vs Live System`:
1. **Breakeven Trades Exclusion from Actual System Performance**:
   - The actual system performance metrics are strictly forbidden from being diluted or distorted by breakeven trades.
   - All breakeven trades (`resolveOutcome(s) === 'BREAKEVEN'`) are excluded ab-initio from:
     - **Actual Profit Factor (`actual pf`)**: Evaluated strictly on gross profit from winning trades divided by gross loss from losing trades.
     - **Actual Win Rate (`actual win rate`)**: Evaluated as Wins / (Wins + Losses) * 100, eliminating dilution from non-directional breakeven trades.
     - **Net Return & Expectancy**: Total return of non-breakeven trades with expectancy evaluated over Wins + Losses.
     - **Total Evaluated Trades**: Defined strictly as Wins + Losses.
     - **Drawdown Curve**: Peak-to-valley drawdown evaluated on the equity trajectory of executed win/loss trades.
   - **BE Transparency**: Breakeven trade counts (`beCount`) remain tracked and presented clearly in subtitles and table rows (e.g., `3W / 1L / 0BE` or `3W / 1L (1 BE)`).
   - **Strict Scope Isolation Mandate**: This exclusion is strictly isolated to the VectorBT comparative analysis on the INSIGHTS tab and is not implemented or considered at any other locations or metrics across the application.

2. **Actual Drawdown Metric Integration in Summary Card**:
   - In Card 2 (`⚡ OUR ACTUAL SYSTEM PERFORMANCE`), the grid layout was upgraded from 3 columns to 4 symmetrical columns:
     1. **Actual PF**: `profitFactorText` with `▲ BEATING BENCHMARK` / `LIVE REALIZED` indicator.
     2. **Actual Win Rate**: Win percentage with W / L / BE breakdown.
     3. **Actual Drawdown**: Peak-to-valley drawdown percentage of evaluated trades alongside benchmark comparison (`▲ BEATING BENCHMARK` / `PEAK-TO-VALLEY`).
     4. **Net Return**: Total net return percentage with per-trade expectancy subtitle.

---

## 2. Core Architectural Implementation

### 2.1 Confluence Benchmark Statistics Engine (`confluenceBenchmarkStats`)
In `Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, and `RemoteURL/page.tsx`:
- Filtered out `resolveOutcome(s) === 'BREAKEVEN'` from evaluated trades.
- Excluded breakeven trades from `actual pf`, `actual win rate`, `net return`, `expectancy`, and `total trades`.
- Evaluated peak-to-valley drawdown solely across executed directional trades.

### 2.2 Card 2 Four-Column Symmetrical UI
- Expanded summary grid from `grid-cols-3` to `grid-cols-4 gap-1.5 sm:gap-2`.
- Included **Actual Drawdown** alongside Actual PF, Actual Win Rate, and Net Return.
- Retained `W / L / 0BE` or `W / L (X BE)` formatting in trade breakdown.

---

## 3. Verification & Parity Audit

- **Mathematical Proof**: Evaluated sample distribution (3W, 1L, 1BE). Verified that Win Rate equals 75.0% (3 / 4), Total Trades equals 4, and Breakeven trades do not dilute the metrics.
- **Byte Parity**: `page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, and `RemoteURL/page.tsx` remain 100% synchronized at 1,470,305 bytes.
- **Production Readiness**: Preserves Platform Version 5.0 integrity with zero regressions.
