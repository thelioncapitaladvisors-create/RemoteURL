# Obsidian Document 112: Platform v4.0 HUB Tab Bifurcated Live Signals & Dedicated Watchlist Architecture

**Status**: Implemented & Verified in Production  
**Date**: November 19, 2026  
**Platform Version**: v4.0 (`tv-alert-mobile@4.0.0`)  
**Scope**: HUB Opportunities Matrix (`activeTab === 'DASHBOARD'`), `Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, `RemoteURL/page.tsx`

---

## 1. Executive Summary & Architectural Motivation

In prior iterations of the **HUB Live Opportunities Dashboard** (`activeTab === 'DASHBOARD'`), all institutional parameter signals were rendered inside a single consolidated table under a red `🚨 LIVE SIGNALS` banner. While functional, this layout blended genuine real-time execution signals (`MISSILE`, `SCALP`, `LIGHTNING`, `EXTREME REVERSAL`, `DIVERGENCE`, `CONFLUENCE`) with day-type market structure watchlists (`REJECTED BULLISH`, `REJECTED BEARISH`, `REJECTION BLUEPRINT`, `BULLISH CONTINUATION`, `BEARISH CONTINUATION`, `INSIDE DAY CPR`, `NCPR`, `VCPR`, `ABSORPTION`, `FAILED NEW LOW/HIGH`, `OUTSIDE DAY`, `STOP RUN`, `ACCUMULATION`).

Consequently, qualifying day-type market regimes were rendered with badges such as `🛡️ LIVE REJECTION SIGNAL` and `🚀 LIVE CONTINUATION SIGNAL` inside the `🚨 LIVE SIGNALS` container, creating potential operator ambiguity between an executed trade and a qualifying day-type watchlist candidate.

To achieve clean visual hierarchy, institutional distinction, and effortless scanning, the HUB Opportunities Matrix has been bifurcated into two dedicated, cleanly tiered sections with dedicated filter tab buttons and master view switcher controls.

---

## 2. Core Architectural Changes

### 2.1 Master View Switcher Bar
Positioned directly above the matrices, a high-contrast 3-way toggle provides seamless filtering:
- **`🌐 ALL SECTIONS`**: Displays both Live Signals and Watchlist stacked vertically.
- **`🚨 LIVE SIGNALS ({count})`**: Isolates the real-time execution signal table.
- **`📋 WATCHLIST ({count})`**: Isolates the day-type watchlist candidates table.

### 2.2 Section 1: Live Signals Matrix (`🚨 LIVE SIGNALS`)
- **Banner**: Red-to-amber gradient with glowing status ping and `REAL-TIME SCAN` badge.
- **Dedicated Strategy Filter Pills**:
  - `🌐 ALL LIVE` (Live Execution Count)
  - `⚡ CONFLUENCE` (Fire Alert Scalp Confluence)
  - `⚡ DIVERGENCE` (RSI Regular & Hidden Divergence)
  - `⚡ LIGHTNING` (Missile + Scalp Native Confluence)
  - `⚡ EXT REV` (Bollinger Extreme Reversal)
  - `⚡ MISSILE` (Intraday Momentum)
  - `⚡ SCALP` (High-Velocity Scalp)
  - `📋 VIEW WATCHLIST` (One-tap direct switch to Watchlist Candidates)
- **Table Scope**: Exclusively displays genuine trade execution signals. Non-execution day-types are strictly excluded.

### 2.3 Section 2: Dedicated Watchlist Section Below It (`📋 DAY TYPE WATCHLIST`)
- **Banner**: Cyan-to-indigo gradient with pulsing cyan beacon and `DAY-TYPE CANDIDATES` badge.
- **Dedicated Setup Filter Pills**:
  - `📋 ALL WATCHLIST` (Total Watchlist Count)
  - `🛡️ REJECTIONS` (Rejected Bullish, Rejected Bearish, Rejection Blueprint)
  - `🚀 CONTINUATIONS` (Bullish Continuation, Bearish Continuation)
  - `🎯 INSIDE DAY` (Inside Day CPR - 2-Day Pivot Inclusion)
  - `📐 NCPR` (Narrow CPR Breakout Candidates < 5.0% Range)
  - `🧲 VCPR` (Virgin CPR Magnets)
  - `🏛️ BLUEPRINTS` (Absorption, Failed New Low/High, Outside Day, Stop Run, Accumulation)
- **Outcome-Consistent Labels**: Badging dynamically displays `🛡️ REJECTION WATCHLIST` and `🚀 CONTINUATION WATCHLIST` (replacing misleading "LIVE SIGNAL" tags).

### 2.4 Collapsible Card Architecture (INSIGHTS Standard Alignment)
Following the exact visual rhythm and collapsible architecture of the **INSIGHTS tab** (`media_1795108519207.png`):
- Both Section 1 (`🚨 LIVE SIGNALS`) and Section 2 (`📋 DAY TYPE WATCHLIST`) are wrapped in `shiny-card rounded-3xl p-4 sm:p-5 relative overflow-hidden` containers.
- **Header Elements**:
  - Distinctive icon and uppercase section title (`⚡ LIVE SIGNALS` / `🩵 WATCHLIST`).
  - Clear descriptive subtitle (`ACTIVE LIMIT ORDERS & EXECUTING TRADES` / `DAY-TYPE CANDIDATES & PIVOT REGIME SETUPS`).
  - Real-time active counter badges (`• X ACTIVE SIGNALS` / `• X CANDIDATES`).
  - Native `EXPAND` / `COLLAPSE` toggle buttons with dynamic chevron indicators (`ChevronUp` / `ChevronDown`).
- **Initial State**: Both cards default to collapsed (`isHubLiveMasterExpanded: false`, `isHubWatchlistMasterExpanded: false`), providing an ultra-clean, decluttered mobile viewport while offering immediate expansion on tap.
- **Top-Level Toggle Integration**: Selecting `🚨 LIVE SIGNALS` or `📋 WATCHLIST` from the master view switcher automatically auto-expands the targeted section (`setIsHubLiveMasterExpanded(true)` / `setIsHubWatchlistMasterExpanded(true)`).

---

## 3. Parity & Build Verification

1. **Next.js Production Build**:
   ```bash
   next build
   ✓ Compiled successfully
   ✓ Linting and checking validity of types
   ✓ Generating static pages (8/8)
   ```
3. **Mirror Parity Checksum**:
   All 3 instances maintain exact SHA256 byte-for-byte synchronization:
   - `Tv-Alert-Mobile/src/app/page.tsx`: `4fc60e435bf31495bd05f89f0fd64b8a971ac0f459163089763974a02a0fa655`
   - `page.tsx`: `4fc60e435bf31495bd05f89f0fd64b8a971ac0f459163089763974a02a0fa655`
   - `RemoteURL/page.tsx`: `4fc60e435bf31495bd05f89f0fd64b8a971ac0f459163089763974a02a0fa655`


