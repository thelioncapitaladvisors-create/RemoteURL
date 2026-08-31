## Version 1.0: System Architecture & Single Source of Truth Rules
- As of Version 1.0, we have globally deprecated all `r_multiple` and TradingView-provided `outcome_pct` parsing.
- **NEVER** attempt to extract, parse, or rely on `r_multiple` or `profit_pct` coming from the webhook body payload for performance metrics. 
- ALWAYS use the exact percentage method: `((Exit - Entry) / Entry) * 100`. This exact math is automatically injected by the backend webhook into the Supabase JSONB column at `metadata.exact_pct` upon trade closure.
- The entire web dashboard (`index.html`, `scanner.js`, `commodity-scanner.js`) and the mobile app (`page.tsx`) rely strictly on this `exact_pct`.
- When calculating Profit Factor, Expectancy, Win Rate, Best Trade, and Max Drawdown, base ALL metrics strictly off the Exact Percentage values, regardless of whether the user is in "Novice Mode" or "Pro Mode".

## Strict Netlify Hosting & Single Infrastructure Rule
- **NETLIFY ONLY**: The entire system infrastructure (Web Dashboard, Mobile App backend endpoints, Netlify background workers, and Telegram dispatchers) is hosted **EXCLUSIVELY on Netlify** (`thelioncapitalsolutions.com`).
- **NO VERCEL DEPLOYMENTS EXIST**: Do NOT reference, configure, or troubleshoot Vercel hosting, Vercel routes, or Vercel environment variables. All backend functions (`process-webhook-background.js`, `test-telegram.js`, `cron-heal-outcomes.js`) run as Netlify functions on Netlify servers.

## Market-Wise Telegram Channel Routing (Active Trades Only)
- **MARKET-WISE ROUTING**: Telegram channel notifications are distributed dynamically based on the market category of the symbol (NIFTY, MCX, NYMEX, Crypto, Forex, World Indices). The backend resolves the market and looks up the corresponding environment variable for the Chat ID (e.g., `TELEGRAM_CHAT_ID_NIFTY`, `TELEGRAM_CHAT_ID_CRYPTO`, etc.).
- **ACTIVE TRADES ONLY (No Active Limits)**: Telegram alerts must **NEVER** fire for unexecuted limit orders (`ACTIVE LIMIT` / `OPEN`). Telegram alerts fire **ONLY** when a limit trade actually fills and transitions to a **LIVE ACTIVE** executed trade (`⚡ TRADE ACTIVE`), or when an active trade updates trailing stop / closes (`TARGET` / `SL`).


## Exit Categorization (Rigid vs Dynamic Exits)
- Do NOT bucket trades into static levels (e.g., "TP3" or "TP4") based on the highest level they *touched*. This corrupts the data because it hides the actual realized exit.
- A trade belongs in a `TP` bucket ONLY if it *actually closed* at that exact level (e.g., via a limit order, or a step-based trailing stop that precisely locked in that previous level).
- For arbitrary, continuous trailing stops that close between defined levels, do NOT mathematically guess the closest level. The Pine Script should explicitly send `"status": "Trailing Stop"`.
- Both the Web and Mobile UIs have a dedicated `TRAIL` (or `Trailing Stop`) bucket to correctly categorize these dynamic, arbitrary exits without polluting the fixed `TP` buckets.
- **Strict Level vs Outcome Alignment**: If `resolveOutcome(s) === 'LOSS'` (or `exact_pct < 0`), the trade level label MUST NEVER display `TP1`, `TP2`, `TP3`, or `TP4` (even if TradingView payload sent a mismatched `"Completed TP4"` string). If `resolveOutcome(s) === 'LOSS'`, the level label MUST be `SL` (or `EMA`/`DIV`/`EOD`). Conversely, if `resolveOutcome(s) === 'WIN'` (or `exact_pct > 0`), the level label MUST NEVER display `SL` or `B/E`. (Winning trades that hit a breakeven trailing stop should be labeled as `TRAIL`). Level resolution functions (`getExitLevel`, `getDisplayExitLevel`, `outcomePill`) must enforce canonical outcome validation.

## Symbol Normalization and Market Categorization
- ALWAYS normalize symbol names before performing market category checks (e.g., strip exchange prefixes like `NSE:`, `TVC:`, and continuous suffix `1!`). Use the normalized/cleaned symbol for list-based matching.
- Multi-market overlap: Some symbols (such as indices like `NIFTY`) theoretically belong to multiple categories (e.g., domestic equities and world indices). However, to avoid double-counting, ALWAYS assign a trade to exactly ONE primary category (e.g. by using the `getMarket` function and strictly filtering by `getMarket(s) === m.id`). Do NOT populate a single trade into multiple tabs simultaneously.

## Strict Bias and Day Type Parsing
- Prioritize keys sent by the TradingView indicator (`opening_bias` and `day_type`) on the backend and frontend. NO artificial or fictitious guesswork is permitted as a fallback on the website or the mobile application. Rely exclusively on the alert JSONs. Do not implement scripts (like `fetch-tv-fallback`) or perform lookups on previous signals to inject missing values.
- Only apply cosmetic label replacements on the frontend UI:
  - Map `"Double Distribution"` to `"DD"` (and `"Double Distribution Trend"` to `"DD Trend"`) to match the dashboard conventions.
- Maintain column sizing for table containers (`min-width: 180px` for Bias and `min-width: 160px` for Day Type) on the scanner pages to prevent longer text labels from truncating or wrapping.

## Strict Prohibition on Scanner & Day Type Name Alterations
- **NEVER** introduce extra, fictitious, or variant terminology (e.g. `"Failed Breakout"`, `"Retest"`, `"Fade"`, `"Continuation"`) into scanner headers, subtitles, card descriptions, or table labels.
- The ONLY valid, canonical names for Day Type Blueprints and Sequences across the entire Web & Mobile platform are:
  - **Day Type Blueprints**: `Rejection Day Blueprint`, `Absorption Day Blueprint`, `Failed New Low Blueprint`, `Outside Day Blueprint`, `Stop Run Day Blueprint`.
  - **Trade Sequences**: `Rejection Day Sequence`, `Stop Run Sequence`, `Failed Absorption Sequence`, `Accumulation / Distribution Sequence`.
- Always keep the original names strictly intact without any alterations or variations.


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

## resolveOutcome — Canonical Implementation (Read This Fully Before Touching resolveOutcome)

> **⚠️ CRITICAL REGRESSION HISTORY — This bug has been fixed and re-broken multiple times. Read before making any change.**
>
> The root cause of every regression: `exact_pct` math was checked **after** keyword string matching. The words "B/E" and "SL" in status strings hijacked the outcome before the math was ever evaluated:
> - `"Hit B/E"` → keyword check returns `BREAKEVEN` — even though `exact_pct = +1.35%` (a WIN)
> - `"Hit Initial SL"` on a SHORT → keyword check returns `LOSS` — even though `exact_pct = +1.33%` (a WIN, since SHORT exit < entry)
>
> **The fix is permanent and must never regress: `exact_pct` math is ALWAYS checked FIRST, before any keyword string.**

### The One Canonical resolveOutcome (copy exactly to all 5 files)

This exact implementation MUST be used in **all five files**:
- `TLCS_Website_Deploy/trade-metrics.js` (as `window.resolveOutcome`)
- `TLCS_Website_Deploy/scanner.js`
- `TLCS_Website_Deploy/commodity-scanner.js`
- `TLCS_Website_Deploy/dashboard.html`
- `Tv-Alert-Mobile/src/app/page.tsx`

```javascript
function resolveOutcome(s) {
    if (!s) return 'OPEN';
    const st = (s.status  || '').toUpperCase();
    const o  = (s.outcome || '').toUpperCase();
    // Step 2: exact_pct is the SINGLE SOURCE OF TRUTH — check it BEFORE any keyword string.
    // This is mandatory. "Hit B/E" with +1.35% exact_pct is a WIN, not BREAKEVEN.
    // "Hit Initial SL" on a SHORT with +1.33% exact_pct is a WIN, not LOSS.
    let meta = s.metadata || {};
    if (typeof meta === 'string') { try { meta = JSON.parse(meta); } catch(e) { meta = {}; } }
    if (meta.exact_pct != null) {
        const pct = parseFloat(meta.exact_pct);
        if (!isNaN(pct)) {
            if (pct > 0)  return 'WIN';
            if (pct < 0)  return 'LOSS';
            return 'BREAKEVEN'; // pct === 0 is a genuine breakeven
        }
    }


    // Step 1: Hard-kill CANCELLED/UNKNOWN first — these are never WIN/LOSS
    if (o.includes('CANCEL') || st.includes('CANCEL') || st.includes('UNKNOWN') || o.includes('UNKNOWN')) return 'CANCELLED';
    // EXPIRED and COMPLETED with no exit → unexecuted limit orders → CANCELLED
    if ((st.includes('EXPIRED') || st.includes('COMPLETED')) && !s.exit_price) return 'CANCELLED';


    // Step 3: Keyword fallback — only reached when exact_pct is genuinely absent
    if (st.includes('ACTIVE') || o === 'OPEN' || st === 'OPEN') return 'OPEN';
    if (o === 'WIN'  || st.includes('WIN'))  return 'WIN';
    if (o === 'LOSS' || st.includes('LOSS')) return 'LOSS';
    // TRAIL with no exact_pct: genuinely ambiguous — do NOT assume WIN
    if ((st.includes('STOP') || st.includes('SL')) && !st.includes('TRAIL')) return 'LOSS';
    return 'OPEN'; // default: treat as still open
}
```

