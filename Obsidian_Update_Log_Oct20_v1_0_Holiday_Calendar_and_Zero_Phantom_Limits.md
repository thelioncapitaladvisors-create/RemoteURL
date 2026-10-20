# Obsidian Update Log: Version 1.0 Indian Exchange Holiday Calendar & Zero-Phantom Holiday Signal Gating
**Date**: October 20, 2026  
**Module**: Algo Engine (`algo_engine/nse100_scanner.py`), Mobile Terminal (`Tv-Alert-Mobile/src/app/page.tsx`), API Routes (`/api/option-chain`, `/api/fno-buildups`), Serverless Functions (`TLCS_Website_Deploy/netlify/functions/dhan-option-chain.js`, `TLCS_Website_Deploy/netlify/functions/dhan-fno-buildups.js`), Documentation (`AGENTS.md`)  

### Key Updates:
1. **Official 2026 Holiday Calendar Enforcement**: Integrated canonical 2026 NSE Equities (`NSE_HOLIDAYS_2026`) and MCX Commodities (`MCX_FULL_HOLIDAYS_2026`, `MCX_MORNING_HOLIDAYS_2026`) calendars across the entire platform.
2. **Scanner Daemon Hardening**: Hardened `algo_engine/nse100_scanner.py` with candle timestamp and IST date validation against exchange holidays. Prior-day closing candles returned by DhanHQ on holidays are no longer evaluated as active today.
3. **Database Cleanup**: Hard-deleted all 10 phantom signals from Supabase `public.shadow_signals` (`outcome=eq.OPEN&created_at=gte.2026-10-20T00:00:00Z`). Verified count dropped to 0.
4. **Client-Side Limit Gating**: Updated `isActiveLimit()` in `Tv-Alert-Mobile/src/app/page.tsx` to strictly require `isNseMarketHours()` / `isMcxMarketHours()`. Unexecuted limit orders are strictly inactive when markets are closed.
5. **API Route Holiday Resilience**: Hardened `/api/option-chain` and `/api/fno-buildups` to return `marketStatus: 'EOD'` and serve authentic Supabase EOD snapshots during holidays.
