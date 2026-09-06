# Version 1.0 Production Release: Screener Matrix START AFRESH Removal Protocol & Paper Trading Single 10L Option

**Release Date:** September 6, 2026  
**Milestone Version:** `v1.0` (Production Master)  
**System Components Affected:** `Tv-Alert-Mobile/src/app/page.tsx`, `.agents/AGENTS.md`, `RemoteURL`

---

## 1. System Overview & Release Motivation

Version 1.0 delivers key enhancements and operational control refinements across the **TLCS Mobile Terminal** (`Tv-Alert-Mobile`):

1. **TLCS Screener Matrix START AFRESH Intraday Removal Protocol**:
   - Resolved the behavior where the **START AFRESH** button previously re-fetched unchanged data without clearing or modifying displayed records.
   - Formalized the explicit requirement: **Tapping START AFRESH removes all TLCS Intraday Signals for the current week**, giving traders a clean slate to begin monitoring fresh intraday setups.
   - Built with persistent state (`screenerSignalsResetTs`) stored in `localStorage` (`tlcs_screener_signals_reset_ts`), auto-filtering all current week intraday signals (Missile, Divergences, Scalp, Lightning) while strictly preserving Day Type Blueprints and Trade Sequences.
   - Introduced a bidirectional **`[RESTORE]`** control allowing users to revert the clearing action and restore all historical intraday signals at any time.
   - Enhanced user flow: Automatically expands the matrix, resets the active market selection back to `ALL MARKETS`, and smoothly scrolls horizontally to the `Today / Recent` view.

2. **Virtual Paper Portfolio Simulator Single 10 Lacs (₹10,00,000) Baseline**:
   - Streamlined the simulated capital selection by deprecating `1L`, `5L`, and `25L` quick presets.
   - Retained exclusively **`[10L]`** as the single, standardized virtual currency preset option.
   - Standardized default capital baseline across all market configurations (`NIFTY 50`, `MCX COMMODITIES`, `NYMEX & COMEX`, `CRYPTO TOP 25`, `FOREX PAIRS`, `WORLD INDICES`, and `ALL MARKETS`) to **₹10,00,000**.
   - Guaranteed that paper portfolio resets cleanly restore to ₹10,00,000.

3. **Sequential Metrics & Disaster Recovery Codebase Backups**:
   - Standardized chronological sorting for consecutive loss streaks and maximum drawdown to use canonical signal entry timestamps (`getSignalTime`) with `created_at` tie-breakers, achieving 100% metric parity across mobile and web dashboards (2 consecutive losses, -0.56% Max Drawdown).
   - Created pristine local uncompressed codebase backups and 3.5 MB standalone `.zip` archives mirrored in `/Users/vishant/Documents/Project/Backups/` and `/Users/vishant/Documents/Backups/`.

---

## 2. Key Architectural & Technical Implementations

### A. Screener Matrix START AFRESH & Selective Reset Protocol
In `Tv-Alert-Mobile/src/app/page.tsx`:
- **State Initialization**:
  ```typescript
  const [screenerSignalsResetTs, setScreenerSignalsResetTs] = useState<number | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('tlcs_screener_signals_reset_ts');
        if (saved) {
          const ts = parseInt(saved, 10);
          if (!isNaN(ts)) return ts;
        }
      } catch (e) {}
    }
    return null;
  });
  ```
- **Reset Handler (`handleResetScreenerMatrix`)**:
  - Captures `nowTs = Date.now()` and saves to state and `localStorage`.
  - Resets `setAnalyticsMarket('ALL')` and forces `setIsScreenerExpanded(true)`.
  - Scrolls horizontal table container smoothly to the right (`el.scrollWidth`) representing Today / Recent.
  - Refetches system state via `fetchStateRef.current()`.
  - Displays persistent notification banner with quick `[RESTORE]` trigger.
- **Selective Section 1 Suppression**:
  - `pivotBossScans` in Section 1 ("TLCS SIGNALS") are suppressed when `screenerSignalsResetTs` is active.
  - `daySigs` are filtered: `if (screenerSignalsResetTs && sigTs < screenerSignalsResetTs) return false;`.
  - Sections 2 (**DAY TYPE BLUEPRINTS**) and 3 (**TRADE SEQUENCES**) remain untouched and fully preserved.
  - When no active signals exist post-reset, displays: `"No active Intraday Signals in the last 7 days."`.
- **Restore Handler (`handleRestoreScreenerSignals`)**:
  - Clears `screenerSignalsResetTs` to `null` and purges `localStorage`, instantly re-rendering all historical signals.

### B. Paper Portfolio Simulator Single 10L Option
- **Preset Buttons**: Replaced multi-button preset array `[1L, 5L, 10L, 25L]` with single option `[{ val: 1000000, label: '10L' }]`.
- **Market Configurations (`DEFAULT_LOT_CONFIG`)**:
  - `nifty`, `mcx`, `nymex`, `crypto`, `forex`, `world`, and `ALL` standardized with `defaultCapital: 1000000`.
- **Initial State**: `useState<number>(1000000)`.

---

## 3. Verification & Deployment Status

- **Code Repositories**:
  - `Tv-Alert-Mobile`: Commit `22e993a` pushed to `origin/main`.
  - `Project` (Root): Commit `9423ea6` pushed to `origin/main`.
- **Netlify Hosting**: Production build auto-triggered and live on `thelioncapitalsolutions.com`.
- **System Documentation**: Formalized in `.agents/AGENTS.md`.
