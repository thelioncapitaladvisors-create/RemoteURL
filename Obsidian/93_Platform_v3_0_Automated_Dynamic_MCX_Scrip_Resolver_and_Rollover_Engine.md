# 93. Platform v3.0: Automated Dynamic MCX Scrip Resolver & Rollover Engine

**Date:** November 13, 2026  
**Release:** Version 3.0 Production Maintenance & Zero-Intervention Architecture  
**Components:**
- algo_engine/scrip_resolver.py (Dynamic DhanHQ Scrip Master Resolver)
- algo_engine/feeds/dhan_feed.py (Automatic Symbol Map Ingestion)
- algo_engine/dhan_executor.py (Dynamic Execution Lot Size & Scrip Resolution)
- TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js (Dynamic Supabase Sync)
- TLCS_Website_Deploy/netlify/functions/cron-dhan-scanner.js (08:30 IST Pre-Market Trigger)
- algo_engine/tests/test_scrip_resolver.py (Unit Test Suite)
- Supabase public.system_config (Shared mcx_front_month_symbols Cache)

---

## 1. Executive Summary

This production release deploys the **Automated Dynamic MCX Scrip Resolver**, permanently eliminating manual contract rollovers for Indian commodity markets.

Every morning, the resolver queries the official DhanHQ daily security master (https://images.dhan.co/api-data/api-scrip-master.csv), filters for active unexpired MCX Commodity Futures (FUTCOM), identifies the nearest front-month contract, and synchronizes the active security IDs across:
1. In-memory feed mappings (DhanFeed.symbol_map).
2. Local disk caches (/tmp/dhan_mcx_contracts.json).
3. Supabase shared cache (system_config -> mcx_front_month_symbols).
4. Netlify background batch scanner (dhan-scanner-background.js).

When commodity contracts expire monthly, contract rollovers happen automatically with **zero human intervention**.

---

## 2. Dynamic Contract Resolution Specifications

The resolver monitors all 11 MCX commodities:
1. CRUDEOIL (Crude Oil 100 BBL)
2. CRUDEOILM (Crude Oil Mini 10 BBL)
3. NATURALGAS (Natural Gas 1250 mmBtu)
4. GOLD (Gold 1 KG)
5. GOLDM (Gold Mini 100 Grams)
6. SILVER (Silver 30 KG)
7. SILVERM (Silver Mini 5 KG)
8. COPPER (Copper 2500 KG)
9. ZINC (Zinc 5000 KG)
10. ALUMINIUM (Aluminium 5000 KG)
11. ALUMINI (Aluminium Mini 1000 KG)

### Multi-Tier Resolution Flow:
1. Tier 1: In-memory dictionary cache for sub-microsecond tick routing.
2. Tier 2: Local disk cache (/tmp/dhan_mcx_contracts.json) with calendar-day TTL.
3. Tier 3: Supabase shared configuration (system_config key mcx_front_month_symbols).
4. Tier 4: Streaming parse of https://images.dhan.co/api-data/api-scrip-master.csv filtering SEM_EXM_EXCH_ID == 'MCX' and SEM_INSTRUMENT_NAME == 'FUTCOM'.

---

## 3. Netlify Cloud Scanner Dynamic Integration

In TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js:
- At the start of every scan cycle, the background worker reads mcx_front_month_symbols from Supabase system_config.
- Dynamically overrides security_id, trading_symbol, and expiry in symbolsMap for all 11 MCX commodities.
- In cron-dhan-scanner.js, market hours gating updated to start at 08:30 AM IST (510 minutes), ensuring the daily pre-market cycle executes scrip synchronization prior to market open.

---

## 4. Test Verification & Code Quality

- New unit test module algo_engine/tests/test_scrip_resolver.py passes 4/4 tests.
- Full test suite: 133/133 tests passed (100% OK).
- Zero unilateral modification lock preserved across all Pine Script indicators and regime styling.
