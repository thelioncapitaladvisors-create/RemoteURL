# 136 — Platform v1.0 Multi-Day 1D Swing Trade Retention & Age/Date Badges Mandate

**Date**: November 27, 2026  
**Status**: Canonical Production Release (`v1.0.0`)  
**Target Files**: `page.tsx`, `RemoteURL/page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, `AGENTS.md`, `.agents/AGENTS.md`, `RemoteURL/AGENTS.md`, `RemoteURL/.agents/AGENTS.md`

---

## 1. Executive Summary

In direct response to the user's explicit directive ("Ensure to always show past limit or live trades untill invalidated on the insights page swing dashboard. Put age or date whereever required for better understanding"), two architectural enhancements were implemented:
1. **Multi-Day 1D Swing Trade Retention**: Pending limit orders (`tradeLifecycle === 'ACTIVE LIMIT'`) and executing positions (`tradeLifecycle === 'LIVE'`) for the Daily Timeframe (`1D` / `DAILY`) persist and remain 100% visible across session calendar date boundaries on the `INSIGHTS` tab (`Swing Trading Opportunities`) until explicitly closed or invalidated (hit Initial SL, hit TP targets, cancelled, or closed by trader).
2. **Deterministic Signal Age & Calendar Date Badges**: Every trade signal dynamically computes elapsed age (`Today`, `1d ago`, `${diffDays}d ago`) and IST calendar date (`Nov 25`, `Nov 27`), rendering high-contrast informational badges across the compact Matrix chips, the detailed List view, and the Trade Detail inspection modal.

---

## 2. Problem Statement & Multi-Day Swing Execution Physics

### A. Session Boundary Truncation Issue
By definition, Swing Trading on the Daily Timeframe (`1D`) operates on structural swing horizons lasting multiple trading days or weeks. An active limit order placed on Tuesday testing a Weekly Camarilla level ($W\text{-}H_4$ / $W\text{-}L_4$) or Weekly CPR remains a valid pending limit until price tests the limit or the order is explicitly cancelled. Previously, standard intraday session filters (`sessionFilter === 'TODAY'`) would drop older limit orders when a new calendar session opened, leaving users blind to valid pending swing limits.

### B. Lack of Elapsed Age Context
Users inspecting swing trading setups in the compact Matrix view had no immediate visual indication of whether a pending limit was placed in the current session or 2 days prior, requiring manual modal lookups.

---

## 3. Implementation Details

### A. Persistent Multi-Day Retention Logic (`page.tsx`)
1. **Decoupled Session Filter for `INSIGHTS` Tab**:
   In `liveSignalsAssets` memo hook:
   ```typescript
   const { assets } = extractDhanScreenerAssets(
     'ALL_LIVE',
     liveSignalsMarketFilter,
     liveSignalsDirectionFilter,
     activeTab === 'INSIGHTS' ? 'ALL' : liveSignalsSessionFilter,
     '',
     undefined,
     undefined,
     undefined,
     undefined,
     undefined,
     true, // liveActionOnly: strictly retains ACTIVE LIMIT and LIVE condition trades
     false
   );
   ```
2. **Confluence Filter Exemption for Live & Swing Trades**:
   In `eligibleSignals`:
   ```typescript
   if (confluenceMode === 'CONFLUENCE_ONLY' && setupType !== 'ALL_LIVE' && setupType !== 'VCPR' && setupType !== 'DIV' && setupType !== 'REJ' && setupType !== 'CONT' && setupType !== 'FIRE') {
     const conf = isConfluenceSignal(s, rawSignalsPool);
     if (!conf.isConfluence) return false;
   }
   ```
3. **Augmented 1D Swing Signal Detection**:
   ```typescript
   const rawTfStr = String(meta.timeframe || meta.interval || (s as any).timeframe || (s as any).interval || '').toUpperCase().trim();
   const isSwingSignal = rawTfStr === '1D' || rawTfStr === 'D' || rawTfStr === 'DAILY' || rawTfStr === '1440' ||
                         meta.is_swing === true || (s as any).is_swing === true || (s.type || '').toUpperCase().includes('SWING') ||
                         (s.type || '').toUpperCase().includes('DAILY') || (meta.strategy || '').toUpperCase().includes('DAILY') ||
                         (s.trigger || '').toUpperCase().includes('DTF') || (meta.trade_id || '').toUpperCase().includes('DTF') ||
                         (s.trigger || '').toUpperCase().includes('DAILYSIGNALSMATRIX') ||
                         (s.source || '').toUpperCase().includes('DAILY');
   ```
4. **Full 1D Strategy Parity in Live Matrix**:
   Added `CONFLUENCE` (`FIRE`) alongside `LIGHTNING`, `EXT_REV`, `OUTSIDE_REV`, `MISSILE`, `SCALP`, `DIV`, `WICK_REV`, `DOJI_REV`, and `SWING` so that all approved daily execution setups appear in both Tier 1 filter pills and matrix rows.

### B. Signal Age & Date Calculation Engine
```typescript
const sigMs = dObj.getTime();
dateStr = dObj.toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short' });

const nowMs = Date.now();
const diffMs = Math.max(0, nowMs - sigMs);
const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
const diffHrs = Math.floor(diffMs / (1000 * 60 * 60));

if (diffDays === 0) {
  ageStr = 'Today';
} else if (diffDays === 1) {
  ageStr = '1d ago';
} else {
  ageStr = `${diffDays}d ago`;
}
```

### C. Visual Interface Enhancements
1. **Compact Matrix View (Chips)**:
   Appended `📅 {asset.ageStr}` badge to Bullish and Bearish chips:
   ```tsx
   {asset.ageStr && (
     <span className="text-[7.5px] px-1 py-0.2 rounded font-mono font-bold bg-black/10 dark:bg-white/10 text-slate-700 dark:text-slate-300 ml-0.5 whitespace-nowrap">
       📅 {asset.ageStr}
     </span>
   )}
   ```
2. **Detailed List View**:
   - **Col 1 (Symbol & Time)**: Renders calendar date pill (`asset.dateStr`) alongside the candle time (`asset.timeIST IST`).
   - **Col 2 (Signal & Status)**: Renders elapsed age badge (`📅 {asset.ageStr}`) alongside the lifecycle status tag (`⏳ ACTIVE LIMIT` / `⚡ LIVE`).
3. **Asset Detail Modal**:
   - Subtitle header: `Session: {selectedDhanOorAsset.sessionDate} • 📅 {dateStr} ({ageStr}) • ⏰ {timeIST} IST`
   - Timeline Banner: `PLACED: {dateStr} ({ageStr})`

---

## 4. Verification & Validation

- **Next.js Production Build**: Executed `npm --prefix Tv-Alert-Mobile run build` on Node v20.20.2:
  - `✓ Compiled successfully`
  - `✓ Linting and checking validity of types`
  - `✓ Generating static pages (8/8)`
  - Total Errors: 0
- **Cross-Repository Synchronization**:
  - `Tv-Alert-Mobile`: Commit `ee8c676` pushed to `origin/main` & `alt/main`.
  - `RemoteURL`: Commit `7b33588` pushed to `origin/main`.
  - `TLCS_Website_Deploy`: Commit `22ee077b` pushed to `origin/main`.
  - Root Project Repo: Commit `323a433` pushed to `origin/main`.
