# TLCS Terminal Update Log - Version 3.7.0
**Date**: August 8, 2026

## Version Synchronization
- **System-Wide Bump**: Synchronized version numbering across both the Mobile (`Tv-Alert-Mobile`) and Web (`TLCS_Website_Deploy`) repositories to Version 3.7.0.

## Mobile Analytics Improvements (Tv-Alert-Mobile)
- **Market Filters**: Added interactive market type filters (NIFTY 50, MCX, NYMEX, CRYPTO TOP 25, FOREX PAIRS, WORLD INDICES) to the Analytics tab.
- **Dynamic Data Engine**: Upgraded the `weekly_performance_logs` data fetcher to instantly recalculate performance metrics on the client-side when toggling markets.
- **Statistics Summary Bar**: Integrated a distinct 6-column statistics bar (Win Rate, Half-Kelly %, Profit Factor, Avg Profit, Total Trades, Wins/Losses) tracking cumulative data per market.
- **Theme Adaptation**: Refactored the statistics bar and market buttons to natively adapt to the app's dynamic light/dark mode CSS variables (`bg-secondary`, `text-primary`, `text-dim`, `shiny-card`).
- **Hook Optimization**: Extracted the Analytics recompute logic to the top-level of the component to enforce strict React Hook compliance and prevent client-side runtime exceptions.

## Web Dashboard UI (TLCS_Website_Deploy)
- **Layout Restructuring**: Promoted the **Performance Statistics** section in the Intelligence Terminal (`metrics.html`) to the very top of the page, above the primary Strategy Grid table.
- **Distinctive Visuals**: Wrapped the Performance Statistics metrics board and Data Integrity disclaimer in a distinct dark-card container with a sleek background (`rgba(0,0,0,0.2)`) and box-shadow to heavily separate it from the functional grid section below it.
