# The Lion Capital Solutions (TLCS) System Architecture & Update Log
## Version 1.0 Release: INSIGHTS Tab Engine Isolation & Webhook Signal Bleed Elimination
**Date**: October 4, 2026  
**Status**: Production Hardened Baseline (Release Tags `v1.0` / `v1.0.0`)  
**Architect**: Vishant Vyankat Meshram (*CFTe, CMT L3 Dec 2024*)

---

### Executive Overview
This release implements strict dual-engine isolation across the **INSIGHTS** tab on the mobile terminal (`page.tsx`). Previously, selecting the `BLACK BOX` engine could result in webhook signals (such as `ETHUSDT` crypto scalps) bleeding into the `STRATEGY PERFORMANCE` metrics, strategy filter chips, signal feed cards, and `ALERT SIGNAL RANKINGS` whenever the active guidance filters had no matching shadow trades. This update enforces 100% deterministic engine partitioning, ensuring that Black Box telemetry reflects strictly DhanHQ executed shadow trades with zero webhook signal contamination.

---

### Root Cause Analysis & Architecture Fixes

#### 1. Strategy Source Signal Resolution (`page.tsx`)
- **Vulnerability**: In `strategyCategoryStats` and `strategyInsights`, when `strategyTypeFilter !== 'ALL'` and guidance filters produced zero matches for the selected strategy, the fallback expression unconditionally evaluated `? todayClosedSignals : guidanceClosedSignals`. Because `todayClosedSignals` represents live TradingView webhook signals from the `signals` database table, Black Box mode inadvertently ingested external crypto and forex webhook trades.
- **Remediation**:
  - Bound fallback source strictly to `currentTodayClosed = engineSource === 'SHADOW' ? dhanTodayClosed : todayClosedSignals`.
  - Added explicit dependencies `engineSource` and `dhanTodayClosed` to both `strategyCategoryStats` and `strategyInsights` `useMemo` hooks.

#### 2. Strategy Filter Chips Engine Sourcing
- **Vulnerability**: The strategy selector chips (`availableStrategies`) mapped directly over `todayClosedSignals`, causing non-existent strategies in Black Box (e.g. `LONG SCALP` from `ETHUSDT`) to appear as clickable filter chips in the Black Box viewport.
- **Remediation**:
  - `availableStrategies` now dynamically maps over `currentTodayClosed = engineSource === 'SHADOW' ? dhanTodayClosed : todayClosedSignals`.
  - When in `BLACK BOX` mode, chips are strictly populated from DhanHQ shadow closed signals.

#### 3. Filtered Strategy Signals Display (`matchingStratSignals`)
- **Vulnerability**: When clicking an active strategy chip, `matchingStratSignals` filtered `todaySignals` (unconditionally pulling from webhook signals).
- **Remediation**:
  - Sourced from `currentTodaySignals = engineSource === 'SHADOW' ? dhanTodaySignals : todaySignals`.
  - Under `BLACK BOX` mode, the card list renders only DhanHQ shadow signals matching the strategy filter.

#### 4. Clean Engine Toggle State Sanitization
- Toggling between `[WEBHOOK SIGNALS]` and `[BLACK BOX]` on the INSIGHTS tab now automatically resets `strategyTypeFilter`, `openingBiasFilter`, and `dayTypeFilter` to `'ALL'`, preventing active filter selections from lingering across engine switches.

#### 5. Indian Equities Category Tracking (`marketCategoryStats`)
- Added `'STOCKS'` to the category initialization array (`cats = ['NIFTY', 'STOCKS', 'MCX', 'NYMEX', 'CRYPTO', 'FOREX', 'WORLD']`), ensuring that Indian equity trades executed by DhanHQ Black Box are tracked in category metrics.

---

### Verification & Test Suite
1. **Engine Separation**: Verified that when `BLACK BOX` is active, zero webhook crypto/forex signals appear in `STRATEGY PERFORMANCE` or `ALERT SIGNAL RANKINGS`.
2. **Dynamic Filter Chips**: Verified that strategy chips reflect only strategies present in the active engine's closed dataset.
3. **Engine Toggle Reset**: Verified seamless filter reset upon toggling between `WEBHOOK SIGNALS` and `BLACK BOX`.
4. **Triple Mirror Backup**: Synchronized to `Project Backup/`, `Backups/`, and `Documents/Backups/`.
