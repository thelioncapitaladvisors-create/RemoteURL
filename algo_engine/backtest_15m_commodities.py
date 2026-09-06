"""
15-Minute VectorBT & Quantitative Backtest Engine for NG, CL, SI, and GC
Comparing Performance Across Signal Types: MISSILE vs SCALP vs LIGHTNING
Rule: Consecutive Losses Restricted Strictly to Individual Symbol
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import numpy as np
import pandas as pd
import vectorbt as vbt
import yfinance as yf
from datetime import datetime

vbt.settings.caching['enabled'] = False

TARGET_COMMODITIES = {
    'NG': {'name': 'Natural Gas', 'ticker': 'NG=F', 'unit': '$/MMBtu'},
    'CL': {'name': 'Crude Oil WTI', 'ticker': 'CL=F', 'unit': '$/bbl'},
    'SI': {'name': 'Silver Futures', 'ticker': 'SI=F', 'unit': '$/oz'},
    'GC': {'name': 'Gold Futures', 'ticker': 'GC=F', 'unit': '$/oz'}
}

def compute_indicators_15m(df):
    high = df['High']
    low = df['Low']
    close = df['Close']
    open_p = df['Open']
    
    # Typical Price
    typical_price = (high + low + close) / 3.0
    
    # 15m EMAs (Short = 13, Medium = 32)
    ema13 = typical_price.ewm(span=13, adjust=False).mean()
    ema32 = typical_price.ewm(span=32, adjust=False).mean()
    
    # ATR (14)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    
    # ADX (14)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(14).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(14).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14).mean().fillna(0)
    
    # RSI (14)
    delta = close.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).rolling(14).mean()
    avg_loss = pd.Series(loss, index=df.index).rolling(14).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs)).fillna(50)
    
    # Daily CPR approximation (rolling 96 15-min bars = 24h)
    rolling_h = high.rolling(96).max()
    rolling_l = low.rolling(96).min()
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

def generate_signals_15m(df):
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
    
    bull_trend = (ema13 > ema32) & (plus_di > minus_di)
    bear_trend = (ema13 < ema32) & (minus_di > plus_di)
    
    # 1. LIGHTNING: Confluence & Divergence
    bull_div = (l <= l.rolling(15).min()) & (rsi > rsi.rolling(15).min()) & (rsi < 40)
    bear_div = (h >= h.rolling(15).max()) & (rsi < rsi.rolling(15).max()) & (rsi > 60)
    
    lightning_long = ((bull_trend & (adx > 22) & (c > ema13) & (c.shift(1) <= ema13.shift(1))) | (bull_div & (c > o)))
    lightning_short = ((bear_trend & (adx > 22) & (c < ema13) & (c.shift(1) >= ema13.shift(1))) | (bear_div & (c < o)))
    
    # 2. SCALP: 15m CPR/EMA Rebound
    scalp_long = bull_trend & (l < ema13) & (c > ema13) & (c > o) & (~lightning_long)
    scalp_short = bear_trend & (h > ema13) & (c < ema13) & (c < o) & (~lightning_short)
    
    # 3. MISSILE: Momentum Breakout
    missile_long = (ema13.shift(1) <= ema32.shift(1)) & (ema13 > ema32) & (c > pivot) & (~lightning_long) & (~scalp_long)
    missile_long = missile_long | (bull_trend & (c > h.shift(1)) & (adx > 20) & (c.shift(1) <= c.shift(2))) & (~lightning_long) & (~scalp_long)
    
    missile_short = (ema13.shift(1) >= ema32.shift(1)) & (ema13 < ema32) & (c < pivot) & (~lightning_short) & (~scalp_short)
    missile_short = missile_short | (bear_trend & (c < l.shift(1)) & (adx > 20) & (c.shift(1) >= c.shift(2))) & (~lightning_short) & (~scalp_short)
    
    return {
        'MISSILE': {'long': missile_long.fillna(False), 'short': missile_short.fillna(False)},
        'SCALP': {'long': scalp_long.fillna(False), 'short': scalp_short.fillna(False)},
        'LIGHTNING': {'long': lightning_long.fillna(False), 'short': lightning_short.fillna(False)}
    }

def simulate_trades_15m(df, signals, symbol):
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
            c = df['Close'].iloc[i]
            h = df['High'].iloc[i]
            l = df['Low'].iloc[i]
            o = df['Open'].iloc[i]
            atr_val = df['ATR'].iloc[i-1]
            if np.isnan(atr_val) or atr_val <= 0:
                continue
                
            if in_trade:
                exit_price = None
                exit_reason = None
                
                if trade_dir == 'LONG':
                    if l <= sl_price:
                        exit_price = sl_price
                        exit_reason = 'Hit Initial SL' if not hit_tp1 else 'Hit B/E'
                    elif not hit_tp1 and h >= tp1_price:
                        hit_tp1 = True
                        sl_price = entry_price  # Move SL to Breakeven
                        if c < entry_price:
                            exit_price = entry_price
                            exit_reason = 'Reversal Exit (B/E)'
                    elif hit_tp1 and h >= tp2_price:
                        exit_price = tp2_price
                        exit_reason = 'Completed TP2'
                        
                elif trade_dir == 'SHORT':
                    if h >= sl_price:
                        exit_price = sl_price
                        exit_reason = 'Hit Initial SL' if not hit_tp1 else 'Hit B/E'
                    elif not hit_tp1 and l <= tp1_price:
                        hit_tp1 = True
                        sl_price = entry_price
                        if c > entry_price:
                            exit_price = entry_price
                            exit_reason = 'Reversal Exit (B/E)'
                    elif hit_tp1 and l <= tp2_price:
                        exit_price = tp2_price
                        exit_reason = 'Completed TP2'
                        
                # 15m Intraday session timeout: 48 bars (12 hours)
                if not exit_price and (i - entry_idx) >= 48:
                    exit_price = c
                    exit_reason = 'Session Close Timeout'
                    
                if exit_price is not None:
                    if trade_dir == 'LONG':
                        exact_pct = ((exit_price - entry_price) / entry_price) * 100.0
                    else:
                        exact_pct = ((entry_price - exit_price) / entry_price) * 100.0
                        
                    if exact_pct > 0.04:
                        outcome = 'WIN'
                    elif exact_pct < -0.04:
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

def compute_metrics(trades_list):
    if not trades_list:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_winner': 0.0, 'avg_loser': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'max_consec_losses': 0,
            'sharpe': 0.0, 'calmar': 0.0
        }
        
    df_trades = pd.DataFrame(trades_list).sort_values('entry_time').reset_index(drop=True)
    total = len(df_trades)
    wins = df_trades[df_trades['outcome'] == 'WIN']
    losses = df_trades[df_trades['outcome'] == 'LOSS']
    bes = df_trades[df_trades['outcome'] == 'BREAKEVEN']
    
    win_rate = (len(wins) / total * 100.0) if total > 0 else 0.0
    gross_profit = wins['exact_pct'].sum() if len(wins) > 0 else 0.0
    gross_loss = abs(losses['exact_pct'].sum()) if len(losses) > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
    
    net_return = df_trades['exact_pct'].sum()
    expectancy = df_trades['exact_pct'].mean()
    
    avg_win = wins['exact_pct'].mean() if len(wins) > 0 else 0.0
    avg_loss = abs(losses['exact_pct'].mean()) if len(losses) > 0 else 0.0
    realized_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0
    
    cum_returns = df_trades['exact_pct'].cumsum()
    peak = cum_returns.cummax()
    dd = peak - cum_returns
    max_dd = dd.max() if len(dd) > 0 else 0.0
    
    # Consecutive Losses: STRICTLY RESTRICTED TO ONLY ONE SYMBOL
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
    std = df_trades['exact_pct'].std()
    sharpe = (expectancy / std) if (std and not np.isnan(std) and std > 0) else 0.0
    calmar = (net_return / max_dd) if max_dd > 0 else 0.0
    
    return {
        'total_trades': total, 'wins': len(wins), 'losses': len(losses), 'breakevens': len(bes),
        'win_rate': win_rate, 'profit_factor': profit_factor, 'net_return': net_return,
        'expectancy': expectancy, 'avg_winner': avg_win, 'avg_loser': avg_loss,
        'realized_rr': realized_rr, 'max_drawdown': max_dd, 'max_consec_losses': max_consec_losses,
        'symbol_streaks': symbol_streaks, 'sharpe': sharpe, 'calmar': calmar
    }

def main():
    print("=" * 85)
    print("   15-MINUTE TIMEFRAME BACKTEST: NG, CL, SI, GC")
    print("   Rule: Consecutive Losses Restricted Strictly to Individual Symbol")
    print("=" * 85)
    
    all_trades = []
    
    for sym, info in TARGET_COMMODITIES.items():
        ticker = info['ticker']
        print(f"Downloading 15m data for {sym} ({info['name']}: {ticker})...")
        df_raw = yf.download(ticker, period='60d', interval='15m', progress=False)
        if df_raw.empty:
            print(f"  [!] No data for {sym}")
            continue
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.get_level_values(0)
            
        df_ind = compute_indicators_15m(df_raw)
        sigs = generate_signals_15m(df_ind)
        trades = simulate_trades_15m(df_ind, sigs, sym)
        all_trades.extend(trades)
        print(f"  [✓] {sym}: {len(df_ind)} bars ({df_ind.index.min().strftime('%b %d')} to {df_ind.index.max().strftime('%b %d')}), {len(trades)} executed trades.")
        
    # Table 1: Commodity-Wise Performance (15-Minute)
    print("\n" + "=" * 85)
    print("   TABLE 1: 15-MIN PERFORMANCE FOR NG, CL, SI, GC (ALL SIGNALS)")
    print("=" * 85)
    
    comm_rows = []
    for sym in TARGET_COMMODITIES.keys():
        t_sym = [t for t in all_trades if t['symbol'] == sym]
        m = compute_metrics(t_sym)
        streak = m['symbol_streaks'].get(sym, 0)
        comm_rows.append({
            'Commodity': f"{sym} ({TARGET_COMMODITIES[sym]['name']})",
            'Trades': m['total_trades'],
            'W / L / BE': f"{m['wins']} / {m['losses']} / {m['breakevens']}",
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}",
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.2f}%",
            'Avg Win': f"+{m['avg_winner']:.2f}%",
            'Avg Loss': f"-{m['avg_loser']:.2f}%",
            'Max Consec. Losses (Single Symbol)': f"{streak} trades",
            'Max DD': f"-{m['max_drawdown']:.2f}%"
        })
    print(pd.DataFrame(comm_rows).to_string(index=False))
    
    # Table 2: Signal Type Comparison on 15m (MISSILE vs SCALP vs LIGHTNING)
    print("\n" + "=" * 85)
    print("   TABLE 2: SIGNAL TYPE BREAKDOWN ON 15m (NG, CL, SI, GC)")
    print("=" * 85)
    
    sig_rows = []
    for sig in ['MISSILE', 'SCALP', 'LIGHTNING']:
        t_sig = [t for t in all_trades if t['signal_type'] == sig]
        m = compute_metrics(t_sig)
        sig_rows.append({
            'Signal Type': sig,
            'Trades': m['total_trades'],
            'W / L / BE': f"{m['wins']} / {m['losses']} / {m['breakevens']}",
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}",
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.2f}%",
            'Realized R:R': f"{m['realized_rr']:.2f}R",
            'Max Consec. Losses (Single Symbol)': f"{m['max_consec_losses']} trades",
            'Max DD': f"-{m['max_drawdown']:.2f}%"
        })
    print(pd.DataFrame(sig_rows).to_string(index=False))
    
    # Table 3: Cross Matrix (Commodity x Signal Type on 15m)
    print("\n" + "=" * 85)
    print("   TABLE 3: COMMODITY x SIGNAL TYPE 15m PERFORMANCE MATRIX")
    print("=" * 85)
    matrix_rows = []
    for sym in TARGET_COMMODITIES.keys():
        for sig in ['MISSILE', 'SCALP', 'LIGHTNING']:
            t_cell = [t for t in all_trades if t['symbol'] == sym and t['signal_type'] == sig]
            m = compute_metrics(t_cell)
            streak = m['symbol_streaks'].get(sym, 0)
            matrix_rows.append({
                'Symbol': sym,
                'Signal': sig,
                'Trades': m['total_trades'],
                'Win Rate': f"{m['win_rate']:.1f}%",
                'Profit Factor': f"{m['profit_factor']:.2f}",
                'Net Return': f"{m['net_return']:+.2f}%",
                'Expectancy': f"{m['expectancy']:+.2f}%",
                'Consec Losses': f"{streak} trades",
                'Max DD': f"-{m['max_drawdown']:.2f}%"
            })
    print(pd.DataFrame(matrix_rows).to_string(index=False))

if __name__ == '__main__':
    main()