### What MUST NOT happen (these are the recurring regression patterns):
- ❌ `exact_pct` checked after `B/E` keyword → `"Hit B/E"` (+1.35%) becomes BREAKEVEN
- ❌ `exact_pct` checked after `SL` keyword → `"Hit Initial SL"` SHORT (+1.33%) becomes LOSS
- ❌ `TRAIL` keyword mapped to `WIN` → TRAIL with null exact_pct inflates win rate
- ❌ Locally redefining `resolveOutcome` inside inner functions in `trade-metrics.js` — creates divergent copies
- ❌ Using `o === 'CANCELLED'` instead of `o.includes('CANCEL')` — misses `outcome: 'CANCEL'` variant
- ❌ Checking `st.includes('CLOSED')` in the CANCELLED guard — `"Force Closed (Stale)"` is a real executed trade

### Self-Healing Architecture (never needs manual repair):
- `cron-heal-outcomes.js` runs every 30 minutes on Netlify and auto-corrects any row where `outcome` ≠ `exact_pct` math
- `AUTO_CORRECT_OUTCOME_TRIGGER.sql` contains a PostgreSQL trigger (apply once in Supabase SQL Editor) that enforces this at the database write level

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
  - Analytics Tab (`id: ANALYTICS`) is labeled as **ANALYTICS**.
- **Scanners**:
  - `PIVOTBOSS COMBINED SCANNER` is renamed and strictly labeled as **TLCS DAY TYPE SCANNER**. It resides on the Web Dashboard and the Analytics tab of the Mobile App.

## Push Notification Dispatch Rules
- **Scanner Aggregation**: Scanners (e.g., TLCS Day Type Scanner) send bulk JSON array payloads. The Netlify `send-push-background` dispatcher MUST parse the array and aggregate active signals to send a single summarized push notification (e.g., "3 Blueprints detected..."). It MUST NOT iterate and fire individual push notifications for every symbol.
- **Empty Scanner Guard**: If a scanner payload arrives with 0 active blueprints, the `send-push-background` dispatcher must forcefully abort and skip sending any push notifications to prevent spam.
## Standard Strategy Filters
- The 6 standard strategy filters (`LONG MISSILE`, `SHORT MISSILE`, `LONG SCALP`, `SHORT SCALP`, `LONG LIGHTNING`, `SHORT LIGHTNING`) are permanently hardcoded in the INSIGHTS tab of the mobile app to ensure they remain visible even on days with 0 active trades.

## Strict Prohibition on Unilateral Logic & Fallback Changes
- Do NOT introduce any "artificial fallback logic" (e.g., mathematically guessing exit prices, guessing missing parameters) unless explicitly requested by the user. If the data from the source (e.g., TradingView payload) is missing, fail gracefully or leave it blank, but do NOT write scripts to arbitrarily guess values.
- Do NOT unilaterally alter established business logic, categorizations, or definitions (e.g., moving symbols like NIFTY out of the WORLD index if they were previously there) without explicit prior approval from the user.
- If an optimization or feature request seems to require fundamentally changing how data is parsed, categorized, or handled, you MUST stop and ask the user for permission and explain the proposed architectural shift before writing the code.

## Hold Duration & "Real Trade" Timestamps
- When calculating Hold Duration or displaying timestamps on the UIs, NEVER base calculations strictly on the limit trade entry time (`signal_ts` or `created_at`). Always prioritize `metadata.real_entry_time` (the exact millisecond the limit order filled). Only fall back to `created_at` if `real_entry_time` is missing.
- For Exit times, prioritize `exit_at` or `updated_at`, but if a trade opens and closes in the exact same webhook (rendering `exit_at` missing/null), you MUST gracefully fallback to `real_entry_time` or `created_at` so that a valid 0-minute or <1m hold duration is calculated and exit dates are rendered instead of displaying `--`.

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
- **Strict Prohibition on UI Mathematical Fallbacks**: The UI must NEVER artificially deduce or invent an exit price (e.g. by pulling `trail_sl`, `stop`, or a `TP` target) if the `exit_price` column in the database is strictly null. The system must rely purely on empirical data recorded from the webhooks. If the exit price is missing, fail gracefully or leave it blank (e.g. `---`), but do NOT mathematically invent it.

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
- The `resolveOutcome` function MUST be **bit-for-bit identical** across all five files.
- See **"resolveOutcome — Canonical Implementation"** section above for the exact code to copy.
- Key requirements enforced by the canonical version:
  - `o.includes('CANCEL')` not `o === 'CANCELLED'` (catches `outcome: 'CANCEL'` variant)
  - `exact_pct` math checked at Step 2, BEFORE keyword strings at Step 3
  - `st.includes('CLOSED')` is NOT in the CANCELLED guard ("Force Closed (Stale)" is a real trade)

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
- **Chronological Metrics Sorting**: Sequential calculations (`maxDrawdown`, `consecLosses`, equity curve) MUST sort closed signals using `getSignalTime(a).getTime() - getSignalTime(b).getTime()`, and MUST include a `created_at` tie-breaker (`aCreated - bCreated`) when exit timestamps match. When 100+ trades share identical batch update timestamps (`updated_at`), sorting without a tie-breaker leaves pre-grouped arrays (e.g. `[...wins, ...losses]`) in contiguous blocks, producing false 53+ consecutive loss streaks and false -13.85% drawdowns.
- **resolveOutcome Protection**: `resolveOutcome` MUST NOT contain `st.includes('CLOSED')` in its early `CANCELLED` return condition, as executed trades with status `"Closed"` or `"Force Closed (Stale)"` must resolve to WIN/LOSS via `exact_pct`.
- **Board Metrics Alignment**:
  - `CLOSED TRADES`: Represents `todayClosedSignals.length` (186 closed trades for today).
  - `WIN RATE`: `(todayWins / (todayWins + todayLosses)) * 100` (45.2%).
  - `PROFIT FACTOR`: `todayGrossProfit / todayGrossLoss` (0.19).
  - `WEEKLY TRADES`: `weeklyClosedSignals.length` (226 closed trades).
  - `WEEKLY SUCCESS`: `(weeklyWins / (weeklyWins + weeklyLosses)) * 100` (41.6%).
  - `WEEKLY PROFIT FACTOR`: `weeklyGrossProfit / weeklyGrossLoss` (0.19).
  - `TLCS WEEKLY EXPECTANCY`: Displays the Average Profit % (Avg Return per trade across all closed trades from all past periods till this moment, e.g. +0.54%).



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
- See the canonical `resolveOutcome` implementation above — the CANCELLED guard checks `EXPIRED` / `COMPLETED` only when `!s.exit_price`, protecting all genuinely-executed closed trades.

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
- In the keyword-fallback step of `resolveOutcome` (Step 3, only reached when `exact_pct` is null), TRAIL status MUST NOT be mapped to `'WIN'`.
- If `exact_pct` is null for a TRAIL exit, the outcome is genuinely ambiguous. Return `'OPEN'` so it is excluded from closed-trade metrics.
- See canonical implementation above: `return 'OPEN'` is the last line, TRAIL falls through to it.

## Strict Original Entry Baseline & Trailing SL Principles
- **Original Entry Baseline**: ALL trade percentage returns (`exact_pct`) across web dashboards, mobile applications, and backend webhooks MUST be calculated strictly using the **Original Entry Price** (`entry`).
- **LONG Trades**: `exact_pct = ((Exit Price - Original Entry Price) / Original Entry Price) * 100`
- **SHORT Trades**: `exact_pct = ((Original Entry Price - Exit Price) / Original Entry Price) * 100`
- **Trailed Levels Are Trigger-Only**: Trailing stop levels (`trail_sl` or `stop`) are exclusively used as dynamic execution boundaries to determine when a position should close. Trailed levels MUST NEVER be used as the denominator or baseline price for P&L percentage math.
- **Breakeven Exit Clarification**: Moving a Stop Loss to Breakeven sets the exit price equal to the Original Entry Price (yielding `0.00%`). A trade is categorized as `BREAKEVEN` only if price actually returns to and closes at that exact entry level after hitting TP1. On trading sessions where positions either reach targets (e.g. TP1) or hit initial SLs without returning to entry, 0 trades will exit at Breakeven, which is normal and mathematically sound.

## Today's Market Guidance & Terminal UI Render Guarantee
- **Async Function Declaration**: Function `window.renderTodayMarkets` in `trade-metrics.js` MUST be declared as `async function` (`window.renderTodayMarkets = async function(stats, container)`). Omitting `async` while using `await` inside the body causes a fatal JavaScript `SyntaxError` that completely halts script parsing, leaving "Analyzing strategies..." and "Analyzing today's market performance..." loaders stuck indefinitely.
- **Safe DOM Ready Execution**: `startMetricsEngine()` MUST inspect `document.readyState` (`if (document.readyState === 'loading') ... else startMetricsEngine()`) to ensure initialization functions (`init()`, `localizeExperience()`) execute reliably even if `DOMContentLoaded` has already fired.
- **Market-Wide Performance Statistics**: When loading active trades in `loadAllActiveTrades()`, performance statistics MUST NOT be narrowed to a single symbol (`sig.symbol`). The top metrics card is MARKET-WIDE by design, and should only narrow to a specific symbol when the user explicitly searches for that symbol.

