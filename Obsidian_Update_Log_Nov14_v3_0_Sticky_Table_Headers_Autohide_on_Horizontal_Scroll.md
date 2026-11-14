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

---

## Zero Overlapping Text & Responsive Font Sizing Alignment Standard

### Problem Addressed
Under mobile viewports and dynamic accessibility font scaling, 3 text overlap collisions occurred in the simulated paper portfolio cards:
1. **Equity Curve Baseline vs Peak Marker**: `BASELINE ₹10L` (anchored at `end` on `x=486`) collided directly with `▲ PEAK` when the peak occurred near the latest trade on the right edge.
2. **Chart X-Axis Labels vs Trade Feed Header**: Placing the X-axis label `<div>` inside a fixed-height container (`h-36`) caused it to overflow down directly on top of `Recent Simulated Paper Signals (1):` and `1 LOT POSITION SIZING`.
3. **Simulated Paper Trade Rows**: Six badges and metrics (`[BREAKEVEN]`, `NIFTY1!`, `[🔥 MISSILE + DIV]`, `[65 Qty]`, `Δ 0.00 pts`, `+₹0`) crammed into a single row on mobile screens caused `65 Qty` and `Δ 0.00 pts` to collide directly over each other (`Δ 650.00 pQty`).

### Solution Implemented
1. **Dynamic SVG Baseline & Peak Separation**:
   - `BASELINE` label dynamically checks `paperStats.peakPoint.x`. When peak is on the right (`x >= 180`), baseline anchors at `x=18` (`textAnchor="start"`) on the left; when peak is on the left (`x < 180`), baseline anchors at `x=482` (`textAnchor="end"`) on the right.
   - Constrained `▲ PEAK` and `▼ TROUGH` x-coordinates with `Math.max(35, Math.min(465, ...))` so labels never clip borders or overlap the baseline.
2. **Decoupled X-Axis Labels from Fixed Canvas Height**:
   - SVG canvas div given dedicated height (`h-32 sm:h-40`), and the X-axis labels placed in normal layout flow below it with `text-[8.5px] sm:text-[9.5px]` and proper vertical spacing (`pt-1 pb-1.5`).
   - Feed header styled with `text-[10px] sm:text-xs`, flex-wrap, and a compact `1 Lot Position Sizing` pill badge.
3. **Two-Tier Mobile / Single-Tier Desktop Trade Item Alignment**:
   - Mobile (< 640px): Tier 1 displays badges and symbol (`[BREAKEVEN]`, `NIFTY1!`, `[🔥 MISSILE + DIV]`, `[65 Qty]`) with tuned micro-font scaling (`text-[9px]`, `text-[8.5px]`, `text-xs`) and flex-wrap. Tier 2 displays `Δ 0.00 pts` on the left and `+₹0` on the right with full horizontal breathing room.
   - Desktop (>= 640px): Seamlessly aligns as a single flex row.
   - Applied symmetrically to both `TLCS_PAPER` and `DHAN_PAPER`.

---

## Universal Fixed Sticky Row Headers with Hover & Blurred Background Standard (User Specification)

### Problem Addressed & Refinement
Upon inspecting the row header blur effect in production, the user recognized that scrolling row headers off to the left is unnecessary when paired with the hover and blur treatment:
> *"For this effect no need to scroll the row headers to the left. Instead keep them fixed with this hover and blurred background effects. It will be very professional look. Make changes throught application version v3.0"*

### Architecture & Solution Implemented
1. **Fixed Sticky Positioning (`position: sticky; left: 0`)**:
   - Row headers remain permanently pinned at `left: 0` during horizontal scroll across all tables (preserving Option Chain's 2-sided symmetrical strike layout via `.option-chain-scroll`).
   - Users never lose row context while scrolling deeply through metric columns.
2. **Frosted Glassmorphism Backdrop Blur & Soft Blur Hierarchy**:
   - When horizontally scrolled (`.table-is-scrolled`):
     - `backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);` applies to the sticky cell with theme-tuned translucent backgrounds across all 6 skins (Dark, Light, Slate Gray, The Lion, Golden Gate, Golden Gate Light).
     - Row names softly blur (`filter: blur(2.5px); opacity: 0.45; user-select: none;`), giving a high-tech frosted aesthetic where metric numbers to the right are 100% visible and unblurred.
     - Subtle elevation edge shadow (`box-shadow: 4px 0 12px -2px rgba(...)`) crisply delineates the fixed column boundary.
3. **Instant Hover & Touch Focus Reveal**:
   - Touching or hovering over any row header cell (or its parent row):
     `filter: blur(0px); opacity: 0.98; background-color: var(--theme-hover-bg); z-index: 25;`
     Immediately brings the row title and its status badges into 100% sharp, readable focus.
4. **Sharp Data Columns Underneath**:
   - Data columns (`th:not(:first-child)`, `td:not(:first-child)`) slide smoothly behind the frosted row header and remain 100% sharp, crisp, and unblurred (`filter: none !important; opacity: 1 !important;`).
5. **Top-Left Corner Pinned**:
   - `thead tr th:first-child` stays pinned in both dimensions (`sticky top-0 left-0 z-35`), ensuring seamless vertical and horizontal scrolling coexistence.

---

## Version Classification
- **v3.0** (User-directed production refinement, Nov 14, 2026).


