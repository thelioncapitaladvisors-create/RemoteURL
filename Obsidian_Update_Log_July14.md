# July 14, 2026 - Distorted Statistics & Missing exact_pct Fix

## RCA
- The dashboards and metrics on the mobile app and website were showing 0.00% Exact Percentage and 0 wins for all recently closed trades (like `Hit SL` and `Hit TP`).
- This was occurring because TradingView alerts for trades hitting the Stop Loss or Take Profit frequently omit a `close_price` in the payload. 
- Without an exit price, `exact_pct` math inside the webhook evaluated to `null`, causing the `exact_pct` property to be entirely missing from the Supabase JSONB `metadata` column upon trade closure.
- Since the V1.0 rule strictly requires exact percent math for performance metrics, the UI fell back to 0.00% and miscategorized trades.
- Additionally, a bug in the Next.js `route.ts` API route directly spread the stringified `metadata` returned by the Supabase client (`{ ...activeSignal.metadata }`), corrupting the object into a string-indexed array.

## Resolution
1. **Intelligent Fallback in Webhooks (`route.ts` and `process-webhook-background.js`)**: 
   - Added logic to safely fallback to the `stop` price (when hitting SL) or the `target` price (when hitting TP) if a direct `close_price` is missing from the incoming alert payload.
   - This ensures `exact_pct` is always mathematically computed and injected into the metadata upon trade closure.

2. **Metadata Parsing Fix (`route.ts`)**: 
   - Modified `route.ts` to explicitly parse the existing `metadata` using `JSON.parse()` before spreading it, ensuring the JSONB column is never overwritten with corrupted string indices.

3. **Database Retroactive Repair**: 
   - Wrote and ran a Python script (`fix_missing_exact_pct.py`) to query all 97 closed trades in the database missing `exact_pct`. 
   - The script successfully inferred their missing exit prices based on their outcomes (Stop Loss vs Target) and retroactively recalculated and patched their `metadata.exact_pct` directly in Supabase.

## Impact
- The AI Dashboard and AI Research pages immediately reflect accurate, mathematically-derived win rates, exact percentages, and active trade counts.
- Historic trades that were previously missing `exact_pct` are fully restored.
