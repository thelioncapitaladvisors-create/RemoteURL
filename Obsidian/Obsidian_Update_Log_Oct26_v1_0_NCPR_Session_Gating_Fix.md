# Obsidian Update Log: Narrow CPR Session Gating Calibration & Historical Date Offset Fix (v1.0)

**Date**: October 26, 2026  
**Author**: Antigravity Quantitative AI Engineering Team  
**Scope**: Mobile Terminal Screener (`Tv-Alert-Mobile/src/app/page.tsx`), Dhan Feed Historical Level Ingestion (`algo_engine/feeds/dhan_feed.py`), Phase 2 Test Suite (`algo_engine/tests/test_phase2.py`).

---

### Key Accomplishments
1. **Fact-Backed Verification**:
   - Proven that ONGC was Narrow CPR on Friday, Oct 23, 2026 (CPR ratio = 3.03% < 5.0%), and Wide CPR on Monday, Oct 26, 2026 (CPR ratio = 33.33% >> 5.0%).
   - Verified that Supabase `shadow_signals` logged ONGC and LUPIN on `2026-10-23` with `is_ncpr: true`, and zero NCPR signals on `2026-10-26`.
2. **System-Wide Active Session Principle in Screener**:
   - Implemented `hasAnyBlackboxToday` checking if *any* BlackBox signal exists for today across the system.
   - When `sessionFilter === 'TODAY'` and the market has traded today, setup categories strictly filter for `isToday === true`. Categories with 0 setups legitimately display 0 setups rather than silently falling back to Friday's date.
   - Added interactive `[TODAY]` vs `[ALL]` session selector toggle in the screener table header.
   - Added session date badges (`[TODAY]` in emerald, `[23-OCT]` in slate) next to every symbol in the screener table.
3. **Historical Candle Timestamp Ingestion**:
   - Updated `fetch_daily_levels` in `algo_engine/feeds/dhan_feed.py` to inspect the last bar timestamp. If the last bar is yesterday (closed candle), it takes `highs[-1]`, preventing taking Thursday (`highs[-2]`) when calculating Monday's CPR.
4. **Verification**:
   - Added `test_dhan_historical_daily_levels_indexing` in `algo_engine/tests/test_phase2.py`.
   - All 114 unit tests pass with 0 errors.
   - Next.js build passes with 0 errors.
