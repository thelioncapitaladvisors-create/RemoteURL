## No R-Multiple Recalibration or Fallbacks
- NEVER try to mathematically guess or recalibrate missing values on the frontend using other fields.
- For example, if a TradeClose webhook exits via a trailing stop and TradingView sends `status: "Break Even"` with no `r_multiple` or `profit_pct`, DO NOT try to recalculate what TP level it reached based on the profit amount or an R-multiple threshold (e.g. `r >= 2.5`). If it says "Break Even", it goes straight into the `B/E` bucket.
- Similarly, NEVER use fallback math to infer `profit_pct` from `r_multiple` (e.g., `profit_pct = r_multiple * 0.5`) or vice-versa. If the Pine Script does not send the specific metric directly in the webhook payload, that metric remains 0 or null. The system must STRICTLY respect exactly what the Pine Script sends, even if it results in empty states or zeroes in the UI.

## Exit Categorization (Rigid vs Dynamic Exits)
- Do NOT bucket trades into static levels (e.g., "TP3" or "TP4") based on the highest level they *touched*. This corrupts the data because it hides the actual realized exit.
- A trade belongs in a `TP` bucket ONLY if it *actually closed* at that exact level (e.g., via a limit order, or a step-based trailing stop that precisely locked in that previous level).
- For arbitrary, continuous trailing stops that close between defined levels, do NOT mathematically guess the closest level. The Pine Script should explicitly send `"status": "Trailing Stop"`.
- Both the Web and Mobile UIs have a dedicated `TRAIL` (or `Trailing Stop`) bucket to correctly categorize these dynamic, arbitrary exits without polluting the fixed `TP` buckets.

## Pure R-Multiple Math for Performance Metrics
- When calculating Profit Factor and Expectancy on historical data where absolute percentage amounts (`profit_pct`) might be absent or 0, ALWAYS use raw R-Multiples instead of injecting fallback percentage math.
- **Profit Factor**: Calculate as `(Sum of Winning R's) / (Sum of Losing R's)`
- **Expectancy**: Calculate natively using R `((Win Rate * Avg Win R) - (Loss Rate * Avg Loss R))` and denote the metric with an `R` suffix instead of a `%` sign, representing the expected R per trade.

## Symbol Normalization and Market Categorization
- ALWAYS normalize symbol names before performing market category checks (e.g., strip exchange prefixes like `NSE:`, `TVC:`, and continuous suffix `1!`). Use the normalized/cleaned symbol for list-based matching.
- Multi-market overlap: Some symbols (such as indices like `NIFTY`) belong to multiple categories (e.g., domestic equities and world indices). Ensure that signal lists and performance filters check both the primary resolved category and explicit symbol membership arrays to correctly populate all relevant tabs or display cards.

## Strict Bias and Day Type Parsing
- NEVER try to mathematically guess, calculate, or inject fallback values for Bias or Day Type on the backend or frontend based on CPR or price levels. Always rely strictly and exclusively on the keys sent by the TradingView indicator (`opening_bias` and `day_type`).
- Only apply cosmetic label replacements on the frontend UI:
  - Map `"Double Distribution"` to `"DD"` (and `"Double Distribution Trend"` to `"DD Trend"`) to match the dashboard conventions.
- Maintain column sizing for table containers (`min-width: 180px` for Bias and `min-width: 160px` for Day Type) on the scanner pages to prevent longer text labels from truncating or wrapping.


