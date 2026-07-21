## Version 1.4.0: System Architecture & Single Source of Truth Rules
- As of Version 1.0, we have globally deprecated all `r_multiple` and TradingView-provided `outcome_pct` parsing.
- **NEVER** attempt to extract, parse, or rely on `r_multiple` or `profit_pct` coming from the webhook body payload for performance metrics. 
- ALWAYS use the exact percentage method: `((Exit - Entry) / Entry) * 100`. This exact math is automatically injected by the backend webhook into the Supabase JSONB column at `metadata.exact_pct` upon trade closure.
- The entire web dashboard (`index.html`, `scanner.js`, `commodity-scanner.js`) and the mobile app (`page.tsx`) rely strictly on this `exact_pct`.
- When calculating Profit Factor, Expectancy, Win Rate, Best Trade, and Max Drawdown, base ALL metrics strictly off the Exact Percentage values, regardless of whether the user is in "Novice Mode" or "Pro Mode".

## Exit Categorization (Rigid vs Dynamic Exits)
- Do NOT bucket trades into static levels (e.g., "TP3" or "TP4") based on the highest level they *touched*. This corrupts the data because it hides the actual realized exit.
- A trade belongs in a `TP` bucket ONLY if it *actually closed* at that exact level (e.g., via a limit order, or a step-based trailing stop that precisely locked in that previous level).
- For arbitrary, continuous trailing stops that close between defined levels, do NOT mathematically guess the closest level. The Pine Script should explicitly send `"status": "Trailing Stop"`.
- Both the Web and Mobile UIs have a dedicated `TRAIL` (or `Trailing Stop`) bucket to correctly categorize these dynamic, arbitrary exits without polluting the fixed `TP` buckets.

## Symbol Normalization and Market Categorization
- ALWAYS normalize symbol names before performing market category checks (e.g., strip exchange prefixes like `NSE:`, `TVC:`, and continuous suffix `1!`). Use the normalized/cleaned symbol for list-based matching.
- Multi-market overlap: Some symbols (such as indices like `NIFTY`) theoretically belong to multiple categories (e.g., domestic equities and world indices). However, to avoid double-counting, ALWAYS assign a trade to exactly ONE primary category (e.g. by using the `getMarket` function and strictly filtering by `getMarket(s) === m.id`). Do NOT populate a single trade into multiple tabs simultaneously.

## Strict Bias and Day Type Parsing
- Prioritize keys sent by the TradingView indicator (`opening_bias` and `day_type`) on the backend and frontend. NO artificial or fictitious guesswork is permitted as a fallback on the website or the mobile application. Rely exclusively on the alert JSONs. Do not implement scripts (like `fetch-tv-fallback`) or perform lookups on previous signals to inject missing values.
- Only apply cosmetic label replacements on the frontend UI:
  - Map `"Double Distribution"` to `"DD"` (and `"Double Distribution Trend"` to `"DD Trend"`) to match the dashboard conventions.
- Maintain column sizing for table containers (`min-width: 180px` for Bias and `min-width: 160px` for Day Type) on the scanner pages to prevent longer text labels from truncating or wrapping.


## Global Market Symbols Memory
This is the definitive truth for symbol-to-market mappings. ALWAYS refer to these sets when categorizing markets or setting up filters.
- **nifty**: ADANIENT, ADANIPORTS, APOLLOHOSP, ASIANPAINT, AXISBANK, BAJAJ-AUTO, BAJAJFINSV, BAJFINANCE, BHARTIARTL, BPCL, BRITANNIA, CIPLA, COALINDIA, DIVISLAB, DRREDDY, EICHERMOT, GRASIM, HCLTECH, HDFCBANK, HDFCLIFE, HEROMOTOCO, HINDALCO, HINDUNILVR, ICICIBANK, INDUSINDBK, INFY, ITC, JSWSTEEL, KOTAKBANK, LT, LTIMindtree, M&M, MARUTI, NESTLEIND, NTPC, ONGC, POWERGRID, RELIANCE, SBILIFE, SBIN, SHRIRAMFIN, SUNPHARMA, TATACONSUM, TATAMOTORS, TATASTEEL, TCS, TECHM, TITAN, ULTRACEMCO, WIPRO
- **mcx**: ALUMINIUM, ALUMINIUMM, COPPER, COTTON, CRUDEOIL, CRUDEOILM, GOLD, GOLDM, GOLDPETAL, LEAD, LEADMINI, MENTHAOIL, NATURALGAS, NATURALGASM, NICKEL, NICKELMINI, SILVER, SILVERM, SILVERMIC, ZINC, ZINCMINI
- **nymex**: CL, GC, HG, HO, NG, PA, PL, RB, SI
- **crypto**: ADAUSDT, APTUSDT, ARBUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT, ETHUSDT, FILUSDT, ICPUSDT, LINKUSDT, LTCUSDT, NEARUSDT, POLUSDT, SHIBUSDT, SOLUSDT, STXUSDT, TONUSDT, TRXUSDT, UNIUSDT, XLMUSDT, XRPUSDT
- **forex**: AUDCAD, AUDINR, AUDJPY, AUDNZD, AUDUSD, CADJPY, EURAUD, EURCAD, EURCHF, EURGBP, EURINR, EURJPY, EURUSD, GBPAUD, GBPCAD, GBPCHF, GBPINR, GBPJPY, GBPUSD, JPYINR, NZDUSD, USDCAD, USDCHF, USDINR, USDJPY
- **world**: AU200, DE40, EU50, FR40, HK50, JP225, NAS100, SPX500, UK100, US2000, US30

