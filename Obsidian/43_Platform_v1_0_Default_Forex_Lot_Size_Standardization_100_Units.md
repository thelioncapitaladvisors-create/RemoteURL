# Platform Architecture Note: Version 1.0 Default Forex Lot Size Standardization (100 Units)
**Author**: The Lion Capital Solutions (Quantitative Engineering & Research)  
**Date**: October 16, 2026  
**Status**: ACTIVE PRODUCTION  
**Release**: Version 1.0 Baseline  

---

### 1. Executive Summary & Problem Context
In the TLCS Terminal Paper Trading Simulator (`SCREENER` tab), Global Forex currency pairs (`EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `USDCHF`, `USDCAD`, `NZDUSD`, and cross/INR pairs) were previously mapped to a default mini-lot multiplier of `10,000` units (`10K Units`, equivalent to 0.1 standard lot). 

While standard in institutional FX margin accounts, this disproportionately amplified simulated Rupee P&L relative to the 1-Lot baseline of other asset classes (such as 100 shares for Indian Equities or 100 bbl for WTI Crude), causing small 0.00021-pip price movements to generate large Rupee swings (`+₹1,749` on near-flat trades).

---

### 2. Standardization Mandate: 100 Units Default
To ensure consistent, institutional micro-lot risk sizing across all asset classes, the default lot size and contract multiplier for all Global Forex pairs is strictly set to **100 Units**:
- **Market Configuration (`DEFAULT_LOT_CONFIG['forex']`)**:
  - `size`: `100` (was `10000`)
  - `symbolLabel`: `'FOREX PAIRS (100 Units)'` (was `'FOREX PAIRS (10K Units)'`)
- **Signal Multiplier Mapping (`paperSimulatedTrades`)**:
  - Forex pairs (`cleanS.length === 6` / `MARKET_SYMBOLS.forex`) and INR cross-pairs (`cleanS.endsWith('INR')`):
    - `mult`: defaults to `100` (or `Number(customLotMultiplier)` if user enters custom stepper override in the Forex tab)
    - `qtyLabel`: `'100 Units'` (or `${mult} Units`)
- **Contract / Share Quantity Selector Display**:
  - Displays `'100 Units'` when `paperMarket === 'forex'`
  - Subtitle updates to: \`Forex Pairs: 100 Units (USD to ₹ @ \${usdInrRate.toFixed(2)})\`

---

### 3. Verification & Parity
- **TypeScript Compilation**: `npx tsc --noEmit` verified with 0 errors across the application.
- **Rulebook Codified**: Updated canonical guidelines in `AGENTS.md` and `.agents/AGENTS.md`.
- **Multi-Repository Synchronization**: Committed across `Tv-Alert-Mobile`, `RemoteURL`, `TLCS_Website_Deploy`, and Root `Project`.