## Webhook Background Worker Variable Ordering (TDZ Rule)
- In `process-webhook-background.js`, ALL payload parsing and condition variables (`calcOpeningBias`, `calcDayType`, `isPivotUpdate`) MUST be fully declared before any guard conditions (such as `if (!isExitOrUpdate && !isPivotUpdate)`).
- Accessing `const` or `let` variables before their declaration line causes a Temporal Dead Zone (TDZ) `ReferenceError: Cannot access 'variable' before initialization` in Node.js, crashing the serverless worker silently on every incoming webhook.

## Telegram Channel Dispatching (HUB Trades & Lifecycle)
- Telegram notifications are automatically dispatched when `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables are present.
- Dispatches are active across all 3 trade lifecycle events:
  1. **New Trade Entry**: `🚨 LONG / SHORT Signal` with Entry, SL, TP, Bias, and Day Type.
  2. **Trade Close / Outcome**: `🎯 WIN / ❌ LOSS / ⚖️ BREAKEVEN` with Exit Price, Status, and Exact PnL %.
  3. **Trailing SL Update**: `📈 TRAILING SL UPDATED` with new Stop Loss level.
- Must be maintained in both Netlify background functions (`process-webhook-background.js`) and Next.js mobile routes (`route.ts`).

## AI Scanner Statistics Pane & TLCS WEEKLY EXPECTANCY Real System Alignment
- **Default System-Wide Metrics Mode**: The AI Scanner page (`scanner.html` & `scanner.js`) defaults to system-wide mode (`activeTab = 'all'`) where no single market tab is highlighted.
- **Deselect Market Tab Toggle**: Clicking an active market tab toggles it off back to system-wide `'all'` mode.
- **Consolidated Weekly System Edge Calculation**:
  - The default statistics pane (`WIN RATE`, `HALF-KELLY %`, `PROFIT FACTOR`, `AVG PROFIT` / System Edge, `TOTAL TRADES`, `WINS / LOSSES`, `BEST TRADE`) on `scanner.html` and the `TLCS WEEKLY EXPECTANCY` card on `dashboard.html` MUST calculate metrics for **all 6 markets' consolidated metrics for the current week** (starting Monday 00:00 local time).
  - `TLCS WEEKLY EXPECTANCY` on `dashboard.html` and `AVG PROFIT` on `scanner.html` must always produce the exact same mathematical average profit percentage for the current week across all 6 markets consolidated.
  - The scanner table (`tabRows`) strictly retains the daily time boundary (`sigTs >= startOfToday`) for active market symbol tracking, while `cachedData.signals` stores `weeklySignals` for current week consolidated metrics.

## Strict Secrets & Environment Variable Policy (Netlify Build Security)
- **NO Hardcoded Secret Keys**: NEVER hardcode real secret key strings (such as `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SERVICE_KEY`, or `WEBHOOK_SECRET`) into test files, debug scripts, or utility files in the repository.
- Netlify's automated build engine performs strict secrets scanning across all repo files during build and will immediately reject builds if a secret environment variable's exact value is detected in source code.
- ALWAYS retrieve credentials dynamically via environment variables:
  ```javascript
  const SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY;
  ```
  ```python
  SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
  ```

## Next.js Client Component Scope Integrity (`page.tsx`)
- All utility functions referenced within Next.js page JSX or component handlers (such as `isNYMEXSymbol`) MUST be explicitly defined at module scope or imported at top of file.
## Automated EOD Market Closure Netlify Scheduled Background Worker
- **15-Minute Netlify Cron (`cron-eod-close.js`)**: Scheduled to run every 15 minutes (`schedule("*/15 * * * *")`) on Netlify background infrastructure (`netlify/functions/cron-eod-close.js`).
- **Market Closure Sweeping**: Automatically scans and closes all open trades across NYMEX, Nifty, MCX, World, and Forex markets upon session close and weekend close:
  - **Unexecuted Limit Orders** (`!s.updated_at`): Marked as `status: 'CANCELLED'`, `outcome: 'CANCELLED'`, `metadata.exit_reason: 'EXPIRED_LIMIT'`.
  - **Executed Active Positions**: Closed at session end with `status: 'EOD Exit'`, `exit_price: closePrice`, `metadata.exact_pct: exactPct`, and resolved outcome (`WIN` / `LOSS` / `BREAKEVEN`).

## Default Mode Symbol Table Exclusion & Weekly Edge Header Pill
- **No Symbol Rows in Default Mode**: In default mode (`activeTab = 'all'`), the scanner table (`#scanner-tbody`) MUST NOT display individual market symbol rows. It renders a clean prompt (`SELECT A MARKET CATEGORY ABOVE TO VIEW SYMBOL SIGNALS`). Symbol rows are displayed ONLY when a specific market tab is active.
- **Weekly Edge Header Market Pill**: The middle of the Weekly Performance Edge header line MUST display a centered, styled theme badge (`#weekly-edge-market-pill`) showing the active market view (e.g., `🌐 SYSTEM-WIDE (ALL MARKETS)` in gold for default mode, `₿ CRYPTO TOP 25` in cyan, `🛢️ NYMEX` in orange, etc.).

## Weekly Performance Edge — Universal Average Metric Rule Across All Views
- **Pure Average Consolidation (Default & Individual Tabs)**: For ALL market views (both system-wide `all` and individual market tabs like `crypto`, `nifty`, `mcx`, `nymex`, `forex`, `world`), all metrics in the Weekly Performance Edge table MUST reflect weekly averages.
- **Cumulative Edge Row (`ALL`)**: The top `ALL - CUMULATIVE EDGE` row MUST ALWAYS compute the mathematical average across recorded weeks (e.g. Average Weekly Net Edge, Average Win Rate, Average Profit Factor, Average Half-Kelly %), ensuring cumulative figures are never inflated by summing multiple weeks together.

## Mandatory Stop, Target & R:R Completeness Rule for Closed & EOD Trades
- **No Missing Levels on Closed Trades**: All closed trades (including `EOD Exit`, `Hit SL`, `Hit TP`, `Hit B/E`, `Divergence`, and legacy signals) MUST display valid numeric values for `STOP`, `TARGET`, and `R:R` (e.g. `1.0R`, `1.5R`).
- **Dynamic Level Deduction Engine (`getTradeLevels`)**: If a trade signal payload lacks explicit `stop` or `target` fields (e.g. EOD force closures or divergence webhooks), the UI layer (`scanner.js`, `commodity-scanner.js`, `page.tsx`) MUST dynamically deduce `stop`, `target`, and `R:R` from `entry`, direction, and asset-class default stop percentages (`0.5%` for Crude/Silver, `0.3%` for Gold, `0.35%` for Nifty, `0.75%` for Crypto, `0.25%` for Forex, `0.4%` for World Indices), ensuring `STOP`, `TARGET`, and `R:R` are NEVER rendered as `--`.

## Zero `--` Display Policy on Real Metrics
- **Strict Formatting Fallbacks**: All metric summary cards (`WIN RATE`, `HALF-KELLY %`, `PROFIT FACTOR`, `AVG PROFIT`, `BEST TRADE`) and symbol table columns (`SYM WIN%`, `HALF-KELLY %`) MUST display valid numeric defaults (`0.0%`, `+0.00%`, `0.00`, `0%`) instead of `--` when no trades exist or when Half-Kelly evaluates to 0/null.

## Official TLCS Automated Social Media & Marketing Architecture Plan
- **Multi-Channel Distribution Funnel**:
  1. **Telegram Channel (`@TLCS_Alerts` / `-1001555378566`)**:
     - **Target Audience**: Active Energy & Metals traders.
     - **Scope**: Exclusive real-time NYMEX trade execution alerts (`CL`, `GC`, `NG`, `SI`).
     - **Conversion Lead Capture**: Reframed landing page callout box on [`index.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/index.html) (`Join Telegram Channel (@TLCS_Alerts) →`) driving free traffic to Telegram alerts channel.
  2. **Instagram Official Account (`@thelioncapitaladvisors`)**:
     - **Target Audience**: Retail & institutional traders seeking daily/weekly performance transparency.
     - **Session Close Automation**: Automated Netlify background dispatcher [`cron-instagram-stats.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js) posts performance reports linked to exact market close hours:
       - `Nifty 50`: 15:35 IST (10:05 UTC)
       - `MCX`: 23:45 IST (18:15 UTC)
       - `NYMEX`: 02:35 IST / 17:00 EST (21:35 UTC)
       - `Forex`: 02:40 IST / 17:00 EST (21:40 UTC)
       - `World Indices`: 02:45 IST / 17:00 EST (21:45 UTC)
       - `Crypto`: 05:35 IST (00:05 UTC)
     - **3-Tier Performance Breakdown**: Every post includes Daily Session Close Metrics, Weekly Performance Cards, and All-Time Cumulative Edge.
  3. **Content Marketing & SEO Knowledge Base (`blog.html` & `article.html`)**:
     - **4 Core Publications**:
       1. `🦁 TRADE WHAT YOU SEE, NOT WHAT YOU FEEL` (Trade Management)
       2. `🌪️ NAVIGATING VOLATILITY IN MODERN MARKETS` (Market Psychology)
       3. `🎯 MASTERING THE TLCS TERMINAL` (Trading Tools & Systems)
       4. `🔔 THE PSYCHOLOGY OF ALERTS TRADING` (Trading Automation)
     - **Reader Navigation**: Glassmorphic fullscreen reader modal on `blog.html` + standalone `article.html?id=...` pages with back buttons (`← Back to Blogs and FAQs`) routing back to `#blog-section`.