## Supabase Metadata Stringification
- Supabase sometimes returns the `metadata` JSONB column as a raw stringified JSON string instead of an object on the frontend.
- When retrieving `metadata` anywhere on the frontend (e.g. `s.metadata.exact_pct`, `s.metadata.day_type`, `s.metadata.opening_bias`), you MUST defensively parse it first.
- ALWAYS use this pattern before accessing keys inside metadata:
  ```javascript
  let meta = s.metadata || {};
  if (typeof meta === 'string') {
      try { meta = JSON.parse(meta); } catch(e) { meta = {}; }
  }
  ```
- Failure to do this will cause silent UI failures (e.g. Day Type and Bias fields turning blank or into `--`) and calculation fallback errors.
## Safe Date Parsing and Formatting
- Always sanitize timestamps before parsing them or passing them into `Intl.DateTimeFormat`.
- If a Date object is instantiated from an empty, null, or corrupted string, it becomes an `Invalid Date`.
- Passing an `Invalid Date` to `Intl.DateTimeFormat.formatToParts()` causes a fatal `RangeError: Invalid time value` that halts all Javascript execution on the page and causes silent UI hangs (like getting stuck on "Analyzing..." loaders).
- Always safeguard against this by verifying the validity of the Date object immediately:
  ```javascript
  let sigTime = new Date(s.created_at);
  if (isNaN(sigTime.getTime())) return false; // Or provide a safe default
  ```

## Supabase v2 Javascript Client Syntax
- When building queries using the Supabase Javascript client, you MUST place `.select()` BEFORE any filter methods (like `.eq()`, `.gte()`, `.ilike()`, etc).
- Incorrect: `client.from('table').gte('column', value).select('*')` (Will throw `TypeError: client.from(...).gte is not a function`)
- Correct: `client.from('table').select('*').gte('column', value)`
- This is a strict requirement of the PostgREST query builder in Supabase JS v2.

## "Today's Trades" and Scanner Time Boundaries
- ALWAYS use the `0 Hrs` strict local boundary (e.g. `startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()`) to determine "Today's trades" across all dashboards, metrics, and scanners.
- Do NOT use `globalStartOfWeekISO` or arbitrary time-zone math when computing daily metrics or populating daily scanner lists.
- For AI Scanner pages specifically: they should strictly filter signals to `sigTs >= startOfToday`. Do not show past signals from earlier in the week.
- For active trades logic (dashboards/metrics): Yesterday's open trades must persist as open for today unless they are explicitly closed by their market close time. Always check `if (resolveOutcome(s) === 'OPEN') return true;` to ensure active trades from previous days are not prematurely hidden.

## resolveOutcome Fallback Guidelines
- You MUST use `exact_pct` (positive or negative) as a fallback to categorize WIN/LOSS for trades that lack a definitive string status/outcome (e.g. trades closed via EOD, EMA, or TRAIL). If `exact_pct` > 0, return `WIN`. If `exact_pct` < 0, return `LOSS`.
- If using `exact_pct` for legacy outcome resolution, you MUST handle `exact_pct === 0` by explicitly returning `BREAKEVEN` so they do not fall through to incorrect categories.

## Terminology & Page Name Mappings (V3 Optimization Journey)
- **Website Navigation**:
  - `metrics.html` is referred to as the **AI Research** page.
  - `index.html` is referred to as the **AI Dashboard**.
  - `scanner.html` was previously the AI Scanner / Alerts Scanner.
- **Mobile App Tabs (`page.tsx`)**:
  - Dashboard Tab (`id: DASHBOARD`) is labeled as **HUB**.
  - Alerts Tab (`id: ALERTS`) is labeled as **LOGS**.
  - Analysis Tab (`id: ANALYSIS`) is labeled as **MARKETS**.
  - Insights Tab (`id: INSIGHTS`) remains **INSIGHTS**.


## Standard Strategy Filters
- The 6 standard strategy filters (`LONG MISSILE`, `SHORT MISSILE`, `LONG SCALP`, `SHORT SCALP`, `LONG LIGHTNING`, `SHORT LIGHTNING`) are permanently hardcoded in the INSIGHTS tab of the mobile app to ensure they remain visible even on days with 0 active trades.

