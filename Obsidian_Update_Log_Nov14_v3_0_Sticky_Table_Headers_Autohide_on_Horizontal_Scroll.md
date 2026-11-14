# Obsidian Update Log — Nov 14, 2026 · v3.0 · Sticky Table Headers & Row Header Auto-Push on Horizontal Scroll

## Summary
Resolved the table usability issue across all mobile terminal tables (v3.0) where table data columns (Total Trades, Wins, Win Rate, Net Return, Profit Factor, Expectancy, etc.) were blurred, obscured, and hidden behind pinned row headers on mobile screens. 

First-column row headers now push naturally and smoothly out of view to the left during horizontal (left) scroll, allowing users to inspect every data column with 100% clarity, zero blur, and no text obstruction. Top column headers remain firmly pinned (`sticky top-0 z-30`) so that column definitions stay visible during vertical scroll.

---

## Problem Identified & User Feedback
- On mobile viewports (~320px–420px), pinning the first column with `sticky left-0` and `backdrop-blur-md` caused the row header (e.g. "CONFIRMED BULLISH", "BEARISH CONTINUATION", "REJECTED BEARISH", "EQUITIES (NSE)", "CRUDE OIL") to consume 45%–55% of the total screen width.
- When users scrolled horizontally to inspect performance metrics (Wins, Losses, Win Rate, Net Return, Profit Factor, Expectancy, Max Drawdown), data cells slid *directly beneath* the pinned row header cell.
- Due to `bg-background/95 backdrop-blur-md`, the numbers and labels from the data columns showed through as semi-transparent blurred ghost text, making the table contents unreadable.

---

## Root Cause
- First-column `<th>` and `<td>` elements across all major tables were styled with `sticky left-0 z-20` (or `z-10`), `bg-white/95 dark:bg-[#090e17]/95 backdrop-blur-md`, and `shadow-[2px_0_5px_rgba(0,0,0,0.05)]`.
- While vertical column pinning (`sticky top-0`) is essential to keep column headings visible while reading rows, static horizontal pinning of wide row headers on narrow mobile screens forcibly occupies half the viewport and obstructs underlying metric columns.

---

## Solution Implemented: Row Header Auto-Push on Horizontal Scroll

1. **Removed `sticky left-0` and Backdrop Blur from Row Headers**:
   - Stripped all `sticky left-0`, `z-10`, `z-20`, `backdrop-blur-md`, and horizontal drop shadows from the row header `<th>` and `<td>` cells across all 7 affected tables.
   - Row headers now scroll naturally with the table body. When scrolling right to read data columns, the row header smoothly pushes to the left off-screen, giving 100% of the mobile viewport width to data metrics.
   - When the user scrolls back to the beginning, row headers are immediately restored in full view.

2. **Preserved Sticky Column Headers (`sticky top-0 z-30`)**:
   - All column header rows retain `.wc-table-thead` (`position: sticky; top: 0; z-index: 30`) and `sticky top-0 z-30` so that column titles (TOTAL, WINS, LOSSES, WIN RATE, RETURN, etc.) remain anchored at the top of the table container during vertical scrolling.

3. **Updated System Governance Rules**:
   - Updated `AGENTS.md` and `.agents/AGENTS.md` to formally adopt the **Unobstructed Horizontal Scrolling & Row Header Auto-Push Standard**, replacing the legacy first-column sticky parity requirement.

---

## Complete Table Inventory Covered (All 7 Mobile Tables)

| # | Table Name | Tab / View | Header Elements Updated |
|---|---|---|---|
| 1 | **Market Segment Performance** | MARKETS (Top Overview) | First `<th>` and all row `<td>` headers unpinned |
| 2 | **Signal Performance Metrics by Market Segment** | MARKETS (Bottom Breakdown) | Segment row `<th>` and child signal `<td>` headers unpinned |
| 3 | **Performance Breakdown by Canonical Signal Family** | INSIGHTS | Signal family `<th>` and data `<td>` headers unpinned |
| 4 | **VectorBT Confluence Quantitative Benchmark** | INSIGHTS | Setup row `<th>` and `<td>` headers unpinned |
| 5 | **Performance Breakdown by Day Type & Market Regime** | INSIGHTS | Regime category `<th>` and `<td>` headers unpinned |
| 6 | **TLCS Signals 7-Day Matrix** | SCREENER | Filter type `<th>` and signal category `<td>` headers unpinned |
| 7 | **DhanHQ Signals 7-Day Matrix** | SCREENER (BlackBox) | Filter type `<th>` and strategy sequence `<td>` headers unpinned |

---

## Verification & Build Status
- **Next.js Production Build**: Executed in `Tv-Alert-Mobile` (`npm run build`). Passed with zero errors:
  - `✓ Compiled successfully`
  - `✓ Linting and checking validity of types`
  - `✓ Generating static pages (8/8)`
- **Codebase Audit**: Ripgrep search across `Tv-Alert-Mobile` confirms 0 instances of `sticky left-0` remain on table row headers.

---

## Version Classification
- **v3.0** (User-directed production refinement, Nov 14, 2026).
