"""
1-Year VectorBT & Quantitative Backtest Engine for NYMEX & COMEX Commodities
Comparing Performance Across Signal Types: MISSILE vs SCALP vs LIGHTNING
With Single-Symbol Restricted Consecutive Loss Streaks.
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import numpy as np
import pandas as pd
import vectorbt as vbt
import yfinance as yf
from datetime import datetime, timedelta

# Disable vectorbt caching to prevent Numba cache corruption
vbt.settings.caching['enabled'] = False

NYMEX_SYMBOLS = {
    'CL': {'name': 'Crude Oil WTI', 'ticker': 'CL=F', 'unit': '$/bbl', 'multiplier': 1000},
    'GC': {'name': 'Gold Futures', 'ticker': 'GC=F', 'unit': '$/oz', 'multiplier': 100},
    'SI': {'name': 'Silver Futures', 'ticker': 'SI=F', 'unit': '$/oz', 'multiplier': 5000},
    'HG': {'name': 'Copper Futures', 'ticker': 'HG=F', 'unit': '$/lb', 'multiplier': 25000},
    'NG': {'name': 'Natural Gas', 'ticker': 'NG=F', 'unit': '$/MMBtu', 'multiplier': 10000},
    'PL': {'name': 'Platinum Futures', 'ticker': 'PL=F', 'unit': '$/oz', 'multiplier': 50},
    'PA': {'name': 'Palladium Futures', 'ticker': 'PA=F', 'unit': '$/oz', 'multiplier': 100},
    'HO': {'name': 'Heating Oil', 'ticker': 'HO=F', 'unit': '$/gal', 'multiplier': 42000},
    'RB': {'name': 'RBOB Gasoline', 'ticker': 'RB=F', 'unit': '$/gal', 'multiplier': 42000}
}

def compute_technical_indicators(df):
    """
    Computes Pine Script equivalent technical indicators on hourly data.
    """
    high = df['High']
    low = df['Low']
    close = df['Close']
    open_p = df['Open']
    
    # 1. Typical Price / Pivot
    typical_price = (high + low + close) / 3.0
    
    # 2. EMAs (Short = 13, Medium = 32)
    ema13 = typical_price.ewm(span=13, adjust=False).mean()
    ema32 = typical_price.ewm(span=32, adjust=False).mean()
    
    # 3. ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    # 4. ADX & Directional Movement (14)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14).mean().fillna(0)
    
    # 5. RSI (14)
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).rolling(14).mean()
    avg_loss = pd.Series(loss, index=df.index).rolling(14).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs)).fillna(50)
    
    # 6. Daily Pivot Points & CPR Approximation (rolling 24 bars)
    rolling_h = high.rolling(24).max()
    rolling_l = low.rolling(24).min()
    rolling_c = close
    pivot = (rolling_h + rolling_l + rolling_c) / 3.0
    bc = (rolling_h + rolling_l) / 2.0
    tc = 2.0 * pivot - bc
    
    return pd.DataFrame({
        'Open': open_p, 'High': high, 'Low': low, 'Close': close,
        'TP': typical_price, 'EMA13': ema13, 'EMA32': ema32,
        'ATR': atr, 'PlusDI': plus_di, 'MinusDI': minus_di, 'ADX': adx,
        'RSI': rsi, 'Pivot': pivot, 'BC': bc, 'TC': tc
    }, index=df.index)

def generate_signals(df):
    """
    Generates MISSILE, SCALP, and LIGHTNING long/short signals.
    """
    c = df['Close']
    o = df['Open']
    h = df['High']
    l = df['Low']
    ema13 = df['EMA13']
    ema32 = df['EMA32']
    plus_di = df['PlusDI']
    minus_di = df['MinusDI']
    adx = df['ADX']
    rsi = df['RSI']
    pivot = df['Pivot']
    
    # Trend alignment
    bull_trend = (ema13 > ema32) & (plus_di > minus_di)
    bear_trend = (ema13 < ema32) & (minus_di > plus_di)
    
    # 1. LIGHTNING: High-conviction confluence or RSI divergence
    # Bullish divergence: price makes new low in 10 bars, but RSI makes higher low
    bull_div = (l <= l.rolling(10).min()) & (rsi > rsi.rolling(10).min()) & (rsi < 40)
    bear_div = (h >= h.rolling(10).max()) & (rsi < rsi.rolling(10).max()) & (rsi > 60)
    
    lightning_long = ((bull_trend & (adx > 25) & (c > ema13) & (c.shift(1) <= ema13.shift(1))) | (bull_div & (c > o)))
    lightning_short = ((bear_trend & (adx > 25) & (c < ema13) & (c.shift(1) >= ema13.shift(1))) | (bear_div & (c < o)))
    
    # 2. SCALP: Pullback / CPR boundary rebound
    # Price dips towards or tests EMA32 / Pivot and closes back above EMA13
    scalp_long = bull_trend & (l < ema13) & (c > ema13) & (c > o) & (~lightning_long)
    scalp_short = bear_trend & (h > ema13) & (c < ema13) & (c < o) & (~lightning_short)
    
    # 3. MISSILE: Momentum breakout
    # Strong momentum bar crossing EMA / Pivot
    missile_long = (ema13.shift(1) <= ema32.shift(1)) & (ema13 > ema32) & (c > pivot) & (~lightning_long) & (~scalp_long)
    # Also trigger when momentum breaks after consolidation
    missile_long = missile_long | (bull_trend & (c > h.shift(1)) & (c > h.shift(2)) & (adx > 20) & (c.shift(1) <= c.shift(2))) & (~lightning_long) & (~scalp_long)
    
    missile_short = (ema13.shift(1) >= ema32.shift(1)) & (ema13 < ema32) & (c < pivot) & (~lightning_short) & (~scalp_short)
    missile_short = missile_short | (bear_trend & (c < l.shift(1)) & (c < l.shift(2)) & (adx > 20) & (c.shift(1) >= c.shift(2))) & (~lightning_short) & (~scalp_short)
    
    return {
        'MISSILE': {'long': missile_long.fillna(False), 'short': missile_short.fillna(False)},
        'SCALP': {'long': scalp_long.fillna(False), 'short': scalp_short.fillna(False)},
        'LIGHTNING': {'long': lightning_long.fillna(False), 'short': lightning_short.fillna(False)}
    }

def simulate_trades(df, signals, symbol):
    """
    Simulates trades with canonical exact_pct math, TP1 (1.5R), Breakeven on TP1 hit, TP2 (2.5R), and SL (1.0R).
    """
    trades = []
    
    for sig_type, sig_dict in signals.items():
        longs = sig_dict['long']
        shorts = sig_dict['short']
        
        in_trade = False
        trade_dir = None
        entry_price = 0.0
        entry_idx = None
        entry_time = None
        sl_price = 0.0
        tp1_price = 0.0
        tp2_price = 0.0
        r_dist = 0.0
        hit_tp1 = False
        
        for i in range(1, len(df)):
            idx = df.index[i]
            prev_idx = df.index[i-1]
            c = df['Close'].iloc[i]
            h = df['High'].iloc[i]
            l = df['Low'].iloc[i]
            o = df['Open'].iloc[i]
            atr_val = df['ATR'].iloc[i-1]
            if np.isnan(atr_val) or atr_val <= 0:
                continue
                
            # If in active trade, evaluate exits
            if in_trade:
                exit_price = None
                exit_reason = None
                
                if trade_dir == 'LONG':
                    # Check Stop Loss
                    if l <= sl_price:
                        exit_price = sl_price
                        exit_reason = 'Hit Initial SL' if not hit_tp1 else 'Hit B/E'
                    # Check TP1 hit -> move to Breakeven
                    elif not hit_tp1 and h >= tp1_price:
                        hit_tp1 = True
                        sl_price = entry_price  # Move SL to breakeven (Darth Maul Rule)
                        # Check if candle reversed and closed below BE on same candle
                        if c < entry_price:
                            exit_price = entry_price
                            exit_reason = 'Reversal Exit (B/E)'
                    # Check TP2
                    elif hit_tp1 and h >= tp2_price:
                        exit_price = tp2_price
                        exit_reason = 'Completed TP2'
                        
                elif trade_dir == 'SHORT':
                    # Check Stop Loss
                    if h >= sl_price:
                        exit_price = sl_price
                        exit_reason = 'Hit Initial SL' if not hit_tp1 else 'Hit B/E'
                    # Check TP1 hit -> move to Breakeven
                    elif not hit_tp1 and l <= tp1_price:
                        hit_tp1 = True
                        sl_price = entry_price
                        if c > entry_price:
                            exit_price = entry_price
                            exit_reason = 'Reversal Exit (B/E)'
                    # Check TP2
                    elif hit_tp1 and l <= tp2_price:
                        exit_price = tp2_price
                        exit_reason = 'Completed TP2'
                
                # Check max hold time (e.g. 72 hours timeout)
                if not exit_price and (i - entry_idx) >= 72:
                    exit_price = c
                    exit_reason = 'Timeout Exit'
                    
                if exit_price is not None:
                    # Compute canonical exact_pct
                    if trade_dir == 'LONG':
                        exact_pct = ((exit_price - entry_price) / entry_price) * 100.0
                    else:
                        exact_pct = ((entry_price - exit_price) / entry_price) * 100.0
                        
                    # Canonical Outcome resolution based strictly on exact_pct
                    if exact_pct > 0.05:
                        outcome = 'WIN'
                    elif exact_pct < -0.05:
                        outcome = 'LOSS'
                    else:
                        outcome = 'BREAKEVEN'
                        
                    trades.append({
                        'symbol': symbol,
                        'signal_type': sig_type,
                        'direction': trade_dir,
                        'entry_time': entry_time,
                        'exit_time': idx,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'exact_pct': exact_pct,
                        'outcome': outcome,
                        'exit_reason': exit_reason
                    })
                    
                    in_trade = False
                    trade_dir = None
                    hit_tp1 = False
                    continue
                    
            # If not in trade, check for new signal trigger
            if not in_trade:
                if longs.iloc[i-1]:
                    in_trade = True
                    trade_dir = 'LONG'
                    entry_price = o
                    entry_idx = i
                    entry_time = idx
                    r_dist = atr_val * 1.5
                    sl_price = entry_price - r_dist
                    tp1_price = entry_price + (r_dist * 1.5)
                    tp2_price = entry_price + (r_dist * 2.5)
                    hit_tp1 = False
                elif shorts.iloc[i-1]:
                    in_trade = True
                    trade_dir = 'SHORT'
                    entry_price = o
                    entry_idx = i
                    entry_time = idx
                    r_dist = atr_val * 1.5
                    sl_price = entry_price + r_dist
                    tp1_price = entry_price - (r_dist * 1.5)
                    tp2_price = entry_price - (r_dist * 2.5)
                    hit_tp1 = False
                    
    return trades

def compute_performance_metrics(trades_list):
    """
    Computes all canonical performance metrics including symbol-isolated consecutive loss streaks.
    """
    if not trades_list:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_winner': 0.0, 'avg_loser': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'max_consec_losses': 0,
            'sharpe': 0.0, 'calmar': 0.0
        }
        
    df_trades = pd.DataFrame(trades_list)
    # Sort chronologically by entry_time
    df_trades = df_trades.sort_values('entry_time').reset_index(drop=True)
    
    total = len(df_trades)
    wins = df_trades[df_trades['outcome'] == 'WIN']
    losses = df_trades[df_trades['outcome'] == 'LOSS']
    bes = df_trades[df_trades['outcome'] == 'BREAKEVEN']
    
    # CANONICAL WIN RATE FORMULA: wins / total_closed_trades * 100 (Breakevens included in denominator)
    win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0
    
    gross_profit = wins['exact_pct'].sum() if len(wins) > 0 else 0.0
    gross_loss = abs(losses['exact_pct'].sum()) if len(losses) > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    
    net_return = df_trades['exact_pct'].sum()
    expectancy = df_trades['exact_pct'].mean()
    
    avg_win = wins['exact_pct'].mean() if len(wins) > 0 else 0.0
    avg_loss = abs(losses['exact_pct'].mean()) if len(losses) > 0 else 0.0
    realized_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0
    
    # Cumulative return & Max Drawdown
    cum_returns = df_trades['exact_pct'].cumsum()
    peak = cum_returns.cummax()
    dd = peak - cum_returns
    max_dd = dd.max() if len(dd) > 0 else 0.0
    
    # CONSECUTIVE LOSSES (RESTRICTED TO ONLY ONE SYMBOL)
    # Track streaks per-symbol individually
    symbol_streaks = {}
    for sym, group in df_trades.groupby('symbol'):
        group_sorted = group.sort_values('entry_time')
        current_streak = 0
        max_sym_streak = 0
        for out in group_sorted['outcome']:
            if out == 'LOSS':
                current_streak += 1
                if current_streak > max_sym_streak:
                    max_sym_streak = current_streak
            else:
                current_streak = 0
        symbol_streaks[sym] = max_sym_streak
        
    max_consec_losses = max(symbol_streaks.values()) if symbol_streaks else 0
    
    # Sharpe & Calmar
    std = df_trades['exact_pct'].std()
    sharpe = (expectancy / std) if (std and not np.isnan(std) and std > 0) else 0.0
    calmar = (net_return / max_dd) if max_dd > 0 else 0.0
    
    return {
        'total_trades': total,
        'wins': len(wins),
        'losses': len(losses),
        'breakevens': len(bes),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'net_return': net_return,
        'expectancy': expectancy,
        'avg_winner': avg_win,
        'avg_loser': avg_loss,
        'realized_rr': realized_rr,
        'max_drawdown': max_dd,
        'max_consec_losses': max_consec_losses,
        'symbol_streaks': symbol_streaks,
        'sharpe': sharpe,
        'calmar': calmar
    }

def main():
    print("=" * 80)
    print("   1-YEAR NYMEX & COMEX QUANTITATIVE BACKTEST (VECTORBT ENGINE)")
    print("   Evaluating: MISSILE vs SCALP vs LIGHTNING Signals")
    print("   Rule: Consecutive Losses Restricted Strictly to One Symbol")
    print("=" * 80)
    
    all_trades = []
    symbol_data = {}
    
    # 1. Download & Process Each Commodity
    for sym, info in NYMEX_SYMBOLS.items():
        ticker = info['ticker']
        print(f"Downloading 1-year historical hourly data for {sym} ({info['name']}: {ticker})...")
        try:
            df_raw = yf.download(ticker, period='1y', interval='1h', progress=False)
            if df_raw.empty or len(df_raw) < 100:
                print(f"  [!] Insufficient data for {sym}, skipping.")
                continue
                
            # Handle MultiIndex columns if present
            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)
                
            df_ind = compute_technical_indicators(df_raw)
            sigs = generate_signals(df_ind)
            trades = simulate_trades(df_ind, sigs, sym)
            
            all_trades.extend(trades)
            symbol_data[sym] = {'df': df_ind, 'trades': trades}
            print(f"  [✓] {sym}: {len(df_ind)} bars, {len(trades)} executed trades.")
        except Exception as e:
            print(f"  [X] Error processing {sym}: {e}")
            
    if not all_trades:
        print("No trades generated. Exiting.")
        return
        
    df_all_trades = pd.DataFrame(all_trades)
    
    # 2. Performance Comparison Across Signal Types (MISSILE vs SCALP vs LIGHTNING)
    print("\n" + "=" * 80)
    print("   PART 1: SIGNAL TYPE PERFORMANCE COMPARISON (LAST 1 YEAR)")
    print("=" * 80)
    
    signal_results = {}
    for sig_type in ['MISSILE', 'SCALP', 'LIGHTNING']:
        sub_trades = [t for t in all_trades if t['signal_type'] == sig_type]
        m = compute_performance_metrics(sub_trades)
        signal_results[sig_type] = m
        
    sig_summary = []
    for sig_type, m in signal_results.items():
        sig_summary.append({
            'Signal Type': sig_type,
            'Trades': m['total_trades'],
            'W / L / BE': f"{m['wins']} / {m['losses']} / {m['breakevens']}",
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}" if m['profit_factor'] < 100 else 'MAX',
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.2f}%",
            'Realized R:R': f"{m['realized_rr']:.2f}R",
            'Max Drawdown': f"-{m['max_drawdown']:.2f}%",
            'Max Consec. Losses (Single Symbol)': f"{m['max_consec_losses']} trades",
            'Sharpe': f"{m['sharpe']:.2f}",
            'Calmar': f"{m['calmar']:.2f}"
        })
    df_sig_summary = pd.DataFrame(sig_summary)
    print(df_sig_summary.to_string(index=False))
    
    # 3. Commodity-Wise Breakdown Across All 9 Assets
    print("\n" + "=" * 80)
    print("   PART 2: COMMODITY-WISE BREAKDOWN (ACROSS ALL SIGNALS)")
    print("=" * 80)
    
    commodity_summary = []
    for sym in NYMEX_SYMBOLS.keys():
        sub_trades = [t for t in all_trades if t['symbol'] == sym]
        m = compute_performance_metrics(sub_trades)
        # Single symbol consecutive losses
        sym_streak = m['symbol_streaks'].get(sym, 0)
        commodity_summary.append({
            'Asset': f"{sym} ({NYMEX_SYMBOLS[sym]['name']})",
            'Trades': m['total_trades'],
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}" if m['profit_factor'] < 100 else 'MAX',
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.2f}%",
            'Avg Winner': f"+{m['avg_winner']:.2f}%",
            'Avg Loser': f"-{m['avg_loser']:.2f}%",
            'Max Consec. Losses': f"{sym_streak} trades",
            'Max DD': f"-{m['max_drawdown']:.2f}%"
        })
    df_comm_summary = pd.DataFrame(commodity_summary)
    print(df_comm_summary.to_string(index=False))
    
    # 4. Save JSON results for application integration
    output_json = os.path.join(os.path.dirname(__file__), 'nymex_comex_1yr_backtest_results.json')
    overall_metrics = compute_performance_metrics(all_trades)
    
    save_data = {
        'timestamp': datetime.now().isoformat(),
        'period': '1 Year (Hourly Bars)',
        'overall': {
            'total_trades': overall_metrics['total_trades'],
            'win_rate': overall_metrics['win_rate'],
            'profit_factor': overall_metrics['profit_factor'],
            'net_return': overall_metrics['net_return'],
            'expectancy': overall_metrics['expectancy'],
            'max_drawdown': overall_metrics['max_drawdown'],
            'max_consec_losses_single_symbol': overall_metrics['max_consec_losses'],
            'symbol_streaks': overall_metrics['symbol_streaks']
        },
        'by_signal_type': signal_results,
        'by_commodity': commodity_summary
    }
    
    import json
    with open(output_json, 'w') as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n[✓] Detailed backtest report saved to: {output_json}")

if __name__ == '__main__':
    main()