## Strict Prohibition on Unilateral Logic & Fallback Changes
- Do NOT introduce any "artificial fallback logic" (e.g., mathematically guessing exit prices, guessing missing parameters) unless explicitly requested by the user. If the data from the source (e.g., TradingView payload) is missing, fail gracefully or leave it blank, but do NOT write scripts to arbitrarily guess values.
- Do NOT unilaterally alter established business logic, categorizations, or definitions (e.g., moving symbols like NIFTY out of the WORLD index if they were previously there) without explicit prior approval from the user.
- If an optimization or feature request seems to require fundamentally changing how data is parsed, categorized, or handled, you MUST stop and ask the user for permission and explain the proposed architectural shift before writing the code.

## Hold Duration & "Real Trade" Timestamps
- When calculating Hold Duration or displaying timestamps on the UIs, NEVER base calculations on the limit trade entry time (`signal_ts`). Always prioritize `created_at` (the actual time the webhook fired and the real trade was executed).
- For Exit times, prioritize `exit_at` or `updated_at`, but if a trade opens and closes in the exact same webhook (rendering `exit_at` missing/null), you MUST gracefully fallback to `created_at` so that a valid 0-minute or <1m hold duration is calculated and exit dates are rendered instead of displaying `--`.

## Pine Script JSON & Exact Percentage Math (Version 1.1)
- Always enforce that Pine Script webhooks send clean numeric parameters (using `format.mintick` on all prices) and explicitly provide a `"trigger":"TradeClose"` property in the payload.
- The backend should strictly calculate percentages using pure entry/exit math. The backend must NEVER fall back to parsing legacy strings like `profit_pct` or `r_multiple` to mathematically determine an exit price. The Pine Script must bear the sole responsibility of transmitting explicit levels.

## Late Fill & EOD Trailing Exit (TP1 Force)
- Limit signals filled within the last 2 hours of the regular market session (`time_close("D", session.regular) - time <= 7200000`) must be explicitly tagged as a "Late Fill".
- Late fills forcefully exit 100% of their remaining position at TP1.
- Standard and EMA Trailing stop mechanisms must be unconditionally disabled for Late Fill trades to prevent unpredictable overnight gap exposure.

## Intra-Candle Reversal Safeguard (Darth Maul Rule)
- When TP1 is hit within the current candle (`justHitTP`), the engine immediately moves the SL to breakeven.
- To avoid Pine Script's inherent intra-candle high/low ambiguity, the script must check the candle's `close` price against the new breakeven SL (instead of checking `low` or `high`).
- If the candle wicks TP1 and violently reverses to close below breakeven on the exact same bar, the engine forcefully terminates the trade.

## Granular Exit Labeling (No Generic 'Hit SL')
- The Pine Script must definitively label the specific mechanism of exit in the `status` string instead of a generic "Hit SL".
- The string should be mapped to precise conditions: e.g., `"Hit Initial SL"`, `"Hit B/E"`, `"Hit TP1 Trailing"`, `"Trailing Stop"`, `"Hit EMA"`, `"Divergence Exit"`, `"Invalidated"`, or `"EOD Exit (TP1)"`. 
- This removes all ambiguity on the backend and ensures that the exact reason for the mathematically derived WIN/LOSS/BREAKEVEN categorization is explicitly recorded and displayed in the UI logs.

## Strict Prohibition on Artificial Logic (No Continuous Trailing SL)
- The system must remain utterly rigid. NEVER introduce artificial backend logic to forcefully overrule definitively granular Pine Script strings (e.g., `"Hit B/E"`, `"Hit TP1 Trailing"`).
- The exact mathematical percentage (`exact_pct`) is ONLY to be used as a backend fail-safe fallback for ambiguous labels.
- **Continuous Trailing SL Deprecation**: The strategy engine permanently relies on mathematically exact rigid levels (Breakeven, TP1, TP2, TP3) or the EMA boundary. The "Standard Distance-Based Trailing SL" block (`trailLevel := high - trailRange`) has been permanently deleted from the Pine Script architecture and should not be reintroduced.

## UI Dynamic State Presentation
- **Active Trade Targets**: When a trade is `ACTIVE`/`OPEN` and has no exit price, the UI MUST NOT display a blank or `---` "EXITED AT" box. Instead, dynamically flip the box to display the upcoming Take Profit level (labeled "TARGET" in amber styling). It should only flip to a green "EXITED AT" box upon trade closure.
- **Risk to Reward Formatting**: The Risk:Reward ratio must always be suffixed with `R` (e.g., `2.00R`) across all UI elements, web dashboards, and mobile views. Never append a percentage `%` to a multiplier ratio.

