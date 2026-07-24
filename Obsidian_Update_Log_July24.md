# TLCS System Update Log — July 24, 2026

## Version 3.2.13: Metric Renaming (TLCS Edge %) & Strict Outcome-Level Alignment

### 1. Renamed Metric Card: `TLCS EDGE %` (Mobile & Web)
- **Problem**: The 4th card on the 2nd row was labeled `TLCS PROFIT FACTOR`, which duplicated the Weekly Profit Factor ratio (`1.82`) when all loaded trades belonged to the current week, and caused confusion when displaying a percentage.
- **Solution**:
  - Renamed the card header to **`TLCS EDGE %`** across Mobile ([`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)) and Web Dashboard ([`dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html)).
  - The card now displays the overall Average Profit % (`avgR`) per trade across all closed trades from all past periods till this moment (e.g. `+0.12%` / `+0.54%`), formatted with explicit sign and `%`.
  - Applied dynamic styling: `text-success glow-success` (green `#27c93f`) for positive average return, and `text-danger glow-danger` (red `#ff5f56`) for negative return.
  - Updated single source of truth rules in [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md).

### 2. Strict Outcome-Level Alignment (Eliminated Loss vs. TP Contradiction)
- **Problem**: Signal `5765ffd0-542e-4b38-be99-e9442f348c9f` (`GC1!`, `SHORT SCALP`, Entry `4,051.95`, Exit `4,052.30`) was a `-0.01%` loss. `resolveOutcome` correctly resolved it as `❌ LOSS -0.01%`, but `getExitLevel` inspected the raw TradingView status string (`"Completed TP4"`), causing the UI to display a green `[TP4]` header badge and `EXIT TP4` right next to a red `❌ LOSS` badge.
- **Solution**:
  - Updated `getExitLevel()` and `getDisplayExitLevel()` in Mobile ([`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)) and Web ([`trade-metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js)).
  - Level resolution now strictly enforces `resolveOutcome(s)`:
    - **Losing Trades (`resolveOutcome === 'LOSS'`)**: Can NEVER display `TP1`, `TP2`, `TP3`, or `TP4` badges or exit labels. Corrupted status strings from TradingView are strictly overridden to `SL` (or `EMA`/`DIV`/`EOD`).
    - **Winning Trades (`resolveOutcome === 'WIN'`)**: Can NEVER display `SL` badges.
  - Updated `outcomePill()` in web scanners ([`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) and [`commodity-scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js)).

### 3. Database Status Repair & Netlify Cron Healing
- Repaired signal `5765ffd0-542e-4b38-be99-e9442f348c9f` and all matching losing trades in Supabase by patching their `status` to `Hit Initial SL`.
- Upgraded Netlify 30-minute background worker ([`cron-heal-outcomes.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-heal-outcomes.js)) to automatically reconcile both `outcome` and `status` columns for corrupt losing trades.

---

### Files Modified & Tested
- [`.agents/AGENTS.md`](file:///Users/vishant/Documents/Project/.agents/AGENTS.md)
- [`Tv-Alert-Mobile/src/app/page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)
- [`TLCS_Website_Deploy/dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html)
- [`TLCS_Website_Deploy/trade-metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js)
- [`TLCS_Website_Deploy/scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js)
- [`TLCS_Website_Deploy/commodity-scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js)
- [`TLCS_Website_Deploy/netlify/functions/cron-heal-outcomes.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-heal-outcomes.js)
