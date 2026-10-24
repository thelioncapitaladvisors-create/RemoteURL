# Platform V1.0: DhanHQ Out of Range / Out of Value Opening Bias Screener & Security Hardening

**Document Version:** 1.0  
**Effective Date:** October 24, 2026 (21:05 IST)  
**Status:** COMPLETE PRODUCTION RELEASE & REPOSITORY ANCHOR  
**Infrastructure & Environment:** Next.js PWA Mobile Terminal (`Tv-Alert-Mobile`), Netlify Webhook (`TLCS_Website_Deploy`), DhanHQ Python BlackBox Engine (`algo_engine`), Supabase Production (`dwepduvhzuhzeehbeaaz`)  
**Architect:** *Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*  

---

## 1. Executive Summary & Production Objectives

Under Platform Version 1.0, an institutional quantitative screener module and critical infrastructure hardening updates were deployed:

1. **DhanHQ Out of Range / Out of Value Opening Bias Screener**:
   - Built an institutional screener positioned at the bottom of the DhanHQ Screener view (`screenerViewTab === 'DHAN_SCREENER'`), beneath Section 3 Trade Sequences.
   - Screener logic strictly implements Frank Ochoa's **PivotBoss Swing Trade Pro 2.0** Opening Relationship framework: identifying assets opening completely outside the prior day's range and value area (`OUT OF RANGE / OUT OF VALUE`).
   - **Strict BlackBox Isolation Rule**: The screener feeds **ONLY** from the standalone DhanHQ BlackBox Python engine (`source: 'blackbox_dhan'` / `meta.source_feed: 'DhanHQ'`) in `public.shadow_signals`, completely segregated from webhook signals.
   - **Multi-Asset Indian Universe Gating**: Filters constituent symbols strictly to Indian exchange assets (NSE Top 100 Equities and MCX Commodities: Crude Oil, Natural Gas, Gold, Silver, Base Metals).
   - **Directional Gap Classification**:
     - `▲ BULLISH EXPANSION`: Market opens above prior day's High / VAH (`open > prevHigh`), signaling aggressive buying conviction and continuation bias.
     - `▼ BEARISH BREAKDOWN`: Market opens below prior day's Low / VAL (`open < prevLow`), signaling aggressive institutional selling and breakdown bias.
   - **Continuous Session Fidelity**: Automatically binds to the current calendar day's active session, with an intelligent fallback to the most recent active exchange session (e.g., Friday October 23 during weekend/pre-market hours) and an interactive toggle to view `ALL RECENT SESSIONS`.

2. **Novice Mode Deprecation & Visual Elevation**:
   - Deprecated the legacy `🎓 Novice Mode` toggle and 7 orphaned variables from the HUB tab.
   - Subsection headings across all tabs (`INSIGHTS`, `MARKETS`, `SCREENER`, `HUB`) elevated with subtle, theme-adaptive hues and glowing indicator dots, achieving WCAG AAA contrast across all 6 themes.
   - Typography across all tables, tearsheets, and metric cards standardized to Apple SF Pro (`-apple-system, BlinkMacSystemFont, "SF Pro Text"`) with tabular numerals (`font-feature-settings: 'tnum' 1, 'zero' 1`).

3. **Web Infrastructure & Security Hardening (CERT-In Civn Compliance)**:
   - Hardened `TLCS_Website_Deploy/.htaccess` against CVE-2024-4577 (PHP CGI argument injection), directory browsing, and automated vulnerability scanners.
   - Enforced PHP 8.3+ execution and configured `TLCS_Website_Deploy/.user.ini` with strict execution boundaries (`max_execution_time=30`, `memory_limit=256M`, `display_errors=Off`).
   - Hardened `TLCS_Website_Deploy/_headers` with `X-Frame-Options: SAMEORIGIN` and strict CSP `frame-ancestors`.

---

## 2. Quantitative Opening Bias Logic & Mathematical Proof

In PivotBoss Swing Trade Pro 2.0, the Opening Relationship provides the earliest and highest-probability indicator of the market's conviction for the day:

