# Platform Version 3.0: Final Production Freeze & Architecture Specification
**Effective Date:** November 15, 2026  
**Document ID:** TLCS-DOC-100-v3.0-FREEZE  
**Classification:** Canonical System Specification & Production Freeze Declaration  
**Status:** 🔒 FROZEN & FINALIZED (Version 3.0 Final)  

---

## 1. Formal Production Freeze Declaration (v3.0)

As of **November 15, 2026 (22:30 IST)**, **TLCS Platform Version 3.0 (`v3.0`)** is officially declared **frozen, finalized, and locked**.

### Strict Zero-Modification Lock:
1. **Zero Unilateral Alterations**: All core logic, Pine Script trading triggers, BlackBox quantitative algorithms, database schemas, API routes, and mobile terminal layout engines under Version 3.0 are strictly immutable.
2. **Version 4.0 Successor Mandate**: All future enhancements, new feature additions, structural refactors, or new asset integrations must be conducted strictly under the **Version 4.0 (`v4.0`)** designation. No new code shall be committed under the v3.0 designation.
3. **Backup Snapshot Integrity**: A complete timestamped production snapshot is permanently preserved in `Backups/TLCS_v3.0_Final_Production_Freeze_20261115_224500/` and `Backups/TLCS_v3.0_Final_Production_Freeze_20261115_222500/`, synced with `Project Backup/`.

---

## 2. Complete Final Version 3.0 Architectural Specifications

### A. Screener Layout: Clean, Non-Cluttered 3-Column Layout Architecture
- **Location**: `renderDhanUnifiedBiasScreener` in `Tv-Alert-Mobile/src/app/page.tsx`
- **Design Philosophy**: Simple, non-complicated, instantly comprehensible at a glance on mobile viewports (320px to 4K). Strictly focused on essential trade attributes.
- **Column Structure (`table-fixed` 100% Responsive Grid)**:
  1. **Column 1 (`Symbol & Time`, w-[36%] sm:w-[34%])**:
     - Line 1: Clean Symbol name (`DOGEUSDT`, `BTCUSDT`, `CRUDEOIL`) in bold tabular text.
     - Line 2: Entry / Exit Times (`19:00 → 19:45` for closed, `19:00 IST` for live/active).
  2. **Column 2 (`Signal & Status`, w-[36%] sm:w-[38%])**:
     - Line 1: Directional Signal Name Badge (`▲ BULL REGULAR` emerald / `▼ BEAR HIDDEN` rose / `▲ BULL REJ` / `▼ BEAR FIRE`).
     - Line 2: Signal Status viz Active Limit, Live or Closed (`⏳ ACTIVE LIMIT` pulsing amber, `⚡ LIVE` pulsing emerald, `🔒 CLOSED` neutral slate) with session date indicator when prior.
  3. **Column 3 (`Outcome / Return`, w-[28%] text-right)**:
     - Line 1: Win/Loss status tag (`WIN` / `LOSS`) alongside outcome-consistent percentage return (`+1.20%` emerald / `-0.35%` rose).
     - Line 2: Exact Point Move (`+804.55 pts` / `-0.00 pts`).
- **Zero Horizontal Scrolling & Zero 48px Overlap Bug**:
  - The table fits naturally without requiring horizontal overflow.
  - Bypasses `.table-scroll-container` and horizontal scroll triggers, permanently preventing the `td:first-child` 48px collapse bug and eliminating text collisions.
- **Deep Inspection Decoupling**: Tapping any row opens the elevated floating detail popover (`setSelectedDhanOorAsset`) displaying full entry/exit timestamps, hold duration, session date, and institutional execution rules.

---

### B. Hi-Pro Alert Designation (Neutral Zone Confluence Framework)
- **Classification**: Signals triggered by the canonical `FIRE` / `FIRE_ALERT` condition (`Anysignal and not (Greenzone or Redzone)`).
- **Naming Standard**: Renamed from legacy "Scalp Alert" to **"Hi-Pro Alert"** / **"Hi-Pro Alerts"** across all 9 screener cards, subfilters, parameter categories, table badges, and detail modal popovers.
- **Rationale**: Clarifies that this setup represents high-probability confluence occurrences of existing signal types operating completely free from conflicting Greenzone and Redzone momentum boundaries, removing confusion with standalone `SCALP` momentum triggers.
- **Backward Compatibility**: Preserved all underlying database column queries (`setup_type === 'FIRE'`, `FIRE_ALERT`) and webhook payload parsers.

