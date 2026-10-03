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

## 4. Verification & Validation Baseline

* **TypeScript Compilation**: `npx tsc --noEmit` verified with 0 syntax or type errors.
* **Next.js Production Build**: `npm run build` compiled 100% cleanly across all 9 static and dynamic routes.
* **Local Backup Synchronization**: Mirrored to `Project Backup/Tv-Alert-Mobile/src/app/page.tsx`, `Project Backup/.agents/AGENTS.md`, and Obsidian documentation directories.
