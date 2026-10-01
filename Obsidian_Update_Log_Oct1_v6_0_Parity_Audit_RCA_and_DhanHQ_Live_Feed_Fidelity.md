# Platform Update Log — October 1, 2026: Parity Audit RCA & DhanHQ Live Feed High Fidelity

## Overview
Comprehensive Root Cause Analysis (RCA) and architectural resolution for the Parity Audit screen anomalies (28.6% composite score, 0.0% level fidelity) caused by DhanHQ v2 unnested response handling, synthetic mock level fallbacks, expired MCX security IDs, and cross-day naive frontend matching.

## Key Changes
1. **DhanHQ v2 API Response Handling**:
   - Updated `TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js` and `algo_engine/feeds/dhan_feed.py` to parse `res.data.open` directly.
   - Removed all `cur = 1500.0` synthetic candle generation loops.
2. **Intraday Bar Aggregation for Daily Levels**:
   - Replaced failing `/v2/charts/historical` requests with deterministic aggregation of 15m intraday bars grouped by calendar date (`YYYY-MM-DD` IST).
3. **Active MCX Security IDs**:
   - Updated near-month active contract IDs for `COPPER`, `ZINC`, and `ALUMINIUM` in `dhan-scanner-symbols.json`.
4. **Supabase Database Hygiene**:
   - Purged 73 corrupted mock records (`h4 = 1527.75` / `l4 = 1478.25` or `CRUDEOIL < 7000`) from `shadow_signals`.
5. **Session-Aware Parity Telemetry in Mobile Terminal**:
   - Updated `Tv-Alert-Mobile/src/app/page.tsx` with 1-to-1 session-aware matching within 4 hours or same trading day.
   - Replaced static `PASS` text with dynamic status badge (`PASS` ≥99.0%, `EVAL` ≥90.0%, `AUDIT` <90.0%).
