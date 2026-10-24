# Platform V1.0: DhanHQ Out of Range / Out of Value Opening Bias Screener & Security Hardening

**Document Version:** 1.0  
**Effective Date:** October 24, 2026 (21:05 IST)  
**Status:** COMPLETE PRODUCTION RELEASE & REPOSITORY ANCHOR  
**Infrastructure & Environment:** Next.js PWA Mobile Terminal (`Tv-Alert-Mobile`), Netlify Webhook (`TLCS_Website_Deploy`), DhanHQ Python BlackBox Engine (`algo_engine`), Supabase Production (`dwepduvhzuhzeehbeaaz`)  
**Architect:** *Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*  

---

## 1. Executive Summary & Production Objectives

Under Platform Version 1.0, user experience optimizations, an institutional opening bias screener, and system security hardening were executed across the codebase:

1. **DhanHQ Out of Range / Out of Value Screener**:
   - Built an institutional screener positioned at the bottom of the DhanHQ Screener view (`screenerViewTab === 'DHAN_SCREENER'`), beneath Section 3 Trade Sequences.
   - Screened assets strictly evaluate PivotBoss Swing Trade Pro 2.0 Opening Relationships: identifying assets opening completely outside the prior day's range and value area (`OUT OF RANGE / OUT OF VALUE`).
   - **Strict BlackBox Isolation Rule**: Sourced **ONLY** from standalone DhanHQ BlackBox Python engine feeds (`source: 'blackbox_dhan'` / `meta.source_feed: 'DhanHQ'`) in `public.shadow_signals`, completely segregated from TradingView webhook signals.
   - **Multi-Asset Indian Universe Gating**: Filters constituent symbols strictly to Indian exchange assets (NSE Top 100 Equities and MCX Commodities: Crude Oil, Natural Gas, Gold, Silver, Base Metals).
   - **Directional Classification**:
     - `▲ BULLISH EXPANSION`: Market opens above prior day's High / VAH (`open > prevHigh`), signaling continuation and institutional buying imbalance.
     - `▼ BEARISH BREAKDOWN`: Market opens below prior day's Low / VAL (`open < prevLow`), signaling breakdown and institutional selling imbalance.
   - **Continuous Session Fidelity**: Automatically binds to current calendar day or falls back gracefully to the latest active market session with an interactive `ALL RECENT SESSIONS` toggle.
   - **4-Card KPI Strip**: Displays `Total Screened`, `NSE Stocks`, `MCX Commodities`, and `BlackBox Win Rate` (with canonical breakeven retention in denominator).
   - **Inspection Modal**: Tap `INSPECT` to review Open/Fill prices, Prior Day High/H4, Prior Day Low/L4, exact P&L, triggered signals, and tactical PivotBoss continuation guidelines.

2. **Novice Mode Deprecation & UI Subtle Color Harmony**:
   - Deprecated the legacy `🎓 Novice Mode` toggle and 7 orphaned variables from the HUB tab.
   - Subsection headings across all tabs elevated with subtle, theme-adaptive hues and glowing indicator dots, achieving WCAG AAA contrast compliance across all 6 themes.
   - Standardized typography across all tables, tearsheets, and metric cards to Apple SF Pro with tabular numerals (`font-feature-settings: 'tnum' 1, 'zero' 1`).

3. **Web Infrastructure & Security Hardening (CERT-In Civn Compliance)**:
   - Hardened `TLCS_Website_Deploy/.htaccess` against CVE-2024-4577 (PHP CGI argument injection), directory browsing, and automated vulnerability scanners.
   - Enforced PHP 8.3+ execution and configured `TLCS_Website_Deploy/.user.ini` with strict execution boundaries (`max_execution_time=30`, `memory_limit=256M`, `display_errors=Off`).
   - Hardened `TLCS_Website_Deploy/_headers` with `X-Frame-Options: SAMEORIGIN` and strict CSP `frame-ancestors`.

---

## 2. Verification & Validation Results

- **TypeScript Compilation**: `tsc --noEmit` passed with 0 errors across 17,258 lines of code.
- **Next.js Production Build**: Next.js 14.2.35 production build compiled successfully with static and dynamic routes verified.
- **Local Backup**: Synchronized updated `page.tsx` and documentation to `Project Backup/`.
