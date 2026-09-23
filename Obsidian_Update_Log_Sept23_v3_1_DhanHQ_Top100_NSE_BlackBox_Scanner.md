# Obsidian Update Log: Version 3.1 (23 Sept 2026)
## DhanHQ Top 100 Liquid NSE Stocks 15-Minute Black Box Scanner Integration

---

### 1. Overview & Core Enhancements
Version 3.1 integrates the **Top 100 Liquid NSE Stocks Universe** into the **HUB Tab's Live Filters Section (`TLCS ALERTS DASHBOARD`)**, powered entirely through our standalone **Python Black Box Engine** fetching live 15-minute market data from **DhanHQ Trading API**:

1. **Top 100 NSE Liquid Stocks Universe Mapping**:
   - Downloaded and analyzed the official Dhan Scrip Master (`https://images.dhan.co/api-data/api-scrip-master.csv`).
   - Filtered for all 100 constituents of the Nifty 100 index with verified Dhan `security_id` mappings, exchange segment `NSE:EQ`, and handled all corporate demergers and renames (e.g. `TMPV`/`TMCV` for Tata Motors, `ETERNAL` for Zomato, `LTM` for LTIMindtree).
   - Saved canonical master in `algo_engine/data/dhan_nse100_symbols.json` and `algo_engine/data/nse_top100_master.py`.

2. **DhanHQ 15-Minute Data Fetching & Level Generation**:
   - Updated `algo_engine/feeds/dhan_feed.py` with:
     - `fetch_intraday_candles(symbol, interval=15)`: Queries Dhan's official charts API (`POST https://api.dhan.co/v2/charts/intraday`) to fetch completed 15-minute OHLC bars.
     - `fetch_daily_levels(symbol)`: Queries daily historical OHLC to compute Camarilla (H4/L4) and CPR levels.
     - Built-in graceful simulation/mock fallback when credentials are not configured or outside market hours.

3. **Autonomous 15-Minute Quantitative Scanner**:
   - Created `algo_engine/nse100_scanner.py` and executable runner `algo_engine/run_nse100_scanner.py`.
   - Iterates across the Top 100 NSE stocks evaluating all 13 strategy categories:
     - Breakaway (Missile)
     - Momentum Scalp
     - Lightning Trend
     - Extreme Reversal
     - Regular & Hidden Divergence
     - 5 Day Type Blueprints (Rejection, Absorption, Failed New High/Low, Outside Day, Stop Run)
     - 2 Trade Sequences (Rejection Day Sequence, Stop Run Sequence)
   - Adheres strictly to the **H4 / L4 limit touchpoint gating rule** (`low < H4` for buys, `high > L4` for sells).
   - Emits active signals tagged with `source: 'blackbox_dhan'`, syncing automatically into the Supabase `shadow_signals` table via `algo_engine/shadow_pipeline.py`.

4. **HUB Tab Alerts Dashboard Integration**:
   - Modified `Tv-Alert-Mobile/src/app/page.tsx`:
     - Merges active signals from Supabase `shadow_signals` (`source: 'blackbox_dhan'`) alongside existing webhook signals.
     - Existing live webhook trades, execution logs, and trade guidance remain 100% unaltered.
     - Stocks discovered via the DhanHQ Black Box scanner display a high-visibility `⚡` lightning badge directly next to their ticker symbol in the `Current Signal` cell of the HUB tab's Alerts Dashboard.

5. **Zero Webhook Regression & Deterministic Safety**:
   - Complete architectural decoupling: TradingView webhook alerts and existing executed trades remain the single source of truth for portfolio metrics and trade execution.
   - Black Box scanner signals are stored in `shadow_signals` without corrupting production `signals` table outcomes or metrics.

---

### 2. Code Modifications & Repositories
- **Algorithm Engine (`algo_engine`)**:
  - `data/nse_top100_master.py`: Constituent definitions and Dhan `security_id` resolver.
  - `data/dhan_nse100_symbols.json`: JSON mapping dictionary for all 100 NSE stocks.
  - `feeds/dhan_feed.py`: Added 15m intraday candle and daily level query methods.
  - `nse100_scanner.py`: 15m multi-strategy scanner for Top 100 NSE universe.
  - `run_nse100_scanner.py`: Autonomous CLI runner supporting `--once`, `--interval`, `--limit`, `--mock`.
  - `shadow_pipeline.py`: Added `sync_signal()` for Supabase `shadow_signals` upserts.
- **Mobile Terminal (`Tv-Alert-Mobile`)**:
  - `src/app/page.tsx`: Added `source?: string` to `Signal` interface, unified active Black Box stock signals into HUB tab parameter & sequence categories, and added the `⚡` badge indicator for Dhan Black Box stocks.

---

### 3. Authentication & Configuration
- **Dhan Account Inputs**:
  - No inputs are needed from the user to test or run builds.
  - For live market hours (9:15 AM - 3:30 PM IST), the user simply sets two variables in `algo_engine/.env`:
    - `DHAN_CLIENT_ID=<10-digit Dhan Client ID>`
    - `DHAN_ACCESS_TOKEN=<24-hour API Access Token from web.dhan.co>`
