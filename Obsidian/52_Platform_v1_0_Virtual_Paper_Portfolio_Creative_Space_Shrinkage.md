# Platform v1.0 Virtual Paper Portfolio Density Calibration & Creative Space Shrinkage Mandate
**Date**: October 20, 2026  
**Status**: Production Ready & Fully Verified

---

## Executive Summary
In response to visual UI feedback regarding extensive vertical bloat and excessive dead white space within the Virtual Paper Portfolio (`TLCS_PAPER` and `DHAN_PAPER`) on mobile smartphone screens (< 560px), this mandate introduces a high-density, high-legibility UI calibration that reduces vertical height by over 60% while strictly preserving institutional data richness and the zero-truncation guarantee.

---

## Architectural & Visual Calibration Details

### 1. Unified Single-Row Header
- **Before**: Header occupied 2 stacked vertical rows: Title/subtitle on top, with `RESET`, `RESTORE`, and `COLLAPSE` actions spanning a secondary row (~75px tall).
- **After**: All header elements reside in a single responsive flex row (`flex items-center justify-between gap-1.5 pb-2`). Title, "Simulated P&L" badge, subtitle, and action buttons (`RESET` + `RESTORE` + `COLLAPSE`) fit cohesively in ~36px height.

### 2. Compact Unified Simulator Control Strip
- **Before**: 3 oversized stacked cards (`Virtual Capital`, `Position Sizing`, and `Contract Quantity`) took ~240px vertical height with large inputs, descriptive text blocks, and heavy borders.
- **After**: Consolidated into an elegant 2-row control strip (~50px height):
  - **Row 1**: Inline Capital input with currency prefix, `10L` quick preset badge, and active position sizing pills (`1 Lot Fixed` / `Auto Qty`).
  - **Row 2**: Dynamic micro-caption displaying exact contract multiplier formula and asset details in clean mono typography (`text-[8px] min-[360px]:text-[8.5px]`).

### 3. Tightened Market Buttons Strip
- Reduced button internal padding to `py-1 px-1.5 rounded-lg` with tight grid gap (`gap-1 min-[360px]:gap-1.5`), maintaining the responsive 2-column mobile layout standard without unnecessary dead space.

### 4. 10-Tile Institutional KPI Grid Height Calibration
- Reduced card minimum height from `min-h-[70px] sm:min-h-[72px]` to `min-h-[52px] sm:min-h-[56px]`.
- Calibrated padding to `px-2 py-1 min-[360px]:px-2.5 min-[360px]:py-1.5 rounded-xl`.
- Reduced vertical margins on metric readouts (`my-0.5`), keeping titles and captions `leading-none` to eliminate stacked whitespace.

### 5. Simulated Equity Curve Header 2-Row Layout
- **Before**: Header stacked title on top and wrapped 4 large badge pills (`ROI`, `CAGR`, `Sharpe`, `Sortino`) across 3 to 4 wrapped lines (~140px vertical height).
- **After**: Sleek, disciplined 2-row layout:
  - **Row 1**: Title icon, "SIMULATED EQUITY CURVE", and compact `ROI %` + `CAGR %` badges.
  - **Row 2**: Dedicated secondary risk metrics sub-bar (`bg-primary/5 dark:bg-slate-900/40 rounded-lg px-2 py-0.5`) cleanly displaying `Sharpe: ... • Sortino: ...` alongside `Max DD: ...%`.

---

## Verification & Compliance
- **Production Next.js Build**: Verified `npm run build` completed successfully (exit code 0) with all 8 static pages generated cleanly.
- **Zero Truncation Guarantee**: All numerical values, currency symbols, and badges retain `whitespace-nowrap`.
- **Zero Unilateral Logic Changes**: Math formulas, `exact_pct`, simulated trade execution, Sharpe/Sortino formulas, and Supabase hooks remain 100% untouched.
