---
Date: 2026-08-08
Version: 3.5
Author: The Lion Capital Solutions AI
---

# 🚀 TLCS System Update v3.5: H4/L4 Boundary Enforcement & Entry Time Fallback Fix

## Overview
This update introduces a performance-driven Camarilla pivot boundary filter in the Pine Script strategy engine that prevents all new trade signals from firing when price is at or beyond the H4 (upside) and L4 (downside) levels. Additionally, a mobile app bug was fixed where executed trades were displaying `HELD: --` and missing entry timestamps when `real_entry_time` was absent from the metadata.

## Modifications

### 1. Pine Script (`TLCS_Live_Pivot_Alerts.pine` / TradingView)

- **H4/L4 Boundary Enforcement**: Added two boolean flags (`longAllowed = close < H4`, `shortAllowed = close > L4`) that gate all 6 trade signal booleans (Missile Buy/Sell, Scalp Buy/Sell, Lightning Buy/Sell). Trades at or beyond these Camarilla extremes are now universally blocked across all markets.
- **Bounce Arrow Gating**: The `BounceUp` / `BounceDown` large arrow `plotshape()` calls are also gated by the same H4/L4 flags, preventing visual noise in overextended zones.
- **Defensive Safety Net**: Added an inner H4/L4 gate inside `initializeAndPushTrade()` using local boolean copies (`_buy = buyCond and close < H4`, `_sell = sellCond and close > L4`) to prevent trade object creation even if upstream booleans slip through. This approach avoids Pine Script v6's immutable function parameter restriction (`CE10175`).
- **What is NOT changed**: All pivot level labels (H3, H4, H5, L3, L4, L5, VAH, VAL), reversal pattern markers (Wick, Extreme, Outside, Doji), TP/SL visual lines, CPR/weekly/monthly structures, S&R lines, and bar coloring remain completely untouched.

### 2. Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`)

- **Entry Time Fallback Fix**: Fixed a bug where executed trades that lacked `metadata.real_entry_time` displayed `HELD: --` and no entry timestamp. The `entryTime` variable now falls back to `signal_ts` or `created_at` for executed (non-limit-order) trades while still correctly showing `null` for unfilled Active Limit orders.
- **Affected Trades**: This fix retroactively corrects display for all historical trades in the HUB tab where `real_entry_time` was not injected by the webhook (e.g., older trades or edge cases).

### 3. Web Dashboard (`TLCS_Website_Deploy/trade-metrics.js`)

- **Entry Time Fallback Fix**: Applied the same fallback logic to the blackbox entry time renderer. When `meta.real_entry_time` is missing for a live/closed trade, the engine now falls back to `data.signal_ts` or `data.created_at` instead of displaying an empty string.

### 4. Frontend & Backend Assessment (No Changes Required)

- **`process-webhook-background.js`**: Already stores H4/L4 in the `pivots` table. Since filtered signals never fire webhooks, no defensive backend filtering is needed.
- **Dashboard/Scanner/Mobile**: These are display layers that render only what exists in Supabase. H4/L4-filtered trades will never appear because they are never created.
- **Conclusion**: The Pine Script is the single authoritative signal source. By blocking signals at the TradingView level, the entire downstream pipeline (webhook → Netlify → Supabase → Dashboard/Mobile) automatically respects the H4/L4 boundary.

## Architectural Rationale

The H4 and L4 Camarilla pivot levels represent statistical extremes of the prior day's range. Trades initiated at or beyond these levels historically show lower win rates because:
1. Price is already overextended relative to the prior day's range
2. The risk-to-reward ratio degrades as price moves further from the pivot center
3. Mean reversion probability increases at these extremes

By enforcing this boundary at the signal source (Pine Script), the system eliminates low-probability trades before they consume capital, improving the overall Profit Factor and Win Rate metrics across all 6 markets.

### 5. Architectural Rules Established
- **NCPR Exception Immutable**: The Narrow CPR (`NCPR`) logic exception must NEVER be removed from the sideways filter block.
- **Dynamic Variable Truth**: The system acknowledges that variables calculated on a tick-by-tick basis (e.g., `mX`) may drift over the course of a day. The engine strictly respects the evaluation of these variables at the precise moment a signal was generated, even if the label at the end of the day renders differently (e.g., drifting from "BIG MOVE" back to "TYPICAL DAY").

### Universal Normalized NCPR (Exact Mathematics)
* **Problem**: Measuring CPR width against absolute asset prices (e.g., `DPi`) causes the formula to fail on assets with high nominal prices but small relative daily ranges (like Forex). Furthermore, normalizing against a single previous day's range (`DH - DL`) causes the formula to fail when the market experiences back-to-back compressed days.
* **Exact Mathematical Anchor**: The formula for CPR width is mathematically capped at a maximum of `33.33%` of the True Range `(|2C - H - L| / 3)`. Therefore, a "Narrow" CPR (representing the bottom third of all possible CPR widths) is exactly bounded at `< 11.11%`.
* **Solution**: The engine now uses the exact mathematical formula anchored against the 14-day Daily ATR to calculate the Normalized NCPR constraint. This universalizes the logic across Forex, Crypto, Indices, and Commodities:
  ```pine
  float daily_atr = request.security(syminfo.tickerid, 'D', ta.atr(14)[1], lookahead = barmerge.lookahead_on)
  float stableRange = math.max(daily_atr, syminfo.mintick)
  float cprWidth    = math.abs(DTcf - DBcf)
  bool  NCPR        = 11.11 > (cprWidth / stableRange) * 100
  ```
