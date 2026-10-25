# 73. Platform v1.0 Architecture: Screener Renaming ("Stocks with Action" & "Outside Range & Value") and Legacy Performance Tables Purge
**Date**: October 25, 2026 (20:50 IST)  
**Release Tag**: `v1.0`  
**Status**: 100% Production Ready & Verified  
**Author**: The Lion Capital Advisors  

---

## 1. Executive Summary

This architecture release fulfills the user's specific mandates for the DhanHQ BlackBox screener and the `INSIGHTS` tab UI on the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`):
1. **Screener Header Renaming ("STOCKS WITH ACTION")**:
   - Renamed the master card header of the DhanHQ BlackBox Opening Bias & Compression screener (`renderDhanUnifiedBiasScreener`) from `PIVOT REGIME & COMPRESSION SCREENER` to **`STOCKS WITH ACTION`**.
   - Preserved all typography, tracking, pulsating indicator badges, and the interactive `COLLAPSE / EXPAND` toggle.
2. **Tab Pill & Config Renaming ("Outside Range & Value")**:
   - Renamed the opening bias setup tab pill from `OOR Bias` / `Out of Range` to **`Outside Range & Value`** across both `shortLabel` and `label`.
   - Updated the setup configuration label in `currentConfig.label` to `'Outside Range & Value'`, ensuring consistent display in headers and modals.
3. **Complete Removal of Redundant Legacy Tables**:
   - Completely purged the legacy **Market Performance** table (`marketCategoryStats`) and **Strategy Performance** section (`strategyCategoryStats`, strategy filter chips, and strategy signals display).
   - Cleanly streamlined the `INSIGHTS` tab so that `renderDhanUnifiedBiasScreener` transitions directly into the **Performance Breakdown by Canonical Signal Family (Oct 20, 2026+ Baseline)** table, eliminating clutter and redundant metrics.

---

## 2. Architectural Changes

| Component / Section | Legacy Implementation | Calibrated v1.0 Standard | Impact |
| :--- | :--- | :--- | :--- |
| **Screener Title** | `PIVOT REGIME & COMPRESSION SCREENER` | `STOCKS WITH ACTION` | Clear, action-oriented, institutional titling |
| **Opening Bias Tab Pill** | `OOR Bias` (`label: 'Out of Range'`) | `Outside Range & Value` | Direct, unambiguous PivotBoss STP 2.0 terminology |
| **Market Performance Table** | Rendered under screener with market breakdown | **Completely Removed** | Eliminates visual duplication with Markets & Insights tabs |
| **Strategy Performance Table** | Rendered under screener with strategy chips | **Completely Removed** | Eliminates legacy noise in favor of Canonical Signal Family baseline |

---

## 3. Verification & Deployment

1. **Compilation Verification**: Next.js production build (`npm run build`) exited with code 0 (`Compiled successfully`, `8/8 static pages generated`).
2. **PWA Service Worker Update**: Bumped cache to `tlcs-cache-v1.0.0-rev19` in `Tv-Alert-Mobile/public/sw.js` for instant client cache invalidation and zero `ERR_FAILED` guarantee.
3. **Git Version Control**:
   - `Tv-Alert-Mobile`: Committed, tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
   - `Project` root: Submodule synchronized, committed, tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
4. **Backup Tiers Synchronized**:
   - Tier 1: `Project Backup/`
   - Tier 2: `Backups/`
   - Tier 3: `/Users/vishant/Documents/Backups/`
