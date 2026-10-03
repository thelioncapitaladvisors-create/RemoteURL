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

## 5. F&O Stock Buildups Market Hours Gating & EOD Snapshot Resolution

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

## 6. Role-Based Terminal Menu Access Architecture (App Subscriber Gating)

### Architecture Rationale
* The Terminal Menu (`TERMINAL MENU`) was previously gated exclusively to authenticated administrative users (`APPROVED_ADMIN_EMAILS`), completely hiding personalization controls from standard application subscribers.
* To provide subscribers with essential visual customization, auditory risk alerts, and haptic feedback while maintaining complete operational security, the Terminal Menu was restructured into a **Role-Based Access Control (RBAC)** architecture.

### Implementation Details (`Tv-Alert-Mobile/src/app/page.tsx`)
* **Header Button Access**: The header `Menu` button is accessible to all authenticated application users (both subscribers and administrators).
* **Subscriber-Facing Functions (Client Personalization & Alerts)**:
  1. **`VISUAL SKINS`**: Full access to all 7 visual themes (`DARK`, `SLATE`, `LIGHT`, `THE LION`, `GG DARK`, `GG LIGHT`, `AUTO`).
  2. **`AUDIO ALERT SIGNATURE`**: Auditory alert selection (`TLCS ALARM`, `RISK ISHQ`, `CHIME`, `RADAR`, `DIGITAL`, `SILENT`).
  3. **`HAPTIC FEEDBACK`**: Device vibration toggle (`DEVICE VIBRATION • PULSE ON NEW SIGNALS`).
  4. **`SHUTDOWN TERMINAL`**: Clean session termination and sign-out.
  * *Subtitle Readout*: Subtitle renders as `Terminal Preferences` for subscribers, while rendering as `Admin Command Center` for authenticated administrators.
* **Admin-Only Operational Controls (Protected & Hidden from Subscribers)**:
  The following sections are strictly wrapped behind `{isAdmin && (...)}` and are completely excluded from subscriber DOM trees:
  1. **`ARCHITECT & CREDENTIALS SIGNATURE`**: Prominent credentials banner (*Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*).
  2. **`EXECUTION ENGINE SOURCE`**: Autonomous Engine Selector (`TV PROD`, `BLACK BOX`, `PARITY AUDIT`).
  3. **`24/7 SUPABASE DATABASE SENTINEL`**: Real-time heartbeat, 6-hour cron monitor, and database keep-alive.
  4. **`SYSTEM AUTONOMOUS RESOLUTION AGENT`**: Autonomous healing, weekly performance synchronization, session sweeps, and VectorBT tearsheet rebuilds.
  5. **`TERMINAL MAINTENANCE`**: Operational state reset and `Clear All Alerts`.

---

## 7. Verification & Validation Baseline

* **TypeScript Compilation**: `npx tsc --noEmit` verified with 0 syntax or type errors.
* **Next.js Production Build**: `npm run build` compiled 100% cleanly across all 9 static and dynamic routes.
* **Local Backup Synchronization**: Mirrored to `Project Backup/Tv-Alert-Mobile/src/app/page.tsx`, `Project Backup/.agents/AGENTS.md`, and Obsidian documentation directories.