## Market-Wide Edge % Mathematical Calculation
- **CRITICAL DEFINITION**: The Global "TLCS WEEKLY EXPECTANCY" for the "MARKET-WIDE (ALL ASSETS)" view must ALWAYS be calculated as the **mathematical average of the 6 individual market weekly edges** (NIFTY, MCX, NYMEX, Cryptocurrency, Global Forex, World Indices).
- **NO RAW AVERAGES**: It must NEVER be calculated as the raw average of all closed trades combined across the system, because high-frequency scalping markets (like Cryptocurrency) will disproportionately overwrite and distort the Edge of lower-frequency swing markets (like NIFTY).
- **Weekly Isolation**: The Global Edge % must always be strictly isolated to the current week's closed trades (calculated via `startOfCurrentWeekMS`), preventing the metric from reverting to a lifetime overall value. This applies universally across the Web Dashboard (`dashboard.html`) and the Mobile App (`page.tsx`).

## Dhan HQ Trading & Backtesting Architecture (VectorBT + Supabase)

### 1. VectorBT Backtesting Edge (`algo_engine/backtest_edge.py`)
- **Data Ingestion Philosophy**: Bypasses theoretical OHLC Dhan historical data entirely.
- **Supabase Integration**: Connects directly to the `signals` table via `.env` credentials to fetch actual recorded TradingView webhooks.
- **Outcome Validation**: Strictly enforces `resolveOutcome` to purge invalid limit orders and dynamically extract the true `exact_pct` payload.
- **Performance Output**: Generates `strategy_tearsheet.html` using VectorBT's `ReturnsAccessor` applied directly to the chronological sequence of exact signal returns. The tearsheet is saved directly into `TLCS_Website_Deploy/` and embedded on the `admin.html` page for real-time portfolio analytics.

### 2. Live Dhan Execution (`algo_engine/dhan_executor.py`)
- **Polling**: Polls the Supabase `signals` table every 2 seconds for newly ingested TradingView webhooks.
- **Order Parsing**: Normalizes TradingView symbols into DhanHQ Security IDs.
- **Safety**: Managed by the `PAPER_TRADING = True` flag in `.env`. Must be toggled to `False` to send live execution orders.

## Version 2.0 Architecture Updates
- **Cross-Platform Auto-Refresh Mechanism**: Implemented native auto-reloading intervals for the VectorBT Tearsheet across both platforms to bypass browser caching.
  - **Mobile App**: Included in a new `ANALYTICS` tab, utilizing a React `useEffect` interval (5 minutes) to forcefully remount the iframe via state `key` injection.
  - **Website Dashboard**: Admin panel `admin.html` uses a lightweight Vanilla JS `setInterval` (5 minutes) to append cache-busting timestamp queries to the iframe src.
- **GitHub Actions Cloud Scheduler**: Completely decoupled backtesting from local cron. A dedicated GitHub Action workflow (`generate-tearsheet.yml`) strictly triggers at the 4 distinct global market closes (NIFTY, MCX, US/World, Crypto) to pull Supabase data, compute stats, and push `strategy_tearsheet.html` back to the main branch automatically.
- **VectorBT Comparative Market Analysis**: Updated the backend VectorBT engine (`algo_engine/backtest_edge.py`) to natively plot 6 simultaneous market timelines on a single interface. It restricts the data query to the exact local `startOfToday` boundary, pivots the market returns into a 6-column dataframe, and resamples strictly to a `15min` frequency for granular, synchronous intraday comparison.
- **Cross-Origin Iframe Embedding Security**: Overhauled `_headers` on the live Netlify deployment to fix Capacitor/Expo mobile embedding blocks. Completely removed indented `X-Frame-Options` comments that were misparsed by Netlify. Explicitly added `frame-ancestors *;` to the `Content-Security-Policy` to globally whitelist external webview framing, and whitelisted `https://cdn.plot.ly` in `script-src` to guarantee VectorBT charts render dynamically.
- **Interactive Analytics Tearsheet Interface**: Replaced the static, single-plot VectorBT output with a custom, dark-mode HTML template. The tearsheet now features interactive vanilla JS tab filters to seamlessly toggle between 3 distinct dynamic Plotly visualizations (Full Equity Curve, Drawdowns, and Raw Returns) without reloading the iframe. Admin panel branding was also streamlined by removing specific VectorBT framework references.

## Version 2.1 Architecture Updates
- **Mobile Analytics Table Expansion**: Restructured the `ANALYTICS` tab in the Next.js mobile app to significantly expand the statistics table container height (`min-h-[1100px]`), removing the need for internal scrolling. Users can natively scroll the full list of VectorBT statistics.
- **Sticky Matrix Headers**: Modified the Python tearsheet generation logic (`backtest_edge.py`) to inject custom CSS freezing the top `thead th` row (containing Market Names) alongside the first column, dynamically managing `z-index` so headers remain permanently visible during dense data scrolling.
- **Optimized Sales Funnel via Relocation**: Extracted the "Terminal & Contact" form block from the AI Dashboard and cleanly injected it into the bottom of the `products.html` page to streamline user conversion and inquiries.
- **Public Democratization of Performance Analytics**: Shifted the multi-tab "Alerts Intelligence Edge: Performance Analytics" iframe from the authenticated `admin.html` dashboard directly to the public `dashboard.html` interface. This allows any website visitor full visibility into the real-time AI trading tearsheet.
- **Global Version Bumping**: Standardized the system-wide application version to **v2.1** across the Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`) and Website Cache/Auth Logic (`sw.js` and `auth.js`).
- **Plotly Binary Compression Glitch (Empty Trades)**: Plotly Python aggressively compresses numpy arrays containing identical numbers (e.g., exactly `0.0` for markets with zero trades today) into binary base64 `bdata` strings. Mobile WebViews fail to decode these strings, causing Plotly to fall back to plotting raw index values (`y = [0, 1, 2, 3...]`), resulting in artificial identical diagonal lines across all empty markets. The architecture strictly intercepts all-zero `0.0` data columns and replaces them with `np.nan` prior to rendering to safely hide inactive markets from the chart.
- **Fluid Mobile Analytics UI**: The Analytics HTML UI dynamically responds to extremely narrow mobile viewport widths without spilling over horizontally. `width: 100vw` is strictly prohibited inside the iframe; it relies solely on `width: 100%` and `box-sizing: border-box`. All generated Plotly traces explicitly inject `config={'responsive': True, 'displayModeBar': False}` to compress horizontally, and UI tabs are styled using a `.tab-container { display: flex }` and `.tab-btn { flex: 1 }` architecture to ensure all options fit evenly on one single line without requiring any touch-scroll logic.

## Instagram Automated Marketing Architecture
- **Market-Specific Triggers**: A serverless background Cron job (`cron-instagram-stats.js`) executes automatically based on the precise daily close time for each of the 6 distinct global markets (e.g. NIFTY at 15:35 IST, MCX at 23:45 IST).
- **Metric Extraction**: The engine queries the Supabase `signals` and `weekly_performance_logs` tables to aggregate Daily (Session Close), Weekly (WTD), and All-Time (Cumulative Edge) statistics including executed trades, win rates, profit factors, average winners/losers, and the best-performing trade of the day.
- **Dynamic Content Generation**: The script automatically constructs a highly readable, emoji-rich Instagram caption injected with market-specific hashtags and performance analytics.
- **Autopilot Meta Dispatch**: The architecture securely dispatches the post directly to the @thelioncapitaladvisors Instagram account utilizing the official Meta Graph API (`INSTAGRAM_ACCOUNT_ID`, `INSTAGRAM_ACCESS_TOKEN`), creating an entirely hands-free, autonomous social media marketing funnel to drive traffic to the web dashboard.

## User Session Management
- **Strict Subscription Enforcement**: Once a user's subscription ends or expires, they MUST be completely cut off and forcefully logged out (e.g. via `client.auth.signOut()`) from ALL access points, including the web dashboard, the mobile application, and Telegram. Do not allow expired users to linger in the system.
- **Free Promotion Access**: If a registered user is offered a free subscription (e.g., a 3-month trial), their `subscription_status` is considered active until the expiry date. During this active period, they MUST receive full, unrestricted access to everything that is otherwise available to paid users (treated as 'Elite'). **Exception:** This free tier equivalence applies ONLY to website/mobile app plans and does NOT include access to premium TradingView Indicator subscriptions.


## Exact UI Exit Price Fallback Logic
- The UI MUST NEVER rigidly default to printing `---` just because the `exit_price` column in the database is strictly null (which occurs heavily on legacy webhooks). 
- The UI layer MUST proactively use the underlying mathematical engine logic to deduce the exit price (by pulling `trail_sl`, `stop`, or the appropriate `TP` target based on the status string) and dynamically inject that calculated value into the `EXIT` or `EXITED AT` visual card.
- Cosmetic string labels (like `B/E` or `SL`) MUST ONLY be rendered in the specific outcome badging pills next to the symbol, NEVER in the primary numeric price output boxes (like Entry or Exit).

## Strict One-Column Tablet UI for Trade Feeds
- The `GLOBAL SIGNAL FEED` (Dashboard/HUB tab) and `LOGS` tab trade feeds must strictly render trade cards in a single column (`grid-cols-1`) across both Mobile and Tablet (iPad) breakpoints.
- Do NOT introduce multi-column `md:grid-cols-2` or `lg:grid-cols-3` layouts for dense trade feed cards, as it violently squishes and vertically stretches the internal 6-box (`Entry`, `Stop`, `Outcome`, `Target`, etc.) matrices.

## INSIGHTS Tab Bulletin Layout
- The `INSIGHTS` tab strategy filter tags (`LONG MISSILE`, `SHORT SCALP`, etc.) must strictly utilize a rigid CSS Grid (`grid-cols-2`) to guarantee exactly two pills per row globally (including iPad). Do not rely on dynamic flex-wrapping for these top-level filters, which could artificially misalign them into 3-tag or 4-tag clusters on wider viewports.


## Plotly BData Glitch (iOS/Android WebViews)
- **UNIVERSAL BYPASS**: Plotly aggressively compresses identically numbered NumPy arrays (e.g. `[0.0, 0.0]`) into binary Base64 `bdata` strings to save memory. Standard iOS/Android WebViews cannot natively decode these binary arrays, causing Plotly to drop the `Y` values and artificially plot sequence indices instead, creating perfectly overlapping diagonal lines up to 9600%.
- **Strict Casting**: To globally circumvent this, ALWAYS explicitly cast Plotly `trace.x` and `trace.y` data from numpy arrays into pure Python lists (e.g., `trace.y.tolist()`) before calling `.to_html()` or `.to_json()`. This forces the Plotly JSON encoder to serialize the arrays as standard JSON lists `[...]` rather than `bdata`, fully immunizing the Mobile App and Web Dashboards against rendering glitches.

## Dynamic Telegram Market Prefixing
- **No Hardcoded Markets**: The Telegram dispatcher (`process-webhook-background.js`) MUST dynamically resolve the market prefix using `getMarketForSymbol(sym).toUpperCase()` instead of hardcoding `NYMEX TRADE ACTIVE` for all channels.

## Supabase CDN Independence
- **Local Vendoring**: Do not rely on external CDNs (like `cdn.jsdelivr.net`) for critical libraries like `supabase-js-v2`. Adblockers or strict network firewalls often block these domains, which causes silent JavaScript failures that break SSO interception and UI updates. Always vendor `supabase-js-v2.min.js` locally in `TLCS_Website_Deploy` and reference the local file.

## Bulletproof DOMContentLoaded Timing
- **readyState Fallback**: Never attach `document.addEventListener('DOMContentLoaded', ...)` without checking `document.readyState === 'loading'` first. If a script executes asynchronously or at the bottom of the body tag, the `DOMContentLoaded` event may have already fired, causing the initialization function (e.g., `bootAuth` or `initMain`) to never execute. Always use the standard fallback pattern: `if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', initFn); } else { initFn(); }`

