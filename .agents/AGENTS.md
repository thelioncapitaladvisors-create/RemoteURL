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
- NEVER try to mathematically guess, calculate, or inject fallback values for Bias or Day Type on the backend or frontend based on CPR or price levels. Always rely strictly and exclusively on the keys sent by the TradingView indicator (`opening_bias` and `day_type`).
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