# Platform V1.0: Canonical Trigger Hardening, Required Win Rate (Req WR) Metric Integration & Composite Signal Rankings

**Document Version:** 1.0  
**Effective Date:** October 13, 2026 (22:20 IST)  
**Status:** COMPLETE PRODUCTION ARCHITECTURE & REPOSITORY ANCHOR  
**Infrastructure & Environment:** Next.js 14 Mobile Terminal (`Tv-Alert-Mobile`), Netlify Production Web (`thelioncapitalsolutions.com`), Supabase Real-Time Engine (`dwepduvhzuhzeehbeaaz`), DhanHQ Live Feed Daemon  
**Architect:** *Vishant Vyankat Meshram, CFTe, CMT L3 Dec 2024*  

---

## 1. Executive Summary & Core Mandates

On October 13, 2026, four key architectural advancements were deployed across the TLCS quantitative platform to enforce strict institutional integrity, eradicate signal ambiguity, enhance performance transparency, and correct ranking models.

### 1.1 Canonical Trigger Hardening & Zero Blueprint Signal Mandate
- **Day Types vs Execution Triggers**: Re-asserted the foundational rule that Day Types (Failed New High `FNH`, Failed New Low `FNL`, Rejection, Absorption, Outside, Stop Run) and Trade Sequences are market context classifications and strictly NOT standalone trade execution alert signals.
- **12 Canonical Triggers Only**: Only the 12 canonical Swing Trade Pro 2.0 execution triggers (`LONG MISSILE`, `SHORT MISSILE`, `LONG SCALP`, `SHORT SCALP`, `LONG LIGHTNING`, `SHORT LIGHTNING`, `LONG DIVERGENCE`, `SHORT DIVERGENCE`, `LONG HIDDEN DIVERGENCE`, `SHORT HIDDEN DIVERGENCE`, `LONG EXTREME REVERSAL`, `SHORT EXTREME REVERSAL`) are permitted to be generated, recorded, or registered as trade signals.
- **Scanner & Shadow Pipeline Hardening**:
  - Removed all blueprint and sequence trade registration loops from `algo_engine/nse100_scanner.py` and `RemoteURL/algo_engine/nse100_scanner.py`.
  - Added strict guard `if sig.name not in CANONICAL_EXECUTION_TRIGGERS: continue` in scanner signal aggregation.
  - Added strict rejection filters in `algo_engine/shadow_pipeline.py` inside both `record_signal()` and `sync_signal()`.
  - Gated Dhan mock fallback generator strictly on `self.mock_mode == True` to prevent synthetic levels in live execution.
  - Purged all non-canonical blueprint rows from Supabase `shadow_signals`.
  - Added automated test `test_reject_non_canonical_and_blueprint_signals` in `algo_engine/tests/test_phase3.py` (9/9 tests passed).

### 1.2 HUB Tab Operational Architecture Refinement
- **Parameter Matrix Relocation**: Relocated the live opportunity parameter block above the `Normalized Trade Performance` section on the HUB tab, migrated from the LOGS tab of the mobile application for immediate top-level operational visibility.

### 1.3 Required Win Rate (`Req WR`) Formula & Column Integration
- In full compliance with quantitative breakeven edge mathematics, the platform calculates the exact Required Win Rate ($W_{\text{req}}$) required for breakeven based on the realized Reward-to-Risk ratio ($R$):
  $$W_{\text{req}} = \frac{1}{1 + R} \times 100\% \quad \text{where } R = \frac{\text{Profit Factor} \times \text{Losses}}{\text{Wins}}$$
