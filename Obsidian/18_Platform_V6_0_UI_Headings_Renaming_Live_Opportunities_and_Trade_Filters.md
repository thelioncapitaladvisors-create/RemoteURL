# Platform V6.0 UI Headings Renaming: Live Opportunities Dashboard, Signal Performance & Trade Filters

**Date**: October 2, 2026  
**Version**: `v6.0.0`  
**Classification**: UI / Information Architecture Standardization  

---

## 1. Overview of Renaming Mandate

To enhance operational clarity and align terminology directly with active execution workflows across the TLCS Terminal, three key section headings were updated:

| Tab | Previous Title | New Canonical Title | Visual Icon & Subtitle |
| :--- | :--- | :--- | :--- |
| **HUB Tab** | `TLCS ALERTS DASHBOARD` | **`TLCS LIVE OPPORTUNITIES DASHBOARD`** | `<SlidersHorizontal size={22} />`<br>`CURRENT ACTIVE PARAMETER SIGNALS ACROSS ALL MARKETS` |
| **LOGS Tab (Top)** | `TRADE GUIDANCE` | **`TODAY'S TRADE SIGNAL PERFORMANCE`** | `<LayoutGrid size={22} />`<br>Execution metrics, 2-row performance grid, and Data Source toggle |
| **LOGS Tab (Bottom)** | `GLOBAL SIGNAL FEED` | **`TRADE FILTERS`** | `<Bell size={22} />`<br>`RECENT TRADE AUDIT LOGS` |

---

## 2. Updated Components & Files

1. **Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`)**:
   - Line 5915: Renamed `TLCS ALERTS DASHBOARD` to `TLCS LIVE OPPORTUNITIES DASHBOARD`.
   - Line 6821: Renamed `TRADE GUIDANCE` to `TODAY'S TRADE SIGNAL PERFORMANCE`.
   - Line 7041: Renamed `GLOBAL SIGNAL FEED` to `TRADE FILTERS`.
   - Section comments and references updated accordingly.

2. **Web Portal (`TLCS_Website_Deploy/blog.html`)**:
   - Line 366: Renamed `TLCS Alerts Dashboard` to `TLCS Live Opportunities Dashboard`.
   - Line 380: Renamed table placeholder to `Loading TLCS Live Opportunities Dashboard data...`.

3. **Engineering Standard (`.agents/AGENTS.md`)**:
   - Standardized layout integrity rules and command center definitions to reflect the updated headings while preserving strict typography equality:
     - Tag: `h2`
     - Classes: `text-xl sm:text-2xl font-bold italic tracking-tighter uppercase leading-[1.1] text-primary flex items-center gap-2`
     - Icon: `size={22}` accent icon
     - Subtitle: `text-[10px] sm:text-[11px] font-mono font-bold text-dim uppercase tracking-wider block mt-1`

---

## 3. Verification & Parity Audit

- **TypeScript Compilation**: `PATH=... ./node_modules/.bin/tsc --noEmit` passed with 0 errors.
- **Zero Layout Collisions**: Verified heading sizes, badge alignment, and margins maintain complete spacing integrity across both mobile and desktop viewports.
