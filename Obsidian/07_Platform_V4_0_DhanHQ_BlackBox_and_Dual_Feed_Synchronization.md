# Obsidian Architectural Documentation: September 23, 2026 (v4.0)
## Version 4.0 Golden Baseline: DhanHQ Top 100 NSE Black Box Mini-Project & Dual-Feed Synchronization

---

### 1. Executive Summary & Version 4.0 Baseline
Version 4.0 ratifies and standardizes the platform infrastructure at **Version 4.0 (`v4.0` / `4.0.0`)** across the **Next.js Mobile PWA (`Tv-Alert-Mobile`)**, the **Static Web Dashboard (`TLCS_Website_Deploy`)**, and the **Quant Python Engine (`algo_engine`)**.

This milestone introduces the **DhanHQ Top 100 Liquid NSE Stocks Quantitative Scanner** as an autonomous, self-contained standalone mini-project within the mobile application. All execution telemetry, performance calculations, and signal distribution across both TradingView webhooks and DhanHQ Black Box feeds are unified with absolute mathematical fidelity.

Key architectural pillars delivered in Version 4.0:
1. **Strict Multi-Layer Isolation Mandate**: The DhanHQ Black Box engine operates in a dedicated sandbox container visible strictly on the HUB tab and LOGS tab of the mobile terminal. Production webhooks and website assets remain 100% untainted.
2. **Dual-System Global Signal Feed Synchronization**: The `GLOBAL SIGNAL FEED & EXECUTION LOG` on the LOGS tab dynamically switches between production TradingView alerts (`TV PROD`) and autonomous DhanHQ executions (`BLACK BOX LIVE`).
3. **Interactive Normal Distribution Bell-Curve Toggle**: Dynamic switching between linear execution feeds and statistical Gaussian bell-curve return distribution with enlarged, high-contrast typography.
4. **Unified 10-Tile KPI Performance Grid (Weekly Calmar Parity)**: The 10-stat performance grid dynamically switches between systems and features risk-adjusted `WEEKLY CALMAR` ratio parity across both data sources.
5. **2:00 PM IST (14:00 IST) Entry Cutoff Guard**: Prohibits new black box trade initiation after 14:00 IST to prevent late-session slippage and illiquid whipsaws.
6. **Automated Market Close (15:30 IST) Limit Order Cancellation**: Automatic transition of unfilled limit orders to `CANCELLED`, eliminating false "breakeven" trades and safeguarding the canonical win rate denominator.

---

### 2. Architectural Pillars

#### A. Strict Multi-Layer Isolation Architecture
* **Zero Web Exposure**: The web application (`thelioncapitalsolutions.com`) remains strictly dedicated to canonical TradingView webhook alerts. Web databases and UI scanners never ingest or display DhanHQ blackbox signals.
* **Zero Cross-Tab Bleed on Webhook Production Tabs**: Within the mobile application, DhanHQ signals (`shadow_signals` with `source: 'blackbox_dhan'`) are strictly filtered out of calculations on `MARKETS`, `ANALYTICS`, `ADMIN`, and `RESEARCH`. Production portfolio KPIs, win rates, and trade cards remain 100% bound to TradingView webhooks.
* **Targeted Terminal Exposure**: Only the HUB tab (via the system toggle) and the LOGS tab (via the dual-feed toggle) expose Black Box data.

#### B. Synchronized Dual-System Global Signal Feed (LOGS Tab)
* **Interactive Control**: Toggle buttons atop the `GLOBAL SIGNAL FEED & EXECUTION LOG` allow instant switching:
  - `[ 📡 TV PROD | ⚡ BLACK BOX LIVE ]`
* **Dynamic Feed Filtering**:
```typescript
const isBlackBox = s.source === 'blackbox_dhan' || s.source === 'blackbox' || (s.metadata && s.metadata.source === 'blackbox_dhan');
const matchesFeedSource = dhanFeedMode === 'DHAN' ? isBlackBox : !isBlackBox;
```
* **Execution Status Alignment**: Real executed trades require verifiable fill signatures (`TRADE ACTIVE`, `⚡`, `real_entry_time`, or `TradeFill`). Unexecuted limit orders are cleanly separated.
* **Pill Counter Parity**: Status pill counters (`ALL`, `ACTIVE`, `WIN`, `LOSS`, `B/E`, `LIMITS`) strictly reflect the selected system mode.