## Strict Webhook Time-Binding and Zero-Guesswork DB Updates
- **No Artificial Backend Searching**: The backend must NEVER attempt to artificially guess or locate an open trade using ambiguous fuzzy matching (e.g., `.eq('symbol', symbol).in('status', ['OPEN', 'Active'])` alone). 
- **Time-Binders are Mandatory**: All webhook update queries (`TradeClose`, `TrailingSLUpdate`) MUST definitively uniquely target the active trade by binding it to the time explicitly provided in the JSON payload (e.g., `entryTime`, mapped to `.eq('signal_ts', payload.entryTime)` or via `activeSignal.id`). 
- **Exact Payload Math**: No "backend support" or artificial lookup logic is permitted to mathematically determine metrics if the JSON payload strictly provides the necessary values (e.g., `entryPrice`, `closePrice`). The pure entry/exit math is performed definitively using these values, and the `update` query MUST directly target the time-bound ID to avoid inadvertently overwriting multiple open positions for the same symbol.

## Universal Metric Sync & Mathematical Fallbacks (Web vs Mobile)
- **Supabase Query Integrity**: The Web Dashboard (`dashboard.html`) and external scripts (`trade-metrics.js`) MUST always strictly include all mathematical boundaries (`target`, `tp2`, `tp3`, `tp4`, `trail_sl`) in their `.select()` queries. Failing to fetch these fields completely destroys the Profit Factor fallback engine for legacy trades or trailing exits.
- **Universal Status Mapping**: Both the Mobile app (`page.tsx`) and the Web Dashboard (`dashboard.html`) must handle ambiguous statuses (e.g. `UNKNOWN`, `CANCEL`) perfectly identically. They must map to `CANCELLED` and be gracefully filtered out of closed trade metrics rather than breaking the state parser.
- **UI Mathematical Fallback**: The UI must NEVER rigidly default to printing `---` just because the `exit_price` column in the database is strictly null (which occurs heavily on legacy webhooks). The UI layer MUST proactively use the underlying `getExactPct` mathematical engine logic to deduce the exit price (by pulling `trail_sl`, `stop`, or the appropriate `TP` target based on the status string) and dynamically inject that calculated value into the `EXITED AT` visual card.

## UI Persistent Market Rendering
- Dashboards and Web Scanners must persistently display all defined market categories (NIFTY, MCX, NYMEX, Cryptocurrency, Global Forex, World Indices) by default. 
- If a market has 0 active or closed trades for the day, the engine must NOT hide or skip rendering the section. It must gracefully render the UI with `0` or `--` metrics.

## Dynamic Payment Localization
- **International vs Domestic Gateways**: The website must dynamically display region-specific payment methods based on the visitor's IP location via `localization.js`. 
- **Indian Traffic**: Must see Razorpay Standard (Card/Intl) and Razorpay UPI buttons. PayPal buttons must remain strictly hidden.
- **International Traffic**: Must see Razorpay Standard (Card/Intl) and PayPal buttons. The script must explicitly hide UPI buttons.
- Pricing tables must automatically toggle between INR (`₹`) and USD (`$`) equivalents.

## Indicator Branding (V3 Standards)
- **Beginner Plan**: TLCS Standard Pivots Indicator
- **Pro Plan**: TLCS Day Type and Opening Bias Indicator
- **Premium Plan**: TLCS Live Alerts Indicator
- **Elite Plan**: TLCS Custom Alerts Indicator

## Pure Exit Level Badging (No Numeric Prices)
- The UI must strictly render the resolved **Level Label** (e.g. `TP1`, `TRAIL (TP2)`, `EOD`, `SL`) in the outcome badges next to the strategy name. 
- The UI MUST NOT dynamically deduce or append the exact numeric exit price (e.g. `64,416.14`) to the badge text under any circumstances. Stick strictly with level labels only.

## Strict UI Misleading Label Override
- When rendering legacy generic labels like `ACTIVE LIMIT`, `ACTIVE`, or `OPEN`, the UI MUST strictly override these if the trade definitively has a resolved outcome (WIN, LOSS, or BREAKEVEN).
- The `isMisleading` function must forcefully identify these legacy open labels as misleading if the underlying trade is closed, to ensure closed trades properly display `SL` or `B/E` instead of indefinitely hanging as `ACTIVE LIMIT`.

## Expired Limit Order Filtration & Unexecuted Close Fallbacks
- A Limit Order is distinctly defined as an `OPEN` trade that lacks an `updated_at` timestamp.
- Limit Orders from previous days MUST be aggressively purged from all active metrics (including `activeSignals`, `activeAlertLogs`, `todaySignals`, and website market snapshots).
- Failing to aggressively hide them causes an artificial inflation of "ACTIVE LIMITS" over time. The condition `!signal.updated_at && !isToday` MUST return false when filtering `OPEN` trades.
- **Unexecuted Closure Safety**: If an unexecuted Limit Order is manually closed, expired, or cancelled in TradingView (sending a TradeClose webhook with `status: 'CLOSED'`, `'EXPIRED'`, or `'COMPLETED'`), the backend webhook will NOT set `updated_at`. To prevent `resolveOutcome` from mathematically failing and categorizing these unexecuted closed trades as `'OPEN'` (which forces the UI to render them as `'ACTIVE LIMIT'`), the `resolveOutcome` engine MUST explicitly catch `'CLOSED'`, `'EXPIRED'`, and `'COMPLETED'` and aggressively fallback to returning `'CANCELLED'`.

