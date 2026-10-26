# Platform Version 1.0 Update Log: Virgin CPR Touch Alerts & Insights Tab Filter

**Timestamp:** October 26, 2026 (22:53 IST)  
**Author:** Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024  
**Release Tag:** `v1.0`  

## Changes Summary
1. **DhanHQ Python BlackBox Engine (`algo_engine/pivots.py` & `algo_engine/nse100_scanner.py`)**:
   - Added `is_touching: bool = False` to `VirginCPRZone`.
   - Updated `detect_virgin_cpr_zones` to retain currently testing zones rather than skipping with `continue`.
   - Added `zone_date` and `is_support` to `detect_virgin_cpr_touches`.
   - In `algo_engine/nse100_scanner.py`, wired `detect_virgin_cpr_touches` into each bar evaluation cycle to generate `LONG VIRGIN CPR` and `SHORT VIRGIN CPR` with complete metadata (`is_vcpr: True`, `is_vcpr_touch: True`, `vcpr_touch_date`, `vcpr_touch_price`, `vcpr_direction`).
2. **Next.js Webhook Fallback Parser (`Tv-Alert-Mobile/src/app/api/webhook/route.ts`)**:
   - Added fallback regex parser for TradingView alert dialog notifications containing `VCPR` or `Virgin CPR`.
   - Successfully converts text alerts (e.g. `🚨 [LUPIN (VCPR Dated 22-Oct-2026)] BULLISH SUPPORT TEST (Bounce)...`) into canonical trades with touch metadata.
3. **Mobile Terminal Insights Tab Screener (`Tv-Alert-Mobile/src/app/page.tsx`)**:
   - Added `dhanVcprSubFilter` state: `'TOUCH' | 'MAGNET' | 'ALL'`.
   - Guaranteed permanent visibility of the `Virgin CPR` tab (`count > 0 || t.id === 'VCPR'`).
   - Added sub-filter button group: `[⚡ TOUCHED ALERTS]` vs `[🧲 UNTOUCHED MAGNETS]` vs `[ALL]`.
   - Enhanced screener table row with `⚡ TOUCHED` tag, `VCPR Dated <Date>`, touch price `• Touch @ ₹...`, zone range, and directional badge (`▲ SUPPORT BOUNCE` / `▼ RESIST REJECT`).
   - Enhanced Asset Inspection modal with formation date, touch price level, zone coordinates, and PivotBoss execution guidelines.
4. **TradingView Pine Script Indicator (`TV Indicator/TLCS_Virgin_CPR_Zones.pine`)**:
   - Added input `alertFormatMode` (`'Text Alert'` vs `'JSON Webhook'`).
   - Supports structured JSON webhook dispatch and text alerts.
5. **Testing & Build Verification**:
   - 114/114 Python unit tests pass in `algo_engine/tests`.
   - Next.js production build (`npm run build`) completed with 0 errors across all routes.
