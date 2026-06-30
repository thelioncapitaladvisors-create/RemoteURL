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
- Multi-market overlap: Some symbols (such as indices like `NIFTY`) belong to multiple categories (e.g., domestic equities and world indices). Ensure that signal lists and performance filters check both the primary resolved category and explicit symbol membership arrays to correctly populate all relevant tabs or display cards.

## Strict Bias and Day Type Parsing
- NEVER try to mathematically guess, calculate, or inject fallback values for Bias or Day Type on the backend or frontend based on CPR or price levels. Always rely strictly and exclusively on the keys sent by the TradingView indicator (`opening_bias` and `day_type`).
- Only apply cosmetic label replacements on the frontend UI:
  - Map `"Double Distribution"` to `"DD"` (and `"Double Distribution Trend"` to `"DD Trend"`) to match the dashboard conventions.
- Maintain column sizing for table containers (`min-width: 180px` for Bias and `min-width: 160px` for Day Type) on the scanner pages to prevent longer text labels from truncating or wrapping.
