# Obsidian Update Log — Nov 14, 2026 · v3.0 · Sticky Table Headers (Auto-Hide on Horizontal Scroll)

## Summary
Applied a universal sticky-header enhancement across **all table views** in the TLCS Mobile Terminal (v3.0) to resolve the horizontal-scroll usability issue where column headers were not visible when scrolling right to view additional data columns.

---

## Problem Identified
When a table is wider than the mobile viewport (e.g. the **Day Type / Regime** performance breakdown table in the **INSIGHTS** tab), horizontal scrolling caused the header row to scroll out of view. Users could not identify which column they were reading data from (e.g. RETURN, EXPECTANCY, AVG WIN/LOSS) because the header had disappeared vertically or the layout made header tracking impossible.

---

## Root Cause
- All `wc-table-thead` class instances lacked `position: sticky; top: 0; z-index: 30` in `globals.css`.
- Four plain `<thead>` elements in `page.tsx` lacked `sticky top-0 z-30` Tailwind classes.
- First-column pinning (`sticky left-0 z-20`) was already implemented correctly — only vertical header stickiness was missing.

---

## Changes Made

### `Tv-Alert-Mobile/src/app/globals.css`
- Added `position: sticky; top: 0; z-index: 30;` to the `.wc-table-thead` global CSS class.
- **Impact:** All 7 `wc-table-thead` table instances in `page.tsx` automatically inherit sticky header behavior:
  - INSIGHTS → Performance Breakdown by Canonical Signal Family (Amber)
  - INSIGHTS → VectorBT Confluence Quantitative Benchmark (Amber)
  - INSIGHTS → Performance Breakdown by Day Type & Market Regime (Cyan)
  - MARKETS → Signal Performance Metrics by Market Segment (Sky)
  - ANALYTICS → Weekly EDGE Performance Table (Amber)
  - HUB → Live Signals Header (Rose)

### `Tv-Alert-Mobile/src/app/page.tsx`
Added `className="sticky top-0 z-30"` to 5 plain `<thead>` elements:

| Line (approx) | Table | Tab |
|---|---|---|
| ~2094 | Market Segment Performance (purple) | MARKETS |
| ~2560 | Option Chain Strikes Matrix (CE/PE) | HUB / Option Chain |
| ~11079 | Opening Bias Screener (Symbol/Bias/Move%) | SCREENER |
| ~16473 | TLCS Signals 7-Day Matrix | SCREENER |
| ~17193 | DhanHQ Signals 7-Day Matrix | SCREENER |

---

## Behaviour After Fix
- Table header rows **auto-stick to the top** of their scrollable container when the user scrolls vertically within any table.
- Column labels remain visible at all times while scrolling horizontally to view right-side fields (RETURN, EXPECTANCY, AVG WIN/LOSS, etc.).
- First column (`sticky left-0 z-20`) continues to anchor the row label (Day Type / Regime, Signal Family, etc.) during horizontal scroll.
- Z-index hierarchy: `thead` row = `z-30` > first column header cell = `z-20` > regular sticky first-column cells = `z-10` — prevents overlap artifacts.
- All 6 application themes (Obsidian, Gray, Cloud, Lion, Golden Gate, Golden Gate Light) inherit the fix via the shared `.wc-table-thead` CSS rule.

---

## Files Modified
- `Tv-Alert-Mobile/src/app/globals.css` — `.wc-table-thead` sticky positioning
- `Tv-Alert-Mobile/src/app/page.tsx` — 5 plain `<thead>` elements updated

---

## Version Classification
- **v3.0** (user-directed explicit change, Nov 14, 2026)
