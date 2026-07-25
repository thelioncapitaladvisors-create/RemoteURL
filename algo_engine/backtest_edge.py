import os
import json
import pandas as pd
import vectorbt as vbt
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Error: Missing Supabase credentials in .env file.')
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

def fetch_closed_trades_for_today():
    print("Fetching today's historical trades from Supabase...")
    
    # 0 Hrs strict local boundary (Asia/Kolkata)
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = datetime.now(ist)
    start_of_today_ist = datetime(now_ist.year, now_ist.month, now_ist.day, tzinfo=ist)
    
    # Convert to UTC string for Supabase query
    start_utc = start_of_today_ist.astimezone(ZoneInfo('UTC')).isoformat()
    
    response = supabase.table('signals').select('*').gte('created_at', start_utc).order('created_at', desc=False).limit(2000).execute()
    data = response.data
    
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
                    continue
                    
    return closed_trades, start_of_today_ist, now_ist

def run_returns_backtest():
    trades, start_of_today_ist, now_ist = fetch_closed_trades_for_today()
    
    markets = ['NIFTY', 'MCX', 'NYMEX', 'CRYPTO', 'FOREX', 'WORLD']
    
    if not trades:
        print('No closed trades found for today with valid exact_pct. Creating empty timeline.')
        df_pivot = pd.DataFrame(columns=markets)
    else:
        df = pd.DataFrame(trades)
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)
        
        print(f'\nLoaded {len(df)} closed trades for today.')
        print('Analyzing performance using VectorBT...\n')
        
        # Ensure timezone aware (UTC -> IST)
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert(start_of_today_ist.tzinfo)
        
        # Pivot table so each market has its own column, sum returns for simultaneous trades
        df_pivot = df.pivot_table(index='datetime', columns='market', values='return', aggfunc='sum').fillna(0.0)
    
    # Ensure all 6 core markets exist in columns
    for m in markets:
        if m not in df_pivot.columns:
            df_pivot[m] = 0.0
            
    # Filter out UNKNOWN markets and order columns
    df_pivot = df_pivot[markets]
    
    # Create a full minute-by-minute timeline for today up to current time
    full_idx = pd.date_range(start=start_of_today_ist, end=now_ist, freq='15min')
    
    # Resample to 15-minute frequency and fill missing with 0.0
    if df_pivot.empty:
        df_resampled = pd.DataFrame(0.0, index=full_idx, columns=markets)
    else:
        df_resampled = df_pivot.resample('15min').sum().reindex(full_idx, fill_value=0.0)
    
    # Feed to VectorBT (multi-column)
    vbt_returns = df_resampled.vbt.returns(freq='15min')
    
    # Print stats
    print("--- TODAY'S BACKTEST METRICS ---")
    print(vbt_returns.stats())
    
    # Save Tear Sheet to the website deployment folder
    output_path = os.path.join(os.path.dirname(__file__), '..', 'TLCS_Website_Deploy', 'strategy_tearsheet.html')
    vbt_returns.plot().write_html(output_path)
    print(f'\nMulti-market tear sheet saved to {output_path}')

if __name__ == '__main__':
    run_returns_backtest()