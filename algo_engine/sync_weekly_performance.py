#!/usr/bin/env python3
"""
sync_weekly_performance.py
============================================================
TLCS Automated End-of-Week Statistics & Market Closure Engine
============================================================
1. Sweeps and resolves any stale/unclosed trades when markets close.
2. Aggregates all closed trades from Supabase by market & IST week (Monday–Sunday).
3. Enforces single source of truth exact_pct math & canonical win rate formula:
   Win Rate = Wins / (Wins + Losses + Breakevens) * 100
4. Computes Net Edge, Profit Factor, and Half-Kelly % risk edge.
5. Upserts into public.weekly_performance_logs.
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from supabase import create_client

MARKETS = {
    'nifty': ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BHARTIARTL', 'BPCL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIMINDTREE', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHRIRAMFIN', 'SUNPHARMA', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'ULTRACEMCO', 'WIPRO', 'NIFTY', 'BANKNIFTY'],
    'mcx': ['ALUMINIUM', 'ALUMINIUMM', 'COPPER', 'COTTON', 'CRUDEOIL', 'CRUDEOILM', 'GOLD', 'GOLDM', 'GOLDPETAL', 'LEAD', 'LEADMINI', 'MENTHAOIL', 'NATURALGAS', 'NATURALGASM', 'NICKEL', 'NICKELMINI', 'SILVER', 'SILVERM', 'SILVERMIC', 'ZINC', 'ZINCMINI'],
    'nymex': ['CL', 'GC', 'HG', 'HO', 'NG', 'PA', 'PL', 'RB', 'SI'],
    'crypto': ['ADAUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DOTUSDT', 'ETHUSDT', 'FILUSDT', 'ICPUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT', 'POLUSDT', 'SHIBUSDT', 'SOLUSDT', 'STXUSDT', 'TONUSDT', 'TRXUSDT', 'UNIUSDT', 'XLMUSDT', 'XRPUSDT'],
    'forex': ['AUDCAD', 'AUDINR', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURINR', 'EURJPY', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPINR', 'GBPJPY', 'GBPUSD', 'JPYINR', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDINR', 'USDJPY'],
    'world': ['AU200', 'DE40', 'EU50', 'FR40', 'HK50', 'JP225', 'NAS100', 'SPX500', 'UK100', 'US2000', 'US30']
}

def get_supabase_client():
    url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY')
    
    # Fallback to local .env.local file if in dev
    if not url or not key:
        search_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'Tv-Alert-Mobile', '.env.local'),
            os.path.join(os.path.dirname(__file__), '..', 'TLCS_Website_Deploy', '.env.local'),
            '.env.local'
        ]
        for p in search_paths:
            if os.path.exists(p):
                with open(p) as f:
                    for line in f:
                        if line.startswith('NEXT_PUBLIC_SUPABASE_URL='): url = line.split('=', 1)[1].strip()
                        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='): key = line.split('=', 1)[1].strip()
                if url and key:
                    break
                    
    # Known project fallback keys
    if not url:
        url = 'https://dwepduvhzuhzeehbeaaz.supabase.co'
    if not key:
        key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg'
        
    return create_client(url, key)

def clean_symbol(sym):
    if not sym: return ''
    raw = sym.upper().split(':')[-1].strip()
    return raw.replace('1!', '').replace('!', '').strip()

def get_market(sym):
    clean = clean_symbol(sym)
    for m, symbols in MARKETS.items():
        if clean in symbols:
            return m
    if clean.endswith('USDT') or clean.endswith('BTC'):
        return 'crypto'
    return 'unknown'

def is_market_closed(symbol, now_dt=None):
    """
    Returns True if the market for the symbol is currently closed.
    Traditional markets are closed on weekends (Saturday and Sunday)
    and outside their respective trading hours.
    """
    ist_tz = ZoneInfo('Asia/Kolkata')
    now = now_dt.astimezone(ist_tz) if now_dt else datetime.now(ist_tz)
    
    mkt = get_market(symbol)
    if mkt == 'crypto':
        return False # 24/7
        
    # Saturday (5) or Sunday (6) in weekday()
    if now.weekday() in (5, 6):
        return True
        
    cur_mins = now.hour * 60 + now.minute
    if mkt == 'nifty':
        # 09:15 to 15:30 IST
        return cur_mins < (9 * 60 + 15) or cur_mins >= (15 * 60 + 30)
    elif mkt == 'mcx':
        # 09:00 to 23:30 IST
        return cur_mins < (9 * 60) or cur_mins >= (23 * 60 + 30)
    elif mkt in ('nymex', 'forex', 'world'):
        # Mon-Fri session break ~02:30 to 03:30 IST
        return False
        
    return False

def sweep_unclosed_trades(sb):
    """
    Sweeps any stale/open trades whose market is closed (e.g. at the close of the week).
    Ensures NO TRACE of the previous session remains open.
    """
    print("[SWEEP] Checking for unclosed trades in closed markets...")
    ist_tz = ZoneInfo('Asia/Kolkata')
    now_ist = datetime.now(ist_tz)
    
    # Query all trades that are active or have no exit price
    res = sb.table('signals').select('*').or_('exit_price.is.null,outcome.eq.OPEN,status.ilike.%active%,status.ilike.%limit%').execute()
    signals = res.data or []
    
    swept_count = 0
    for s in signals:
        st = (s.get('status') or '').upper()
        out = (s.get('outcome') or '').upper()
        if 'CANCEL' in st or 'CANCEL' in out or 'UNKNOWN' in st:
            continue
            
        sym = s.get('symbol') or ''
        mkt = get_market(sym)
        
        # Check if the market is closed or trade was from a previous calendar day
        ts_str = s.get('created_at') or s.get('signal_ts')
        ts_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).astimezone(ist_tz) if ts_str else now_ist
        hours_old = (now_ist - ts_dt).total_seconds() / 3600.0
        
        market_closed = is_market_closed(sym, now_ist)
        is_weekend = now_ist.weekday() in (5, 6)
        
        # Stale threshold: traditional markets on weekends, or non-crypto > 16 hours old
        if (market_closed and (is_weekend or hours_old > 12)) or (mkt == 'crypto' and hours_old > 36):
            meta = s.get('metadata') or {}
            if isinstance(meta, str):
                try: meta = json.loads(meta)
                except: meta = {}
                
            is_limit = ('LIMIT' in st or 'OPEN' in st) and not s.get('updated_at')
            if is_limit:
                print(f"[SWEEP] Cancelling unexecuted limit order: {sym} ({s.get('id')})")
                sb.table('signals').update({
                    'status': 'CANCELLED',
                    'outcome': 'CANCELLED',
                    'updated_at': now_ist.isoformat()
                }).eq('id', s.get('id')).execute()
                swept_count += 1
            else:
                # Active position closed at EOD
                entry = float(s.get('entry') or 0)
                exit_p = float(s.get('current_price') or s.get('stop') or entry)
                is_long = 'SHORT' not in (s.get('type') or '').upper()
                exact_pct = ((exit_p - entry) / entry * 100.0) if is_long else ((entry - exit_p) / entry * 100.0) if entry else 0.0
                
                final_out = 'WIN' if exact_pct > 0.005 else ('LOSS' if exact_pct < -0.005 else 'BREAKEVEN')
                status_lbl = 'EOD Exit (TP1)' if final_out == 'WIN' else ('EOD Exit (SL)' if final_out == 'LOSS' else 'EOD Exit')
                
                meta['exact_pct'] = round(exact_pct, 2)
                meta['exit_reason'] = 'WEEKEND_EOD_CLOSE'
                print(f"[SWEEP] Force-closing stale active trade at session close: {sym} ({s.get('id')}) -> {final_out} ({exact_pct:.2f}%)")
                sb.table('signals').update({
                    'status': status_lbl,
                    'outcome': final_out,
                    'exit_price': exit_p,
                    'exit_at': now_ist.isoformat(),
                    'metadata': meta,
                    'updated_at': now_ist.isoformat()
                }).eq('id', s.get('id')).execute()
                swept_count += 1
                
    print(f"[SWEEP] Completed sweep. Resolved {swept_count} stale signals.")

def resolve_outcome(s):
    meta = s.get('metadata') or {}
    if isinstance(meta, str):
        try: meta = json.loads(meta)
        except: meta = {}
        
    pct = meta.get('exact_pct')
    if pct is not None:
        try:
            p = float(pct)
            if p > 0: return 'WIN', p
            if p < 0: return 'LOSS', p
            return 'BREAKEVEN', 0.0
        except: pass
        
    o = (s.get('outcome') or '').upper()
    st = (s.get('status') or '').upper()
    if 'CANCEL' in o or 'CANCEL' in st or 'UNKNOWN' in o or 'UNKNOWN' in st:
        return 'CANCELLED', 0.0
    if ('EXPIRED' in st or 'COMPLETED' in st) and not s.get('exit_price'):
        return 'CANCELLED', 0.0
        
    if o == 'WIN': return 'WIN', 0.0
    if o == 'LOSS': return 'LOSS', 0.0
    return 'OPEN', 0.0

def sync_weekly_performance():
    sb = get_supabase_client()
    ist_tz = ZoneInfo('Asia/Kolkata')
    
    # 1. Sweep any lingering traces of previous session if market is closed
    sweep_unclosed_trades(sb)
    
    # 2. Fetch all closed signals
    print("[SYNC] Fetching all historical closed trades...")
    all_signals = []
    page_size = 1000
    start = 0
    while True:
        res = sb.table('signals').select('*').not_.is_('exit_price', 'null').range(start, start + page_size - 1).execute()
        chunk = res.data or []
        all_signals.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
        
    print(f"[SYNC] Retrieved {len(all_signals)} closed trades.")
    
    # 3. Group by (week_start_date, market_type)
    weeks = {}
    for s in all_signals:
        out, pct = resolve_outcome(s)
        if out in ['OPEN', 'CANCELLED']:
            continue
            
        mkt = get_market(s.get('symbol'))
        if mkt == 'unknown':
            continue
            
        ts_str = s.get('exit_at') or s.get('updated_at') or s.get('created_at')
        if not ts_str:
            continue
            
        try:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).astimezone(ist_tz)
            # Monday of the week in IST
            mon = (dt.date() - timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
        except Exception:
            continue
            
        if mon not in weeks:
            weeks[mon] = {}
        if mkt not in weeks[mon]:
            weeks[mon][mkt] = []
            
        weeks[mon][mkt].append((out, pct))
        
    # 4. Calculate metrics for each market & week
    logs_to_insert = []
    print("\n" + "="*80)
    print(f"{'WEEK':<12} | {'MARKET':<8} | {'TRADES':<6} | {'WIN RATE':<9} | {'NET EDGE':<9} | {'PF':<6} | {'KELLY':<7}")
    print("="*80)
    
    for mon in sorted(weeks.keys()):
        for mkt in sorted(weeks[mon].keys()):
            trades = weeks[mon][mkt]
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
            
            # Canonical Win Rate: wins / (wins + losses + breakevens) * 100
            win_rate = (wins / total) * 100.0
            avg_r = net_r / total
            
            # Profit Factor
            if gross_loss > 0:
                pf = gross_profit / gross_loss
            elif gross_profit > 0:
                pf = 99.99
            else:
                pf = 0.0
                
            # Half-Kelly %
            avg_win = (gross_profit / wins) if wins > 0 else 0.0
            avg_loss = (gross_loss / losses) if losses > 0 else 1.0
            realized_rr = (avg_win / avg_loss) if avg_loss > 0 else (999 if avg_win > 0 else 0)
            
            wl_count = wins + losses
            kw_dec = wins / wl_count if wl_count > 0 else 0.0
            kl_dec = losses / wl_count if wl_count > 0 else 0.0
            
            kelly = 0.0
            if realized_rr > 0 and realized_rr != 999:
                kelly = ((kw_dec - (kl_dec / realized_rr)) * 100.0) * 0.5
            elif realized_rr == 999:
                kelly = (kw_dec * 100.0) * 0.5
            if kelly < 0:
                kelly = 0.0
                
            log_item = {
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
            }
            logs_to_insert.append(log_item)
            
            print(f"{mon:<12} | {mkt:<8} | {total:<6} | {win_rate:6.2f}%   | {net_r:+6.2f}%   | {pf:6.2f} | {kelly:+6.2f}%")
            
    print("="*80 + "\n")
    
    # 5. Upsert into Supabase weekly_performance_logs
    if logs_to_insert:
        CHUNK_SIZE = 50
        for i in range(0, len(logs_to_insert), CHUNK_SIZE):
            chunk = logs_to_insert[i:i + CHUNK_SIZE]
            res = sb.table('weekly_performance_logs').upsert(chunk, on_conflict='market_type, week_start_date').execute()
        print(f"[SYNC] Successfully upserted {len(logs_to_insert)} weekly performance logs into Supabase!")
    else:
        print("[SYNC] No closed trades found to log.")
        
    return logs_to_insert

if __name__ == '__main__':
    sync_weekly_performance()
