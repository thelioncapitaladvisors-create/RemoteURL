# 74. Platform v1.0 Architecture: "Stocks with Action" Collapsible Filter Buttons & Accordion Architecture
**Date**: October 26, 2026 (20:25 IST)  
**Release Tag**: `v1.0`  
**Status**: 100% Production Ready & Verified  
**Author**: The Lion Capital Advisors  

---

## 1. Executive Summary

This architecture release fulfills the user's specific ergonomic and layout optimization mandate for the **Stocks with Action** screener component (`renderDhanUnifiedBiasScreener`) located at the top of the **INSIGHTS** tab in the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`):

### User Request Mandate:
> *"Make these as collapsible buttons like we did earlier for other filter buttons/pills."*

Previously, the "Stocks with Action" component forcefully defaulted `dhanBiasActiveTab` to `'OOR'`, causing the entire metric strip and 3-column screener assets table to remain perpetually expanded on initial page load, consuming substantial vertical viewport height before users could reach the Canonical Signal Family Performance Breakdown below.

Following the identical battle-tested pattern implemented in **F&O Stock Buildups** (`HubFnoBuildups` in Note 68) and **Option Chain** (`HubOptionChain` in Note 71), this release converts the setup pills (`Outside Range & Value`, `Inside CPR`, `Narrow CPR`, `Narrow Value`, `Virgin CPR`) into interactive **two-way collapsible/expandable buttons** with dynamic chevrons and keeps the screener table **strictly collapsed by default** on load.

---

## 2. Interactive Collapsible Pill Architecture

### 2.1 State Management & Null Baseline
- Replaced the persistent non-nullable active tab string with a nullable toggle state:
  ```tsx
  const [dhanBiasActiveTab, setDhanBiasActiveTab] = useState<'OOR' | 'INSIDE' | 'NCPR' | 'NVA' | 'VCPR' | null>(null);
  ```
- **Default State**: `null` (100% collapsed by default on initial page load).
- **Safe Fallback**: `currentConfig.setupType` gracefully defaults to `dhanBiasActiveTab || 'OOR'`, preventing null dereferencing while keeping data ready for instantaneous expansion.

### 2.2 Two-Way Toggle Action & Tactile Feel
- **Two-Way Toggle**:
  ```tsx
  onClick={() => setDhanBiasActiveTab(prev => prev === tab.id ? null : tab.id)}
  ```
  - Tapping any collapsed pill immediately opens the corresponding screener metrics and asset table accordion.
  - Tapping an already active/expanded pill cleanly collapses the table back to the ultra-compact resting state.
- **Tactile Affordance**:
  - `cursor-pointer active:scale-95 transition-all shadow-2xs select-none`.

### 2.3 Visual Affordance & Dynamic Chevron Indicators
- **Collapsed State**:
  - Displays setup icon (`tab.icon`), setup short label (`tab.shortLabel`), live qualifying count badge, and a muted downward chevron (`<ChevronDown size={13} className="opacity-50 shrink-0" />`).
- **Expanded State**:
  - Highlights with royal purple ring & active styling (`bg-purple-600 text-white border-purple-500 shadow-sm ring-2 ring-purple-400/40`), elevated count badge (`bg-white/25 text-white`), and transforms the chevron to an active upward chevron (`<ChevronUp size={13} className="text-current shrink-0 animate-in fade-in" />`).

---

## 3. Expandable Accordion Layout & Controls

When `dhanBiasActiveTab !== null`:
1. **Header Bar with Quick Collapse**:
   - Renders `{cfg.label} Setups ({cfg.stats.total})` with a top-right `[COLLAPSE ⌃]` button.
2. **Metric Summary Strip**:
   - Displays `Screened: X • ▲ Y Bullish • ▼ Z Bearish • Avg Move: +W%`.
3. **3-Column Intuitive Assets Table**:
   - `SYMBOL` (with clean ticker + NSE/MCX market chip) | `BIAS` (`▲ BULLISH` / `▼ BEARISH`) | `MOVE (%)` (high-contrast percentage pill). Tapping any row opens the deep-dive context modal.
4. **Ergonomic Bottom Collapse Button**:
   - When table assets exist, displays a centered `[COLLAPSE TABLE ⌃]` button at the bottom of the table, allowing instantaneous one-tap collapse without scrolling back to the top.
5. **Smooth Animation**:
   - Smooth entry transition (`animate-in fade-in slide-in-from-top-1 duration-200`).

---

## 4. Verification & Deployment Audit

1. **Next.js Production Build**:
   - `npm run build` in `Tv-Alert-Mobile` compiled cleanly with **exit code 0** (`8/8 static pages generated`).
2. **Edge Cache Invalidation**:
   - Service worker cache bumped to **`tlcs-cache-v1.0.0-rev20`** in `Tv-Alert-Mobile/public/sw.js` for instant client cache invalidation and zero `ERR_FAILED` guarantee.
3. **Git Version Control**:
   - `Tv-Alert-Mobile`: Committed, tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
   - `Project` root: Submodule synchronized, committed, tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
4. **3-Tier Local Backups**:
   - Tier 1: `Project Backup/`
   - Tier 2: `Backups/`
   - Tier 3: `/Users/vishant/Documents/Backups/`
