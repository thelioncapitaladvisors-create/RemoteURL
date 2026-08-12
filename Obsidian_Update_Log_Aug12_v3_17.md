# TLCS System Update Release Notes — Version 3.17

## Release Overview
**Version**: `v3.17`  
**Date**: August 12, 2026  
**Scope**: Pine Script Indicators, Mobile App (`Tv-Alert-Mobile`), Website Platform (`TLCS_Website_Deploy`), Backend Webhook Dispatchers.

---

## 1. Indicator Matrix & Column Ordering Standard
- **Reverse Chronological Day Columns**: Both indicators (`TLCS VERTICAL DASHBOARDS` & `TLCS QWEN DASHBOARDS`) now render historical days in reverse order from **Column 7** (6 days ago) down to **Column 1 (Today)** on the far right.
- **Clean Ticker Names**: Ticker names remain clean string identifiers (e.g., `NIFTY1`, `CRUDEOIL1`, `GC1`, `SI1`) without appended offset tags.
- **Fixed CE10013 Indentation Error**: Corrected tab spacing inside `f_render_matrix_row`.

---

## 2. Daily Signal Dashboard (Mobile App & Website)
- **Mobile App (`Tv-Alert-Mobile/src/app/page.tsx`)**:
  - Re-positioned the **TLCS Daily Signal Dashboard** directly below the **Weekly Performance Edge** card on the **ANALYTICS** tab.
  - Headers set to `7 | 6 | 5 | 4 | 3 | 2 | 1 (Today)`.
- **Website Platform (`TLCS_Website_Deploy/blog.html`)**:
  - Embedded the **Daily Signal Dashboard** matrix table on the **Blogs and FAQs** (`blog.html`) page.
  - Dynamically fetches past 7-day signals from Supabase and populates signals across parameter categories (Missile, Scalp, Lightning, Day Type Blueprints, Sequences).

---

## 3. Session Opening Webhook Alert Payloads
For automated session opening broadcasts across all 6 market categories (NIFTY, MCX, NYMEX, Crypto, Forex, World Indices):

### TradingView Alert JSON Template:
```json
{
  "ticker": "{{ticker}}",
  "trigger": "SessionOpenMatrix",
  "opening_bias": "Bullish",
  "day_type": "Rejection Day Blueprint",
  "signals_matrix": {
    "missile": true,
    "scalp": false,
    "lightning": false,
    "blueprint": "Rejection Day Blueprint",
    "sequence": "Rejection Day Sequence"
  },
  "market_category": "MCX",
  "timestamp": "{{time}}"
}
```