## EOD, EMA, and Trail Mathematical Fallback
- Legacy trades or setups that exit via EOD (End of Day), EMA, or TRAIL exits do not inherently provide an `exit_price` or `exact_pct`.
- To prevent these trades from indefinitely hanging as `OPEN`, the `getExactPct` mathematical engine must explicitly check for `EOD`, `EMA`, and `TRAIL` within the status string and aggressively fall back to computing the exit percentage using `trail_sl` or `stop`.

## Strict Prohibition on Deduplication Logic
- Our application NEVER faces deduplication issues because every single trade is definitively time-bound.
- There is zero risk of duplication or new trades leading to the corruption of old trades.
- DO NOT artificially attempt to deduplicate limits, hide "ghost limits," or prune trades based on newer IDs or identical symbols. 
- The real root cause of "inflated Active Limits" comes from Unexecuted Closure Safety (failing to handle CLOSED/EXPIRED strings in `resolveOutcome`) and Market Closure Hiding (failing to prune `!updated_at` limit orders after 15:30 IST / 23:30 IST).

## Strict Timezone and Local 0 Hrs Boundaries (Split-Timezone Bug)
- When calculating `isThisWeek` or any daily/weekly boundaries, NEVER apply arbitrary isolated timezones (like `America/New_York` to US markets and `Asia/Kolkata` to Indian markets) within the same calculation loop.
- Doing so creates a "Split-Timezone Reality" on Monday mornings, where Indian markets correctly wipe their trades for the new week, while US markets erroneously retain all 110+ trades from the previous week, causing extreme distortions in Weekly Metrics.
- ALWAYS strictly enforce a universal local `0 Hrs` boundary (`startOfWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate())`) for ALL markets to ensure the slate is wiped uniformly.

## Metric Protection via resolveOutcome (Mathematical Inflation Bug)
- When computing `Today's Profit Factor` or `Weekly Profit Factor`, NEVER iterate through trades and blindly group them into "Profits" or "Losses" purely based on the raw positive/negative sign of `getExactPct(s)`.
- A bugged webhook (e.g. a SHORT trade hitting a stop loss) will mathematically return a positive percentage (since Exit < Entry). If relying on raw math, this loss is instantly placed into the Profits bucket, massively inflating the overall Profit Factor (e.g. up to 14.07).
- ALL metric generators must strictly filter and group trades by calling `resolveOutcome(s) === 'WIN'` and `resolveOutcome(s) === 'LOSS'` FIRST, and only then applying `Math.abs(getExactPct(s))` to the appropriate numerator or denominator.

## UI Bifurcation (Filtering vs Badging)
- **Bucket Filtering:** `getExitLevel(s)` MUST strictly prioritize dynamic exits (`TRAIL`, `EOD`, `EMA`, `DIV`, `B/E`) over fixed Take Profit buckets (`TP1`, `TP2`). If a trade hits a trailing stop at TP2, its bucket filter classification is rigorously **TRAIL**, ensuring it shows up when the user clicks the TRAIL filter.
- **UI Badging:** A separate `getDisplayExitLevel(s)` function MUST be used for generating the visual badge text (e.g., the badge next to the strategy name). This function extracts the *precise mathematical or mapped level* where the dynamic exit occurred.
- For trailing stops: If `status="Hit TP2 Trailing"`, the badge must render as **`TRAIL (TP2)`**. If simply `"Trailing Stop"`, the badge renders as **`TRAIL`**.
- For EOD Exits: If `status="EOD Exit (SL)"`, the badge explicitly extracts and renders **`SL`**. For `"EOD Exit (TP1)"`, the badge renders **`TP1`**. The trade still fundamentally belongs to the EOD filter bucket.

- The EOD Cron job (`eod-close/route.ts`) must never rely on a narrow, strict array of status strings (`['Active', 'OPEN', 'Open', 'Limit Order Placed']`) to fetch unexecuted limit orders, because UI re-labeling or slight webhook variations (e.g. `status="ACTIVE LIMIT"`) will cause those trades to be completely ignored by the cron, permanently inflating active counts.
- The cron query must broadly fetch all potentially active signals by checking if `outcome` is `'OPEN'` (or null) or `status` contains 'active', 'limit', or 'open' (`.or('outcome.eq.OPEN,outcome.is.null,status.ilike.%active%,status.ilike.%limit%,status.ilike.%open%')`).
- Inside the cron loop, a rigorous local implementation of `resolveOutcome` must validate that the fetched trade is *genuinely* open before processing it. This prevents the cron from improperly forcing an `EOD Exit` onto a valid `TRAIL` trade that hasn't explicitly populated the outcome column yet.