## Automated NYMEX to MCX Live Trading Integration (Dhan Engine)
- **Symbol Mirroring**: NYMEX active limit alerts (`CL`, `NG`, `GC`, `SI`) are fully integrated into the live Dhan execution engine (`dhan-engine.js`). The backend intercepts these signals and automatically translates them into their MCX counterparts (`CRUDEOIL`, `NATURALGAS`, `GOLD`, `SILVER`).
- **Session Time Guard**: MCX Automated Trading via NYMEX alerts is strictly bounded by live MCX session timings (9:00 AM to 11:30 PM IST, Monday - Friday). If a NYMEX alert fires outside of these hours (e.g. 2:00 AM IST), the engine gracefully aborts execution to prevent rejected API calls and false execution logs.
- **Strike Price Resolution (Option B)**: The Dhan engine fetches the exact At-The-Money (ATM) Option strike by querying the Dhan HQ Marketfeed API (`/marketfeed/ltp`) for the live MCX Futures contract the moment the NYMEX alert fires. This perfectly syncs the strike to the live INR spot price.
- **Mathematical Fallback**: If the Dhan API is slow or unavailable, the engine uses fixed mathematical multipliers (e.g. `$83.5` USD/INR exchange rate, adjusting for Troy Ounce/Gram conversions) on the NYMEX Entry price to instantly compute a safe fallback ATM strike.

## Live Trades vs Active Limits Categorization (V2 — Corrected)
- **Canonical Definition**: A Limit Order is strictly defined as an `OPEN` trade that **lacks an `updated_at` timestamp**. A Live Trade is an `OPEN` trade that **has an `updated_at` timestamp** (meaning the limit order filled and the backend updated the row).
- **DEPRECATED (V1 — Broken)**: The previous approach checked if `status` or `trigger` contained the substring `"LIMIT"` to classify active limits vs live trades. This caused a critical regression: limit signals with `status: "Active"` or `status: "OPEN"` (no "LIMIT" substring) were miscategorized as LIVE trades, breaking the ACTIVE LIMITS filter (showing 0 results) and leaking unfilled limit orders into the LIVE filter.
- **The Correct Implementation** (applied in `page.tsx`, `trade-metrics.js`):
  ```javascript
  // Canonical: updated_at is the SINGLE differentiator
  return !s.updated_at ? 'ACTIVE LIMITS' : 'LIVE TRADES';
  ```
- **What MUST NOT happen** (recurring regression pattern):
  - ❌ Using `(s.status || '').toUpperCase().includes('LIMIT')` to detect limit orders — fails when status is `"Active"` or `"OPEN"`
  - ❌ Using `(s.trigger || '').toUpperCase().includes('LIMIT')` — trigger field is often null or absent
  - ❌ Combining both with `const isLive = !!s.updated_at || (!isLimitStatus && !isLimitTrigger)` — the fallback branch `(!isLimitStatus && !isLimitTrigger)` forces `isLive = true` for ALL signals without "LIMIT" in status, regardless of `updated_at`
- **Dashboard Filter Alignment**: The HUB tab's filter buttons (`ACTIVE LIMITS`, `LIVE`) must use the same canonical check: `outcome === 'OPEN' && !signal.updated_at` for limits, `outcome === 'OPEN' && !!signal.updated_at` for live.

## HUB Tab Exact Percentage Display
- When a trade on the HUB tab (mobile app `page.tsx`) has a resolved outcome of `WIN`, `LOSS`, or `BREAKEVEN`, the card MUST display the `exact_pct` value inline next to the outcome badge pill (e.g., `SL HIT  -0.22%` or `TP1  +1.35%`).
- The percentage uses `getExactPct(signal)` and renders in green for positive values, red for negative.
- Active/open trades do NOT show a percentage (they have no `exact_pct` yet).
- This matches the existing behavior on the LOGS tab, ensuring consistency across all tabs.


## System Reliability & Webhook Hardening
- **Pine Script JSON Sanitization**: TradingView webhooks often contain unescaped control characters (`\n`, `\t`, `\r`, `\f`) within multi-line string fields (like `opening_bias`). The backend webhook (`process-webhook-background.js`) MUST globally intercept and sanitize all literal control characters using `replace(/[\n\r\t\v\f\b]+/g, ' ')` before calling `JSON.parse()` to prevent fatal `400 Invalid JSON` parse errors.
- **Global DB Fetch Timeouts**: Netlify Functions enforce a strict 10-second execution limit. All Supabase JS clients running on Netlify (`process-webhook-background.js`, `razorpay-webhook.js`) MUST inject a global fetch handler with `AbortSignal.timeout(5000)`. This forces the Supabase connection to abort early during transient DB latency spikes, allowing internal error handling to gracefully execute and exit instead of crashing the serverless container with a `502/504 Bad Gateway`.
- **Graceful Payment Degradation**: `razorpay-webhook.js` must strictly wrap its DB RPC lookups (`get_user_id_by_email`) in a `try/catch`. If the DB fetch times out, the script must catch the error and intentionally return a `200 OK` directly to Razorpay. Do NOT return a `500` error, as Razorpay will infinitely retry the webhook every 20 minutes and violently flood the system with duplicate alerts.
- **Mobile Network Resilience**: The mobile app (`Tv-Alert-Mobile/src/lib/supabase.ts`) handles 4G/5G packet loss by injecting a custom Exponential Backoff Retry Engine directly into the Supabase global fetch handler. It silently intercepts 500-level errors and fetch failures, retrying up to 3 times (with 1s, 2s, 4s expanding delays) and enforcing a 10s maximum timeout per attempt to eliminate blank screens.

## Signal Interface Definition
- The `Signal` interface in Next.js (e.g. `page.tsx`) MUST include `trigger?: string;` to ensure the strict Netlify production build compiles successfully when checking for limit order triggers.

