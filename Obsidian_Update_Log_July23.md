# Version 1.5.0 Update Log - July 23, 2026

## 🛠️ Critical Bug Fixes & Feature Enhancements

### 1. Netlify Background Function TDZ ReferenceError Fix (`isPivotUpdate`)
- **Root Cause**: In commit `b4a82ba`, the recency guard line was updated to `if (!isExitOrUpdate && !isPivotUpdate)`. However, `isPivotUpdate` was declared with `const` further down on line 383.
- In Node.js ES6+, accessing a `const` or `let` variable before its declaration line triggers a **Temporal Dead Zone (TDZ) `ReferenceError: Cannot access 'isPivotUpdate' before initialization`**.
- Because the relayer `webhook.js` instantly returned `200 OK` to TradingView, TradingView reported webhooks as delivered. However, `process-webhook-background.js` crashed silently on every alert before writing to Supabase, halting signal ingestion since last night.
- **Fix**: Reordered variable declarations in `process-webhook-background.js` so `calcOpeningBias`, `calcDayType`, and `isPivotUpdate` are evaluated prior to the `SIGNAL RECENCY GUARD` block. Signal ingestion restored 100%.

---

### 2. Automatic Telegram Channel Notifications for HUB Trades
- **New Trade Entries**: Dispatches structured Telegram alert cards formatted with Symbol, Direction (`LONG/SHORT`), Entry, Stop Loss, Target, Opening Bias, and Day Type.
  ```markdown
  🚨 *CRUDEOIL* - *LONG*
  📍 *Entry*: `6450` | *SL*: `6400` | *TP*: `6550`
  🎯 *Bias*: `BULLISH` | *Day*: `TREND`
  📝 New trade signal detected.
  ```
- **Trade Close / Outcomes**: Automatically dispatches live trade close notifications to the Telegram channel with emoji indicators (`🎯 WIN`, `❌ LOSS`, `⚖️ BREAKEVEN`), Realized Exit Price, Status (`Hit TP1`, `Hit B/E`, etc.), and Exact PnL `%`.
  ```markdown
  🎯 *TRADE CLOSED* — *CRUDEOIL*
  📊 *Outcome*: *WIN* (`+1.55%`)
  📍 *Exit Price*: `6550` | *Entry*: `6450`
  🏷️ *Status*: `Hit TP1`
  ```
- **Trailing SL Adjustments**: Notifies the channel whenever a trailing stop loss is adjusted or locked into breakeven.
  ```markdown
  📈 *TRAILING SL UPDATED* — *CRUDEOIL*
  🛡️ *New Trailing Stop*: `6450`
  📝 Trailing stop level locked.
  ```
- **Dual Dispatcher Integration**: Implemented in both Netlify serverless background worker (`process-webhook-background.js`) and Next.js mobile API route (`route.ts`).

---

### 3. Enhanced HUB Trade Card Share Formatting
- **Mobile App (`page.tsx`)**: Upgraded `handleShare` text formatting on HUB trade cards to generate Telegram-friendly structured markdown text with entry, target, stop loss, outcome status, and website link when sharing via native share sheet or social channels.

---

### 4. Repository & Submodule Synchronization
- **`TLCS_Website_Deploy`**: Committed and pushed commit `c25ddd3` to `main`.
- **`Tv-Alert-Mobile`**: Committed and pushed commit `e65400c` to `main`.
- **Root Repository**: Updated submodule pointers and pushed commit `6d32748` to `main`.
