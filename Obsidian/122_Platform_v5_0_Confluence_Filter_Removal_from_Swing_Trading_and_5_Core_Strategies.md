# 122: Version 5.0 Confluence Filter Removal from Swing Trading & 5 Core Strategies

**Date**: November 24, 2026  
**Status**: APPROVED & DEPLOYED (v5.0)  
**Modules**: `Tv-Alert-Mobile/src/app/page.tsx`, `RemoteURL/page.tsx`, `page.tsx`, `AGENTS.md`

---

## 1. Executive Summary

Per institutional user directive, the **Confluence** (`⚡ CONFLUENCE` / `FIRE`) filter category and matrix table row have been permanently removed from the **Swing Trading Opportunities** section on the INSIGHTS tab (`activeTab === 'INSIGHTS'`). The Daily Timeframe (`1D`) execution pipeline is strictly locked to the **5 canonical core swing execution strategies**:

1. **Missile** (`🚀 MISSILE`)
2. **Scalp** (`💎 SCALP`)
3. **Lightning** (`⚡ LIGHTNING`)
4. **Extreme Reversal** (`🔥 EXT REV`)
5. **Divergence** (`🎯 REGULAR DIV` / `🔍 HIDDEN DIV`)

Confluence is preserved strictly on the HUB tab for 15-minute intraday signals.

---

## 2. Quantitative Root Cause & Asset Analysis

### 2.1 CRUDEOIL vs NATURALGAS Daily Bar Evaluation & Noise Identification
- **CRUDEOIL (`CRUDEOIL1!`)**:
  - Triggers the **`SHORT MISSILE`** strategy (verified on TradingView Daily chart with red downward trend arrow and targets `7921`, `7648`, `6736`).
  - Correctly qualifies for **`🚀 MISSILE`** on the INSIGHTS tab.
- **NATURALGAS (`NATURALGAS1!`) & Noise Identification**:
  - **Visual Noise Identified**: The purple circled lightning bolt `⚡` icon on the bottom timeline axis of the TradingView chart was identified as TradingView's native **Dow Jones Newswires "Latest updates" news event** (*"U.S. Natural Gas Futures Sink on Milder Weather Outlook — Market Talk"*), completely separate from indicator signals.
  - On the indicator level, Natural Gas only had a Camarilla touch point without any Missile, Scalp, Lightning, Extreme Reversal, or Divergence trigger.
  - When tested against the BlackBox daily scanner (`DailyBlackboxScanner(market='mcx').scan_symbol('NATURALGAS')`), it returned `[]` (0 qualifying swing strategies).
  - **Database Purge**: The spurious historical webhook record (`68e9fe8f-8e81-4872-8e51-dc8216089ecd`) that had been created from external noise was permanently deleted from the Supabase `signals` table.
  - **Purity Mandate**: Enshrined strict rule that alert generation must derive purely from authentic mathematical signal logic (`CanBuy`, `CanSell`, `ScalpBuy`, `ScalpSell`, `Elongsignal`, `Eshortsignal`, Divergence math) with zero third-party chart event noise incorporated.

---

## 3. Architecture & Code Changes

### 3.1 Frontend (`Tv-Alert-Mobile/src/app/page.tsx`)
1. **`liveFilterOptions`**:
   - `...(activeTab !== 'INSIGHTS' && liveSignalsStats.fireCount > 0 ? [{ value: 'FIRE', label: '⚡ CONFLUENCE', count: liveSignalsStats.fireCount }] : [])`
   - Omitted from the INSIGHTS tab.
2. **`liveMatrixCategories`**:
   - Excludes `FIRE` when `activeTab === 'INSIGHTS'`, rendering strictly the 5 core swing strategies.
3. **`filteredByTabTf`**:
   - Strictly enforces the 5 approved strategies in `matchesApproved`.

---

## 4. Verification

- **Next.js Production Build**: `npm run build` compiled with 0 errors (`✓ Compiled successfully`).
- **Git Commits & Release Tags**: Synced across `Tv-Alert-Mobile`, `RemoteURL`, and root workspace with release tags `v5.0` and `v5.0.0`.
