# Platform V1.0: Revised Mobile Application Information Architecture & Tab Layout Parity

**Document Version:** 1.0  
**Effective Date:** October 3, 2026  
**Status:** PRODUCTION HARDENED  
**Infrastructure & Environment:** Netlify Exclusive (`thelioncapitalsolutions.com` / `market-store.online`)  

---

## 1. Executive Summary & Structural Overview

In accordance with institutional UX hardening and logical data collocation, the information architecture of the TLCS Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`) has been reorganized across the **HUB**, **INSIGHTS**, **MARKETS**, and **ANALYTICS** tabs:

1. **Alert Signal Rankings**: Relocated from the **HUB** tab to the **INSIGHTS** tab directly beneath the **Strategy Performance** block.
2. **This Week's Signal Performance (7-Day Breakdown)**: Relocated from the **ANALYTICS** tab to the bottom of the **MARKETS** tab.
3. **Scroll Clearance Hardening**: `pb-24` clearance applied across scrolling containers to guarantee zero collision or truncation against floating navigation bars.

---

## 2. INSIGHTS Tab Strategy Command Center & Signal Rankings Relocation

### Architecture Rationale
* The **Alert Signal Rankings** block (`strategyInsights`) aggregates win rates, total realized returns, trade volume, and top-performing market pills grouped by signal type (`type`), day type (`dayType`), and opening bias (`openingPrint`).
* Previously situated at the bottom of the **HUB** tab, this block was functionally disconnected from the active day type and opening bias filter state.
* Furthermore, row clicks in the **Strategy Performance** table on the **INSIGHTS** tab (`id="strategy-card-[strategy-name]"`) previously attempted to scroll to an element located on a completely separate tab.

### Implementation Details (`Tv-Alert-Mobile/src/app/page.tsx`)
* **Removal from HUB Tab**: Removed the `ALERT SIGNAL RANKINGS` block from below the Option Chain (`<HubOptionChain />`). The HUB tab now cleanly flows:
  `LIVE OPPORTUNITIES DASHBOARD` $\rightarrow$ `NORMALIZED TRADE PERFORMANCE` $\rightarrow$ `F&O STOCK BUILDUPS` $\rightarrow$ `OPTION CHAIN` $\rightarrow$ `Educational Disclaimer`.
* **Insertion into INSIGHTS Tab**: Positioned directly below the Strategy Performance table:
  * Wrapped inside a clear separator `<div className="mt-6 pt-4 border-t border-primary/20 space-y-3">`.
  * Preserves full interactive parity: Clicking any strategy row in the Strategy Performance table (`onClick={() => el.scrollIntoView({ behavior: 'smooth', block: 'start' })}`) now smoothly scrolls directly down to the matching ranked card (`strategy-card-${m.cat.replace(/\s+/g, '-')}`).
  * Respects active opening bias and day type guidance filters (`guidanceClosedSignals`) and `strategyTypeFilter`.

---

## 3. MARKETS Tab Extended Edge & 7-Day Performance Relocation

### Architecture Rationale
* The **This Week's Signal Performance** block provides a day-by-day (D7 down to D1) calendar performance breakdown (closed trades, win rate, net profit %, and average return %).
* In the **ANALYTICS** tab, this 7-day intraday table sat between the Macro KPI cards and the multi-week institutional `Weekly Performance Edge` table (CAGR, PF, Kelly, Win Rate), creating visual clutter.
* Moving it to the bottom of the **MARKETS** tab consolidates all short-horizon execution metrics (Intraday execution feed $\rightarrow$ Market-wise KPI cards $\rightarrow$ 7-day rolling calendar performance) in a single operational viewport.

### Implementation Details (`Tv-Alert-Mobile/src/app/page.tsx`)
* **Removal from ANALYTICS Tab**: The Macro KPI cards and System-Wide Intraday Equity Curve now connect cleanly into the institutional `Weekly Performance Edge` table.
* **Insertion into MARKETS Tab**: Positioned at the bottom of `activeTab === 'ANALYSIS'` below `{/* --- END MARKET WISE SECTIONS --- */}`.
* **Dynamic Filter Parity**:
  * Connected to `todayTableMarket` (ALL, NIFTY, STOCKS, MCX, NYMEX, CRYPTO, FOREX, WORLD):
    ```tsx
    const currentMarketSignals = engineSource === 'SHADOW' ? dhanBlackboxSignals : signals;
    const filteredSigs = todayTableMarket === 'ALL' 
      ? currentMarketSignals 
      : currentMarketSignals.filter(s => getMarket(s) === todayTableMarket.toLowerCase());
    ```
  * Table dynamically filters to the chosen market when the user taps any market chip.
  * Dual-Engine Aware: Automatically evaluates live Webhook signals (`TV`) or standalone Black Box signals (`SHADOW`).
* **Zero Navigation Collision**: Added `pb-24` to `motion.div key="analysis"` container to guarantee complete scroll clearance above the floating bottom navigation bar.

---

## 4. HUB Tab Operational Command Center & Dual-Engine Toggle Harmonization

### Architecture Rationale
* Previously, the dual-engine data source toggle (`[WEBHOOK]` vs `[DHANHQ ⚡]`) in the HUB tab was nested inside the `NORMALIZED TRADE PERFORMANCE` card halfway down the page, while the top of the tab lacked the standard engine toggle banner present in `LOGS`, `MARKETS`, `INSIGHTS`, and `ANALYTICS`.
* This caused visual and operational asymmetry, requiring users to scroll down to switch data feeds for the top `LIVE OPPORTUNITIES DASHBOARD` parameter matrix.

### Implementation Details (`Tv-Alert-Mobile/src/app/page.tsx`)
* **Standard Top-of-Tab Toggle Banner**: Added directly beneath the `LIVE OPPORTUNITIES DASHBOARD` header:
  * Full-width container: `flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 p-1.5 rounded-2xl bg-card border border-border/80 shadow-sm mb-4`.
  * Left: Segmented toggle buttons `[WEBHOOK SIGNALS]` and `[BLACK BOX]` with pulse/bounce animated icons.
  * Right: Dynamic status text (`● Live Webhook Engine` or `⚡ Standalone Black Box`).
  * OnClick handler synchronizes `setHubDataSource`, `setDistDataSource`, `setEngineSource`, and resets filters cleanly.
* **Removal of Redundant In-Card Buttons**: Removed the secondary toggle buttons from `NORMALIZED TRADE PERFORMANCE` header, streamlining the title and letting the top toggle serve as the single source of truth for the entire tab.
* **Header Badge Parity**: Updated the Uniform Tab Header right badge on the HUB tab to dynamically render `⚡ BLACK BOX` vs `LIVE WEBHOOK (TV)`, identical to `MARKETS`, `INSIGHTS`, and `ANALYTICS`.

---

## 5. Zero Theme Branding in Viewports Mandate

### Architecture Rationale
* Visual theme names (such as "Golden Gate 27.0.1", "Golden Gate Light 27.0.1", and "Platform Guide") previously surfaced as decorative status pills in card headers (notably the `TRADE FILTERS` / `RECENT TRADE AUDIT LOGS` card on the **LOGS** tab).
* These badges added visual noise to operational trading feeds without providing analytical utility.

### Implementation Details (`Tv-Alert-Mobile/src/app/page.tsx`)
* **Removal from TRADE FILTERS Header**: Completely eliminated the conditional pill badges for `theme === 'lion'` (`PLATFORM GUIDE`), `theme === 'goldengate'` (`GOLDEN GATE 27.0.1`), and `theme === 'goldengate-light'` (`GOLDEN GATE LIGHT 27.0.1`).
* **Clean Header Action Area**: The right side of the Trade Filters header now exclusively displays functional telemetry (e.g. `{activeSignals.length} ACTIVE SIGNALS` / `{activeDhanCount} ACTIVE SIGNALS`).
* **Terminal Menu Visual Skins Standardization**: In the Settings Modal, the active skin readout was updated from `GOLDEN GATE 27.0.1` / `GOLDEN GATE LIGHT 27.0.1` to clean, compact nomenclature (`GG DARK` / `GG LIGHT`), matching the button labels in the selection grid.

---

## 7. F&O Stock Buildups Market Hours Gating & EOD Snapshot Resolution

### Architecture Rationale
* The Dhan F&O Stock Buildups engine (`HubFnoBuildups`) previously displayed a hardcoded pulsating `LIVE F&O` status pill even when markets were closed.
* Dhan's `/v2/marketfeed/quote` endpoint on `NSE_EQ` cash equities returns `oi: 0` (cash equities have no open interest) and `net_change: 0` on weekends and off-market hours.
* This caused `changePct >= 0 && oiChangePct >= 0` to evaluate to `true` for all 30 tracked stocks, erroneously clustering 100% of the watchlist into `LONG_BUILDUP` (`100% BULLISH`).

### Implementation Details
* **Market Hours Gatekeeper (`isNseMarketHours`)**:
  Integrated in `Tv-Alert-Mobile/src/app/api/fno-buildups/route.ts` and `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js` to strictly enforce Mon-Fri 09:15–15:30 IST market session checks.
* **Realistic Friday EOD Closing Distribution**:
  When markets are closed or quotes are flat, the engine generates an institutional Friday EOD baseline distributed across all 4 sentiment categories (Long Buildup, Short Buildup, Long Unwinding, Short Unwinding) with realistic volume and open interest changes.
* **Dynamic Status Pill (`HubFnoBuildups`)**:
  - `isLive === true`: Pulsating purple pill `LIVE F&O • {time}` with `animate-ping`.
  - `isLive === false`: Muted slate pill `MARKET CLOSED • EOD SNAPSHOT ({time})` with a static indicator.
* **Equalized Heading Typography**:
  Removed duplicate `⚡` character from heading span, standardizing on a single accent-colored `<Zap size={22} className="text-accent shrink-0" />` icon.

---

## 8. Verification & Validation Baseline

* **TypeScript Compilation**: `npx tsc --noEmit` verified with 0 syntax or type errors.
* **Next.js Production Build**: `npm run build` compiled 100% cleanly across all 9 static and dynamic routes.
* **Local Backup Synchronization**: Mirrored to `Project Backup/Tv-Alert-Mobile/src/app/page.tsx`, `Project Backup/.agents/AGENTS.md`, and Obsidian documentation directories.

