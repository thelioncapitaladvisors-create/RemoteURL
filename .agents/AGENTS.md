## Version 1.0: Exact Percentage Math IS THE SINGLE SOURCE OF TRUTH (DEPRECATION OF R-MULTIPLE)
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

## Exact Exit Level Badging
- The UI must NOT render generic strings like "TP HIT" or "TP1" in outcome badges (such as the badge next to the strategy name) for `WIN` trades.
- For all winning trades, the UI logic must dynamically deduce and display the exact numeric exit price (e.g. `64,416.14`) in the badge using the same mathematical extraction logic applied to the `EXITED AT` metric.

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

## Intra-Day Ghost Limit Order Deduplication
- The Pine Script engine can occasionally fire multiple webhooks for the same limit order setup on the same day, creating duplicate rows in the database.
- Since only the latest executed row receives the `TradeClose` or `TradeUpdate` webhook, the older unexecuted limit order rows become permanently stuck as `OPEN` with `!updated_at` (Ghost Limits).
- Because they occurred "today", the midnight expiration rule does not catch them. The UI engine must aggressively deduplicate these intra-day ghost limits by explicitly hiding any unexecuted limit order if there is a *newer* signal (or a duplicate with a higher ID) for the exact same symbol.