## UI Active Limit Signal Time Rule
- Real entry and active limit can never be the same time. For an ACTIVE LIMIT trade (which has not executed yet), the UI MUST dynamically display **SIGNAL TIME** instead of **REAL ENTRY**. Once the limit order actually fills and becomes an executed active trade, the text should dynamically flip back to reading **REAL ENTRY**.

## Supabase CDN Fallback & Webhook Error Resilience
- **Supabase UMD CDN Dependency**: Do NOT rely on locally hosting the `supabase-js-v2.min.js` file if downloaded directly via CLI. CDNs often block raw CLI downloads, resulting in corrupted script files that break the frontend. ALWAYS use the direct CDN link (`https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2`) in `<script>` tags.
- **Netlify Webhook False Positives**: Background functions (`*-background.js`) in Netlify inherently return a `202 Accepted` response before execution. TradingView interprets this as a "Webhook successfully delivered" even if the payload parsing fails. ALWAYS ensure Pine Script `alert()` functions format the string exactly as JSON (e.g. `_divPay`), avoiding generic plain text strings like `"Alert: " + text`, which cause silent 400 Bad Request errors inside the Netlify function.

## PivotBoss Combined Dashboard (V2.2.4)
- The AI Dashboard (`dashboard.html`) and Mobile ANALYSIS tab (`page.tsx`) now include the PivotBoss Combined Scanner table.
- Day-type blueprints (Rejection, FNL/FNH, Absorption, Outside, Stop Run) are sourced from `pivotboss_scans` table (JSONB `scan_data` column).
- Do not break the JSONB parsing logic (`typeof s === "string" ? JSON.parse(s) : s`) when rendering this table.

## Standardized PivotBoss Taxonomy (Blueprints & Sequences)
- **Day Type Blueprints (5 Categories)**:
  1. Rejection Day Blueprint
  2. Absorption Day Blueprint
  3. Failed New Low Blueprint
  4. Outside Day Blueprint
  5. Stop Run Day Blueprint
- **Trade Sequences (4 Sequences)**:
  1. Rejection Day Sequence
  2. Stop Run Sequence
  3. Failed Absorption Sequence
  4. Accumulation Sequence
- This taxonomy MUST be kept identical across Pine Script indicators, Supabase table contracts (`pivotboss_scans`), Netlify background workers, Web Dashboard (`dashboard.html`), and Mobile Application (`page.tsx`).

## System Architecture Update (Version 2.2.8 — August 3, 2026)
- **TradingView Webhook Fast-Relayer Routing**:
  - TradingView enforces a strict 3-second HTTP timeout on webhooks. TradingView alerts must point to `https://thelioncapitalsolutions.com/.netlify/functions/webhook` (the fast relayer) which responds with `200 OK` in <100ms and forwards payloads to background functions to prevent `Webhook delivery failed — request took too long and timed out` errors.
- **Dynamic Scanner Table Auto-Hiding (Pine Script & UI)**:
  - The `TLCS Dashboards` Pine Script indicator (`TLCS_Sequence_Dashboard.pine`) and dashboard components dynamically calculate `activeRows` and hide rows with nil data (`-`), maintaining a compact UI.
- **Timeframe & Symbol Independence Engine (`ta.barssince`)**:
  - The `TLCS Dashboards` indicator replaces chart-dependent `bar_index` lookups with `ta.barssince(...)` in sequence state tracking. This ensures the scanner produces 100% identical and consistent blueprint/sequence results whether viewed on a 1m, 5m, 15m, 1h, or 1D chart.

## System Architecture Update (Version 2.2.9 — August 3, 2026)
- **Continuous Multi-Market Closure Refresh**:
  - Pine Script `alert()` in `TLCS_Sequence_Dashboard.pine` is configured to trigger on every bar close (`alert.freq_once_per_bar_close` without blocking on `has_any_alerts`).
  - This ensures that as each of the 6 market categories (NSE at 15:30 IST, MCX at 23:30 IST, Forex/NYMEX at 02:30 IST, Crypto at 05:30 IST, etc.) reaches its market closure, the Supabase `pivotboss_scans` table is immediately updated with a fresh `updated_at` timestamp.
- **Push Notification Filtering**:
  - While Supabase always receives fresh timestamp updates, push notifications via `send-push-background.js` remain strictly guarded (`hitCount > 0`). Push notifications fire ONLY when active blueprints/sequences are detected, preventing 0-hit notification spam.
- **Recommended Chart Setup**:
  - Load `TLCS Dashboards` on an intraday timeframe (e.g., **15-Minute** chart) with TradingView alert set to `Any alert() function call` and frequency `Once Per Bar Close`.

## System Architecture Major Release (Version 3.0 — August 3, 2026)
- **Version 3.0 Standardization**:
  - Global Version 3.0 release for both the Web Application (`TLCS_Website_Deploy`, package version `3.0.0`) and Mobile Application (`Tv-Alert-Mobile`, package version `3.0.0`, header `TLCS TERMINAL v3.0`).
- **PivotBoss Blueprint & Sequence Unified Architecture**:
  - Complete integration of 5 Day Type Blueprints (Rejection, Absorption, Failed New Low, Outside, Stop Run) and 4 Trade Sequences (Rejection, Stop Run, Failed Absorption, Accumulation).
- **Timeframe & Resolution Agnostic Pine Engine**:
  - Pine Script `TLCS Dashboards` engine is 100% timeframe and symbol independent via `ta.barssince` state evaluation.
- **Fast-Relayer & Multi-Market Alignment**:
  - 100ms fast-relayer (`/.netlify/functions/webhook`) prevents 3-second TradingView timeouts.
  - Automatic continuous updates after each of the 6 market closures (NSE, MCX, NYMEX, Forex, World Indices, Crypto) with guarded push notification dispatches.




## Pine Script Timeframe Dynamism
- **No Hardcoded Timeframes**: All Pine Script indicators and dashboards that rely on `request.security` MUST pass `timeframe.period` instead of a hardcoded string like `"D"`. This ensures the script is dynamically adaptable to intraday chart selections (e.g. 15m, 1H) without breaking sequence logic or locking the user to daily bars.
- **Agnostic Input Labels**: Any input labels relating to time lookbacks must be labeled neutrally as `bars` rather than `days` (e.g. `ATR Lookback (bars)` instead of `ADR Lookback (days)`).

## UI Theme & Contrast Safety
- UI changes (specifically Tailwind styling) must NEVER assume a single theme across the application. 
- ALWAYS explicitly define utility classes for both light and dark variants (e.g. `text-slate-600 dark:text-slate-300` or `bg-white dark:bg-black/40`) to ensure contrast and legibility are perfectly maintained regardless of the user's active theme. Do not apply the same hardcoded colors for all themes.

## Git Workflow
- AUTOMATIC PUSH: After completing any important optimization, feature implementation, or bug fix, you MUST automatically commit and push all changes to the remote repositories (e.g. `Tv-Alert-Mobile`, `TLCS_Website_Deploy`, `TV Indicator`) at the end of your task. Do NOT wait for the user to explicitly ask you to "push changes".

## UI Display Conventions & Analytics
- **Trade Cards Timestamps**: The UI MUST differentiate between Signal Time and Real Entry. The top-right header of trade cards (or equivalent) MUST strictly display the **SIGNAL TIME** (limit order placement time, `signal_ts` or `created_at`), while the `ENTRY` block inside the card MUST strictly display the **REAL ENTRY TIME** (the exact time the order filled, `real_entry_time`). Do not duplicate `real_entry_time` in both places.
- **Analytics Filtering**: Analytics tables for `Day Type Blueprints` and `Trade Sequences` MUST conditionally hide empty rows. If a sequence or blueprint contains 0 active signals (both Bullish and Bearish values are `--`), the row must NOT render, keeping the UI clean on low-volume days.

## Sideways Day & Normalized NCPR Rules
- **NEVER** remove the `NCPR` exception from the sideways day filter. 
- **Normalized CPR Width**: Because measuring CPR width against absolute asset prices (e.g. `DPi`) breaks across different markets (Forex vs Crypto), the CPR width MUST always be mathematically normalized against the **Daily Average True Range (ATR)**. Normalizing against the single previous day's range (`DH - DL`) fails during back-to-back compressed days because the denominator shrinks too much.
- The canonical, universal Normalized NCPR formula is: `NCPR = 11.11 > (math.abs(DTcf - DBcf) / math.max(daily_atr, syminfo.mintick)) * 100`. This strictly identifies Narrow CPR days as those where the CPR width is less than 11.11% (the exact bottom third of the theoretical maximum 33.33% CPR width) of the asset's normal daily volatility. Do NOT revert to price-based normalization.
- Because `mX` is a dynamic, tick-by-tick evaluation based on `close`, the sideways day label on the final bar may differ from the classification at the moment a trade originally fired. If a trade fires and `mX` later evaluates to `TYPICAL DAY, TRADING RANGE, SIDEWAYS`, the trade remains perfectly valid according to the engine logic at the time of execution.