$$\text{Range}_{t-1} = [L_{t-1}, H_{t-1}], \quad \text{Value Area}_{t-1} = [VAL_{t-1}, VAH_{t-1}]$$

$$\text{Out of Range / Out of Value} \iff O_t > H_{t-1} \lor O_t < L_{t-1}$$

### Directional Classification:
1. **Bullish Expansion (Gap Up)**:
   $$O_t > H_{t-1} \quad (\text{or } O_t > VAH_{t-1} \land \text{Signal} = \text{LONG})$$
   - *Institutional Context*: Value has shifted sharply upward overnight.
   - *Playbook*: Look for continuation above opening price; pullbacks toward prior day high or VAH serve as primary support.

2. **Bearish Breakdown (Gap Down)**:
   $$O_t < L_{t-1} \quad (\text{or } O_t < VAL_{t-1} \land \text{Signal} = \text{SHORT})$$
   - *Institutional Context*: Overnight liquidation or heavy selling imbalance.
   - *Playbook*: Look for continuation below opening price; rallies toward prior day low or VAL serve as overhead resistance.

---

## 3. UI/UX Component Specifications

### 3.1 4-Card KPI Summary Strip
- **Total Screened**: Count of active assets meeting criteria, broken down by `X Bull • Y Bear`.
- **NSE Stocks**: Count of liquid Indian equities in the basket.
- **MCX Commodities**: Count of MCX commodity contracts (Metals & Energy).
- **BlackBox Win Rate**: Verified canonical win rate ($\frac{\text{Wins}}{\text{Total Closed}} \times 100$) including breakevens in denominator.

### 3.2 Responsive Asset Cards
- **Header**: Clean Ticker Symbol (`SILVERM`, `CIPLA`, `IDEA`, `ITC`), Market Category badge (`NSE` or `MCX`), and Session Date.
- **Directional Pill**: High-contrast glowing badge (`▲ BULLISH GAP UP` in emerald or `▼ BEARISH GAP DOWN` in rose).
- **Price Metrics**: Open / Fill price (`₹XX.XX`), Net Outcome exact percentage (`+X.XX%` in emerald, `-X.XX%` in rose).
- **Signals Count & Action**: Number of BlackBox strategy signals executed on that session, with an `INSPECT` button opening the blueprint detail modal.

### 3.3 Blueprint Detail Inspection Modal (`selectedDhanOorAsset`)
- Real-time display of Open/Fill price, Prior Day High / H4, Prior Day Low / L4, and Aggregate P&L.
- Detailed list of every individual strategy signal triggered (`ScalpBuy`, `MissileSell`, `LightningBuy`, etc.) with entry price, exit price, and outcome.
- Embedded PivotBoss STP 2.0 tactical continuation checklist.

---

## 4. Verification & Validation Results

- **TypeScript Compilation**: `tsc --noEmit` executed with 0 errors across 17,258 lines of code.
- **Next.js Production Build**: Next.js 14.2.35 production build compiled successfully (8/8 static and dynamic routes verified).
- **Database Verification**: Validated live `public.shadow_signals` records with `source: 'blackbox_dhan'` and `metadata.opening_bias: 'OUT OF RANGE OUT OF VALUE'` across MCX (`SILVERM`, `GOLDM`) and NSE (`CIPLA`, `IDEA`, `ITC`, `DLF`, `GRASIM`).
- **Security Check**: Verified HTTP security headers and Apache `.htaccess` directives preventing unauthorized CGI argument passing.

---

## 5. Architectural Invariants Preserved

1. **Strict Fact-Backed Verification Mandate**: Zero speculation, all metrics backed by deterministic calculation and live database verification.
2. **Engine Isolation Mandate**: Out of Range / Out of Value screener is 100% bound to `dhanBlackboxSignals` and completely independent from TradingView webhooks.
3. **Canonical Exact Percentage Mandate**: Net return and outcomes strictly evaluate `metadata.exact_pct`.
