# Platform v1.0: Native Webhook Tearsheet SVG, Anti-Hang Hardening & EOD Broadcast Automation

**Release Date:** October 5, 2026  
**Version:** `v1.0.0` (Production Hardened Baseline)  
**System Scope:** Next.js Mobile Application (`Tv-Alert-Mobile`), Netlify Background Serverless Functions (`cron-instagram-stats.js`, `cron-eod-close.js`, `dhan-option-chain.js`), Backend API Routes (`api/fno-buildups`, `api/option-chain`), Master Repositories (`Tv-Alert-Mobile`, `TLCS_Website_Deploy`, `RemoteURL`).

---

## 1. Executive Summary

On October 5, 2026, Platform **Version 1.0** underwent critical UI performance standardization, endpoint anti-hang hardening, and automated daily EOD broadcast expansion across Telegram and Instagram channels:

1. **Native SVG Webhook Performance Tearsheet**: Replaced legacy iframe (`strategy_tearsheet.html`) for Webhook signals (`engineSource === 'TV'`) with the native SVG component `DhanHQPerformanceTearsheet`. Maintained full 3-tab functionality (`Equity Curve`, `Drawdowns`, `Trade Waterfall`), explicit high-contrast X/Y axis labels (`fill="currentColor"`), and smooth touch/pointer hover readouts across all 7 visual themes.
2. **F&O Stock Buildups & Option Chain Zero-Hang Hardening**:
   - Backend APIs (`/api/fno-buildups/route.ts` & `/api/option-chain/route.ts`) equipped with `AbortSignal.timeout(4000)` on all outbound Dhan HQ requests.
   - Added socket destroy timeout handling (`req.on('timeout')`) in `netlify/functions/dhan-option-chain.js`.
   - Client component `HubOptionChain` upgraded with `signal: AbortSignal.timeout(5000)` and a continuous 15-second background auto-refresh interval (`setInterval(..., 15000)`).
3. **Automated Daily EOD Telegram & Instagram Broadcaster**:
   - Implemented `postToTelegram(stats)` in `cron-instagram-stats.js` for market-wise HTML performance dispatches (`TELEGRAM_CHAT_ID_NIFTY`, `TELEGRAM_CHAT_ID_MCX`, `TELEGRAM_CHAT_ID_NYMEX`, `TELEGRAM_CHAT_ID_CRYPTO`, `TELEGRAM_CHAT_ID_FOREX`, `TELEGRAM_CHAT_ID_WORLD`).
   - Integrated post-sweep broadcast execution inside `cron-eod-close.js`, ensuring daily session metrics (Closed Executions, Wins/Losses/BE, Win Rate, Profit Factor, Best Trade, WTD Edge, All-Time Edge) are automatically posted to Telegram channels and Instagram (@thelioncapitaladvisors) at session close.

---

## 2. Technical Architecture & Modifications

### A. Native Webhook Tearsheet SVG Component
- **Component File**: [`Tv-Alert-Mobile/src/app/page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx)
- **Engine Source Parity**: `<DhanHQPerformanceTearsheet signals={engineSource === 'TV' ? signals : dhanBlackboxSignals} theme={theme} marketFilter={analyticsMarket} engineSource={engineSource} />`.
- **High-Contrast SVG Ticks**: SVG `<text>` elements enforce explicit `fill="currentColor"` with `text-slate-600 dark:text-slate-300 font-bold`, permanently eliminating invisible white-on-white text in light and dark themes.

### B. Anti-Hang Hardening & Auto-Refresh
- **`api/fno-buildups/route.ts`**: Added `AbortSignal.timeout(4000)`, 30s cache TTL, and fail-safe 200 OK return payload on exception.
- **`api/option-chain/route.ts`**: Added `AbortSignal.timeout(4000)` to TOTP token generation, `expirylist`, `optionchain`, and Netlify proxy calls.
- **`HubOptionChain` (page.tsx)**: Added 15s auto-refresh interval timer and `AbortSignal.timeout(5000)` guards on fetch requests.
- **`netlify/functions/dhan-option-chain.js`**: Added `req.on('timeout', () => { req.destroy(); resolve(null); })` to close hanging Node.js HTTPS sockets instantly.

### C. Automated Daily EOD Telegram & Instagram Dispatcher
- **Function File**: [`TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js)
- **Telegram HTML Formatting**: Formats clean, structured HTML performance reports with section breaks (`📊 DAILY SESSION METRICS`, `📅 CURRENT WEEK PERFORMANCE (WTD)`, `🏆 ALL-TIME CUMULATIVE EDGE`).
- **Session Close Sweeper Integration**: [`cron-eod-close.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-eod-close.js) automatically triggers `runInstagramAutomation()` after trade closures complete.

---

## 3. File Modification Summary

| Repository / Module | File Path | Description of Changes |
| :--- | :--- | :--- |
| **Tv-Alert-Mobile** | [`src/app/page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) | Integrated native SVG Webhook tearsheet, added 15s auto-refresh to `HubOptionChain`, added `AbortSignal.timeout(5000)` to fetches. |
| **Tv-Alert-Mobile** | [`src/app/api/fno-buildups/route.ts`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/fno-buildups/route.ts) | Added `AbortSignal.timeout(4000)` to live quotes fetch, expanded cache TTL, fail-safe payload. |
| **Tv-Alert-Mobile** | [`src/app/api/option-chain/route.ts`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/option-chain/route.ts) | Added `AbortSignal.timeout(4000)` across all external Dhan API requests & Netlify fallback. |
| **TLCS_Website_Deploy** | [`netlify/functions/cron-instagram-stats.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js) | Implemented `postToTelegram(stats)` and integrated into `runInstagramAutomation`. |
| **TLCS_Website_Deploy** | [`netlify/functions/cron-eod-close.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-eod-close.js) | Linked post-sweep EOD broadcast trigger following trade closure completions. |
| **TLCS_Website_Deploy** | [`netlify/functions/dhan-option-chain.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/dhan-option-chain.js) | Added `req.on('timeout')` socket destroy handler. |

---

## 4. Empirical Verification & Build Status

- **Compilation**: Tested via `npm run build` inside `Tv-Alert-Mobile` — **Exit Code 0** (`✓ Compiled successfully`).
- **Git Deployment**: Committed and pushed to `main` branch across `Tv-Alert-Mobile` (`c5b0757`), `TLCS_Website_Deploy` (`ee54eb9b`), and `RemoteURL` (`9c78eb6`).
