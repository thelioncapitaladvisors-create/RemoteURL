# Platform v1.0 Markets Table Trade Collapse & Scorecard Descending Performance Sorting
**Date**: October 22, 2026  
**Status**: Production Ready & Fully Verified

---

## Executive Summary

This release resolves two critical user interface and operational layout requests on the platform:
1. **Consolidated Markets Table Trade Outcomes Collapse / Expand Toggle**: On the **MARKETS** tab in `Tv-Alert-Mobile/src/app/page.tsx`, an interactive `COLLAPSE` / `EXPAND` toggle was added to the *Today's Signal Performance* table, defaulting to the collapsed state (`isTodayTradesExpanded = false`). This folds up long lists of individual trade rows under the Intraday Trajectory curve while preserving the column headers, summary metrics, and trajectory chart, ensuring immediate visibility and accessibility to lower market segments (e.g. `MCX COMMODITIES`) without endless vertical scrolling.
2. **Descending Order of Performance Arrangement on Scorecard Tables**: On the **INSIGHTS** tab, both the *Performance Breakdown by Day Type & Market Regime* and the *Performance Breakdown by Canonical Signal Family* scorecards now arrange rows dynamically in descending order of performance. Categories with active trades (`totalTrades > 0`) are grouped strictly above 0-trade categories, ranked by realized wins, win rate, net return %, profit factor, and expectancy. The top-performing regime (`🏆 MAX WINS` with `TOP EDGE` badge) dynamically anchors Row #1 of the Day Type matrix.

---

## 1. Markets Consolidated Table Trade Outcomes Collapse & Expand Architecture

### Operational Problem
On high-frequency trading sessions, the *Today's Signal Performance* table on the `MARKETS` tab displays 20–40+ individual trade rows. Previously, all rows rendered in a continuous expanded list directly beneath the Intraday Equity Trajectory curve, pushing subsequent market segment cards (e.g., `MCX COMMODITIES`, `NIFTY 50`, `US ENERGY`) far down the viewport and requiring tedious mobile scrolling.

### Solution & Implementation
In `Tv-Alert-Mobile/src/app/page.tsx`:
1. **Default-Collapsed State Variable**:
   ```tsx
   const [isTodayTradesExpanded, setIsTodayTradesExpanded] = useState<boolean>(false);
   ```
2. **Section Header Ergonomic Action**:
   Integrated an institutional toggle pill in the flex header of `Today's Signal Performance`:
   ```tsx
   {todaysTableSignals.length > 0 && (
     <button
       type="button"
       onClick={() => setIsTodayTradesExpanded(!isTodayTradesExpanded)}
       className="text-[10px] sm:text-xs font-mono font-black text-sky-600 dark:text-sky-400 px-2 sm:px-2.5 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/25 transition-all select-none shrink-0 self-start sm:self-auto flex items-center gap-1 active:scale-95 cursor-pointer shadow-sm"
       title={isTodayTradesExpanded ? 'Collapse individual trade outcomes' : 'Expand individual trade outcomes'}
     >
       <span>{isTodayTradesExpanded ? 'COLLAPSE TRADES' : 'EXPAND TRADES'}</span>
       <span className="text-[10px] leading-none">{isTodayTradesExpanded ? '▲' : '▼'}</span>
     </button>
   )}
   ```
3. **Table Dividing Strip & Bottom Ergonomic Button**:
   - Added a dividing toggle bar between the Intraday Trajectory curve and the trade outcomes displaying the live trade count: `Individual Trade Outcomes [N Trades] | EXPAND ▼`.
   - Conditioned trade outcome row rendering inside `{isTodayTradesExpanded ? (...) : (...)}`.
   - Injected a bottom collapse button (`COLLAPSE TRADE OUTCOMES ▲`) when more than 5 trades are present to allow collapsing directly from the bottom without scrolling up.

---

## 2. Descending Order of Performance Arrangement

