# V3.3 Update Log - August 6, 2026

## UI & UX Refinements
- **Trade Cards Timestamps Alignment:**
  - Resolved an issue where both the top-right header and the `ENTRY` block on trade cards displayed the identical `Real Entry Time`.
  - **Top-Right Header:** Now strictly displays the **SIGNAL TIME** (the exact time the limit order was placed).
  - **ENTRY Block:** Continues to display the **REAL ENTRY TIME** (the exact time the limit order was filled and became an active trade).
  - This change applies globally to both the Web Dashboard (`dashboard.html` / `trade-metrics.js`) and the Mobile Application (`page.tsx`).

- **Analytics Tab Optimization:**
  - Improved the `Day Type Blueprints` and `Trade Sequences` tables.
  - Automatically filters and hides any rows that contain 0 active signals (rows displaying `--` for both Bullish and Bearish).
  - This significantly declutters the Analytics interface on days with lower signal volume.
  - Applied to both Web and Mobile platforms.

## System Architecture Rules (AGENTS.md)
- Updated `AGENTS.md` to explicitly enforce these UI logic rules for future AI tasks to prevent regression.