## Strict Scope Adherence
- **No Unsolicited Additions**: Do NOT add any new features, alerts, logic, or plots unless specifically and explicitly requested by the user. If the user asks for divergence plots to be incorporated, ONLY incorporate divergence plots and do not 'improvise' by adding other webhooks or patterns that were not strictly requested.

## GitHub Actions Cron Resiliency & Fallback Credentials Rule
- **No Unhandled Failures**: All GitHub Actions workflow scripts (e.g., `stale_trades_cron.yml`, `eod_cron.yml`, `close_stale_trades.py`, `eod_closer.py`) MUST include hardcoded production fallback credentials (`https://dwepduvhzuhzeehbeaaz.supabase.co` & `sb_publishable_xl3kUBHckB0hTH8n4k3esA_m1qe0stu`).
- **Graceful Error Handling**: Workflow scripts MUST NEVER call `sys.exit(1)` when environment variables or GitHub Secrets are missing or unconfigured. Scripts MUST log a clear warning and return exit code 0 to prevent GitHub workflow failure email notifications.
- **Workflow Versioning & Dependencies**: Actions workflows MUST use `actions/checkout@v4` and `actions/setup-python@v5` with explicit dependency upgrades (`pip install "numpy<2" yfinance supabase`).



## 7-Day Historical Lookback & Strategy Performance Edge Rules (Version 3.16)
- **Pine Script Dashboards ( & )**:
  - Implement a 7-day historical lookback engine using compressed bitmask tuples ().
  - Keep security calls under 20 calls total (max 40 limit) for all 9 domestic and global symbols (, , , , , , , , ).
  - Table section headers (, , ) MUST be conditional and render ONLY if active signals exist for that section.
- **Mobile App ()**:
  - The  tab MUST feature the 7-Day Strategy Performance Edge Table displaying 7-day cumulative signals, Win Rate %, Total Edge %, and Avg Return % for all 6 strategy filters (, , ).

## Version 1.1: TradeFill Webhook Pipeline & Failproof Trade Identity Binding (V1.1)
- **TradeFill Webhook Route**: A dedicated `TradeFill` route must exist in the backend (`process-webhook-background.js`) to capture the exact limit-order fill timestamp from Pine Script. Upon execution, the status must transition from `OPEN` to `Active` and store `metadata.real_entry_time`.
- **Failproof Trade Identity Binding**: Every signal-updating webhook (`TradeFill`, `TradeClose`, `TrailingSLUpdate`, `TradeUpdate`) MUST use `trade_id` (`metadata->>trade_id`) as the primary query binder. All binders must be additive (AND conditions), never mutually exclusive.
- **Bulk Update Prevention**: The backend must never perform bulk updates on active signals. If no unique identifier (`trade_id` or `entryTime`) is provided in the webhook payload, the update MUST be aborted.
- **Duplicate Trade Prevention Guard**: The backend must query the database before inserting a new signal. If an active trade already exists for the same symbol with the exact same `trade_id` or `signal_ts` within ±5s, the insert must be skipped to prevent duplicates.
- **Strict 2-Candle confirmed Divergence Exit**: The indicator strategy MUST NOT trigger divergence exits immediately on the live bar. To prevent unconfirmed repainting flashes, divergence exits MUST require the divergence signal to be at least 1 or 2 bars old (`[1]` or `[2]`) AND verified by two consecutive closed candles closing against the trade direction.
- **Mobile Analytics Multi-Dashboard Matrix**: The mobile app's `ANALYTICS` tab MUST render both the `Daily Signal Dashboard Matrix` (7-day parameter table) and the `Weekly Signal Performance & Achievement Table` (day-wise targets, net edge, and average returns) directly below the Weekly Performance Edge table.

## Limit Order Signal Candle Invalidation Guard
- **Strict Limit Order Protection**: Limit orders MUST NOT be instantly invalidated by the wick of the exact candle that generated the signal.
- In Pine Script, any invalidation check (`isInvalidated = low <= slLevel` or similar) MUST be strictly gated by `and bar_index > trade.startBarIndex` so that the trade survives the signal candle and has a chance to be sent to the backend as an `OPEN` order. 
- Without this guard, the wick of the signal candle itself can artificially trigger the invalidation condition, causing the limit order to be created and cancelled instantaneously, and subsequently deleted by the backend.

## Late Alert Creation & TradeFill Fallback
- **Problem**: If the user creates a TradingView alert *after* a signal has already generated on the chart, the initial `OPEN` webhook (limit order placement) will never be sent to the backend.
- **Solution**: The `TradeFill` block in `process-webhook-background.js` MUST NOT abort if it fails to find an open signal. Instead, it must gracefully insert the missing trade as a brand new active signal using the comprehensive payload data provided by the `TradeFill` webhook. This ensures late alerts are dynamically caught when price hits the limit entry.

## Version 1.2: Webhook Robustness & Scanner Payload Optimization
- **VAPT Payload Size Limits**: The Netlify `process-webhook-background.js` server MUST maintain a minimum payload size limit of **500KB (512,000 bytes)** (`if (rawBody.length > 512000)`). Do NOT restrict it to 10KB. Bulk PivotBoss Scanner payloads (`scan_data`) easily exceed 10KB across multiple markets, which triggers `413 Payload Too Large` rejections and causes TradingView to permanently halt the alerts.
- **TradeFill Missing Signal Robustness**: Webhooks triggered by `TradeFill` MUST NEVER silently abort (`if (!fillSignal) return;`) if a pre-existing limit order is not found. They must gracefully insert a new trade row as a fallback. 
- **Accumulation Sequence Shorthand**: The TradingView Pine Script outputs the shorthand `Acc/Dist Seq` for the Accumulation / Distribution Sequence. Both the Web Dashboard (`blog.html` / `dashboard.html`) and Mobile App (`page.tsx`) must strictly map this by checking `dt.includes('ACCUMULATION') || dt.includes('ACC/DIST')`. Do not overwrite or alter the Pine Script name, handle the shorthand natively on the frontend.

## Standby Status Text Standard
- The canonical standby/fallback status label for Day Type Scanners and Pivot scanners across both Web and Mobile is strictly **"Awaiting Market Close"** (e.g. `let lastUpdated = 'Awaiting Market Close'`). Do NOT use "Awaiting Market Open".

## Mobile Navigation Tab Sequence
- The canonical sequence of bottom navigation tabs in the mobile application (`page.tsx`) is strictly:
  1. `HUB` (`id: 'DASHBOARD'`)
  2. `LOGS` (`id: 'ALERTS'`)
  3. `SCREENER` (`id: 'SCREENER'`)
  4. `INSIGHTS` (`id: 'INSIGHTS'`)
  5. `MARKETS` (`id: 'ANALYSIS'`)
  6. `ANALYTICS` (`id: 'ANALYTICS'`)

## Screener Nomenclature Standards
- The canonical header titles on the Screener matrix (`page.tsx`) are strictly:
  - `TLCS SIGNALS`
  - `DAY TYPE BLUEPRINTS`
  - `TRADE SEQUENCES`
- Do NOT append suffixes such as `(DAILY 1D)` or `(Daily Close)` to section headers or column headers.

## Weekly Performance Table Signal Count Rule
- In the `Weekly Signal Performance & Achievement` table on the mobile app (`page.tsx`) and web (`blog.html`), the `SIGS` column count must strictly equal the total number of closed trades: **`wins + losses`** (rendered as `${wins + losses} (${wins}W/${losses}L)`). Never display raw `daySigs.length` which includes unclosed or unexecuted limit signals.

## Multi-Theme Statistics & Tearsheet Skinning
- The statistics tearsheet (`strategy_tearsheet.html`) and generator scripts (`generate_tearsheet.py`, `backtest_edge.py`) MUST dynamically adapt their background, borders, text, and Plotly templates according to the active theme skin:
  - `theme-gray` / `gray` / `slate`: Slate background (`#F1F5F9`), slate headers (`#CBD5E1`), dark slate text (`#0F172A`), `plotly_white`.
  - `theme-light` / `light`: White background (`#FFFFFF`), light gray headers (`#F1F5F9`), black text (`#000000`), `plotly_white`.
  - `theme-lion` / `lion`: Deep black/gold background (`#0a0a0c`), dark headers (`#1a1a1e`), gold accents (`#f2c64b`), `plotly_dark`.
  - `theme-dark` / `dark`: Obsidian background (`#0A0F14`), dark slate headers (`#1A1F26`), amber accents (`#F6AD55`), `plotly_dark`.

## Version 1.0: Strict 3-Tier Access Control & Zero-Data Leakage Architecture
- **Tier 1 — Visitor (Public)**: Full access to Homepage (`/`), Products & Pricing (`products.html`), Blogs & FAQs (`blog.html`), and Dashboard (`dashboard.html`).
- **Tier 2 — Normal User (Registered Free)**: Full access to all Visitor pages + profile/account management.
- **Tier 3 — Paid Subscriber / Owner (`owner@tlcs.com`)**: Full access to all Visitor pages PLUS **Research** (`metrics.html`), **Screener Matrix** (`screener.html`), **Performance Scanner** (`scanner.html`), and **TLCS Terminal** (`market-store.online`).
- **Zero-Data Leakage & Network Gate**:
  - Gated pages (`metrics.html`, `scanner.html`, `screener.html`) MUST wrap all terminal chrome, tables, and metrics inside hidden containers (`style="display:none;"`) until `window.verifyPageAccess()` confirms active subscriber or owner credentials.
  - Data fetching scripts (`trade-metrics.js`, `scanner.js`, `screener.js`, `loadAnalysisSignals()`) MUST NOT dispatch Supabase queries or subscribe to realtime channels if `verifyPageAccess` fails or `window.isSubscriberVerified` is false.
  - Eliminate duplicate legacy auth gates (e.g. `#scanner-auth-gate`) to prevent stacked lock screens.