## Webhook Timestamp Precision Mismatch (signal_ts Range Query)
- TradingView sends bar open timestamps as **whole-second Unix milliseconds** (e.g. `timenow = 1753023000000` → `"2026-07-20T18:30:00.000Z"`). However, the backend stores `signal_ts` with **sub-second precision** at the moment the webhook fires (e.g. `"2026-07-20T18:30:00.140+00:00"`).
- Using an exact `.eq('signal_ts', parsedEntryTs)` match will **always fail** in this scenario because `18:30:00.000` ≠ `18:30:00.140`.
- When the lookup fails, the Netlify background function inserts a **duplicate "Hit SL" row** instead of updating the open signal, leaving the original OPEN row permanently stuck as "ACTIVE LIMIT".
- **Fix:** ALL `signal_ts` matching in both the Next.js webhook (`route.ts`) and the Netlify background function (`process-webhook-background.js`) MUST use a **±5-second range query**:
  ```javascript
  const entryMs = new Date(parsedEntryTs).getTime();
  const tsStart = new Date(entryMs - 5000).toISOString();
  const tsEnd   = new Date(entryMs + 5000).toISOString();
  query = query.gte('signal_ts', tsStart).lte('signal_ts', tsEnd);
  ```
  This applies to both `TradeClose` and `TrailingSLUpdate` blocks in both webhook handlers.

## isOutcomeUpdate Must Inspect Status Keywords (Not Just trigger Field)
- The `isOutcomeUpdate` flag in `process-webhook-background.js` MUST NOT rely exclusively on `payload.trigger === 'TradeClose'` or `payload.action === 'EXIT'`.
- TradingView Pine Script alerts sometimes omit the `trigger` field entirely and only send `"status": "Hit SL"` or similar. If `isOutcomeUpdate` is false, the handler falls through to the **new-signal insert path**, creating a duplicate ghost row instead of updating the open signal.
- **Fix:** `isOutcomeUpdate` must also inspect `body.status` for close keywords:
  ```javascript
  const isCloseStatus = statusU.includes('SL') || statusU.includes('TP') || statusU.includes('STOP')
    || statusU.includes('TARGET') || statusU.includes('CLOSED') || statusU.includes('WIN')
    || statusU.includes('LOSS') || statusU.includes('B/E') || statusU.includes('BREAKEVEN')
    || statusU.includes('CANCEL') || statusU.includes('UNKNOWN');
  const isOutcomeUpdate = triggerU === 'TRADECLOSE' || actionU === 'EXIT' || triggerU === 'EXIT'
    || triggerU.includes('TP') || triggerU.includes('TARGET') || triggerU.includes('CLOSE')
    || (isCloseStatus && triggerU !== 'TRAILINGSLUPDATE');
  ```

## resolveOutcome Must Be Identical Across All Files
- The `resolveOutcome` function MUST be **bit-for-bit identical** in these four files:
  - `TLCS_Website_Deploy/scanner.js`
  - `TLCS_Website_Deploy/commodity-scanner.js`
  - `TLCS_Website_Deploy/dashboard.html`
  - `Tv-Alert-Mobile/src/app/page.tsx`
- Specifically, ALL four implementations MUST include the VAPT/unexecuted closure safety guard:
  ```javascript
  if (st.includes('CANCEL') || o.includes('CANCEL') || st.includes('UNKNOWN') || o.includes('UNKNOWN')
      || st.includes('CLOSED') || st.includes('EXPIRED') || st.includes('COMPLETED')) return 'CANCELLED';
  ```
  Using `o === 'CANCELLED'` (exact match) instead of `o.includes('CANCEL')` is a bug — it misses the `outcome: 'CANCEL'` variant.

## One-Time DB Cleanup for Timestamp-Mismatch Ghost Records
- When the timestamp mismatch bug produces stuck OPEN records alongside duplicate "Hit SL" rows, a targeted Python cleanup script must be run to:
  1. Fetch all OPEN signals with `updated_at: null` and `outcome: null`.
  2. For each, query same-symbol signals for a closed counterpart with the same direction, entry price (within 1%), and `signal_ts` within 10 seconds.
  3. If a match is found, update the OPEN row: copy `status`, compute `exact_pct` from entry/exit math, set `outcome`, `exit_price`, `exit_at`, and `updated_at`.
- This cleanup is a **backend database maintenance operation** — it does NOT violate the Strict Prohibition on Deduplication Logic, which applies only to frontend UI rendering.

