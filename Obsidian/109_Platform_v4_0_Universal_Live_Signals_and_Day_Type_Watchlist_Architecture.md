# Platform v4.0: Universal Live Signals & Day Type Watchlist Architecture Specification

**Document ID**: 109  
**Effective Date**: November 19, 2026 (22:00 IST)  
**Classification**: Architecture Specification & Production Release Sign-Off  
**Release Target**: TLCS Platform Version 4.0 (`v4.0`)  
**Status**: 🚀 PRODUCTION RELEASED & ACTIVE  

---

## 1. Executive Summary

This release establishes the **Universal Live Signals & Day Type Watchlist Architecture** across the TLCS Mobile Terminal, completing the definitive separation of execution flow from observational market regimes:
1. **Universal Strategy Ingestion for Live Signals**: The Live Signals pipeline (`renderDhanLiveSignalsSection` bound to `liveSignalsAssets`) now captures **all current active limit orders (`tradeLifecycle === 'ACTIVE LIMIT'`) and executing live trades (`tradeLifecycle === 'LIVE'`)** across all strategy types via `setupType === 'ALL_LIVE'` (`MISSILE`, `SCALP`, `LIGHTNING`, `EXTREME REVERSAL`, `DIVERGENCE`, `HIDDEN DIVERGENCE`, `CONFLUENCE / FIRE_ALERT`, `VIRGIN CPR`, `REJECTION`, `CONTINUATION`, `BOUNCE`), completely resolving the legacy blindspot where trades outside 9 screener categories were omitted.
2. **Comprehensive Real-Time Day Type Watchlist**: The Watchlist pipeline (`renderDhanWatchlistSection` bound to `watchlistAssets`) dynamically surfaces **all valid day types and 2-day pivot relationships** (`INSIDE`, `OOR`, `BIG_MOVE`, `NCPR`, `NVA`, `REJ`, `CONT`, `VCPR_MAGNET`) on a real-time basis without dropping signals due to trade execution statuses or lack of synthetic `WATCHLIST` tags.
3. **Zero Text Collision Responsive Geometry**: Table column layout has been rebalanced to `34% | 42% | 24%` with strict `min-w-0 max-w-full overflow-hidden truncate` wrappers, permanently resolving the visual badge overflow bug observed on mobile screens where multi-word pills collided with adjacent outcome return percentages.

---

## 2. Problem Statement & Root Cause Diagnosis

### 2.1 Missing Active Limit Orders in Live Signals
- **The Issue**: Live limit orders and open trades in prominent symbols (`GC1! | SHORT MISSILE | OPEN`, `CAC40 | SHORT MISSILE | OPEN`, `USDJPY | LONG MISSILE | OPEN`, `NIFTY1! | LONG MISSILE | OPEN`) were absent from the Live Signals section.
- **Root Cause**: `liveSignalsAssets` iterated exclusively over 9 pre-defined setup categories (`FIRE`, `DIV`, `REJ`, `CONT`, `VCPR`, `OOR`, `INSIDE`, `NCPR`, `NVA`). Standalone strategy executions (`MISSILE`, `SCALP`, `LIGHTNING`, `EXTREME REVERSAL`) occurring outside a recognized setup boundary were filtered out by `extractDhanScreenerAssets`.
- **Solution**: Implemented `setupType === 'ALL_LIVE'`, allowing all active limit and live trade signals to pass directly into `liveSignalsAssets` with dynamic strategy badging (`⚡ LIGHTNING`, `🔥 EXT REV`, `🚀 MISSILE`, `💎 SCALP`, etc.).

### 2.2 Watchlist Empty / Missing Candidate Day Types
- **The Issue**: Watchlist showed 0 candidates or omitted valid day types (Inside CPR, Big Move, Bearish Rejections) on real-time feeds.
- **Root Cause**: `extractDhanScreenerAssets` enforced `if (watchlistOnly && tradeLifecycle !== 'WATCHLIST') return;`. Because TradingView Webhook signals carry trade lifecycle statuses (`OPEN`, `TradeOpen`, `Closed`, `Hit SL/TP`), their status is never literally `WATCHLIST`. This caused 100% of Webhook signals to be discarded.
- **Solution**: Watchlist candidate extraction is decoupled from trade lifecycle execution states. Any symbol whose intraday data or pivot geometry satisfies the mathematical definition of a day type or relationship (`INSIDE`, `OOR`, `BIG_MOVE`, `NCPR`, `NVA`, `REJ`, `CONT`, `VCPR`) is qualified as a Watchlist candidate.

