# Obsidian Update Log: Version 1.6 (12 Sept 2026)
## EOD Market Session Time Binding, MCX Symbol Sync, Pine Script TradeFill Webhook Pipeline & Pivot Array Restoration

---

### 1. Overview & Key Goals
Version 1.6 delivers critical synchronization across Pine Script alert execution, Netlify serverless market sweepers, and symbol normalization:
1. **Automated EOD Market Session Close Time Binding**: Clamped automated EOD closures (`cron-eod-close.js`) to the specific session close timestamps of the trade's day (e.g., 23:30 IST for MCX, 15:30 IST for NIFTY, 21:00 UTC for NYMEX/Global), preventing weekend/midnight sweepers from polluting weekend P&L.
2. **Comprehensive MCX Symbol Synchronization**: Added `ALUMINI` and `ZINCM` across `cron-eod-close.js`, `algo_engine/sync_weekly_performance.py`, and `algo_engine/backtest_edge.py` to ensure mini contracts are correctly recognized and settled at session close.
3. **Pine Script `TradeFill` Alert Pipeline**: Implemented `sendTradeFillAlert()` in `TLCS_Live_Pivot_Alerts.pine` and `user_code.pine`. The exact moment a pending limit order executes (`wasUnfilled and trade.hasHitEntry`), Pine Script fires `TradeFill` to Netlify to instantly transition web and mobile dashboards from `ACTIVE LIMIT` to `LIVE` (`⚡ TRADE ACTIVE`).
4. **Support & Resistance Pivot Array Restoration**: Restored the exact, user-specified Support & Resistance pivot array logic (`res01..res15`, `sup01..sup15`) across all Pine indicators without artificial gating.
5. **Pine Script Compiler Health**: Fixed `signalTime` type field compiler error in `TradeLogic` and ensured deterministic `trade_id` binding.

---

### 2. Files Modified

| File | Changes Made |
| :--- | :--- |
| `TLCS_Website_Deploy/netlify/functions/cron-eod-close.js` | Added `ALUMINI` and `ZINCM` to `mcxSymbols`. Added `getSessionCloseIso()` to clamp `exit_at` and `updated_at` to the trading session's official close time. |
| `algo_engine/sync_weekly_performance.py` | Added `ALUMINI` and `ZINCM` to `mcx` market definitions. |
| `algo_engine/backtest_edge.py` | Added `ALUMINI` and `ZINCM` to `MCX` market definitions. |
| `TV Indicator/TLCS_Live_Pivot_Alerts.pine` | Added `sendTradeFillAlert()`, added `signalTime` to `TradeLogic`, restored exact user S&R pivot arrays, and wired fill event in `processTradeArray`. |
| `user_code.pine` | Added `sendTradeFillAlert()`, added `signalTime` to `TradeLogic`, restored exact user S&R pivot arrays, and wired fill event in `processTradeArray`. |
| `RemoteURL/user_code.pine` | Restored exact user S&R pivot arrays. |

---

### 3. Verification & Compliance
- **Single Source of Truth**: All percentage calculations strictly use `metadata.exact_pct` math.
- **Strict Netlify Infrastructure**: Fully compatible with Netlify serverless background workers and scheduled functions.
- **Triple-Binding Protocol**: Downstream `TradeFill`, `TrailingSLUpdate`, and `TradeClose` webhooks bind deterministically via `trade_id`.