## Universal Web & Mobile Metric Synchronization Rule
- Both the Web Dashboard (`dashboard.html`, `trade-metrics.js`) and Mobile App (`page.tsx`) read from the exact same Supabase `signals` table and MUST yield 100% identical metrics down to the second decimal place.
- **Supabase Query Boundary**: Both applications MUST fetch signals without applying restrictive `.gte('created_at', ...)` database query filters that omit trades updated/closed in the current window.
- **Deduplication & Time Binders**: Both applications MUST pre-filter signals using `isRealTrade(s)` (`entry > 0` and valid trade direction) BEFORE calling `dedupeSignals` to prevent non-trade records (pivots/logs with `entry=0`) from overwriting real trades. Both MUST use `getSignalTime(s)` logic (`exit_at` -> `updated_at` (for closed trades) -> `signal_ts` -> `created_at`).
- **Chronological Metrics Sorting**: Sequential calculations (`maxDrawdown`, `consecLosses`, equity curve) MUST sort closed signals strictly using `getSignalTime(a).getTime() - getSignalTime(b).getTime()`. Sorting by raw `created_at` or unparsed OR-chains places closed trades out of order, corrupting streak and drawdown metrics.
- **resolveOutcome Protection**: `resolveOutcome` MUST NOT contain `st.includes('CLOSED')` in its early `CANCELLED` return condition, as executed trades with status `"Closed"` or `"Force Closed (Stale)"` must resolve to WIN/LOSS via `exact_pct`.
- **Board Metrics Alignment**:
  - `CLOSED TRADES`: Represents `todayClosedSignals.length` (186 closed trades for today).
  - `WIN RATE`: `(todayWins / (todayWins + todayLosses)) * 100` (45.2%).
  - `PROFIT FACTOR`: `todayGrossProfit / todayGrossLoss` (0.19).
  - `WEEKLY TRADES`: `weeklyClosedSignals.length` (226 closed trades).
  - `WEEKLY SUCCESS`: `(weeklyWins / (weeklyWins + weeklyLosses)) * 100` (41.6%).
  - `WEEKLY PROFIT FACTOR`: `weeklyGrossProfit / weeklyGrossLoss` (0.19).
  - `TLCS PROFIT FACTOR`: `overallGrossProfit / overallGrossLoss` (0.21).



## Pine Script Alert Payload Guarantee (Mandatory Entry Time Binding)
- **Hardcoded Timestamp Guarantee**: `entryTime` / `entry_signal_ts` is strictly hardcoded into every TradingView Pine Script alert payload for both entry and exit webhooks.
- Timestamp will **ALWAYS** be provided by the TradingView indicator payload on exit webhooks.
- Exit matching MUST unconditionally use `entryTime` (parsed as ms 13-digit or sec 10-digit Unix timestamp) combined with `entryPrice` as the primary, mandatory, deterministic time-binder.
- Because `entryTime` is always provided, exit signal resolution is 100% deterministic and unambiguous across all trades.

- When an exit webhook (e.g. `TradeClose` or `Hit SL`) fires, the backend MUST query for an active open signal.
- If NO active signal is found in the database, the handler MUST log a warning and return 200 OK without inserting a new row.
- **NEVER** insert a new signal row on exit webhooks when `activeSignal` is null. Inserting a new row on exit creates phantom duplicate trades with identical entry prices and entry times.

## Single Trade per Symbol at a Point in Time
- Per trading rules: It is acceptable to have multiple trades for a symbol over time across different sessions/candles, but **we cannot have multiple concurrent trades or duplicate cards for a single symbol at the exact same point in time**.
- On the frontend (`page.tsx` and `trade-metrics.js`), signal arrays MUST be deduplicated using `dedupeSignals` based on `(symbol, type, entryPrice, minuteKey)` so that duplicate signal entries or phantom rows for the same entry point are collapsed into a single card.
- On the backend, exit webhooks must never insert duplicate rows, and entry webhooks must not create concurrent active positions for the same symbol at the same time.

## resolveOutcome Must Not Hijack "CLOSED" or "FORCE CLOSED" Trades as CANCELLED
- Trades with status `"CLOSED"`, `"Trade Closed"`, `"Force Closed (Stale)"`, or `"Closed at TP1"` are valid executed closed trades, NOT cancelled trades.
- `resolveOutcome` MUST NOT check `st.includes('CLOSED')` at the top of the function to return `'CANCELLED'`.
- Check `WIN`, `LOSS`, `BREAKEVEN`, and `exact_pct` math FIRST. Only return `'CANCELLED'` if the trade was explicitly cancelled/unknown, or if it is an unexecuted limit order (`EXPIRED` / `COMPLETED`) with NO win/loss outcome.

- `trade-metrics.js` MUST define exactly **one** `window.resolveOutcome` at the top of the file. All inner function scopes (inside `loadInsightsData`, `renderTodayMarkets`, `loadPerformanceStats`, realtime listener) MUST delegate to it with `const resolveOutcome = window.resolveOutcome;`.
- **NEVER** redefine `resolveOutcome` locally inside any inner function in `trade-metrics.js`. Every time a new inner definition is added, it becomes a separate copy that diverges from future patches.
- The canonical definition MUST use `o.includes('CANCEL')` (not `o === 'CANCELLED'`) to catch all cancelled outcome string variants.

## window.todayClosedSignals Must Contain Only Closed Signals
- `window.todayClosedSignals` (used by `renderTodayMarkets` in `trade-metrics.js`) MUST be assigned from the `todayClosed` array — which is filtered by `resolveOutcome(s) !== 'OPEN'`.
- NEVER assign `window.todayClosedSignals = todaySignals` (which includes OPEN trades). This mislabeling causes the markets grid to render active limit orders as if they are closed trades.

