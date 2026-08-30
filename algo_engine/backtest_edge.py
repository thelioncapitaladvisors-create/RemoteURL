import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import json
import pandas as pd
import numpy as np
import vectorbt as vbt
from dotenv import load_dotenv
from supabase import create_client, Client
import warnings
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Disable vectorbt caching to prevent Numba cache corruption issues across Python environments
vbt.settings.caching['enabled'] = False

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '.env'))
load_dotenv(os.path.join(current_dir, '.env.local'))
load_dotenv(os.path.join(current_dir, '..', 'TLCS_Website_Deploy', '.env'))
load_dotenv(os.path.join(current_dir, '..', 'Tv-Alert-Mobile', '.env.local'))
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Error: Missing Supabase credentials in .env file or environment.')
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def resolve_outcome(signal):
    """
    Python implementation of the Canonical resolveOutcome from User Rules.
    """
    st = str(signal.get('status', '')).upper()
    o = str(signal.get('outcome', '')).upper()

    # Step 1: Hard-kill CANCELLED/UNKNOWN first
    if 'CANCEL' in o or 'CANCEL' in st or 'UNKNOWN' in st or 'UNKNOWN' in o:
        return 'CANCELLED'
    if ('EXPIRED' in st or 'COMPLETED' in st) and not signal.get('exit_price'):
        return 'CANCELLED'

    # Step 2: exact_pct is the SINGLE SOURCE OF TRUTH
    meta = signal.get('metadata', {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except:
            meta = {}
            
    if meta and 'exact_pct' in meta and meta['exact_pct'] is not None:
        try:
            pct = float(meta['exact_pct'])
            if pct > 0: return 'WIN'
            if pct < 0: return 'LOSS'
            return 'BREAKEVEN'
        except ValueError:
            pass

    # Step 3: Keyword fallback
    if 'ACTIVE' in st or o == 'OPEN' or st == 'OPEN': return 'OPEN'
    if o == 'WIN' or 'WIN' in st: return 'WIN'
    if o == 'LOSS' or 'LOSS' in st: return 'LOSS'
    if ('STOP' in st or 'SL' in st) and 'TRAIL' not in st: return 'LOSS'
    
    return 'OPEN'

def get_market(symbol):
    """
    Determine primary market for a given symbol based on canonical memory.
    """
    s = symbol.upper().replace('NSE:', '').replace('TVC:', '').replace('MCX:', '').replace('1!', '').strip()
    
    MARKETS = {
        'NIFTY': ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BHARTIARTL', 'BPCL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIMINDTREE', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHRIRAMFIN', 'SUNPHARMA', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'ULTRACEMCO', 'WIPRO'],
        'MCX': ['ALUMINIUM', 'ALUMINIUMM', 'COPPER', 'COTTON', 'CRUDEOIL', 'CRUDEOILM', 'GOLD', 'GOLDM', 'GOLDPETAL', 'LEAD', 'LEADMINI', 'MENTHAOIL', 'NATURALGAS', 'NATURALGASM', 'NICKEL', 'NICKELMINI', 'SILVER', 'SILVERM', 'SILVERMIC', 'ZINC', 'ZINCMINI'],
        'NYMEX': ['CL', 'GC', 'HG', 'HO', 'NG', 'PA', 'PL', 'RB', 'SI'],
        'CRYPTO': ['ADAUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DOTUSDT', 'ETHUSDT', 'FILUSDT', 'ICPUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT', 'POLUSDT', 'SHIBUSDT', 'SOLUSDT', 'STXUSDT', 'TONUSDT', 'TRXUSDT', 'UNIUSDT', 'XLMUSDT', 'XRPUSDT'],
        'FOREX': ['AUDCAD', 'AUDINR', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURINR', 'EURJPY', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPINR', 'GBPJPY', 'GBPUSD', 'JPYINR', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDINR', 'USDJPY'],
        'WORLD': ['AU200', 'DE40', 'EU50', 'FR40', 'HK50', 'JP225', 'NAS100', 'SPX500', 'UK100', 'US2000', 'US30']
    }
    for m, symbols in MARKETS.items():
        if s in symbols:
            return m
    return 'UNKNOWN'

def fetch_all_closed_trades():
    print("Fetching all-time historical trades from Supabase...")
    
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = datetime.now(ist)
    
    data = []
    page_size = 1000
    start = 0
    
    while True:
        response = supabase.table('signals').select('*').order('created_at', desc=False).range(start, start + page_size - 1).execute()
        chunk = response.data
        if not chunk:
            break
        data.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    
    closed_trades = []
    
    for s in data:
        outcome = resolve_outcome(s)
        if outcome in ['WIN', 'LOSS', 'BREAKEVEN']:
            meta = s.get('metadata', {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
                    
            if meta and 'exact_pct' in meta and meta['exact_pct'] is not None:
                try:
                    pct_return = float(meta['exact_pct']) / 100.0  # Convert 1.35 to 0.0135
                    
                    # Sanity check: prevent mathematically impossible single-trade returns from corrupting the graph
                    if abs(pct_return) > 5.0:  # >500% single trade return is mathematically anomalous
                        print(f"Skipping anomalous exact_pct: {meta['exact_pct']}% on {s.get('symbol')}")
                        continue
                    
                    # Prioritize exit_at or updated_at, fallback to created_at
                    ts_str = s.get('exit_at') or s.get('updated_at') or s.get('created_at')
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        continue
                        
                    market = get_market(s.get('symbol', 'UNKNOWN'))
                    
                    closed_trades.append({
                        'datetime': ts,
                        'market': market,
                        'return': pct_return
                    })
                except ValueError:
    sync_weekly_performance_logs(data)
    return closed_trades, now_ist

def sync_weekly_performance_logs(signals_data):
    try:
        weeks = {}
        for s in signals_data:
            outcome = resolve_outcome(s)
            if outcome in ['OPEN', 'CANCELLED']:
                continue
            
            market = get_market(s.get('symbol', 'UNKNOWN')).lower()
            if market == 'unknown':
                continue
                
            ts_str = s.get('created_at') or s.get('exit_at')
            if not ts_str:
                continue
            try:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
                mon = (ist.date() - timedelta(days=ist.weekday())).strftime('%Y-%m-%d')
            except:
                continue
                
            meta = s.get('metadata', {})
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
            
            pct = 0.0
            if meta and 'exact_pct' in meta and meta['exact_pct'] is not None:
                try: pct = float(meta['exact_pct'])
                except: pct = 0.0
                
            if mon not in weeks:
                weeks[mon] = {}
            if market not in weeks[mon]:
                weeks[mon][market] = []
            weeks[mon][market].append((outcome, pct))
            
        logs_to_insert = []
        for mon, mkts in weeks.items():
            for mkt, trades in mkts.items():
                wins = sum(1 for o, r in trades if o == 'WIN')
                losses = sum(1 for o, r in trades if o == 'LOSS')
                bes = sum(1 for o, r in trades if o == 'BREAKEVEN')
                total = wins + losses + bes
                if total == 0:
                    continue
                    
                net_r = sum(r for o, r in trades)
                gross_profit = sum(r for o, r in trades if r > 0)
                gross_loss = sum(abs(r) for o, r in trades if r < 0)
                best_trade = max((r for o, r in trades), default=0.0)
                
                win_rate = (wins / total) * 100.0
                avg_r = net_r / total
                
                pf = 0.0
                if gross_loss > 0:
                    pf = gross_profit / gross_loss
                elif gross_profit > 0:
                    pf = 99.99
                    
                avg_win = (gross_profit / wins) if wins > 0 else 0.0
                avg_loss = (gross_loss / losses) if losses > 0 else 1.0
                realized_rr = (avg_win / avg_loss) if avg_loss > 0 else (999 if avg_win > 0 else 0)
                
                win_loss_count = wins + losses
                kw_dec = wins / win_loss_count if win_loss_count > 0 else 0.0
                kl_dec = losses / win_loss_count if win_loss_count > 0 else 0.0
                
                kelly = 0.0
                if realized_rr > 0 and realized_rr != 999:
                    kelly = ((kw_dec - (kl_dec / realized_rr)) * 100.0) * 0.5
                elif realized_rr == 999:
                    kelly = (kw_dec * 100.0) * 0.5
                if kelly < 0:
                    kelly = 0.0
                    
                logs_to_insert.append({
                    'market_type': mkt,
                    'week_start_date': mon,
                    'win_rate': round(win_rate, 2),
                    'total_trades': total,
                    'profit_factor': round(pf, 2),
                    'avg_exact_pct': round(avg_r, 2),
                    'net_exact_pct': round(net_r, 2),
                    'best_trade': round(best_trade, 2),
                    'kelly_pct': round(kelly, 2),
                    'wins': wins,
                    'losses': losses,
                    'breakevens': bes
                })
                
        if logs_to_insert:
            supabase.table('weekly_performance_logs').upsert(logs_to_insert, on_conflict='market_type, week_start_date').execute()
            print(f"Synchronized {len(logs_to_insert)} weekly performance log entries in Supabase.")
    except Exception as e:
        print(f"Note: Weekly performance log sync encountered: {e}")

def run_returns_backtest():
    trades, now_ist = fetch_all_closed_trades()
    
    markets = ['NIFTY', 'MCX', 'NYMEX', 'CRYPTO', 'FOREX', 'WORLD']
    
    if not trades:
        print('No closed trades found with valid exact_pct. Creating empty timeline.')
        df_pivot = pd.DataFrame(columns=markets)
    else:
        df = pd.DataFrame(trades)
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)
        
        print(f'\nLoaded {len(df)} closed trades for all-time.')
        print('Analyzing performance using VectorBT...\n')
        
        # Ensure timezone aware (UTC -> IST)
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert(now_ist.tzinfo)
        
        # Pivot table so each market has its own column, sum returns for simultaneous trades
        df_pivot = df.pivot_table(index='datetime', columns='market', values='return', aggfunc='sum').fillna(0.0)
    
    # Ensure all 6 core markets exist in columns
    for m in markets:
        if m not in df_pivot.columns:
            df_pivot[m] = 0.0
            
    # Filter out UNKNOWN markets and order columns
    df_pivot = df_pivot[markets]
    
    # Create a full timeline from the first trade up to current time
    if df_pivot.empty:
        start_idx = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_idx = df_pivot.index.min().replace(hour=0, minute=0, second=0, microsecond=0)
    
    full_idx = pd.date_range(start=start_idx, end=now_ist, freq='15min')
    
    # Resample to 15-minute frequency and fill missing with 0.0
    if df_pivot.empty:
        df_resampled = pd.DataFrame(np.nan, index=full_idx, columns=markets)
    else:
        df_resampled = df_pivot.resample('15min').sum().reindex(full_idx, fill_value=0.0)
        
    empty_markets = [col for col in df_resampled.columns if (df_resampled[col] == 0.0).all() or df_resampled[col].isna().all()]
    print(f"DEBUG: empty_markets identified as: {empty_markets}")
    
    # We no longer replace with np.nan here because VectorBT's cumulative returns 
    # implicitly converts them back to 0.0. We will handle trace nullification in the Plotly figures.
    # Feed to VectorBT (multi-column)
    vbt_returns = df_resampled.vbt.returns(freq='15min')
    
    # Print stats
    print("--- ALL-TIME BACKTEST METRICS ---")
    print(vbt_returns.stats())
    
    # Save Tear Sheet to the website deployment folder
    output_path = os.path.join(os.path.dirname(__file__), '..', 'TLCS_Website_Deploy', 'strategy_tearsheet.html')
    
    # 1. Equity Curve
    # EXPLICIT CUMULATIVE RETURN CALCULATION
    # By strictly converting to 1-based index and calculating cumprod, we avoid vectorbt's raw return plotting anomaly
    cum_returns = (1 + df_resampled).cumprod() - 1
    fig_equity = cum_returns.vbt.plot(title="Cumulative Equity Curve")
    fig_equity.update_layout(width=None, height=300, autosize=True, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=25, t=40, b=60), yaxis_tickformat='.2%', dragmode=False, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    
    # 2. Drawdowns
    wealth_index = (1 + df_resampled).cumprod()
    peak = wealth_index.cummax()
    drawdown = (wealth_index - peak) / peak
    fig_dd = drawdown.vbt.plot(title="Drawdowns (%)")
    fig_dd.update_layout(width=None, height=300, autosize=True, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=25, t=40, b=60), yaxis_tickformat='.2%', dragmode=False, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    
    # 3. Raw Returns
    fig_ret = df_resampled.vbt.plot(title="Raw Returns (%)")
    fig_ret.update_layout(width=None, height=300, autosize=True, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=25, t=40, b=60), yaxis_tickformat='.2%', dragmode=False, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    
    # Universal Plotly bdata Glitch Fix
    # iOS/Android WebViews fail to decode Plotly's base64 bdata strings.
    # We must explicitly cast all numpy arrays to pure Python lists to force standard JSON serialization.
    # UI Persistent Market Rendering rule: we NEVER hide empty markets.
    for fig in [fig_equity, fig_dd, fig_ret]:
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None:
                try: trace.x = trace.x.tolist()
                except: trace.x = list(trace.x)
            if hasattr(trace, 'y') and trace.y is not None:
                try: trace.y = trace.y.tolist()
                except: trace.y = list(trace.y)

    # Generate HTML
    html_equity = fig_equity.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})
    html_dd = fig_dd.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})
    html_ret = fig_ret.to_html(full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})
    
    # 4. Statistics Table
    stats_df = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            raw_stats = vbt_returns.stats(agg_func=None)
            if raw_stats is not None and not raw_stats.empty and len(raw_stats) > 0:
                stats_df = raw_stats.T
        except Exception as e:
            print(f"vbt_returns.stats() encountered error: {e}")

    # Fallback to direct calculation if vectorbt stats fails or produces empty rows
    if stats_df is None or stats_df.empty or len(stats_df) == 0:
        print("Computing performance statistics directly...")
        rows = {}
        for m in markets:
            series = df_resampled[m].dropna() if m in df_resampled.columns else pd.Series(0.0, index=full_idx)
            start_val = df_resampled.index.min().strftime('%Y-%m-%d %H:%M:%S%z') if not df_resampled.empty else '-'
            end_val = df_resampled.index.max().strftime('%Y-%m-%d %H:%M:%S%z') if not df_resampled.empty else '-'
            period_val = str(df_resampled.index.max() - df_resampled.index.min()) if not df_resampled.empty else '-'
            
            cum = (1 + series).cumprod() - 1
            total_ret = cum.iloc[-1] * 100 if not cum.empty else 0.0
            
            ann_factor = 252 * 26
            ann_ret = ((1 + total_ret / 100.0) ** (ann_factor / max(len(series), 1)) - 1) * 100 if len(series) > 0 else 0.0
            vol = series.std() * np.sqrt(ann_factor) * 100 if len(series) > 1 else 0.0
            
            wealth = (1 + series).cumprod()
            peak = wealth.cummax()
            dd = (wealth - peak) / peak
            max_dd = abs(dd.min()) * 100 if not dd.empty else 0.0
            
            mean_ret = series.mean()
            std_ret = series.std()
            sharpe = (mean_ret / std_ret) * np.sqrt(ann_factor) if std_ret > 0 else 0.0
            calmar = (ann_ret / max_dd) if max_dd > 0 else 0.0
            
            neg_ret = series[series < 0]
            downside_std = neg_ret.std() * np.sqrt(ann_factor) if len(neg_ret) > 1 else 0.0
            sortino = (ann_ret / downside_std) if downside_std > 0 else 0.0
            
            rows[m] = {
                'Start': start_val,
                'End': end_val,
                'Period': period_val,
                'Total Return [%]': total_ret,
                'Annualized Return [%]': ann_ret,
                'Annualized Volatility [%]': vol,
                'Max Drawdown [%]': max_dd,
                'Sharpe Ratio': sharpe,
                'Calmar Ratio': calmar,
                'Sortino Ratio': sortino,
                'Skew': float(series.skew()) if len(series) > 2 and not np.isnan(series.skew()) else 0.0,
                'Kurtosis': float(series.kurtosis()) if len(series) > 3 and not np.isnan(series.kurtosis()) else 0.0,
                'Tail Ratio': 0.0,
                'Common Sense Ratio': 0.0,
                'Value at Risk': 0.0
            }
        stats_df = pd.DataFrame(rows)

    # Format values for crisp display (handling NaN, inf, percentages, floats)
    formatted_df = stats_df.copy()
    for col in formatted_df.columns:
        for idx in formatted_df.index:
            val = formatted_df.loc[idx, col]
            if pd.isna(val) or str(val) == 'NaT' or str(val) == 'nan' or str(val) == '<NA>':
                formatted_df.loc[idx, col] = '-'
            elif isinstance(val, (float, np.floating)):
                if np.isnan(val) or np.isinf(val):
                    formatted_df.loc[idx, col] = '-'
                elif '%' in str(idx):
                    formatted_df.loc[idx, col] = f'{val:.2f}%'
                else:
                    formatted_df.loc[idx, col] = f'{val:.2f}'

    html_stats = formatted_df.to_html(classes="stats-table", border=0, justify='left')
    
    template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TLCS Performance Analytics</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ margin: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #fff; overflow-x: hidden; overflow-y: hidden; }}
        * {{ box-sizing: border-box; }}
        .tab-container {{ padding: 8px 10px; background-color: #121826; border-bottom: 1px solid #1f2937; display: flex; gap: 4px; justify-content: space-between; width: 100%; }}
        .tab-btn {{ background-color: #1f2937; color: #9ca3af; border: none; padding: 6px 4px; border-radius: 6px; cursor: pointer; font-size: 11px; font-weight: 600; transition: all 0.2s; flex: 1; text-align: center; white-space: normal; line-height: 1.2; }}
        .tab-btn:hover {{ background-color: #374151; color: #fff; }}
        .tab-btn.active {{ background-color: #3b82f6; color: #fff; }}
        .tab-content {{ display: none; padding: 0; width: 100%; height: calc(100vh - 50px); }}
        .tab-content.active {{ display: block; }}
        .plotly-graph-div {{ width: 100% !important; height: 100% !important; }}
        /* Stats Table */
        .stats-container {{ padding: 15px; overflow-y: auto; overflow-x: auto; height: 100%; width: 100%; }}
        .stats-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 12px; text-align: left; background-color: #121826; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
        .stats-table th {{ background-color: #1f2937; color: #9ca3af; padding: 10px 12px; border-bottom: 1px solid #374151; font-weight: 600; }}
        .stats-table td {{ padding: 10px 12px; border-bottom: 1px solid #1f2937; color: #d1d5db; }}
        .stats-table tr:hover td {{ background-color: #1e293b; }}
        
        .stats-table thead th {{
            position: sticky;
            top: 0;
            background-color: #1f2937;
            z-index: 3;
        }}
        /* Freeze first column */
        .stats-table th:first-child,
        .stats-table td:first-child {{
            position: sticky;
            left: 0;
            background-color: #1f2937;
            z-index: 2;
            border-right: 1px solid #374151;
        }}
        .stats-table thead th:first-child {{
            z-index: 4;
        }}
        .stats-table td:first-child {{
            background-color: #121826;
        }}
        .stats-table tr:hover td:first-child {{
            background-color: #1e293b;
        }}
        
        /* Layout overrides for modes */
        body.mode-charts .tab-btn[onclick*="stats"] {{ display: none !important; }}
        body.mode-charts #stats {{ display: none !important; }}
        
        body.mode-stats .tab-container {{ display: none !important; }}
        body.mode-stats .tab-content {{ display: none !important; }}
        body.mode-stats #stats {{ display: block !important; }}
    </style>
</head>
<body>

<div class="tab-container">
    <button class="tab-btn active" onclick="switchTab('equity', this)">Equity Curve</button>
    <button class="tab-btn" onclick="switchTab('drawdown', this)">Drawdowns</button>
    <button class="tab-btn" onclick="switchTab('returns', this)">Raw Returns</button>
    <button class="tab-btn" onclick="switchTab('stats', this)">Statistics</button>
</div>

<div id="equity" class="tab-content active">
    {html_equity}
</div>

<div id="drawdown" class="tab-content">
    {html_dd}
</div>

<div id="returns" class="tab-content">
    {html_ret}
</div>

<div id="stats" class="tab-content">
    <div class="stats-container">
        {html_stats}
    </div>
</div>

<script>
    function switchTab(tabId, btnElement) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        btnElement.classList.add('active');
        window.dispatchEvent(new Event('resize'));
    }}
    
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    const rawTheme = (urlParams.get('theme') || 'dark').toLowerCase();

    if (mode === 'charts') {{
        document.body.classList.add('mode-charts');
    }} else if (mode === 'stats') {{
        document.body.classList.add('mode-stats');
    }}

    const isGray = rawTheme.includes('gray') || rawTheme.includes('slate');
    const isLight = rawTheme.includes('light');
    const isLion = rawTheme.includes('lion');

    const dynamicStyle = document.createElement('style');
    if (isGray) {{
        dynamicStyle.innerHTML = `
            body {{ background-color: transparent !important; color: #0F172A !important; }}
            .tab-container {{ background-color: rgba(203, 213, 225, 0.4) !important; border-bottom: 1px solid rgba(15, 23, 42, 0.15) !important; }}
            .tab-btn {{ background-color: rgba(255, 255, 255, 0.6) !important; color: #334155 !important; }}
            .tab-btn.active {{ background-color: #0F172A !important; color: #FFFFFF !important; }}
            .stats-container {{ background-color: transparent !important; }}
            .stats-table {{ background-color: transparent !important; border: 1px solid rgba(15, 23, 42, 0.15) !important; border-radius: 12px; overflow: hidden; }}
            .stats-table th {{ background-color: rgba(203, 213, 225, 0.65) !important; color: #0F172A !important; border-bottom: 1px solid rgba(15, 23, 42, 0.15) !important; font-weight: 800 !important; }}
            .stats-table td {{ background-color: transparent !important; color: #1E293B !important; border-bottom: 1px solid rgba(15, 23, 42, 0.08) !important; }}
            .stats-table thead th {{ background-color: rgba(203, 213, 225, 0.85) !important; }}
            .stats-table th:first-child {{ background-color: rgba(203, 213, 225, 0.85) !important; color: #0F172A !important; border-right: 1px solid rgba(15, 23, 42, 0.15) !important; font-weight: 800 !important; }}
            .stats-table td:first-child {{ background-color: rgba(226, 232, 240, 0.75) !important; color: #0F172A !important; border-right: 1px solid rgba(15, 23, 42, 0.15) !important; font-weight: 700 !important; }}
            .stats-table tr:hover td {{ background-color: rgba(203, 213, 225, 0.35) !important; }}
            .stats-table tr:hover td:first-child {{ background-color: rgba(203, 213, 225, 0.85) !important; }}
        `;
    }} else if (isLight) {{
        dynamicStyle.innerHTML = `
            body {{ background-color: transparent !important; color: #000000 !important; }}
            .tab-container {{ background-color: rgba(241, 245, 249, 0.6) !important; border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important; }}
            .tab-btn {{ background-color: rgba(255, 255, 255, 0.8) !important; color: #334155 !important; }}
            .tab-btn.active {{ background-color: #0284c7 !important; color: #FFFFFF !important; }}
            .stats-container {{ background-color: transparent !important; }}
            .stats-table {{ background-color: transparent !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; border-radius: 12px; overflow: hidden; }}
            .stats-table th {{ background-color: rgba(241, 245, 249, 0.75) !important; color: #000000 !important; border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important; font-weight: 800 !important; }}
            .stats-table td {{ background-color: transparent !important; color: #1E293B !important; border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important; }}
            .stats-table thead th {{ background-color: rgba(241, 245, 249, 0.9) !important; }}
            .stats-table th:first-child {{ background-color: rgba(241, 245, 249, 0.9) !important; color: #000000 !important; border-right: 1px solid rgba(0, 0, 0, 0.1) !important; font-weight: 800 !important; }}
            .stats-table td:first-child {{ background-color: rgba(248, 250, 252, 0.8) !important; color: #000000 !important; border-right: 1px solid rgba(0, 0, 0, 0.1) !important; font-weight: 700 !important; }}
            .stats-table tr:hover td {{ background-color: rgba(241, 245, 249, 0.5) !important; }}
            .stats-table tr:hover td:first-child {{ background-color: rgba(241, 245, 249, 0.95) !important; }}
        `;
    }} else if (isLion) {{
        dynamicStyle.innerHTML = `
            body {{ background-color: transparent !important; color: #FFFFFF !important; }}
            .tab-container {{ background-color: rgba(10, 10, 12, 0.6) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; }}
            .tab-btn {{ background-color: rgba(26, 26, 30, 0.8) !important; color: #c0c0cf !important; }}
            .tab-btn.active {{ background-color: #f2c64b !important; color: #000000 !important; font-weight: 800 !important; }}
            .stats-container {{ background-color: transparent !important; }}
            .stats-table {{ background-color: transparent !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; border-radius: 12px; overflow: hidden; }}
            .stats-table th {{ background-color: rgba(26, 26, 30, 0.75) !important; color: #f2c64b !important; border-bottom: 1px solid rgba(242, 198, 75, 0.25) !important; font-weight: 800 !important; }}
            .stats-table td {{ background-color: transparent !important; color: #c0c0cf !important; border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important; }}
            .stats-table thead th {{ background-color: rgba(26, 26, 30, 0.9) !important; }}
            .stats-table th:first-child {{ background-color: rgba(26, 26, 30, 0.9) !important; color: #f2c64b !important; border-right: 1px solid rgba(255, 255, 255, 0.12) !important; font-weight: 800 !important; }}
            .stats-table td:first-child {{ background-color: rgba(15, 15, 19, 0.75) !important; color: #f2c64b !important; border-right: 1px solid rgba(255, 255, 255, 0.12) !important; font-weight: 700 !important; }}
            .stats-table tr:hover td {{ background-color: rgba(242, 198, 75, 0.08) !important; }}
            .stats-table tr:hover td:first-child {{ background-color: rgba(26, 26, 30, 0.95) !important; }}
        `;
    }} else {{
        // Dark / Obsidian
        dynamicStyle.innerHTML = `
            body {{ background-color: transparent !important; color: #FFFFFF !important; }}
            .tab-container {{ background-color: rgba(10, 15, 20, 0.6) !important; border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; }}
            .tab-btn {{ background-color: rgba(26, 31, 38, 0.8) !important; color: #9ca3af !important; }}
            .tab-btn.active {{ background-color: #3b82f6 !important; color: #FFFFFF !important; font-weight: 800 !important; }}
            .stats-container {{ background-color: transparent !important; }}
            .stats-table {{ background-color: transparent !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 12px; overflow: hidden; }}
            .stats-table th {{ background-color: rgba(26, 31, 38, 0.75) !important; color: #F6AD55 !important; border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important; font-weight: 800 !important; }}
            .stats-table td {{ background-color: transparent !important; color: #CBD5E0 !important; border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important; }}
            .stats-table thead th {{ background-color: rgba(26, 31, 38, 0.9) !important; }}
            .stats-table th:first-child {{ background-color: rgba(26, 31, 38, 0.9) !important; color: #F6AD55 !important; border-right: 1px solid rgba(255, 255, 255, 0.1) !important; font-weight: 800 !important; }}
            .stats-table td:first-child {{ background-color: rgba(10, 15, 20, 0.75) !important; color: #FFFFFF !important; border-right: 1px solid rgba(255, 255, 255, 0.1) !important; font-weight: 700 !important; }}
            .stats-table tr:hover td {{ background-color: rgba(255, 255, 255, 0.06) !important; }}
            .stats-table tr:hover td:first-child {{ background-color: rgba(26, 31, 38, 0.95) !important; }}
        `;
    }}
    document.head.appendChild(dynamicStyle);

    const updateCharts = () => {{
        let allUpdated = true;
        document.querySelectorAll('.plotly-graph-div').forEach(div => {{
            if (div && div.layout) {{
                const isLightOrGray = isGray || isLight;
                Plotly.relayout(div, {{
                    'template': isLightOrGray ? 'plotly_white' : 'plotly_dark',
                    'paper_bgcolor': 'transparent',
                    'plot_bgcolor': 'transparent',
                    'font.color': isGray ? '#0F172A' : isLight ? '#000000' : '#FFFFFF',
                    'xaxis.gridcolor': isLightOrGray ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.05)',
                    'yaxis.gridcolor': isLightOrGray ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.05)',
                    'xaxis.zerolinecolor': isLightOrGray ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
                    'yaxis.zerolinecolor': isLightOrGray ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
                    'xaxis.linecolor': isLightOrGray ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)',
                    'yaxis.linecolor': isLightOrGray ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)'
                }});
            }} else {{
                allUpdated = false;
            }}
        }});
        
        if (!allUpdated) {{
            setTimeout(updateCharts, 100);
        }}
    }};
    
    setTimeout(updateCharts, 100);
</script>
</body>
</html>
"""
    with open(output_path, "w") as f:
        f.write(template)
    
    print(f'\nMulti-market tear sheet saved to {output_path}')

if __name__ == '__main__':
    run_returns_backtest()