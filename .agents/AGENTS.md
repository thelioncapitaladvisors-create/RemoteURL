## No R-Multiple Recalibration or Fallbacks
- NEVER try to mathematically guess or recalibrate missing values on the frontend using other fields.
- For example, if a TradeClose webhook exits via a trailing stop and TradingView sends `status: "Break Even"` with no `r_multiple` or `profit_pct`, DO NOT try to recalculate what TP level it reached based on the profit amount or an R-multiple threshold (e.g. `r >= 2.5`). If it says "Break Even", it goes straight into the `B/E` bucket.
- Similarly, NEVER use fallback math to infer `profit_pct` from `r_multiple` (e.g., `profit_pct = r_multiple * 0.5`) or vice-versa. If the Pine Script does not send the specific metric directly in the webhook payload, that metric remains 0 or null. The system must STRICTLY respect exactly what the Pine Script sends, even if it results in empty states or zeroes in the UI.

## Exit Categorization (Rigid vs Dynamic Exits)
- Do NOT bucket trades into static levels (e.g., "TP3" or "TP4") based on the highest level they *touched*. This corrupts the data because it hides the actual realized exit.
- A trade belongs in a `TP` bucket ONLY if it *actually closed* at that exact level (e.g., via a limit order, or a step-based trailing stop that precisely locked in that previous level).
- For arbitrary, continuous trailing stops that close between defined levels, do NOT mathematically guess the closest level. The Pine Script should explicitly send `"status": "Trailing Stop"`.
- Both the Web and Mobile UIs have a dedicated `TRAIL` (or `Trailing Stop`) bucket to correctly categorize these dynamic, arbitrary exits without polluting the fixed `TP` buckets.