#### C. Interactive Normal Distribution Histogram & Readability Overhaul
* **Interactive Toggle**: Allows switching between linear execution logs and statistical return distribution bell-curves.
* **Enhanced Typography & Theme Contrast**:
  - Category titles: `text-[11px] font-black uppercase tracking-wider text-slate-800 dark:text-white`
  - Metric counts & percentages: `text-xs font-black tracking-tight`
  - High-contrast visual accents for `Min Loss` (crimson) and `Min Win` (emerald) in both dark and light modes.

#### D. Unified 10-Tile KPI Grid & Weekly Calmar Parity
* Replaced static universe text with dynamic risk-adjusted `WEEKLY CALMAR` ratio (`Weekly Gain % / Max Drawdown %`).
* **KPI Alignment Matrix**:
  | Tile # | Metric Label | Description |
  |---|---|---|
  | 1 | `ACTIVE LIMITS` | Open pending limit orders waiting for touchpoint trigger |
  | 2 | `LIVE TRADES` | Currently active executed trades managing trailing stops |
  | 3 | `TODAY'S TRADES` | Realized closed trades exited during the current session |
  | 4 | `TODAY'S SUCCESS` | Realized Win Rate % (`wins / totalClosed * 100`) |
  | 5 | `TODAY'S PROFIT FACTOR` | Gross Wins % / Gross Losses % |
  | 6 | `WEEKLY TRADES` | Total closed trades since current week start (0 Hrs Monday) |
  | 7 | `WEEKLY SUCCESS` | Realized Weekly Win Rate % |
  | 8 | `WEEKLY PROFIT FACTOR` | Weekly Gross Wins % / Gross Losses % |
  | 9 | `WEEKLY EXPECTANCY` | Average Return % per closed trade |
  | 10 | `WEEKLY CALMAR` | Weekly Net Return % / Max Drawdown % |

#### E. Quantitative Execution Safeguards
* **2:00 PM IST Entry Cutoff**:
```python
# algo_engine/nse100_scanner.py
now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
if now_ist.hour > 14 or (now_ist.hour == 14 and now_ist.minute > 0):
    logger.info("[2:00 PM CUTOFF] Strict entry cutoff active. No new orders generated.")
    return
```
* **Automated Market Close Limit Cancellation**:
  At 15:30 IST, all remaining open limit orders in `shadow_signals` are updated to:
```json
{
  "status": "CANCELLED",
  "outcome": "CANCELLED"
}
```
  Unexecuted limit orders are completely excluded from closed trade counts and win rate denominators (`wins / totalClosed`), eliminating false "breakeven" trades.

---

### 3. File & Repository Matrix

| Repository / Module | Affected File | Version | Core Changes |
|---|---|---|---|
| **Tv-Alert-Mobile** | `package.json` | `4.0.0` | Standardized to Version 4.0.0 |
| **Tv-Alert-Mobile** | `src/app/page.tsx` | `v4.0` | Dual-system toggle on HUB & LOGS, Calmar ratio, enlarged histogram font, strict fill verification, V4.0 branding |
| **TLCS_Website_Deploy** | `package.json` | `4.0.0` | Standardized to Version 4.0.0 |
| **TLCS_Website_Deploy** | `dashboard.html`, `metrics.html`, `scanner.html`, `login.html` | `v4.0` | Standardized footers and engine badges to V4.0 |
| **TLCS_Website_Deploy** | `sw.js` | `v4.0.0` | Cache updated to `tlcs-website-cache-v4.0.0` |
| **algo_engine** | `shadow_pipeline.py` | `4.0.0` | Engine version metadata updated to `4.0.0` |
| **algo_engine** | `nse100_scanner.py` | `4.0.0` | 2 PM entry cutoff and automated 15:30 IST limit order cancellation |
| **Root Repository** | `.agents/AGENTS.md` | `v4.0` | Ratified Version 4.0 Platform Baseline specification |
| **Obsidian Docs** | `Obsidian/07_Platform_V4_0_...` | `v4.0` | Complete architectural master documentation |

---

### 4. Verification & Production Status
1. **Next.js Mobile PWA**: Built cleanly via `npm run build` with 0 type errors across all 8 static and dynamic routes.
2. **Algo Engine Scanner**: Verified via Python test runner with Camarilla H4/L4 touchpoint gating and IST market hours gating.
3. **Database Audit**: Live `shadow_signals` verified with 6 realized closed trades today (83.3% Win Rate, PF 12.98, Expectancy +1.16%, Weekly Calmar 11.98).
4. **Git Repositories**: All branches synchronized and pushed to `origin/main`.