---

### C. Responsive Virtual Paper Portfolio Controls
- **Location**: `screenerViewTab === 'TLCS_PAPER'` and `screenerViewTab === 'DHAN_PAPER'` in `Tv-Alert-Mobile/src/app/page.tsx`.
- **Card Header**: Responsive `flex-col sm:flex-row` layout guarantees 100% full visibility for the portfolio title and subtitle without ellipsis truncation on mobile screens (<360px). Action buttons (`RESET`, `RESTORE`, `COLLAPSE`) remain easily thumb-accessible on their own row.
- **Control Strip (Row 1)**: Capital input and preset (`10L`) align cleanly with sizing model badges (`1 Lot Fixed` + `Auto Qty`) with responsive wrapping, preventing stair-step layout gaps.
- **Micro-Conversion Caption (Row 2)**: Removed redundant side-by-side text that collided on mobile, allowing currency conversion details (`USD/INR: 94.20`) to render unobstructed.

---

### D. Universal 7-Market Expansion
- Standardized across all 9 institutional screener sections:
  1. `Outside Range & Value` (`OOR`)
  2. `Inside CPR` (`INSIDE`)
  3. `Breakouts / NCPR` (`NCPR`)
  4. `Narrow Value / NVA` (`NVA`)
  5. `Virgin CPR` (`VCPR`)
  6. `Divergence` (`DIV`)
  7. `Rejections` (`REJ`)
  8. `Continuations` (`CONT`)
  9. `Hi-Pro Alert` (`FIRE`)
- Supported categories via `ScreenerMarketCategory`: `'ALL' | 'NIFTY' | 'STOCKS' | 'MCX' | 'NYMEX' | 'CRYPTO' | 'FOREX' | 'WORLD'`.

---

### E. Canonical Master Indicator Version 3.0 Parity
- **Indicator Engine**: `TLCS PivotBoss Indicator v3.0` (@version=6) with shorttitle `TLCS v3.0`.
- **Exact Checksum Parity**: Byte-for-byte SHA256 checksum `0b512dd1e00576c8261cfe0be33c5727d2706dcd1153be3bf7d20b6fb733bc48` verified across:
  - `TV Indicator/TLCS_Live_Pivot_Alerts.pine`
  - `TV_Indicator_Full_Code.txt`
  - `user_code.pine`
- **Confirmed-Only Divergence Plotting**: Zero unconfirmed Bar 0 phantom labels. Visual on-chart `D` and `H` labels render strictly on the subsequent directional confirmation candle close, guaranteeing 100% sync with webhook alerts.
- **Dual Price & Oscillator Trendline Validation**: Both price and oscillator trendlines must remain unbreached throughout the divergence pivot window.

---

### F. BlackBox Engine Precision & Zero-Phantom Standard
- **Engines**: `algo_engine/pivots.py` and `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js`.
- **Minimum 2-Bar Swing Separation**: Prohibits consecutive-bar phantom comparisons ($i - j \ge 2$).
- **Prior Swing Pivot Qualification**: Anchor candle $j$ must qualify as a genuine structural swing pivot ($low \le low[j-1]$ and $low \le low[j+1]$ for bullish; $high \ge high[j-1]$ and $high \ge high[j+1]$ for bearish).
- **Structural Extreme Invalidation**: Price breach of the divergence bar's extreme before confirmation immediately invalidates the setup.
- **Symmetrical DMI Directional Momentum Gating**: Long divergence setups strictly suppressed when $DI^- > DI^+$; Short divergence setups strictly suppressed when $DI^+ > DI^-$.

---

## 3. Git Repository Commit & Build Sign-Off

- **Mobile Application Submodule (`thelioncapital-alerts`)**:
  - Latest Commit: `c5571dc` (`fix(mobile): eliminate clutter and overlap in screener table and virtual paper portfolio`)
  - Build Status: Next.js 14.2.35 production build passed (`Exit code 0`, 0 lint/TypeScript errors).
- **Root Repository (`RemoteURL`)**:
  - Latest Commit: `5c67870` (`fix(mobile): sync clean 3-column screener and responsive paper portfolio`)
  - Remote Synchronization: 100% up to date with `origin/main`.
