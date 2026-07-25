import os
import json
import pandas as pd
import vectorbt as vbt
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing Supabase credentials in .env file.")
    exit(1)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def resolve_outcome(signal):
    """
    Python implementation of the Canonical resolveOutcome from User Rules.
    """
    st = str(signal.get("status", "")).upper()
    o = str(signal.get("outcome", "")).upper()

    # Step 1: Hard-kill CANCELLED/UNKNOWN first
    if 'CANCEL' in o or 'CANCEL' in st or 'UNKNOWN' in st or 'UNKNOWN' in o:
        return 'CANCELLED'
    if ('EXPIRED' in st or 'COMPLETED' in st) and not signal.get('exit_price'):
        return 'CANCELLED'

    # Step 2: exact_pct is the SINGLE SOURCE OF TRUTH
    meta = signal.get("metadata", {})
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except:
            meta = {}
            
    if meta and "exact_pct" in meta and meta["exact_pct"] is not None:
        try:
            pct = float(meta["exact_pct"])
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

def fetch_closed_trades():
    print("Fetching historical trades from Supabase...")
    # Since Supabase python client limits to 1000 by default, we might need to paginate or just grab the latest
    response = supabase.table("signals").select("*").order("created_at", desc=False).limit(2000).execute()
    data = response.data
    
    closed_trades = []
    
    for s in data:
        outcome = resolve_outcome(s)
        if outcome in ['WIN', 'LOSS', 'BREAKEVEN']:
            meta = s.get("metadata", {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except:
                    meta = {}
                    
            if meta and "exact_pct" in meta and meta["exact_pct"] is not None:
                try:
                    pct_return = float(meta["exact_pct"]) / 100.0  # Convert 1.35 to 0.0135
                    
                    # Prioritize exit_at or updated_at, fallback to created_at
                    ts_str = s.get("exit_at") or s.get("updated_at") or s.get("created_at")
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    except:
                        continue
                        
                    closed_trades.append({
                        "datetime": ts,
                        "symbol": s.get("symbol", "UNKNOWN"),
                        "return": pct_return
                    })
                except ValueError:
                    continue
                    
    return closed_trades

def run_returns_backtest():
    trades = fetch_closed_trades()
    if not trades:
        print("No closed trades found with valid exact_pct.")
        return
        
    df = pd.DataFrame(trades)
    df.set_index("datetime", inplace=True)
    df.sort_index(inplace=True)
    
    print(f"\nLoaded {len(df)} closed trades.")
    print("Analyzing performance using VectorBT...\n")
    
    # Resample to daily returns for accurate time-based metrics (Sharpe, Annualized Return)
    returns_series = df["return"].resample('D').sum().fillna(0.0)
    
    # For a realistic equity curve from a series of trade percentages, we can use vbt.ReturnsAccessor
    # If a trade returned 5%, our portfolio grew by 5%.
    
    vbt_returns = returns_series.vbt.returns(freq='D')
    
    # Print stats
    print("--- BACKTEST METRICS ---")
    print(vbt_returns.stats())
    
    # Save Tear Sheet to the website deployment folder so it can be embedded in the Admin Panel
    output_path = os.path.join(os.path.dirname(__file__), '..', 'TLCS_Website_Deploy', 'strategy_tearsheet.html')
    vbt_returns.plot().write_html(output_path)
    print(f"\nTear sheet saved to {output_path}")

if __name__ == "__main__":
    run_returns_backtest()
