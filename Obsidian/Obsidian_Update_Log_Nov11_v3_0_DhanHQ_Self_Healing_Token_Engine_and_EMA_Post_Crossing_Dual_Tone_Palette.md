# Obsidian Update Log: November 11, 2026 — Platform v3.0

## Production Release: DhanHQ BlackBox Self-Healing Engine & EMA Dual-Tone Palette

### Key Accomplishments:
1. **DhanHQ BlackBox Self-Healing Authentication**:
   - Resolved two-week silence where background daemon encountered expired Dhan tokens (`HTTP 401 / DH-901`).
   - Implemented dynamic TOTP auto-recovery in `DhanFeed._refresh_token()`.
   - Added daily levels in-memory caching (`self._daily_levels_cache`) reducing redundant requests by 50%.
   - Updated `CRUDEOIL` scrip ID to active contract `573422`.
   - Verified live daemon restart (PID `10512`) with 7 live signals synced to Supabase `shadow_signals` in 17.62s.

2. **Divergence Confirmation Candle Close Gating**:
   - Longs: `(close > open) and (close > close[1])`.
   - Shorts: `(close < open) and (close < close[1])`.
   - Invalidation on extreme penetration (`low < lastBullDivLow` / `high > lastBearDivHigh`).
   - 100% mathematical parity across Pine Script indicator v3.0 and Python BlackBox.

3. **EMA Post-Crossing Dual-Tone Palette**:
   - `fShortEMA` (Fast Line) plotted in `AdxCol` (Green / Red).
   - `fMedEMA` (Medium Line) plotted in `AdxCol1` (Teal / Maroon).
   - Post-crossing state locked to Green & Teal (Bullish) and Red & Maroon (Bearish).

4. **Repository Parity & UI Standardization**:
   - SHA256 parity: `6f4878d217b4b0cfae70c7da6ee75eeb43bc45e03a58efc71580e1ac22dbddb5`.
   - Mobile Header: Renamed to `Markets Today` in `Tv-Alert-Mobile/src/app/page.tsx`.

5. **Live Signals 0-Count Filter Gating Mandate**:
   - Filter buttons with zero active signals ([🔥 SCALP ALERTS], [⚡ DIVERGENCE], [🛡️ REJECTED], [🎯 INSIDE DAY], [🚀 CONTINUATION], [📐 BREAKOUTS]) are hidden until a valid signal fires.
   - [🌐 ALL SIGNALS] anchors the view and dynamically expands to full width when sub-categories are empty.
   - Added `effectiveHubLiveTab` fallback to prevent UI sticking to an empty category.
