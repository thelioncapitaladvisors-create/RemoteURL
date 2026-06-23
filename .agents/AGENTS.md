
## Strict Adherence to Backend Time/Date Logic (Yahoo Helper)
- Do NOT implement custom or fallback time/date filtering logic on the frontend (like converting 'Today' to 'Rolling 24 Hours' or 'Last 50 trades') just to populate empty states.
- The backend already utilizes Yahoo Helper functions to accurately dictate market sessions, close times (e.g. EOD closing), and data validity. If a list like 'Today\'s Best Markets' displays 0 trades, it accurately reflects that no trades have closed during the current session according to the backend's strict logic.
- Do not deviate from or optimize existing structural logic without explicit user consent. The focus should be on building the algo trading framework rather than getting stuck in UI optimization loops.

## Timezone-Aware Date Mapping for Frontend "Today"
- When evaluating "Today" on the frontend (e.g., "Today's Best Markets"), DO NOT use `new Date().toISOString().split('T')[0]` (which forces UTC) or local midnight (`setHours(0,0,0,0)`).
- ALWAYS map "Today" to the specific market's timezone:
  - `IN` / `MCX` -> `Asia/Kolkata`
  - `US` / `WORLD` -> `America/New_York`
- Format the current time and the signal's time (`created_at` or `signal_ts`) using `Intl.DateTimeFormat` with the appropriate market timezone to compare if they fall on the same calendar day for that specific market.

## Trailing Stop Loss & slowEMA Pine Script Logic
- The Pine Script uses Break Even logic to trail the stop loss (SL). 
- At TP1, SL moves to Entry. At TP2, SL moves to TP1. At TP3, SL moves to TP2.
- **IMPORTANT**: When TP4 is triggered, SL must move to TP3. After TP4, the Trailing SL visually snaps to and tracks the `fMed_EMA` (slowEMA).
- The backend `route.ts` failsafe currently evaluates fixed TP steps and does NOT have the OHLC capacity to calculate EMAs on the fly, so it mimics the stops up to TP3. If true EMA parity is required in the backend failsafe in the future, EMA math must be injected directly into the `fetchYahooOHLC` process.

## Pine Script State Tracking & Structural Colors (Learnings)
- **The Amnesia Bug**: Pine script `line.new()` objects store colors visually, but if multiple lines (e.g. support and resistance) are stored into a shared variable array of `float`s (like `sr01` - `sr15`), the `float` variable loses all context of the color. It's just a price number. The math function `isValidBounceUp` cannot "see" the line color, leading to bullish trades firing off red resistance lines.
- **The Solution**: Avoid sharing `float` arrays for conceptually different lines. Use explicit separate arrays (e.g., `sup01` - `sup15` for green supports, and `res01` - `res15` for red resistances).
- **Using Existing Color Logic as Trade Filters**: If breaking up arrays requires too much refactoring, use the exact mathematical logic that determines the color (e.g., `(emaStep3 > emaStep4)`) as a structural `bool` filter directly in the trade entry condition (e.g., `isGreenStructure = ... ; StepUp = ... and isGreenStructure`). This forces the signal to respect the color's mathematical intent without needing to rewrite array variables.

## Pine Script Alert Frequency & State Latching
- **The Intrabar Amnesia Bug**: If you use `var` state-latching variables (like `isClosed := true` or `hasHitEntry := true`) combined with `alert.freq_once_per_bar_close`, TradingView will discard your alerts. The entry condition evaluates to `true` intrabar and sets the latch. At the bar close, the script re-evaluates, but because the latch is already set, the `if` block is bypassed. Since `alert()` is not executed precisely on the closing tick, the pending alert is silently dropped.
- **The Solution**: Always use `alert.freq_all` when wrapping alerts inside an `if` block that uses state-latching flags. The flags will prevent the alert from spamming, and `freq_all` ensures it fires immediately.

## Pine Script Stop Loss Delay Bug
- **Hardcoded Cooldowns**: Be extremely careful about hardcoding bar delays like `(bar_index - trade.startBarIndex) >= X` into Stop Loss logic. This math artificially prevents a Stop Loss from being recognized until X full candles have closed. If a wick blows through both Entry and Stop Loss on the same candle, the script will completely ignore the SL and keep the trade open indefinitely.

## Webhook Silent Failures & Syntax Errors
- **The Bug**: If the Netlify background webhook processor (`process-webhook-background.js`) contains a JavaScript syntax error (e.g., `u0026u0026` replacing `&&`), it will crash upon initialization. However, because TradingView webhooks are received by a front-line relay (`webhook.js`) that instantly returns `200 OK`, TradingView will show the webhook as "successfully delivered" with a green checkmark.
- **The Solution**: When webhooks appear successful in TradingView but no data appears in the Supabase database, always check the background processor for syntax errors or crashes that prevent it from running. Do not assume a `200 OK` in TradingView means the database insertion succeeded.

## EOD Failsafe & Timezone Bugs
- **The Bypassed EOD Bug**: When forcing trades to exit at EOD via Yahoo OHLC data, be careful that trades that hit earlier targets (like TP1) aren't bypassing the EOD close. If a trade hits TP1 and sets its `outcome` to `'WIN'`, a generic `if (!outcome && EOD)` check will fail because `outcome` is no longer falsy. EOD exit conditions must take absolute precedence over trailing targets.
- **The UTC Rollover Bug**: Never determine the "last candle of the day" by comparing UTC dates (`nextTs.getUTCDate() !== currentTs.getUTCDate()`). This causes the day to roll over arbitrarily based on UTC midnight (e.g., 05:30 AM IST). Always format timestamps to the local market timezone (`toLocaleDateString` with specific `timeZone`) and compare the local calendar dates instead.
- **The UTC Minute Math Bug**: When converting local times into UTC minute offsets (e.g. `timeInMins >= 10 * 60 + 15`), double check the timezone math. 3:45 PM IST is 10:15 UTC (`10 * 60 + 15`), NOT `15 * 60 + 45`.