### 2.3 Mobile Cell Overlap (Text Collision)
- **The Issue**: In mobile viewports, Col 2 setup badges (e.g. `▼ ⚡ CONFLUENCE ALERT`) expanded horizontally and collided with Col 3 return badges (`+0.00%`).
- **Root Cause**: Legacy table geometry allocated `36% | 36% | 28%` column widths without inner truncation wrappers on the flex badge container.
- **Solution**: Rebalanced table header and body widths to `34% (Symbol & Time) | 42% (Signal & Status) | 24% (Return %)`, wrapped Col 2 in `flex items-center min-w-0 max-w-full overflow-hidden`, and added `truncate shrink min-w-0` to badge text.

---

## 3. Architecture & Implementation Specifications

### 3.1 Data Flow Pipeline
```
[ TradingView Webhooks / DhanHQ BlackBox Signals ]
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
[ setupType: 'ALL_LIVE' ]   [ setupType: setup.id ]
  liveActionOnly = true       liveActionOnly = false
  watchlistOnly = false       watchlistOnly = false
       │                           │
       ▼                           ▼
[ liveSignalsAssets ]       [ watchlistAssets ]
  • Active Limits             • Inside CPR Candidates
  • Live Executions           • Outside Range/Value (OOR)
  • Dynamic Badging:          • Big Move / Breakout Days
    - LIGHTNING                 • Narrow CPR (NCPR)
    - EXT REV                   • Narrow Value Area (NVA)
    - MISSILE                   • Boundary Rejections
    - SCALP                     • Trend Continuations
    - DIVERGENCE                • VCPR Magnets
    - CONFLUENCE
```

### 3.2 Strategy Filter Synchronization
- **Live Signals Tier 1 Filters**:
  - `ALL`: Total count of active limit orders and live trades.
  - `⏳ ACTIVE LIMITS`: Pending limit orders waiting for fill.
  - `⚡ LIVE TRADES`: Positions currently filled and executing.
  - `🔥 CONFLUENCE`: Trades qualified under VectorBT confluence gating.
  - `⚡ LIGHTNING`: Native Missile + Scalp confluence signals.
  - `🔥 EXT REV`: Climax extreme reversal signals.
  - `🚀 MISSILE`: Trend expansion missile signals.
  - `💎 SCALP`: Momentum scalp signals.
  - `🎯 DIVERGENCE`: Confirmed regular and hidden divergence trades.
  - `🛡️ REJECTIONS`: CPR boundary rejection trades.
  - `🚀 CONTINUATIONS`: Trend continuation breakout trades.
  - `⚡ VCPR TOUCH`: Active Virgin CPR touch-point tests.

- **Watchlist Tier 1 Filters**:
  - `ALL`: Total qualifying day types and setups.
  - `🛡️ REJECTIONS`: Bullish & Bearish CPR boundary rejections.
  - `🚀 CONTINUATIONS`: Bullish & Bearish trend continuations.
  - `⚡ OUT OF RANGE`: Out of Range / Out of Value opening prints.
  - `🎯 INSIDE CPR`: Inside CPR compression days.
  - `💥 BIG MOVE`: Big Move / Breakout expansion days ($mX = \text{BIG MOVE}$).
  - `📐 NCPR`: Narrow CPR ($< 5.0\%$ range or $\le 50\%$ 14-day average).
  - `📊 NVAL`: Narrow Value Area compression ($< 38.0\%$ range).
  - `🧲 VCPR MAGNETS`: Untouched 1-month Virgin CPR magnets.

---

## 4. Verification & Validation Results

1. **Compilation & Build**:
   - Next.js production build (`npm run build --prefix Tv-Alert-Mobile`): `✓ Compiled successfully`, `8/8 static pages generated`, `0 errors`.
2. **Checksum Parity**:
   - `shasum -a 256 Tv-Alert-Mobile/src/app/page.tsx page.tsx RemoteURL/page.tsx`:
     `8ff5621c25630d7bd1ae30482b87f5a9bfcee9abe58d0a27250b3a3e72fa1e44` (100% byte-for-byte identical).
3. **Algorithmic Engine Test Suite**:
   - `python3 -m unittest algo_engine/tests/test_phase*.py`: `Ran 127 tests ... OK`.
4. **Mandate Adherence**:
   - `AGENTS.md` and `.agents/AGENTS.md` updated with the Version 4.0 Universal Live Signals & Day Type Watchlist Architecture Mandate (`58a0bf1b2625309add777ea3b77c524f9de6c0e175c9febfa13f38ff04ac442c`).

---

## 5. Deployment Sign-Off

- **Git Commit**: Version 4.0 Release
- **Remote Push**: `RemoteURL.git` and root repository `main`
- **Application Status**: Officially frozen and designated **Version 4.0 (`v4.0`)**
