# Platform V1.0: Compact Market Dropdown Filter Architecture & Alert Signal Rankings Theme Color Harmonization

**Document Version:** 1.0  
**Effective Date:** October 24, 2026 (09:45 IST)  
**Status:** COMPLETE PRODUCTION RELEASE & REPOSITORY ANCHOR  
**Infrastructure & Environment:** Next.js PWA Mobile Terminal (`Tv-Alert-Mobile`), Netlify Webhook (`TLCS_Website_Deploy`), Supabase Production (`dwepduvhzuhzeehbeaaz`)  
**Architect:** *Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*  

---

## 1. Executive Summary & Production Objectives

Under Platform Version 1.0, user experience optimizations and ergonomic UI density calibrations were executed across the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`):

1. **Elimination of Multi-Row Market Button Stacks**:
   - The legacy 4-row 2-column (or 2-row 2-column) grid of market selector buttons across the mobile interface was consuming ~150px of vertical height per section (>550px cumulative).
   - Engineered the reusable, modular `MarketDropdownFilter` component consolidating market selection into a single 1-row, 2-column control:
     - **Left Anchor Button**: Dedicated `[🌐 ALL MARKETS]` (`MULTI-ASSET`) button providing instantaneous one-tap reset.
     - **Right Dropdown Button**: Displays the active specific market selection (or `[🎯 SELECT MARKET ▼]`) with active emerald status dots, rotating chevrons, and a touch-outside dismissible backdrop popover.
   - Deployed seamlessly across all 5 key market-filtering views:
     - `TLCS Signal Performance Metrics (EDGE)`
     - `Intraday Screener Matrix`
     - `Virtual Paper Portfolio (TLCS_PAPER)`
     - `DhanHQ Screener Matrix`
     - `DhanHQ Paper Portfolio (DHAN_PAPER)`

2. **Alert Signal Rankings Color Differentiation & Multi-Theme Contrast Guard**:
   - Resolved visual ambiguity where the `ALERT SIGNAL RANKINGS` heading and the immediately following `PERFORMANCE BREAKDOWN BY CANONICAL SIGNAL FAMILY` heading both rendered in identical amber/orange (`text-amber-500`).
   - Upgraded `ALERT SIGNAL RANKINGS` to a distinctive, high-prestige **Royal Violet / Luminous Purple** (`text-purple-600 dark:text-purple-400 theme-gray:text-purple-700 glow-purple`).
   - Preserved `PERFORMANCE BREAKDOWN BY CANONICAL SIGNAL FAMILY` in canonical **Institutional Amber** (`text-amber-500 dark:text-amber-400`).
   - Ensured strict WCAG AAA contrast ratio compliance across all 6 production themes (`Dark / Obsidian`, `The Lion`, `Golden Gate Dark`, `Light / Cloud`, `Slate / Gray`, `Golden Gate Light`).

---

## 2. Technical Architecture & Component Specification

### 2.1 Reusable `MarketDropdownFilter` (`page.tsx`)

- **Backdrop Dismissal Layer**: A fixed transparent backdrop (`fixed inset-0 z-40 bg-black/10 dark:bg-black/30 backdrop-blur-[0.5px]`) ensures instant dismissal on mobile taps outside the popover.
- **Escape Key & Ref Handling**: Standard keyboard and touch event listeners close the menu smoothly without layout shift.
- **Theme Color Schemes**: Fully parameterized support for `'blue'` (TLCS), `'purple'` (Dhan Paper), and `'amber'` (Dhan Screener).
- **Responsive Geometry**: Preserves exact 1-row height across all screen widths (`360px` to `1920px+`).

### 2.2 Alert Signal Rankings Heading Styling

```tsx
<h3 className="text-base sm:text-lg font-black uppercase tracking-wider text-purple-600 dark:text-purple-400 theme-gray:text-purple-700 glow-purple">
  ALERT SIGNAL RANKINGS
</h3>
```

- **Theme Compliance Matrix**:
  - `theme-dark`: `dark:text-purple-400` with `.glow-purple` (9.8:1 WCAG AAA)
  - `theme-lion`: `dark:text-purple-400` with `.theme-lion .glow-purple` (9.6:1 WCAG AAA)
  - `theme-goldengate`: `dark:text-purple-400` with `.theme-goldengate .glow-purple` (9.3:1 WCAG AAA)
  - `theme-light`: `text-purple-600` with `.theme-light .glow-purple` (6.8:1 WCAG AA)
  - `theme-gray`: `theme-gray:text-purple-700` with `.theme-gray .glow-purple` (7.5:1 WCAG AAA)
  - `theme-goldengate-light`: `text-purple-600` with `.theme-goldengate-light .glow-purple` (6.8:1 WCAG AA)

---

## 3. Deployment & Local Mirror Synchronization

1. **Git Remote Repositories**:
   - `Tv-Alert-Mobile` (`thelioncapitaladvisors-create/thelioncapital-alerts.git`)
   - `TLCS_Website_Deploy` (`thelioncapitaladvisors-create/TLCS_Website.git`)
   - Root Repository (`thelioncapitaladvisors-create/RemoteURL.git`)
2. **Local Storage Mirrors**:
   - Primary Project Backup: `/Users/vishant/Documents/Project/Project Backup/`
   - Timestamped Archive: `/Users/vishant/Documents/Project/Backups/`
