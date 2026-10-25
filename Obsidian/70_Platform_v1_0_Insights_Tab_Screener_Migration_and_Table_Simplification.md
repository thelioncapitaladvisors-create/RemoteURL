# 70. Platform v1.0 Architecture: Insights Tab Pivot Regime & Compression Screener Migration & Table Simplification
**Date**: October 25, 2026 (19:15 IST)  
**Release Tag**: `v1.0`  
**Status**: 100% Production Ready & Verified  
**Author**: The Lion Capital Advisors  

---

## 1. Executive Summary

This architecture release fulfills the user's specific workflow and ergonomics mandate for the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`):
1. **Migration to Insights Tab**: Moved the **DhanHQ Unified Pivot Regime & Compression Screener** from the Screener tab to the very top of the **INSIGHTS** tab (`activeTab === 'INSIGHTS'`), directly beneath the Webhook/BlackBox engine toggle.
2. **De-cluttering & Removal of Complex Sections**:
   - Removed the legacy **Today's Guidance** filter card and **Matching Criteria Symbols** section from the top of the Insights tab.
   - Removed the **Alert Signal Rankings** section from the Insights tab.
   - Kept the **Market Performance** consolidated breakdown table intact.
   - Kept the **Strategy Performance** table intact.
   - Removed duplicate screener calls in the Screener views (`DHAN_SCREENER` and `DHAN_PAPER`).
3. **Screener Simplification Mandate**:
   - Strictly displays **today's session** (past session values strictly omitted).
   - Only displays true/valid values (filtering out unpopulated setups with `count === 0` from sub-tabs, and table rows filter for clean symbol, valid numeric day move percentage, and active prices).
   - Removed all unnecessary filter buttons, accordion drawer, market filters, directional buttons, session toggles, and reset controls.
   - Replaced bulky 4-card KPI grid with a sleek 1-row metric summary strip: `Screened: X • ▲ Y Bullish • ▼ Z Bearish • Avg Move: +W%`.
   - Streamlined table to strictly **3 columns**: **`SYMBOL` | `BIAS` | `MOVE (%)`**, eliminating redundant setup regime, points, session date, action buttons, and pivot detail columns. Tapping any row opens the detailed inspection modal.

---

## 2. Architectural Modifications

### 2.1 Insights Tab Section Arrangement (`activeTab === 'INSIGHTS'`)
- **Row 1 (Top)**: Webhook Signals vs Standalone DhanHQ Black Box Engine Selector.
- **Row 2 (Top Anchor)**: `{renderDhanUnifiedBiasScreener()}`:
  - Collapsible/expandable master card header with active pulse indicator and collapse toggle.
  - Subtab pills filtered to setups with `count > 0` (`validSubTabs = subTabs.filter(t => t.count > 0)`).
  - High-contrast selected and inactive button styling.
  - Sleek 1-row metric strip.
  - Ultra-clean 3-column table (`SYMBOL` | `BIAS` | `MOVE (%)`).
- **Row 3**: Market Performance Consolidated Table (retained with 100% fidelity).
- **Row 4**: Strategy Performance Table (retained with 100% fidelity).
- **Row 5**: Performance Breakdown by Canonical Signal Family (retained with 100% fidelity).

### 2.2 Table Column Consolidation
| Previous Column (Deprecated) | Simplified Standard (v1.0) | Rationale |
| :--- | :--- | :--- |
| `Symbol` | **`Symbol`** | Retained with clean ticker + NSE/MCX badge |
| `Setup / Regime` | *Removed* | Setup is already isolated by the active sub-tab |
| `Bias` | **`Bias`** | Retained as `▲ BULLISH` / `▼ BEARISH` badge |
| `Day's Move (%)` | **`Move (%)`** | Retained as high-contrast `+X.XX%` / `-X.XX%` |
| `Points` | *Removed* | Omitted to prevent mobile clutter; viewable in modal |
| `Pivot Detail` | *Removed* | Deprecated as requested; available in inspect modal |
| `Session Date` | *Removed* | Deprecated; screener is strictly locked to today |
| `Action (Inspect)` | *Removed* | Redundant button; tapping the entire row opens modal |

---

## 3. Verification & Deployment

1. **Compilation Verification**: Next.js production build (`npm run build`) succeeded with code 0 (`Compiled successfully`, `8/8 static pages generated`).
2. **PWA Service Worker Update**: Bumped cache to `tlcs-cache-v1.0.0-rev14` in `Tv-Alert-Mobile/public/sw.js` for instant client updates.
3. **Git Version Control**:
   - `Tv-Alert-Mobile`: Committed (`95eed1c`), tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
   - `Project` root: Committed (`7860a1b`), tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
4. **Theme Contrast Compliance**: Verified across all 6 themes (`dark`, `gray`, `light`, `lion`, `goldengate`, `goldengate-light`).