## globalStartOfWeekISO Must Be Built from Local Midnight Milliseconds
- The weekly boundary MUST be computed using `new Date(year, month, date + dist).getTime()` to obtain a strict local-midnight millisecond timestamp.
- NEVER call `.toISOString()` directly on a `Date` object after `setHours(0,0,0,0)` — for IST (+5:30) this pushes the UTC ISO string back by 5.5 hours, leaking data from the previous week into weekly metrics.
- Safe pattern:
  ```javascript
  window.globalStartOfWeekMS = (() => {
      const d = new Date();
      const dist = d.getDay() === 0 ? -6 : 1 - d.getDay();
      return new Date(d.getFullYear(), d.getMonth(), d.getDate() + dist).getTime();
  })();
  window.globalStartOfWeekISO = new Date(window.globalStartOfWeekMS).toISOString();
  ```

## Profit Factor MUST Use resolveOutcome, Not Raw exact_pct Sign
- When computing Profit Factor (both global and per-market/strategy breakdowns), trades MUST be bucketed using `resolveOutcome(s) === 'WIN'` and `resolveOutcome(s) === 'LOSS'`. The magnitude is then `Math.abs(getExactPct(s))`.
- **NEVER** use `if (getExactPct(s) > 0)` to determine profit vs loss. A SHORT trade hitting its stop loss produces a mathematically positive `exact_pct` (since exit < entry → `(e - ex)/e > 0`). Using raw sign grouping inflates Profit Factor to 14+ on days with SHORT SL exits.
- Correct pattern (applies to `page.tsx` global PF, `marketsStats` useMemo, and `strategyInsights` useMemo):
  ```javascript
  const out = resolveOutcome(s);
  const r = Math.abs(getExactPct(s) || 0);
  if (out === 'WIN') grossProfitR += r;
  else if (out === 'LOSS') grossLossR += r;
  ```

## isRealTrade Must Exclude EXPIRED / COMPLETED / CLOSED Status
- `isRealTrade` in `page.tsx` MUST check for `expired`, `completed`, and `closed` in the status field in addition to `cancel`, `invalid`, and `unknown`.
- Failing to exclude these causes limit orders that were expired or force-closed by TradingView to pass into all metric arrays, inflating Active Limits counts and corrupting win rates.

## getSignalTime Must Fall Back to updated_at for Stale-Sweeper Closures
- DB audit (July 21) confirmed that trades force-closed by the stale sweeper cron have `exit_at = NULL` and `signal_ts` from the previous day, but `updated_at` = today.
- These trades are invisible to today's metrics because `getSignalTime` falls through to `created_at` (yesterday), placing them outside the `startOfToday` boundary.
- `getSignalTime` MUST check `updated_at` as a fallback before `signal_ts` for CLOSED trades (i.e., trades where `resolveOutcome !== 'OPEN'`):
  ```javascript
  const getSignalTime = (s) => {
      if (s.exit_at) return new Date(s.exit_at);
      const out = resolveOutcome(s);
      if (out !== 'OPEN' && s.updated_at) return new Date(s.updated_at); // stale-sweeper closures
      if (s.signal_ts) { const ts = Number(s.signal_ts); return !isNaN(ts) && ts > 1e12 ? new Date(ts) : new Date(s.signal_ts); }
      return new Date(s.created_at);
  };
  ```

## Phantom "Hit SL" Duplicate Rows — DB Audit Findings (July 21)
- Live DB query on July 21 confirmed: **21 out of 26 closed trades** had `exit_at=NULL`, `updated_at=NULL`, `exact_pct=NULL`, `outcome=null` — only `status="Hit SL"` was set.
- These are phantom duplicate INSERT rows created when the backend `isOutcomeUpdate` check fails to recognize a close webhook, falling through to the new-signal INSERT path instead of UPDATE.
- Root cause: `signal_ts` precision mismatch (TradingView whole-second vs Supabase sub-millisecond). The range query fix (±5s) in `process-webhook-background.js` and `route.ts` is the permanent solution.
- Additionally: **65 OPEN signals ALL had `updated_at=NULL`** — confirming all 65 are unexecuted stale limit orders, not live trades.

## TRAIL Status Alone Must Not Return WIN
- In the last-resort fallback of `resolveOutcome` (after `exact_pct` extraction), TRAIL status MUST NOT be mapped to `'WIN'`.
- If `exact_pct` is null for a TRAIL exit, the trade's outcome is genuinely ambiguous. Return `'OPEN'` so the trade is excluded from closed-trade metrics rather than being incorrectly counted as a win.
- Correct pattern (applies to `scanner.js`, `commodity-scanner.js`, `page.tsx`):
  ```javascript
  if ((st.includes('STOP') || st.includes('SL')) && !st.includes('TRAIL')) return 'LOSS';
  return 'OPEN'; // TRAIL with no exact_pct: defer, do not assume WIN
  ```
