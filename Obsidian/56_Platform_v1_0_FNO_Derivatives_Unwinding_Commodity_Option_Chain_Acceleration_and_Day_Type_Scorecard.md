# Platform v1.0 F&O Derivatives Unwinding, Commodity Option Chain Acceleration & Day Type Performance Scorecard
**Date**: October 22, 2026  
**Status**: Production Ready & Fully Verified

---

## Executive Summary

This release resolves two critical data fidelity and performance bottlenecks across the platform and introduces an institutional Day Type edge matrix:
1. **F&O Stock Buildups Derivatives Unwinding Fidelity**: Fixed the systemic omission of *Long Unwinding* and *Short Unwinding* stocks by mapping equity cash tickers to authentic DhanHQ Stock Futures Security IDs (`futSecId` under `NSE_FNO`). Both live and EOD engines now calculate genuine Open Interest variations from derivatives rather than cash quotes.
2. **Commodity Option Chain Latency Acceleration (<490ms)**: Purged expired MCX contract candidates and pinned verified active front-month scrips (`573422` for Crude Oil, `570750` for Natural Gas). Added in-memory caching (`activeScripCache`) and fixed Netlify function exceptions, slashing option chain load times from 15s client timeouts down to **under 490ms**.
3. **Day Type & Market Regime Performance Breakdown Scorecard**: Integrated a high-density institutional scorecard directly into the `INSIGHTS` tab of the mobile terminal. Evaluates closed trades forward-tested from the October 20, 2026 baseline anchor across canonical PivotBoss day types and market regimes, featuring canonical win rates (with breakevens retained) and a dynamic top-edge badge (`🏆 MAX WINS`).

---

## 1. F&O Derivatives Open Interest & Unwinding Architecture

### Root Cause Analysis (RCA)
In the previous implementation (`/api/fno-buildups` and `dhan-fno-buildups.js`), batch market quotes queried the cash equity segment exclusively (`NSE_EQ:RELIANCE`, `NSE_EQ:INFY`). In Indian equity markets, cash equities do not carry Open Interest (`oi = 0`). Consequently, any calculation measuring Open Interest change ($\Delta\text{OI} = \text{oi} - \text{oi\_prev}$) yielded 0, rendering Long Unwinding and Short Unwinding permanently empty on the application while actively visible on DhanHQ's native terminal.

### Architectural Solution
- **30 F&O Universe Equities Mapped to Futures Scrips**: Mapped each equity ticker to its active DhanHQ Stock Futures Security ID (`futSecId`), querying `NSE_FNO` instruments (`FUTSTK`).
  ```javascript
  const FNO_SECURITY_MAP = {
    RELIANCE:   { eqSecId: '2885',  futSecId: '49217' },
    TCS:        { eqSecId: '11536', futSecId: '49221' },
    HDFCBANK:   { eqSecId: '1333',  futSecId: '49141' },
    INFY:       { eqSecId: '1594',  futSecId: '49147' },
    ICICIBANK:  { eqSecId: '4963',  futSecId: '49143' },
    ...
  };
  ```
- **Dual Batch Quote Synchronization**: The engine queries both `NSE_EQ` (for true spot price action) and `NSE_FNO` (for authentic derivative Open Interest metrics).
- **Buildup Regime Classification**:
  - **Long Buildup**: Price $\uparrow$ and OI $\uparrow$
  - **Short Buildup**: Price $\downarrow$ and OI $\uparrow$
  - **Long Unwinding**: Price $\downarrow$ and OI $\downarrow$
  - **Short Unwinding**: Price $\uparrow$ and OI $\downarrow$
- **Corrupted Snapshot Rejection & Historical Fallback**: When fetching EOD snapshots, any legacy payload where both unwinding categories have 0 stocks is rejected, triggering automated fallback to DhanHQ `/v2/charts/historical` API on `NSE_FNO` futures candles.

---

## 2. Commodity Option Chain Ultra-Low Latency Acceleration

### Root Cause Analysis (RCA)
When opening commodity option chains on the mobile app, users experienced severe delays or infinite loading spinners ("CONNECTING TO LIVE FEED...").
1. In `ASSET_MAP`, candidate scrip #0 for Crude Oil was an expired contract (`569900`).
2. DhanHQ's option chain endpoint returned HTTP 400 for expired contracts, forcing sequential fallback loops that hit Dhan's 3-second throttle, exceeding the client's 5-second fetch timeout.
3. In Netlify functions (`dhan-option-chain.js`), missing properties on fallback structures caused unhandled reference errors (`rawData.last_price`).

### Architectural Solution
- **Front-Month Active Scrip Indexing**:
  - `CRUDEOIL`: `[573422, 576264, 580377]` (Active front-month: `573422`, Nov 2026: `576264`)
  - `NATURALGAS`: `[570750, 574319, 578249, 581135]` (Active front-month: `570750`, Nov 2026: `574319`)
  - `GOLD`: `[495213, 571445, 569424]`
  - `SILVER`: `[495214, 483080, 574825]`
- **In-Memory Active Scrip Caching**: Once a valid active scrip is resolved, it is cached in `activeScripCache[assetKey]`, eliminating trial-and-error roundtrips on subsequent requests.
- **Client & Background Resilience**: Client-side fetch timeout expanded to 12s, rollover fallback timeouts tightened to 2.5s, and Netlify cron pre-warm (`cron-keep-alive.js`) updated with native `https` module.
- **Performance Benchmark**: Latency reduced from >15,000ms (timeout) to **< 490ms** with 90–188 strikes fully rendered.

---

## 3. Day Type & Market Regime Performance Breakdown Scorecard

### Objective
To build trader confidence and identify mathematical market regime edge, a dedicated performance scorecard was deployed on the `INSIGHTS` tab (`Tv-Alert-Mobile/src/app/page.tsx`).

### Institutional Metrics Standard
- **Strict Forward-Only Baseline Anchor**: Trades evaluated in the table strictly filter for closed trades with `effectiveTimestamp >= 1792434600000` (October 20, 2026 00:00:00 IST), eliminating distortion from legacy signals.
- **Categorization Dimensions**:
  1. `Trend Day / Expanded Typical`
  2. `Trend Day / Double Distribution (DD)`
  3. `Big Move / Breakout Day`
  4. `Typical Day / Trading Range / Sideways`
  5. `Expanded Typical Day`
  6. `Rejection / Absorption Regime`
  7. `In Range / In Value`
  8. `Out of Range / Out of Value`
  9. `In Range / Out of Value`
- **Reported Columns**: `Total Trades`, `Wins / Losses / BE`, `Win Rate` (`wins / totalClosed * 100` with breakevens retained in denominator), `Profit Factor`, `Net Return %`, `Expectancy %`, and `Avg Win % / Avg Loss %`.
- **Top Edge Live Highlight**: A prominent banner dynamically identifies the regime with the greatest number of winning trades: `🏆 MAX WINS: {label} ({wins}W • {wr}% WR)`.
- **Composite Total Row**: Summarizes aggregate performance across all regimes.

---

## Verification Summary
- **Live F&O Verification**: All 4 tabs populated with live and EOD data (`LONG BUILDUP`: 3, `SHORT BUILDUP`: 18, `LONG UNWINDING`: 5, `SHORT UNWINDING`: 4).
- **Option Chain Speed**: Verified active MCX commodity strikes render in < 490ms.
- **TypeScript & Production Build**: Next.js compiled cleanly with zero errors.
