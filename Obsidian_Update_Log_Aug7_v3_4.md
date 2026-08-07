---
Date: 2026-08-07
Version: 3.4
Author: The Lion Capital Solutions AI
---

# 🚀 TLCS System Update v3.4: Automation, UI Enhancements, and Divergence Exit Logic

## Overview
This update addresses GitHub Actions automation for tearsheet publishing, enhances the UI on both the Mobile Application and Web Dashboard for accurate active trade presentation, and implements a significant logic change in the Pine Script strategy to prevent premature divergence exits.

## Modifications

### 1. GitHub Automation (`.github/workflows/generate-tearsheet.yml`)
- **Tearsheet Deployment Fix**: Refactored the workflow file to use a secondary checkout with `GH_PAT` to successfully push the generated tearsheet directly to the `TLCS_Website` repository on a daily basis.

### 2. Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`)
- **Dynamic Entry Timestamps**: Updated the rendering logic for alert pills on the LOGS and HUB tabs to display only the "Limit Signal Entry Signal" and show `--` for the real entry time when the trade is still an active limit order. 
- **Hold Time & R:R Accuracy**: Ensured holding time considers ONLY the real entry time. Also, updated the initial Risk:Reward logic to dynamically reflect the closure price, maintaining transparency on the HUB tab.

### 3. Web Dashboard (`TLCS_Website_Deploy/metrics.html`)
- **UI Cleanup**: Completely removed the non-functional and dummy "Alerts Risk" meter.
- **Compact Layout**: Reduced the size of the left-side data integrity pill by 50%, applying a more compact styling to improve single-page visibility and layout efficiency.

### 4. Pine Script (`TLCS_Live_Pivot_Alerts.pine` / TradingView)
- **Disabled Immediate Hidden Divergence Exits**: Refactored the Divergence Exit block within `evaluateTradeProgress`. Regular divergences still trigger an immediate exit, but Hidden Divergences now require **Price Action Confirmation** (the next candle must close against the trade direction and below/above the prior close) before triggering an exit. This prevents premature closures on temporary counter-trend blips.
- **Scope Fixes**: Moved individual divergence sources (`ext_bullishDiv`, `ext_bullishHiddenDiv`, etc.) to the global scope under the TRADES inputs group to resolve scope-related "Undeclared identifier" errors.
- **Chart Label Suppression**: Modified the `getDivergenceType()` function to return `DivergenceType.None` for unconfirmed hidden divergences. This ensures that temporary hidden divergence labels are no longer drawn on the chart unless price action genuinely follows through.
