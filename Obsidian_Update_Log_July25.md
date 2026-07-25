# Version 1.7.0 Update Log - July 25, 2026

## 🛠️ System-Wide Edge & AI Scanner Defaults Upgrade

### 1. Default System-Wide Metrics Mode on AI Scanner Page
- **System-Wide Default State**: Configured [`scanner.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.html) and [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) to default to system-wide mode (`activeTab = 'all'`) on initial page load, where no specific market tab is highlighted.
- **Interactive Market Tab Deselection**: Clicking an active market tab now toggles it off, seamlessly returning the user to the system-wide view (`'all'`).
- **Aggregated Historical Edge Statistics**: The top summary bar (`#scanner-expectancy-bar`) calculates and displays the system-wide aggregated metrics (**Win Rate, Half-Kelly %, Profit Factor, Avg Profit / System Edge, Total Trades, Wins / Losses / BE, Best Trade**) across all 6 markets (`Nifty 50`, `MCX`, `NYMEX`, `Crypto Top 25`, `Forex Pairs`, `World Indices`).

---

### 2. Weekly Consolidated System Edge Alignment (`TLCS EDGE %`)
- **Current Week Consolidated System Edge**: Updated [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) (`cachedData.signals`) and [`dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html) (`systemAvgEdge`) to compute consolidated system edge over **all 6 markets combined for the current week** (starting Monday 00:00 local time).
- **Dashboard & Scanner Parity**: The `TLCS EDGE %` card on `dashboard.html` and the `Avg Profit` summary metric on `scanner.html` match with 100% mathematical precision, showing the consolidated weekly edge of the entire TLCS system.

---

### 3. System-Wide Weekly Performance Edge Historical Aggregation
- **Dynamic System-Wide Weekly Edge Aggregation**: Updated `fetchWeeklyLogs('all')` in [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js) to query all historical weekly performance logs from `weekly_performance_logs`, group by `week_start_date`, and aggregate win rates, net edge, profit factors, and Half-Kelly percentages across all 6 market types week by week.
- **Cumulative All-Time System Edge Row**: The Weekly Performance Edge table renders an `ALL` Cumulative Edge row summarizing overall all-time historical performance across all recorded weeks.

---

### 4. Single Source of Truth & Rule Base Update (`AGENTS.md`)
- **Updated System Guidelines**: Appended new architecture rules to [.agents/AGENTS.md](file:///Users/vishant/Documents/Project/.agents/AGENTS.md) enforcing default system-wide metrics mode on the AI Scanner page, tab deselect toggles, and historical Week 1 to date signal aggregation for `TLCS EDGE %`.

---

### 5. Next.js Mobile Scope & Build Error Resolution (`isNYMEXSymbol`)
- **Resolved Next.js Type Compiler Error**: Defined `isNYMEXSymbol(symbol?: string)` helper function at module scope in [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) to resolve Netlify Next.js build worker exit error (`Type error: Cannot find name 'isNYMEXSymbol'`). Local build test verified 9/9 pages generated cleanly (`npm run build` exit code 0).

---

### 6. Netlify Secrets Scanning Security Enforcement
- **Eliminated Hardcoded Secret Credentials**: Sanitized 7 test/utility script files ([`check_crude.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/check_crude.js), [`debug_metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/debug_metrics.js), [`find_outliers.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/find_outliers.js), [`fix_corrupted_mcx.py`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/fix_corrupted_mcx.py), [`inspect_losses.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/inspect_losses.js), [`test_dash_exact.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/test_dash_exact.js), [`test_metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/test_metrics.js)) by replacing hardcoded service role JWTs with dynamic environment variable lookups (`process.env.SUPABASE_SERVICE_KEY` / `os.environ.get(...)`). Netlify automated secrets scanner verified 0 violations.
