# 99. Platform v3.0: Stocks With Action Universal 7-Market Expansion Architecture Across All 9 Setup Families

**Date:** November 15, 2026  
**Status:** Canonical Production Baseline & Universal Screener Expansion Release  
**Preceding Baseline:** Note 98 (Platform v3.0 Markets Tab Metric Typography & Institutional Numeric Scale Synchronization)  
**Repositories:** Master Pine Script (`TLCS v3.0`), `Tv-Alert-Mobile`, `Project Backup`, `Backups`, Root Workspace  

---

## 1. Executive Summary

In response to user requests to expand the **Stocks with Action** screener beyond equities and commodities, the screening architecture in `renderDhanUnifiedBiasScreener` and `extractDhanScreenerAssets` has been extended from its previous subset to universally support **all 7 canonical market types** across **all 9 signal setup families**:

1. **Universal 7-Market Category Coverage**:
   - The screener now enables comprehensive filtering and asset extraction across:
     - `ALL` (Aggregate across all active markets)
     - `NIFTY` (Benchmark Indices: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX, BANKEX)
     - `STOCKS` (NSE Equities / F&O Top 100 universe)
     - `MCX` (MCX Indian Commodity Futures: CRUDEOIL, NATURALGAS, GOLD, SILVER, COPPER, ZINC, ALUMINIUM)
     - `NYMEX` (International Commodity Futures & Spots: USOIL, UKOIL, XAUUSD, XAGUSD, NG)
     - `CRYPTO` (Digital Assets: BTCUSD, ETHUSD, SOLUSD, etc.)
     - `FOREX` (Major & Cross FX pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDINR, etc.)
     - `WORLD` (Global World Indices: US30, SPX500, NAS100, DAX40, FTSE100, NIKKEI225, HSI, GIFT NIFTY)

2. **Full Parity Across All 9 Signal Setup Families**:
   - Universal market expansion is applied uniformly across:
     - `Outside Range & Value` (`OOR` / Trend & Value Exhaustion)
     - `Inside CPR` (`INSIDE` / Low Volatility Contraction / Coil Setups)
     - `Breakouts / NCPR` (`NCPR` / Directional Breakout Setups)
     - `Narrow Value / NVA` (`NVA` / Range Compression Opportunities)
     - `Virgin CPR` (`VCPR` / Untested Pivot Magnet & Reversal Setups)
     - `Divergence` (`DIV` / Confirmed Regular D & Hidden H Divergences)
     - `Rejections` (`REJ` / Key Level Pivot Rejections)
     - `Continuations` (`CONT` / Trend Continuation Pullbacks)
     - `Scalp Alert` (`FIRE` / Explosive Momentum Scalps)