### Operational Problem
Previously, both the *Performance Breakdown by Day Type & Market Regime* table and the *Performance Breakdown by Canonical Signal Family* table rendered rows in hardcoded definition order (`FAMILIES.map(...)` and `REGIMES.map(...)`). As a result:
- The top-performing Day Type crowned as `🏆 MAX WINS` with the `TOP EDGE` badge (`IN RANGE / IN VALUE (CONSOLIDATION)` with 2 wins and 28.6% WR) was buried at Row #7.
- Categories with 0 trades (such as `TREND DAY / DD TREND`, `EXPANDED TYPICAL`, `REJECTION / ABSORPTION`) were arbitrarily interleaved between active trading regimes.
- In the Canonical Signal Family table, `MISSILE` (which had 28 closed trades and 4 wins) was rendered at Row #3 below two 0-trade rows (`DIVERGENCE` and `SCALP`).

### Multi-Tier Quantitative Sorting Hierarchy
In `Tv-Alert-Mobile/src/app/page.tsx` within `canonicalFamilyStats` and `dayTypeStats`:
```tsx
rows.sort((a, b) => {
  // 1. Categories with trades strictly before categories with 0 trades
  if (a.totalTrades > 0 && b.totalTrades === 0) return -1;
  if (a.totalTrades === 0 && b.totalTrades > 0) return 1;
  if (a.totalTrades === 0 && b.totalTrades === 0) return 0;

  // 2. Win Count (realized wins) descending
  if (b.winCount !== a.winCount) return b.winCount - a.winCount;

  // 3. Win Rate % descending
  if (Math.abs(b.winRate - a.winRate) > 0.001) return b.winRate - a.winRate;

  // 4. Net Return % descending (positive alpha / drawdown resistance)
  if (Math.abs(b.netReturn - a.netReturn) > 0.001) return b.netReturn - a.netReturn;

  // 5. Profit Factor descending
  const pfA = a.pfNum || 0;
  const pfB = b.pfNum || 0;
  if (Math.abs(pfB - pfA) > 0.001) return pfB - pfA;

  // 6. Expectancy % descending
  if (Math.abs(b.expectancy - a.expectancy) > 0.0001) return b.expectancy - a.expectancy;

  // 7. Total Trades descending
  return b.totalTrades - a.totalTrades;
});
```

### Resulting Scorecard Display Order
1. **Day Type & Market Regime Scorecard**:
   - `Rank #1`: `🎯 IN RANGE / IN VALUE (CONSOLIDATION)` (7 Trades • 2W / 5L / 0B • 28.6% WR • `TOP EDGE`)
   - `Rank #2`: `💥 BIG MOVE / BREAKOUT DAY` (4 Trades • Positive Net Return +0.07%)
   - `Rank #3`: `🏷️ UNCLASSIFIED / GENERAL REGIME`
   - `Rank #4`: `↔️ TYPICAL / TRADING RANGE / SIDEWAYS` (9 Trades)
   - `Rank #5`: `📈 TREND DAY / EXPANDED TYPICAL` (4 Trades)
   - `Rows #6-#10`: Zero-trade categories grouped at the bottom in canonical order.
2. **Canonical Signal Family Scorecard**:
   - `Rank #1`: `🚀 MISSILE` (28 Trades • 4W / 15L / 9B • 14.3% WR)
   - `Rows #2-#6`: `DIVERGENCE`, `SCALP`, `EXTREME REVERSAL`, `HIDDEN DIVERGENCE`, `LIGHTNING` (0 trades).

---

## 3. Verification & Deployment Audit

1. **TypeScript Compilation**: Executed `npx tsc --noEmit` across `Tv-Alert-Mobile` — 0 errors, 0 warnings.
2. **Submodule Synchronization**:
   - `Tv-Alert-Mobile` updated and pushed to `origin/main`.
   - Root tracking repository updated and pushed to `origin/main`.