- Added dedicated `Req WR` columns across three core performance tables:
  1. **Table 1 (`WEEKLY PERFORMANCE EDGE`)**: Concludes with target breakeven win rate column headers, cumulative row (`cReqWr`), and historical weekly rows (`log.req_wr`) in both `Tv-Alert-Mobile/src/app/page.tsx` and `TLCS_Website_Deploy/scanner.js`.
  2. **Table 2 (`THIS WEEK'S SIGNAL PERFORMANCE`)**: Concludes with target breakeven win rate across 7 calendar days on the mobile terminal (`page.tsx`), fixing an iteration variable scoping bug (`d, y, m`).
  3. **Table 3 (`MARKET-WISE EXECUTION BREAKDOWN`)**: Concludes with target breakeven win rate across all 6 asset classes (`NIFTY`, `STOCKS`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`) on the mobile terminal (`page.tsx`).
  4. **Parity**: Synchronized table headers and styling across `TLCS_Website_Deploy/blog.html`.

### 1.4 Composite Signal Rankings & Deduped Strategy Cards
- **Root Cause Identification**: Previously, `strategyInsights` sorted purely by win rate (`b.winRate - a.winRate`), which erroneously allowed single lucky trades (`100% WR, +1.11% Net`) to outrank high-performing strategies (`40% WR, +11.57% Net`), and losing strategies (`33% WR, -0.08% Net`) to rank above profitable setups (`25% WR, +0.75% Net`). Furthermore, grouping by `${originalType}|${dayType}|${openingPrint}` fragmented strategies, generating duplicate cards titled `SHORT SCALP`.
- **Deterministic Resolution**:
  - Consolidated grouping key to canonical `upperType` in both `page.tsx` and `trade-metrics.js`. Each signal type now renders exactly one consolidated card matching the `Strategy Performance` table.
  - Implemented the institutional Composite Ranking Score:
    $$\text{Score} = \begin{cases} 
    R \times \left(0.5 + 0.5 \times \frac{W}{100}\right), & \text{if } R > 0 \\
    \frac{W}{100} \times 0.0001, & \text{if } R = 0 \\
    R \times \left(1.5 - 0.5 \times \frac{W}{100}\right), & \text{if } R < 0 
    \end{cases}$$
    - Applied the identical composite score sorting to both `strategyCategoryStats` (Strategy Performance table) and `strategyInsights` (ALERT SIGNAL RANKINGS), ensuring unified row-to-card sequence alignment.

### 1.5 Flashy Breaking News Broadcast Radar for Active Signals Matrix
- **Broadcast Wire Aesthetic**: Transformed the plain `FILTER` | `CURRENT SIGNAL` opportunities parameter matrix on the HUB tab (`Tv-Alert-Mobile/src/app/page.tsx`) into an institutional "Breaking News / Live Wire" broadcast console.
- **Top Broadcast Ribbon**: Integrated a full-width header ribbon with pulsating live beacon (`animate-ping`), `🚨 BREAKING RADAR | LIVE WIRE SIGNALS`, and high-contrast `REAL-TIME SCAN` status badge.
- **Container Ambient Glow**: Styled card borders with `border-rose-500/30` and glowing drop-shadow `shadow-[0_4px_25px_rgba(244,63,94,0.12)]`.
- **Broadcast Header Pill**: Upgraded `CURRENT SIGNAL` column header to a live wire badge with dual-ring pulsing radar dot, crimson `BREAKING` tag, electric animated tri-color gradient typography (`bg-gradient-to-r from-rose-600 via-amber-500 to-sky-500 animate-pulse`), and animated lightning bolt `⚡`.
- **Glowing Ticker Pills**: Upgraded active symbols from comma-separated text into individual glowing ticker pills with directional markers (`▲ [SYMBOL]` in glowing emerald, `▼ [SYMBOL]` in glowing rose, and `⚡` badge for Black Box executions).
- **Scanning Radar Empty State**: Replaced dull static text with an animated radar blip: `RADAR ACTIVE • MONITORING INTRADAY BREAKOUTS`.

---

## 2. Technical Code Modifications & Verification

| Repository | File Path | Key Changes |
| :--- | :--- | :--- |
| **Tv-Alert-Mobile** | `src/app/page.tsx` | Relocated parameters on HUB tab, added `Req WR` across 3 tables, updated composite ranking score & deduped `strategyInsights`, added flashy breaking news live radar styling. |
| **Tv-Alert-Mobile** | `src/app/globals.css` | Added `.text-on-accent` utility class for high-contrast active button states. |
| **TLCS_Website_Deploy** | `scanner.js` | Added `Req WR` column header, cumulative `cumReqWr`, and row fallback calculation to `WEEKLY PERFORMANCE EDGE`. |
| **TLCS_Website_Deploy** | `trade-metrics.js` | Synced canonical signal type grouping and composite return % + win rate score in `renderStrategyInsights`. |
| **TLCS_Website_Deploy** | `blog.html` | Aligned `Req WR` column position and styling in weekly tables. |
| **RemoteURL** & **Root** | `algo_engine/nse100_scanner.py` | Removed blueprint/sequence signal registration blocks, enforced 12 canonical triggers. |
| **RemoteURL** & **Root** | `algo_engine/shadow_pipeline.py` | Hardened `record_signal` and `sync_signal` to reject non-canonical triggers. |
| **RemoteURL** & **Root** | `algo_engine/feeds/dhan_feed.py` | Gated mock fallback generator strictly on `mock_mode == True`. |
| **RemoteURL** & **Root** | `algo_engine/tests/test_phase3.py` | Added test case `test_reject_non_canonical_and_blueprint_signals`. |

---

## 3. Build & Parity Verification Results

- **TypeScript Compilation**: `npx tsc --noEmit` exited code 0 with 0 errors.
- **Production Build**: Next.js 14 production build (`npm run build`) completed successfully with 8/8 static pages generated.
- **Python Unit Testing**: `python3 -m unittest algo_engine/tests/test_phase3.py` passed 9/9 tests in 0.54s.
- **Parity Audit**: Web and mobile platforms exhibit 100% mathematical and layout synchronization.
- **Git Repositories Synced**: `Tv-Alert-Mobile` (commit `fba74f1`), root `Project` / `RemoteURL` (commit `6e7b662`), `TLCS_Website_Deploy` clean on `main`.
- **Local Mirrors & Backups Updated**: Synchronized to `Project Backup/` and `Backups/`.
