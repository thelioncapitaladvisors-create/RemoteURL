# Version 1.6.0 Update Log - July 24, 2026

## 🛠️ System Architecture, Indicator & Telegram Channel Upgrades

### 1. NYMEX-Exclusive Telegram Channel Dispatcher & Live Connection Verification
- **Verified Telegram Connection**: Ran a live diagnostic API dispatch to Telegram channel **`@TLCS_Alerts`** (Numeric Chat ID: **`-1001555378566`**). Telegram API returned `ok: true` and delivered test message ID `#1343`.
- **Strict NYMEX Market Filter**: Updated [`process-webhook-background.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/process-webhook-background.js) and [`route.ts`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/webhook/route.ts) with `isNYMEXSymbol()`. Filtered Telegram notifications **EXCLUSIVELY for NYMEX symbols** (`CL`, `GC`, `HG`, `HO`, `NG`, `PA`, `PL`, `RB`, `SI` and `GC1!`, `CL1!`, `NG1!`, `SI1!`). Non-NYMEX trades (NIFTY, MCX, Crypto, Forex, World) continue processing on Web/Mobile dashboards but are excluded from Telegram to eliminate noise.
- **Active Trades Only Rule (Silenced Pending Limits)**: Telegram notifications fire **ONLY** when a NYMEX trade actually fills and becomes a **LIVE ACTIVE** executed trade (`⚡ NYMEX TRADE ACTIVE`), or when a live trade moves trailing stop / closes (`TARGET` / `SL`). Pending limit orders (`ACTIVE LIMIT` / `OPEN`) are strictly silenced on Telegram.

---

### 2. Pure Level Badging System & UI Standardization
- **Standardized Exit Badging**: Standardized outcome badges across Mobile ([`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)) and Web ([`trade-metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js)) using `getDisplayExitLevel(signal)`.
- **Clean Label Mappings**:
  - `"Hit Initial SL"` / `"Hit SL"` → **`SL`** (🔴 Red Pill)
  - `"Hit B/E"` / `"Hit Breakeven"` → **`B/E`** (🔵 Blue Pill)
  - `"Completed TP1"` → **`TP1`** (🟢 Green Pill)
  - `"Completed TP2"` → **`TP2`** (🟢 Green Pill)
  - `"Completed TP3"` → **`TP3`** (🟢 Green Pill)
  - `"Completed TP4"` → **`TP4`** (🟢 Green Pill)
  - `"Trailing Stop"` → **`TRAIL`** (🟢 Green Pill)
  - `"Hit EMA"` → **`EMA`** (🟢 Green Pill)
  - `"Divergence Exit"` → **`DIV`** (🟢 Green Pill)
  - `"Cancelled"` → **`CANCELLED`** (⚪ Gray Pill)
- **Eliminated Verbose Strings & Price Spills**: Removed raw text strings (e.g. `HIT INITIAL SL`) and numeric price spills (`1,865.14`) from outcome badges.

---

### 3. 1-Tap HD Trade Card Image Sharing for Telegram
- **High-Resolution Graphic Export**: Enhanced `handleShare` in [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) to generate 1080×860 HD JPEG trade card graphics (`${symbol}_TLCS_Alert.jpg`).
- **Auto-Formatted Telegram Caption**: Integrated structured Telegram text formatting (Header, Direction, Entry, SL, Target, R:R ratio like `2.01R`, Opening Bias, Day Type, and Status) into `navigator.share()`. Tapping the share icon on any NYMEX trade card and selecting Telegram attaches the HD card graphic + structured parameters directly.

---

### 4. Divergence Pine Script Webhook Alert Output (JSON Format)
- **Clean JSON Alert Formatting**: Updated [`TLCS_Native_Divergence.pine`](file:///Users/vishant/Documents/Project/TV%20Indicator/TLCS_Native_Divergence.pine) to replace raw text alerts (`alert('Alert : ' + priceTooltipText)`) with clean JSON payloads (`"trigger":"Divergence"`, `"symbol"`, `"type"`, `"price"`, `"oscillator"`).
- **Added `webhook_secret` Input**: Added input string for `webhook_secret` in the Alerts group of `TLCS_Native_Divergence.pine` for zero-guesswork webhook security parsing.

---

### 5. Single Infrastructure & Canonical System Rules Locked (`AGENTS.md`)
- **Strict Netlify Hosting Rule**: Documented in [.agents/AGENTS.md](file:///Users/vishant/Documents/Project/.agents/AGENTS.md#L8-L11) that all system infrastructure (Web Dashboard, Mobile App backend endpoints, Netlify background workers, and Telegram dispatchers) runs **EXCLUSIVELY on Netlify** (`thelioncapitalsolutions.com` / `market-store.online`). No Vercel deployments exist.
- **NYMEX-Only & Active Trades Rule**: Added explicit rules to `AGENTS.md` enforcing NYMEX-only Telegram dispatches and silencing unexecuted limit orders.

---

### 6. Repository & Submodule Synchronization
- **`TV Indicator/TLCS_Native_Divergence.pine`**: Updated and committed to `main` (`bcd0104`).
- **`TLCS_Website_Deploy`**: Committed and pushed `00867f4`, `8c2f345`, `a24ce37`, `81685f3`, `86c8ad4`, `84ceb63` to `main`.
- **`Tv-Alert-Mobile`**: Committed and pushed `3c8bfd6`, `c1e3af9`, `33ad377`, `768e901`, `f726ca5`, `c34b540` to `main`.
- **Root Repository**: Committed and pushed `1453158`, `fb2f1e1` and latest submodule pointer updates to `main`.
