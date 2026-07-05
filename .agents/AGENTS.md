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
- Prioritize keys sent by the TradingView indicator (`opening_bias` and `day_type`) on the backend and frontend. However, if these primary keys are missing or empty (`--`/`""`), it is permitted to silently trigger the mathematical fallback script (`fetch-tv-fallback`) on the frontend to calculate and inject these values based on daily/intraday price data.
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
- Do NOT use `exact_pct` (positive or negative) as a fallback to guess WIN/LOSS for trades that lack a definitive string status/outcome (e.g. trades closed via EOD, EMA, or TRAIL). This will falsely categorize them. They should return `OPEN` (active) until definitively categorized.
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

## Vercel Deployment Protocol (Mobile App)
- Changes pushed to the `thelioncapital-alerts` repository (for `market-store.online`) may not always automatically trigger a Vercel deployment.
- If a recent commit is not reflecting on the live mobile app, manually verify the last deployment timestamp on the Vercel Dashboard and trigger a redeploy if necessary.

## Standard Strategy Filters
- The 6 standard strategy filters (`LONG MISSILE`, `SHORT MISSILE`, `LONG SCALP`, `SHORT SCALP`, `LONG LIGHTNING`, `SHORT LIGHTNING`) are permanently hardcoded in the INSIGHTS tab of the mobile app to ensure they remain visible even on days with 0 active trades.
