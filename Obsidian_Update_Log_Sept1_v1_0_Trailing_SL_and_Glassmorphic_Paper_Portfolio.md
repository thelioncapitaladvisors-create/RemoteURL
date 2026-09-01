# Version 1.0 Production Update: Trailing SL Webhook Resolution, 3-Row Glassmorphic Layout & Screener Matrix Controls

**Release Date:** September 1, 2026  
**Milestone Version:** `v1.0.0` (Production)  
**System Components Affected:** `Netlify Webhooks (process-webhook-background.js)`, `Next.js Webhook Route (route.ts)`, `Tv-Alert-Mobile (page.tsx)`

---

## 1. Trailing Stop Loss Webhook Payload Key Resolution
- **Problem**: In the mobile app trade pills, the `TRAIL SL` box did not update when trailing stop loss moved, continuously displaying the initial `STOP LOSS` level (e.g. `154,407.00`). Telegram Trailing SL alert notifications were also skipped.
- **Root Cause**:
  1. Pine Script's `sendTrailingSLAlert()` transmits the new trailing stop level under the JSON payload key `"slLevel"` (and the message under `"tradeMessage"`).
  2. The webhook processors (`process-webhook-background.js` and `route.ts`) exclusively searched for `body.stop`, which was `undefined`.
  3. Consequently, `updateData.trail_sl` was saved as `null` in Supabase, causing the frontend UI card to fall back to `stopVal` (initial stop loss).
- **Architectural Fix**:
  - **Multi-Key Trailing Resolution**: Webhook processors now resolve trailing levels defensively:
    ```javascript
    const trailLevel = body.slLevel || body.stop || body.trail_sl || body.trailing_stop || body.sl || null;
    const trailMsg = body.tradeMessage || body.analysis || (trailLevel ? `Trailing SL moved to ${trailLevel}` : null);
    ```
  - **Trade Close Persistence**: `TradeClose` webhook handlers now also record and persist the final `trail_sl` level upon position closure.
  - **Telegram & Push Dispatch**: Trailing stop loss movement dispatches live Telegram alerts and Web Push notifications using the resolved `trailLevel`.

---

## 2. Virtual Paper Portfolio 3-Row Glassmorphic Grid Layout
- **Problem**: The market selection chips in the **Virtual Paper Portfolio** were rendered in a single horizontal scrolling row, causing markets on the right to be clipped and requiring tedious horizontal scrolling.
- **Architectural Fix**:
  - **3-Row 2-Column Responsive Grid**: Restructured market selection into a balanced 2-column grid (`grid grid-cols-2 gap-2 w-full`), displaying all 6 markets across exactly 3 rows with zero horizontal scrolling:
    - **Row 1**: 📈 `NIFTY 50` (`NIFTY1! · 65 Qty`) | 🛢️ `NYMEX & COMEX` (`CL / NG / GC / SI · 1 Lot`)
    - **Row 2**: ₿ `CRYPTO TOP 25` (`BTC / ETH`) | 💱 `FOREX PAIRS` (`Major & Minor`)
    - **Row 3**: 🌍 `WORLD INDICES` (`Global Futures`) | 🌐 `ALL MARKETS` (`Multi-Asset`)
  - **Glassmorphic Theme**:
    - Translucent frosted glass containers (`backdrop-blur-md`, `border-white/10` to `border-slate-300/70`).
    - High-contrast typography (`text-emerald-950 dark:text-emerald-200`, `text-amber-950 dark:text-amber-200`, `text-slate-700 dark:text-slate-300`) ensuring 100% legibility in both Light and Dark themes.
    - Active status indicator lights and luminous highlights on selected markets.

---

## 3. TLCS Screener Matrix: 3-Row Glassmorphic Layout & Header Controls
- **Problem**: The market chips above the 7-day multi-section screener matrix were in a single overflowing row, and the large matrix table lacked quick collapse controls on mobile screens.
- **Architectural Fix**:
  - **3-Row 6-Column Responsive Market Grid**:
    - **Row 1** (`col-span-3` each): `🌐 ALL MARKETS` (`Multi-Asset Matrix`) | `📈 NIFTY 50` (`NSE Equities`)
    - **Row 2** (`col-span-3` each): `⛽ MCX COMMODITIES` (`Crude / Gold / Silver`) | `🛢️ NYMEX & COMEX` (`US Energy & Metals`)
    - **Row 3** (`col-span-2` each): `₿ CRYPTO TOP 25` (`BTC / ETH`) | `💱 FOREX PAIRS` (`Major & Minor`) | `🌍 WORLD INDICES` (`Global Futures`)
  - **START AFRESH Button**: Resets the active screener matrix market filter back to `ALL` with an instantaneous status banner notification.
  - **COLLAPSE / EXPAND Button**: Minimizes or expands the entire 7-day screener table and market filters with a single tap.