3. **Dual Engine Source Fidelity (TradingView Webhooks vs DhanHQ BlackBox)**:
   - **TradingView Webhooks (`TV`)**: Native multi-asset webhook feeds populate real-time signals across all 7 markets (`NIFTY`, `STOCKS`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`, `WORLD`) with zero synthetic latency.
   - **DhanHQ BlackBox (`SHADOW`)**: Operates on live Indian market tick data covering NSE F&O, Nifty Indices, and MCX Commodities, while seamlessly allowing webhook cross-market assets when present.

4. **Type-Safe Component Architecture & UI Standardization**:
   - Replaced fragmented and hardcoded chip components with a type-safe `ScreenerMarketCategory` (`'ALL' | 'NIFTY' | 'STOCKS' | 'MCX' | 'NYMEX' | 'CRYPTO' | 'FOREX' | 'WORLD'`).
   - Integrated uniform horizontal scrollable chip selectors with live asset count badges across all 9 collapsible screener cards.
   - Standardized table row market badges with distinct color palettes:
     - `MCX`: Amber (`text-amber-400 bg-amber-500/15 border-amber-500/30`)
     - `NYMEX`: Yellow (`text-yellow-400 bg-yellow-500/15 border-yellow-500/30`)
     - `NIFTY` / `GIFT`: Purple (`text-purple-400 bg-purple-500/15 border-purple-500/30`)
     - `CRYPTO`: Cyan (`text-cyan-400 bg-cyan-500/15 border-cyan-500/30`)
     - `FOREX`: Emerald (`text-emerald-400 bg-emerald-500/15 border-emerald-500/30`)
     - `WORLD`: Rose (`text-rose-400 bg-rose-500/15 border-rose-500/30`)
     - `NSE`: Slate / Neutral (`text-slate-400 bg-slate-500/15 border-slate-500/30`)

---

## 2. Technical Modifications

### A. Screener Market Category Definition & State Management (`Tv-Alert-Mobile/src/app/page.tsx`)
```typescript
type ScreenerMarketCategory = 'ALL' | 'NIFTY' | 'STOCKS' | 'MCX' | 'NYMEX' | 'CRYPTO' | 'FOREX' | 'WORLD';

const [dhanOorMarketFilter, setDhanOorMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanInsideMarketFilter, setDhanInsideMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanNcprMarketFilter, setDhanNcprMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanNvaMarketFilter, setDhanNvaMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanVcprMarketFilter, setDhanVcprMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanDivMarketFilter, setDhanDivMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanRejMarketFilter, setDhanRejMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanContMarketFilter, setDhanContMarketFilter] = useState<ScreenerMarketCategory>('ALL');
const [dhanFireMarketFilter, setDhanFireMarketFilter] = useState<ScreenerMarketCategory>('ALL');
```

### B. Universal Asset Extraction & Market Gating (`extractDhanScreenerAssets`)
```typescript
const extractDhanScreenerAssets = (
  setupType: 'OOR' | 'INSIDE' | 'NCPR' | 'NVA' | 'VCPR' | 'DIV' | 'REJ' | 'CONT' | 'FIRE',
  sideFilter: 'ALL' | 'BULLISH' | 'BEARISH',
  marketFilter: ScreenerMarketCategory | string = 'ALL'
) => {
  const isMarketCategoryAllowed = (cat: string) => {
    if (marketFilter === 'ALL') return true;
    if (marketFilter === 'NIFTY') return cat === 'NIFTY' || cat === 'GIFT NIFTY';
    if (marketFilter === 'STOCKS') return cat === 'NSE STOCKS' || cat === 'STOCKS';
    if (marketFilter === 'MCX') return cat === 'MCX COMMODITIES' || cat === 'MCX';
    if (marketFilter === 'NYMEX') return cat === 'NYMEX COMMODITIES' || cat === 'NYMEX';
    if (marketFilter === 'CRYPTO') return cat === 'CRYPTO';
    if (marketFilter === 'FOREX') return cat === 'FOREX';
    if (marketFilter === 'WORLD') return cat === 'WORLD' || cat === 'INDICES';
    return true;
  };
  // Universal asset gating logic across all 7 market categories
};
```

### C. Trade Signal Exact Chart Candle Timestamping
- Standardized automatic time parsing (`timeIST`, `dateIST`, `fullTimeIST`, `timeUTC`) across all screened assets.
- Integrated high-contrast timestamp badges into table row session pills (`[ 14 Nov • 19:00 ]` and `[ TODAY • 09:45 ]`).
- Embedded detailed timestamp strings in table sub-rows across all 9 setup families:
  `• ⏰ 14 Nov, 19:00 IST (13:30 UTC)`
- Added dedicated `CHART SIGNAL PLOT TIMESTAMP` banner to the detail modal (`selectedDhanOorAsset`), showing the exact candle time for instant verification against TradingView charts.

### D. Trade Lifecycle Badging, Exit Time & Time Spent Duration
- **Dynamic Trade Lifecycle Status**:
  - `⏳ ACTIVE LIMIT`: Pulsing amber tag with ping dot for pending limit orders.
  - `⚡ LIVE`: Pulsing emerald tag with ping dot for active open positions.
  - `🔒 CLOSED`: High-contrast tag with outcome status (`(WIN)` green, `(LOSS)` red, or `(B/E)` slate).
- **Exit Timestamp Synchronization**: Automatically parses `exit_at`, `updated_at`, or close date metadata into `exitTimeIST` (`14 Nov, 19:45 IST`), `exitDateIST`, and `exitTimeUTC`.
- **Duration Spent Computation**: Computes exact duration (`timeSpentStr`: e.g. `45m`, `1h 15m`) from `hold_duration` or milliseconds delta between signal timestamp and exit timestamp.
- **Ubiquitous Presentation**: Rendered across both table row headers/sub-rows for all 9 setup cards and the top banner of the asset inspection popover modal.

### E. Strict Outcome-Consistent Move & Return (%) Mandate (Zero Negative Win Rule)
- **Root Cause Diagnosed**: In `extractDhanScreenerAssets`, raw price subtraction `exitP - entryP` was performed without accounting for trade direction (long vs short), and short percentages were explicitly negated. For short trades that were wins (e.g. `BTCUSDT [CRYPTO] • WIN`), falling asset prices resulted in a `-1.20%` return in a red badge.
- **Single Source of Truth**: Connected `getExactPct(s)` and `canonicalOutcome` directly to `dayMovePct` and `dayMovePts`.
- **Zero Negative Win Guarantee**: A winning trade (`outcome === 'WIN'`) is mathematically guaranteed to display a positive percentage (`+X.XX%`) styled in emerald green (`bg-emerald-500/15 text-emerald-800 border-emerald-500/35`).
- **Dual-Layer Defense**: Enforced at the data ingestion layer in `extractDhanScreenerAssets` and at the UI rendering layer in both the screener table (`Col 3: Move (%)`) and modal inspection popover.

---

## 3. Verification & Build Parity
- **TypeScript Typecheck**: `npx tsc --noEmit` exited cleanly with code 0.
- **Production Build**: `npm run build` completed successfully with all static and dynamic routes compiled.
- **Strict Fact-Backed Verification**: Zero changes to Pine Script indicators, mathematical formulas, or trade triggers.
