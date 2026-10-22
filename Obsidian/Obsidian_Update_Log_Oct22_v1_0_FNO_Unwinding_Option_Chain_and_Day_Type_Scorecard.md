# Obsidian Update Log: Version 1.0 F&O Unwinding, Option Chain Acceleration & Day Type Scorecard
**Date**: October 22, 2026  
**Status**: Completed & Verified  

## Key Enhancements
1. **F&O Derivatives Unwinding Mapping**: Mapped 30 liquid F&O universe equities to authentic DhanHQ Stock Futures Security IDs (`futSecId` under `NSE_FNO` / `FUTSTK`). Both live feeds and EOD fallback calculate genuine Open Interest variations, fully populating Long Unwinding and Short Unwinding categories.
2. **Commodity Option Chain Latency Optimization**: Purged expired MCX contracts and pinned verified active front-month scrips (`573422` for Crude Oil, `570750` for Natural Gas). Added in-memory caching (`activeScripCache`) and resolved Netlify exceptions, cutting load times from >15s timeouts to <490ms.
3. **Day Type & Market Regime Performance Breakdown Table**: Integrated a forward-tested performance scorecard on the `INSIGHTS` tab filtering closed trades from the Oct 20 baseline, tracking Win Rate (retaining breakevens in denominator), Profit Factor, Expectancy, and featuring dynamic `🏆 MAX WINS` top-edge highlight.
4. **Supabase EOD Snapshot Synchronization**: Populated `fno_eod_snapshots` and `system_config` with verified 4-category market data.
