import os
import sys
import json
import yfinance as yf
from datetime import datetime, timedelta, timezone
from supabase import create_client

def get_yfinance_ticker(symbol, exchange=''):
    sym = symbol.upper()
    
    # Forex
    if len(sym) == 6 and (sym.endswith('USD') or sym.endswith('JPY') or sym.endswith('CAD') or sym.endswith('CHF') or sym.endswith('GBP') or sym.endswith('EUR') or sym.endswith('AUD') or sym.endswith('NZD') or sym.endswith('INR')):
        return f"{sym}=X"
    if sym.endswith('USD') and len(sym) > 3 and not sym.endswith('=X'):
        return f"{sym}=X"
        
    # Crypto
    if sym.endswith('USDT'):
        return f"{sym[:-4]}-USD"
    if sym.endswith('BTC'):
        return f"{sym[:-3]}-BTC"
        
    # Indices
    world_idx = {'UK100': '^FTSE', 'DAX': '^GDAXI', 'EU50': '^STOXX50E', 'HK50': '^HSI', 'JP225': '^N225', 'US30': '^DJI', 'SPX500': '^GSPC', 'NAS100': '^IXIC', 'US2000': '^RUT', 'AU200': '^AXJO'}
    if sym in world_idx: return world_idx[sym]
    if sym == 'NIFTY': return '^NSEI'
    if sym == 'BANKNIFTY': return '^NSEBANK'
    if sym == 'FINNIFTY': return 'NIFTY_FIN_SERVICE.NS'
    
    # Futures (NYMEX/MCX mappings from user rule)
    nymex = {'GC': 'GC=F', 'SI': 'SI=F', 'CL': 'CL=F', 'NG': 'NG=F', 'HG': 'HG=F', 'PL': 'PL=F', 'PA': 'PA=F', 'RB': 'RB=F', 'HO': 'HO=F'}
    if sym in nymex: return nymex[sym]
    if sym.endswith('1!'):
        base = sym[:-2]
        if base in nymex: return nymex[base]
        
    # Indian equities (add .NS)
    nse_stocks = ["ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BHARTIARTL", "BPCL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK", "INDUSINDBK", "INFY", "ITC", "JSWSTEEL", "KOTAKBANK", "LT", "LTIMINDTREE", "M&M", "MARUTI", "NESTLEIND", "NTPC", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SHRIRAMFIN", "SUNPHARMA", "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TCS", "TECHM", "TITAN", "ULTRACEMCO", "WIPRO"]
    if sym in nse_stocks: return f"{sym}.NS"
    
    return sym

def process_trades():
    url = ''
    key = ''
    with open('Tv-Alert-Mobile/.env.local') as f:
        for line in f:
            if line.startswith('NEXT_PUBLIC_SUPABASE_URL='): url = line.strip().split('=')[1]
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='): key = line.strip().split('=')[1]

    supabase = create_client(url, key)
    
    res = supabase.table('signals').select('*').in_('status', ['Active', 'OPEN', 'Open']).execute()
    trades = res.data
    
    print(f"Found {len(trades)} open trades to reconstruct.")
    
    fixed_count = 0
    for t in trades:
        symbol = t.get('symbol', '')
        entry = t.get('entry')
        stop = t.get('stop')
        target = t.get('target') or t.get('tp1') or t.get('tp2') or t.get('tp3') or t.get('tp4')
        created_at_str = t.get('created_at')
        
        if not entry or (not stop and not target):
            print(f"Skipping {symbol}: missing price levels.")
            continue
            
        try:
            entry = float(entry)
            if stop: stop = float(stop)
            if target: target = float(target)
        except Exception:
            continue
            
        # Parse created_at
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        
        is_long = True
        ttype = t.get('type', '').upper()
        if 'SHORT' in ttype or 'SELL' in ttype:
            is_long = False
            
        ticker = get_yfinance_ticker(symbol)
        
        # Download 1m or 5m data from created_at to now
        start_date = created_at - timedelta(hours=1) # Buffer
        end_date = datetime.now(timezone.utc)
        
        try:
            # yfinance max 1m history is 7 days. If older, use 5m (max 60 days).
            if (end_date - created_at).days <= 6:
                df = yf.download(ticker, start=start_date, end=end_date, interval='1m', progress=False)
            else:
                df = yf.download(ticker, start=start_date, end=end_date, interval='5m', progress=False)
                
            if df.empty:
                print(f"Could not fetch data for {ticker} ({symbol}). Skipping.")
                continue
                
            # Flatten columns if multiindex
            if isinstance(df.columns, tuple) or hasattr(df.columns, 'levels'):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
                
            hit_stop = False
            hit_target = False
            exit_price = None
            exit_time = None
            
            for index, row in df.iterrows():
                # Make index timezone aware if it isn't
                if index.tzinfo is None:
                    idx_time = index.replace(tzinfo=timezone.utc)
                else:
                    idx_time = index
                    
                if idx_time < created_at:
                    continue
                    
                high = float(row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High'])
                low = float(row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low'])
                
                if is_long:
                    if stop and low <= stop:
                        hit_stop = True
                        exit_price = stop
                        exit_time = idx_time
                        break
                    if target and high >= target:
                        hit_target = True
                        exit_price = target
                        exit_time = idx_time
                        break
                else:
                    if stop and high >= stop:
                        hit_stop = True
                        exit_price = stop
                        exit_time = idx_time
                        break
                    if target and low <= target:
                        hit_target = True
                        exit_price = target
                        exit_time = idx_time
                        break
                        
            if not hit_stop and not hit_target:
                # Still open, or data missing. We will EOD close it to give some stats
                exit_price = float(df['Close'].iloc[-1].iloc[0] if hasattr(df['Close'].iloc[-1], 'iloc') else df['Close'].iloc[-1])
                exit_time = end_date
                outcome = 'BREAKEVEN'
            else:
                outcome = 'LOSS' if hit_stop else 'WIN'
                
            # Calc exact math
            if is_long:
                profit_amount = exit_price - entry
            else:
                profit_amount = entry - exit_price
                
            exact_pct = round((profit_amount / entry) * 100, 3)
            
            if not hit_stop and not hit_target:
                if exact_pct > 0.005: outcome = 'WIN'
                elif exact_pct < -0.005: outcome = 'LOSS'
                
            meta = t.get('metadata') or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
                
            meta['exact_pct'] = exact_pct
            meta['reconstructed_by_ai'] = True
            
            supabase.table('signals').update({
                'status': 'Reconstructed Exit',
                'outcome': outcome,
                'exit_price': exit_price,
                'exit_at': exit_time.isoformat(),
                'metadata': meta,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', t['id']).execute()
            
            print(f"[{symbol}] Reconstructed -> {outcome} at {exit_price} (Pct: {exact_pct}%)")
            fixed_count += 1
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    print(f"Successfully reconstructed {fixed_count} out of {len(trades)} stuck trades.")

if __name__ == '__main__':
    process_trades()
