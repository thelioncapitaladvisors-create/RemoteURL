---
Date: 2026-08-08
Version: 3.6
Author: The Lion Capital Solutions AI
---

# 🚀 TLCS System Update v3.6: Standalone Divergence Alerts & UI Grid Table

## Overview
This update fundamentally integrates the Zigzag Divergence engine natively into the core Live Pivot Alerts script, removing the need for a separate companion indicator. It also introduces a visually distinct, light-themed grid layout for the Strategy Performance tables across both the Web Dashboard and the Mobile App.

## Modifications

### 1. Pine Script (`TLCS_Live_Pivot_Alerts.pine` / TradingView) - v3.5
- **Native Divergence Engine**: The entire `TLCS_Native_Divergence` OOP codebase (Zigzag + Oscillator analysis) has been directly embedded into the main script. The script now calculates `isBullishDiv` and `isBearishDiv` natively without relying on external `input.source` dependencies.
- **Standalone Triggers**: Added `LONG DIVERGENCE` and `SHORT DIVERGENCE` as fully supported trade types. They fire unrestrictedly (no zone filtering) and dispatch the exact same webhook payload structures as Missile/Scalp/Lightning trades.
- **Dependency Reordering Fix**: Resolved compilation error `CE10149` by ensuring the inlined `Drawing` and `Zigzag` libraries appear strictly above the Divergence Screener Code in the file execution order.

### 2. Web Dashboard (`TLCS_Website_Deploy/metrics.html` & `trade-metrics.js`) - v3.6
- **Strategy Performance UI**: Introduced a brand-new Strategy Performance Comparison table built into the AI Research tab (`metrics.html`). The table features a light-themed graph-paper/grid background.
- **Dynamic Metric Rendering**: `trade-metrics.js` was updated to iterate over all closed trades for the day, aggregating Win Rate, Half-Kelly Expectancy, Profit Factor, and Average Profit mathematically, and rendering them dynamically into the grid UI with performance-specific color coding (e.g. Red for negative, Green for positive, Orange for neutral/low).
- **Layout Restructuring**: The global "Performance Statistics" section was moved to the very top of the page, directly beneath the header, with the new Strategy Grid placed prominently above it.

### 3. Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`) - v3.6
- **Strategy Insights Filter**: `LONG DIVERGENCE` and `SHORT DIVERGENCE` were permanently hardcoded into the Strategy Filters list in the INSIGHTS tab, ensuring they are always visible (matching the 6 core strategies).
- **Grid UI Overhaul**: Replaced the previous dark glassmorphic Strategy Performance table with the exact light-themed grid notebook UI design requested. Applied inline Tailwind styling to enforce monospace typography, strict uppercasing, and custom red/green/orange hex colors to exactly mirror the dashboard styling.

## Architectural Rationale
- **Standalone Execution**: By making Divergence a native, self-contained engine, the system eliminates TradingView inter-indicator latency and reduces chart clutter, fulfilling the goal of a single, unified alerts source.
- **UI Consistency**: The light-themed grid table introduces a more analytical, "research-oriented" aesthetic to the performance comparison views, standardizing the presentation of complex metrics across both Web and Mobile platforms.