## Subscriber Mobile Terminal Isolation (`market-store.online`)
- **Subscriber-Only Surface**: `market-store.online` is reserved exclusively for paid subscribers and owner/admins. All public marketing links ("Download App", "Launch App", "Mobile App") are removed from public marketing pages and footers. The `📲 TLCS Terminal` launch button is surfaced strictly inside the logged-in navbar pill when `isSubscriber === true`.
- **AuthGuard Lock**: `AuthGuard.tsx` in `Tv-Alert-Mobile` blocks unauthenticated visitors and free users with an informative "Active Subscription Required" paywall linking to `products.html`.
- **Noindex Protection**: `public/robots.txt` (`Disallow: /`) and `<meta name="robots" content="noindex, nofollow" />` are strictly enforced to prevent search engine indexing of the terminal domain.
- **Unified Nomenclature**: The subscriber application is officially branded **TLCS Terminal**.

## Live Hold Duration & Unentered Trade Suppression Rules
- **Live Active Trades**: Hold duration is dynamically computed from the exact moment the trade entered/filled (`metadata.real_entry_time` or entry timestamp) to the current moment (`Date.now() - liveEntryTs`), reflecting the live accumulating duration (e.g. `<1m`, `15m`, `1h 20m`).
- **Unentered / Skipped / Cancelled / Expired Trades**: Hold duration is strictly suppressed and renders `--`. Limit orders that have not filled (`ACTIVE LIMIT`) must never display hold duration.
- **Active Trade Exit Timestamps**: The `EXIT` timestamp for live active trades must strictly render `--` (never intermediate webhook update timestamps).

## Reverse-Engineering Exit Level & Price Resolution Protocol
When a trade exits but its `exit_price` or canonical exit level was not registered in the incoming webhook payload, the system applies a strict 4-tier reverse-engineering hierarchy:
1. **Tier 1 — Pine Script Status Keyword Direct Binding**:
   - If the status string contains definitive exit terminology (`"Hit TP1"`, `"Hit TP2"`, `"Hit TP3"`, `"Hit TP4"`, `"Hit Initial SL"`, `"Hit B/E"`, `"Trailing Stop"`), directly bind `exit_price` to the corresponding stored database level:
     - `TP1` → `s.target`
     - `TP2` → `s.tp2`
     - `TP3` → `s.tp3`
     - `TP4` → `s.tp4`
     - `B/E` → `s.entry`
     - `SL` → `s.stop`
     - `TRAIL` → `s.trail_sl`
2. **Tier 2 — Exact Percentage Mathematical Inversion**:
   - If `metadata.exact_pct` is recorded on the trade:
     - For Longs: $\text{exit\_price} = \text{entry} \times (1 + \text{exact\_pct} / 100)$
     - For Shorts: $\text{exit\_price} = \text{entry} \times (1 - \text{exact\_pct} / 100)$
   - Proximity Match: Test `exit_price` against canonical levels (`stop`, `entry`, `target`, `tp2`, `tp3`, `tp4`, `trail_sl`) within a $\pm 0.2\%$ tolerance window. If matched, assign the definitive level label (`SL`, `B/E`, `TP1`, `TP2`, `TP3`, `TP4`, `TRAIL`).
3. **Tier 3 — Intraday Yahoo Finance Historical Quote at `exit_at` Timestamp**:
   - Query Yahoo Finance via `fetch_yahoo_price_at_time(ticker, exit_time)` targeting 1-minute / 5-minute intraday bars at the exact exit timestamp (`exit_at` or `updated_at`).
   - If the asset currency/scale matches (within 15% of entry), use the intraday bar close.
   - For currency-mismatched futures (e.g. INR vs USD), calculate the percentage return $\Delta\%$ on Yahoo between `real_entry_time` and `exit_at`, and project it onto the local entry: $\text{exit\_price} = \text{entry} \times (1 + \Delta\%)$.
4. **Tier 4 — Database Healing & Self-Correction**:
   - Automated scripts (`yahoo_helper.py`, `cron-heal-outcomes.js`) write back the resolved `exit_price`, `metadata.exact_pct`, and canonical outcome to Supabase to prevent unclosed trade anomalies and maintain database integrity.

## Version 1.0 Production Milestone & Permanent Trade History Accumulation
- **Release Version**: `v1.0.0` / `v1.0` (Deployed across `thelioncapitalsolutions.com` and `market-store.online`).
- **Permanent Trade Accumulation**: As of August 30, 2026, all historical data reset operations are permanently concluded. Henceforth from today onward, all incoming trade signals, limit orders, fills, closures, and performance metrics are preserved in perpetuity ("till forever") across Supabase tables (`signals`, `weekly_performance_logs`, `strategy_performance`).
- **Virtual Paper Portfolio & Lot-Size Simulator**:
  - Live in the Mobile App **SCREENER Tab** (`Tv-Alert-Mobile` / `market-store.online`).
  - **Fixed Order Sizing**: Strictly 1 lot / position.
  - **Asset Quantities**: `NIFTY1!` Futures = 65 Qty, Indian Equities / Stocks = 100 Shares/Qty, MCX Crude/Gold = 100 Qty, NYMEX = 1000 Qty, Crypto = 1 Unit, Forex = 10,000 Units, World Indices = 1 Contract.
  - **Analytics**: Real-time computation of Paper Expectancy (Currency & R-multiple) and Calmar Ratio (with peak-to-trough Max Drawdown %).
- **Screener Matrix Horizontal Scrolling**:
  - Tables utilize `.table-scroll-container` and `.custom-horizontal-scrollbar` with visible tracks, `overscroll-behavior-x: contain`, and 1-tap `◀ Past Days` / `Today / Recent ▶` quick jump buttons.
- **Top-Level Constant & Function Hoisting (TDZ Safety)**:
  - Global lookup dictionaries (`MARKET_SYMBOLS`, `EXCHANGE_TAB`) and core calculation functions (`resolveOutcome`, `getExactPct`, `isRealTrade`, `formatPrice`, `getMarket`, `getDecimals`) MUST always reside at the very top of `page.tsx` outside all components. This prevents JavaScript `ReferenceError: Cannot access before initialization` (Temporal Dead Zone) when hooks and initial state memos evaluate on mount.

## Deterministic Trade Lifecycle & Ghost Limit Elimination Rules
- **Deterministic Pine Script `trade_id`**: In Pine Script, `initializeTradeSession` MUST initialize `trade.signalTime`, `trade.entryTime`, and `trade.originalEntryTime` using `time` (bar open timestamp), NEVER `timenow` (realtime millisecond clock). Using `time` ensures that `trade_id` (`syminfo.ticker + "_" + str.tostring(trade.signalTime) + "_" + trade.tradeDirection`) remains 100% deterministic and identical between the pending limit order alert, the fill alert, trailing stop updates, and the exit close alert.
- **Two-Tier TradeFill Fallback Matching**: When a `TradeFill` webhook arrives at `process-webhook-background.js`, it first attempts matching by exact `metadata->>trade_id`. If not found, it MUST execute **Attempt 2 Fallback Matching** by querying open records for the same symbol in the last 24 hours (`status IN ('OPEN', 'ACTIVE LIMIT', 'Active Limit', 'Open', 'Active')`) matching the trade direction. Upon finding an open record, it updates the existing pending limit to `Active` rather than inserting a duplicate trade row.
- **Automatic Orphan Cleanup on TradeClose**: When `TradeClose` executes, the backend automatically issues a cleanup query updating any lingering `OPEN` limit rows for that symbol created on the same calendar day to `status = 'CANCELLED'`.
- **Automatic Weekly Performance Logs Synchronization**: `cron-heal-outcomes.js` runs every 30 minutes and automatically aggregates all closed trades into `weekly_performance_logs` across all markets (`nifty`, `mcx`, `nymex`, `crypto`, `forex`, `world`), ensuring the Mobile App **ANALYTICS** tab and Weekly Performance Edge matrix remain synchronized in real-time.
- **Pine Script Bar Replay Memory Optimization**:
  - **No Global `max_bars_back = 2000`**: Indicator declaration must be `indicator('TLCS All Signal Alerts', overlay = true, max_lines_count = 500, max_labels_count = 500)` without `max_bars_back = 2000` to prevent allocating 2,000-element history buffers for every intermediate AST node.
  - **Gate Chart Drawing Loops to `barstate.islast`**: Standard pivot visualization loops (`getPivots`, lines, labels) must be enclosed in `if barstate.islast` so they execute once on the final bar instead of allocating hundreds of thousands of drawing objects across historical bars during bar replay scrubbing.
  - **Zigzag Depth**: Capped to 20 pivots (`Zigzag.new(..., 20, 0)`), reducing User Defined Type (UDT) heap memory by >90%.






