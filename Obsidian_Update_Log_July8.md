# TLCS Platform Updates - July 8, 2026

## 1. Mathematical Accuracy Update: Half-Kelly Formula
*   **Denominator Fix**: Deprecated the logic of using total signals (including break-evens) as the denominator for the Kelly calculation. The win rate (`wrFraction`) and loss rate (`lrFraction`) are now strictly calculated over `Wins + Losses` to prevent break-even trades from artificially suppressing the sizing metric.
*   **Half-Kelly Dampening**: Applied a strict 0.5 dampening factor (Half-Kelly) across the entirety of both platforms to encourage more conservative and practical risk management. 
*   **Codebase Synchronization**: The mathematical changes were deployed identically across all backend crons and frontend dashboards:
    *   `backfill-weekly-logs.js`
    *   `cron-weekly-logs.js`
    *   `scanner.js`
    *   `commodity-scanner.js`
    *   `trade-metrics.js`
    *   `page.tsx` (Mobile App)

## 2. UI Consistency & Transparency
*   **Label Renaming**: Renamed all instances of "Kelly %" to "**Half-Kelly %**" across both the web and mobile applications (AI Dashboard, Mobile Hub, Insights, Log lists, and Scanner tables) to ensure complete transparency for the user regarding the risk calculation being used.

## 3. Web UI Fix: Closed Trade Badges
*   **Day Type Pill Removal**: Modified the rendering logic in `metrics.html` for closed trades. Speculative "Day Type" (e.g., `BIG MOVE`) and "CPR Type" badges are now exclusively shown when a trade is `OPEN`. 
*   **Trailing SL Integration**: For closed trades, the UI now cleanly displays only the final exact close level/trailing SL outcome (e.g., `TP3 HIT`, `B/E`, `EMA SL Hit`) in the badge grid, decluttering the interface and prioritizing realized action.

## 4. Mobile App Fix: State Decoupling (LOGS vs INSIGHTS)
*   **Filter Decoupling**: Resolved a state bleed issue in the mobile application where filtering the `LOGS` tab (e.g. selecting `TP3` or `CRYPTO`) was unintentionally filtering the aggregated data on the `INSIGHTS` tab.
*   **State Isolation**: Removed the `insightsFilter` and `outcomeLevelFilter` dependencies from the `useMemo` hooks calculating `marketCategoryStats` and `strategyInsights`. The INSIGHTS tab now always shows the global data landscape, independent of how the user chooses to sift through individual logs on the neighboring tab.
