"""
TLCS Version 3.0: VectorBT Trailing Stop Loss Quantitative Comparative Analysis
=================================================================================
Compares historical trade performance across 3 distinct Trailing SL regimes:
  1. REGIME A: PRE_TP1_MID (Original Baseline)
     - 50% Midpoint between Entry and TP1 moves SL to Entry (Breakeven)
     - TP1 hit books partial profit, SL stays at Entry
     - TP2 moves SL to TP1, TP3 moves SL to TP2, TP4 moves SL to TP3
  2. REGIME B: MIDPOINT_TP1_TP2 (New User Mandate)
     - TP1 hit books partial profit, SL stays at initial SL (room to breathe)
     - 50% Midpoint between TP1 and TP2 moves SL to Entry (Breakeven)
     - TP2 moves SL to TP1, TP3 moves SL to TP2, TP4 moves SL to TP3
  3. REGIME C: TP1_BREAKEVEN (Milestone Parity Baseline)
     - TP1 hit moves SL to Entry directly (no pre-TP1 midpoint)
     - TP2 moves SL to TP1, TP3 moves SL to TP2, TP4 moves SL to TP3

Universe: Multi-Asset Instruments
Timeframe: 1-Year Hourly (1h) Continuous Historical Data
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import sys
import json
import numpy as np
import pandas as pd
import yfinance as yf
import vectorbt as vbt
from datetime import datetime, timezone

vbt.settings.caching['enabled'] = False

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

TARGET_ASSETS = {
    # Indian Indices & Bluechips
    'NIFTY50': {'name': 'Nifty 50 Index', 'ticker': '^NSEI', 'market': 'Indian Equities'},
    'BANKNIFTY': {'name': 'Bank Nifty Index', 'ticker': '^NSEBANK', 'market': 'Indian Equities'},
    'RELIANCE': {'name': 'Reliance Industries', 'ticker': 'RELIANCE.NS', 'market': 'Indian Equities'},
    'HDFCBANK': {'name': 'HDFC Bank', 'ticker': 'HDFCBANK.NS', 'market': 'Indian Equities'},
    'TCS': {'name': 'Tata Consultancy Services', 'ticker': 'TCS.NS', 'market': 'Indian Equities'},
    'INFY': {'name': 'Infosys Ltd', 'ticker': 'INFY.NS', 'market': 'Indian Equities'},

    # Commodities (MCX / NYMEX)
    'CRUDEOIL': {'name': 'Crude Oil WTI', 'ticker': 'CL=F', 'market': 'Commodities'},
    'GOLD': {'name': 'Gold Futures', 'ticker': 'GC=F', 'market': 'Commodities'},
    'SILVER': {'name': 'Silver Futures', 'ticker': 'SI=F', 'market': 'Commodities'},
    'NATGAS': {'name': 'Natural Gas Futures', 'ticker': 'NG=F', 'market': 'Commodities'},
    'COPPER': {'name': 'Copper Futures', 'ticker': 'HG=F', 'market': 'Commodities'},

    # Global Indices, Forex & Crypto
    'NASDAQ100': {'name': 'Nasdaq 100 Index', 'ticker': '^NDX', 'market': 'Global / FX / Crypto'},
    'SP500': {'name': 'S&P 500 Index', 'ticker': '^GSPC', 'market': 'Global / FX / Crypto'},
    'EURUSD': {'name': 'EUR / USD Forex', 'ticker': 'EURUSD=X', 'market': 'Global / FX / Crypto'},
    'GBPUSD': {'name': 'GBP / USD Forex', 'ticker': 'GBPUSD=X', 'market': 'Global / FX / Crypto'},
    'BTC': {'name': 'Bitcoin / USD', 'ticker': 'BTC-USD', 'market': 'Global / FX / Crypto'},
    'ETH': {'name': 'Ethereum / USD', 'ticker': 'ETH-USD', 'market': 'Global / FX / Crypto'}
}


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    h = df['High']
    l = df['Low']
    c = df['Close']
    o = df['Open']

    tp = (h + l + c) / 3.0
    df['TP'] = tp

    df['EMA13'] = tp.ewm(span=13, adjust=False).mean()
    df['EMA32'] = tp.ewm(span=32, adjust=False).mean()

    def calc_dema(series, span):
        e1 = series.ewm(span=span, adjust=False).mean()
        e2 = e1.ewm(span=span, adjust=False).mean()
        return 2 * e1 - e2

    df['DEMA_FAST'] = calc_dema(tp, 5)
    df['DEMA_SLOW'] = calc_dema(tp, 13)

    tr1 = h - l
    tr2 = (h - c.shift(1)).abs()
    tr3 = (l - c.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean().bfill()

    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/14, adjust=False).mean().fillna(0)

    df['PlusDI'] = plus_di
    df['MinusDI'] = minus_di
    df['ADX'] = adx

    highest_92 = h.rolling(92).max()
    lowest_92 = l.rolling(92).min()
    osc_range = (highest_92 - lowest_92).replace(0, np.nan)
    osc = 100 * (c - lowest_92) / osc_range
    osc = osc.fillna(50)
    df['m0'] = osc.ewm(span=21, adjust=False).mean()
    df['m10'] = osc.rolling(window=96).mean().bfill()

    delta = c.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    avg_loss = pd.Series(loss, index=df.index).ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs)).fillna(50)

    df['date'] = df.index.date
    daily = df.groupby('date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
    daily_shifted = daily.shift(1)

    prior_h = daily_shifted['High']
    prior_l = daily_shifted['Low']
    prior_c = daily_shifted['Close']
    rng = prior_h - prior_l

    cam_h4 = prior_c + rng * 0.55
    cam_h3 = prior_c + rng * 0.275
    cam_l3 = prior_c - rng * 0.275
    cam_l4 = prior_c - rng * 0.55

    cpr_p = (prior_h + prior_l + prior_c) / 3.0
    cpr_bc = (prior_h + prior_l) / 2.0
    cpr_tc = 2.0 * cpr_p - cpr_bc
    actual_tc = pd.concat([cpr_tc, cpr_bc], axis=1).max(axis=1)
    actual_bc = pd.concat([cpr_tc, cpr_bc], axis=1).min(axis=1)
    cpr_width = (actual_tc - actual_bc).abs()
    ncpr = (cpr_width / rng.replace(0, np.nan) < 0.05) | (cpr_width / cpr_p.replace(0, np.nan) < 0.002)

    df['H4'] = df['date'].map(cam_h4).bfill()
    df['H3'] = df['date'].map(cam_h3).bfill()
    df['L3'] = df['date'].map(cam_l3).bfill()
    df['L4'] = df['date'].map(cam_l4).bfill()
    df['Pivot'] = df['date'].map(cpr_p).bfill()
    df['TC'] = df['date'].map(actual_tc).bfill()
    df['BC'] = df['date'].map(actual_bc).bfill()
    df['NCPR'] = df['date'].map(ncpr).fillna(False)

    df['VAH'] = tp.rolling(24).mean() + 0.70 * tr.rolling(24).mean()
    df['VAL'] = tp.rolling(24).mean() - 0.70 * tr.rolling(24).mean()
    df['session_bar_counter'] = df.groupby('date').cumcount()
    df['AverageCandle'] = (h - l).rolling(50).mean().bfill()
    df['AverageBody'] = (c - o).abs().rolling(50).mean().bfill()

    greenzone = (df['PlusDI'] > df['MinusDI']) & (df['EMA13'] > df['EMA32']) & (df['DEMA_FAST'] > df['DEMA_SLOW'])
    redzone = (df['MinusDI'] > df['PlusDI']) & (df['EMA13'] < df['EMA32']) & (df['DEMA_FAST'] < df['DEMA_SLOW'])
    df['Greenzone'] = greenzone
    df['Redzone'] = redzone
    df['IsInFireZone'] = ~(greenzone | redzone)

    return df


def generate_all_signals_v3(df: pd.DataFrame) -> dict:
    c = df['Close']
    o = df['Open']
    h = df['High']
    l = df['Low']
    ema13 = df['EMA13']
    ema32 = df['EMA32']
    dema_f = df['DEMA_FAST']
    dema_s = df['DEMA_SLOW']
    plus_di = df['PlusDI']
    minus_di = df['MinusDI']
    m0 = df['m0']
    m10 = df['m10']
    rsi = df['RSI']
    h4 = df['H4']
    l4 = df['L4']
    tc = df['TC']
    bc = df['BC']
    vah = df['VAH']
    val = df['VAL']
    bar_cnt = df['session_bar_counter']
    avg_candle = df['AverageCandle']
    avg_body = df['AverageBody']

    long_allowed = l < h4
    short_allowed = h > l4
    green1 = (plus_di > minus_di) & (m0 > m10)
    red1 = (minus_di > plus_di) & (m0 < m10)

    roll_l10 = l.rolling(10).min()
    roll_h10 = h.rolling(10).max()
    roll_rsi_l10 = rsi.rolling(10).min()
    roll_rsi_h10 = rsi.rolling(10).max()

    bull_reg_div = (l <= roll_l10) & (rsi > roll_rsi_l10.shift(2)) & (rsi < 38) & (plus_di > minus_di)
    bear_reg_div = (h >= roll_h10) & (rsi < roll_rsi_h10.shift(2)) & (rsi > 62) & (minus_di > plus_di)

    cpr_bull = (l >= bc) & (l <= tc) & (rsi < 45) & (plus_di > minus_di)
    cpr_bear = (h <= tc) & (h >= bc) & (rsi > 55) & (minus_di > plus_di)
    vah_val_bull = (l >= val) & (l <= vah) & (c > o) & (plus_di > minus_di)
    vah_val_bear = (h <= vah) & (h >= val) & (c < o) & (minus_di > plus_di)
    bull_hid_div = cpr_bull | vah_val_bull
    bear_hid_div = cpr_bear | vah_val_bear

    candle_range = h - l
    body_size = (c - o).abs()
    is_exhaustion = (candle_range > 1.8 * avg_candle) & (body_size < 0.35 * candle_range)
    session_guard = bar_cnt >= 2
    bull_ext_rev = is_exhaustion & (c > o) & (l < l4) & session_guard & (plus_di > minus_di)
    bear_ext_rev = is_exhaustion & (c < o) & (h > h4) & session_guard & (minus_di > plus_di)

    missile_long = (c > ema13) & (ema13 > ema32) & (dema_f > dema_s) & green1 & long_allowed
    missile_short = (c < ema13) & (ema13 < ema32) & (dema_f < dema_s) & red1 & short_allowed

    scalp_long = (l <= ema13) & (c > ema13) & (dema_f > dema_s) & (m0 > m10) & long_allowed
    scalp_short = (h >= ema13) & (c < ema13) & (dema_f < dema_s) & (m0 < m10) & short_allowed

    lightning_long = missile_long & scalp_long
    lightning_short = missile_short & scalp_short

    missile_long_pure = missile_long & ~lightning_long
    missile_short_pure = missile_short & ~lightning_short
    scalp_long_pure = scalp_long & ~lightning_long
    scalp_short_pure = scalp_short & ~lightning_short

    signals = {
        'MISSILE_BUY': (missile_long_pure, True, 'MISSILE'),
        'MISSILE_SELL': (missile_short_pure, False, 'MISSILE'),
        'SCALP_BUY': (scalp_long_pure, True, 'SCALP'),
        'SCALP_SELL': (scalp_short_pure, False, 'SCALP'),
        'LIGHTNING_BUY': (lightning_long, True, 'LIGHTNING'),
        'LIGHTNING_SELL': (lightning_short, False, 'LIGHTNING'),
        'REGULAR_DIV_BUY': (bull_reg_div, True, 'DIVERGENCE'),
        'REGULAR_DIV_SELL': (bear_reg_div, False, 'DIVERGENCE'),
        'HIDDEN_DIV_BUY': (bull_hid_div, True, 'HIDDEN DIVERGENCE'),
        'HIDDEN_DIV_SELL': (bear_hid_div, False, 'HIDDEN DIVERGENCE'),
        'EXTREME_REV_BUY': (bull_ext_rev, True, 'EXTREME REVERSAL'),
        'EXTREME_REV_SELL': (bear_ext_rev, False, 'EXTREME REVERSAL')
    }

    return signals


def simulate_single_trade(df: pd.DataFrame, entry_i: int, is_long: bool, entry_price: float, dist: float, regime: str) -> dict:
    if is_long:
        init_sl = entry_price - 1.0 * dist
        tp1 = entry_price + 1.5 * dist
        tp2 = entry_price + 2.5 * dist
        tp3 = entry_price + 3.5 * dist
        tp4 = entry_price + 4.5 * dist
        mid_entry_tp1 = (entry_price + tp1) / 2.0
        mid_tp1_tp2 = (tp1 + tp2) / 2.0
    else:
        init_sl = entry_price + 1.0 * dist
        tp1 = entry_price - 1.5 * dist
        tp2 = entry_price - 2.5 * dist
        tp3 = entry_price - 3.5 * dist
        tp4 = entry_price - 4.5 * dist
        mid_entry_tp1 = (entry_price + tp1) / 2.0
        mid_tp1_tp2 = (tp1 + tp2) / 2.0

    sl_price = init_sl
    hit_tp1 = False
    hit_tp2 = False
    hit_tp3 = False
    hit_mid_entry_tp1 = False
    hit_mid_tp1_tp2 = False

    exit_price = None
    exit_level = None

    for i in range(entry_i, len(df)):
        cur_h = df['High'].iloc[i]
        cur_l = df['Low'].iloc[i]
        cur_c = df['Close'].iloc[i]

        if is_long:
            if regime == 'PRE_TP1_MID':
                if not hit_tp1 and not hit_mid_entry_tp1 and cur_h >= mid_entry_tp1:
                    hit_mid_entry_tp1 = True
                    sl_price = max(sl_price, entry_price)
            elif regime == 'MIDPOINT_TP1_TP2':
                if hit_tp1 and not hit_tp2 and not hit_mid_tp1_tp2 and cur_h >= mid_tp1_tp2:
                    hit_mid_tp1_tp2 = True
                    sl_price = max(sl_price, entry_price)
            elif regime == 'TP1_BREAKEVEN':
                if hit_tp1 and not hit_tp2:
                    sl_price = max(sl_price, entry_price)
            elif regime == 'TP1_BE_AND_MID_ADVANCE':
                if hit_tp1 and not hit_tp2 and not hit_mid_tp1_tp2 and cur_h >= mid_tp1_tp2:
                    hit_mid_tp1_tp2 = True
                    sl_price = max(sl_price, mid_entry_tp1)

            if cur_l <= sl_price:
                exit_price = sl_price
                if sl_price == init_sl:
                    exit_level = 'SL'
                elif abs(sl_price - entry_price) < 1e-5:
                    exit_level = 'BE'
                elif sl_price >= tp2:
                    exit_level = 'TP2_TRAIL'
                elif sl_price >= tp1:
                    exit_level = 'TP1_TRAIL'
                elif abs(sl_price - mid_entry_tp1) < 1e-5:
                    exit_level = 'MID_ENTRY_TP1_TRAIL'
                else:
                    exit_level = 'TRAIL_SL'
                break

            if cur_h >= tp4:
                exit_price = tp4
                exit_level = 'TP4'
                break
            elif cur_h >= tp3 and not hit_tp3:
                hit_tp3 = True
                sl_price = tp2
            elif cur_h >= tp2 and not hit_tp2:
                hit_tp2 = True
                sl_price = tp1
            elif cur_h >= tp1 and not hit_tp1:
                hit_tp1 = True
                if regime in ('TP1_BREAKEVEN', 'TP1_BE_AND_MID_ADVANCE'):
                    sl_price = max(sl_price, entry_price)

        else: # Short
            if regime == 'PRE_TP1_MID':
                if not hit_tp1 and not hit_mid_entry_tp1 and cur_l <= mid_entry_tp1:
                    hit_mid_entry_tp1 = True
                    sl_price = min(sl_price, entry_price)
            elif regime == 'MIDPOINT_TP1_TP2':
                if hit_tp1 and not hit_tp2 and not hit_mid_tp1_tp2 and cur_l <= mid_tp1_tp2:
                    hit_mid_tp1_tp2 = True
                    sl_price = min(sl_price, entry_price)
            elif regime == 'TP1_BREAKEVEN':
                if hit_tp1 and not hit_tp2:
                    sl_price = min(sl_price, entry_price)
            elif regime == 'TP1_BE_AND_MID_ADVANCE':
                if hit_tp1 and not hit_tp2 and not hit_mid_tp1_tp2 and cur_l <= mid_tp1_tp2:
                    hit_mid_tp1_tp2 = True
                    sl_price = min(sl_price, mid_entry_tp1)

            if cur_h >= sl_price:
                exit_price = sl_price
                if sl_price == init_sl:
                    exit_level = 'SL'
                elif abs(sl_price - entry_price) < 1e-5:
                    exit_level = 'BE'
                elif sl_price <= tp2:
                    exit_level = 'TP2_TRAIL'
                elif sl_price <= tp1:
                    exit_level = 'TP1_TRAIL'
                elif abs(sl_price - mid_entry_tp1) < 1e-5:
                    exit_level = 'MID_ENTRY_TP1_TRAIL'
                else:
                    exit_level = 'TRAIL_SL'
                break

            if cur_l <= tp4:
                exit_price = tp4
                exit_level = 'TP4'
                break
            elif cur_l <= tp3 and not hit_tp3:
                hit_tp3 = True
                sl_price = tp2
            elif cur_l <= tp2 and not hit_tp2:
                hit_tp2 = True
                sl_price = tp1
            elif cur_l <= tp1 and not hit_tp1:
                hit_tp1 = True
                if regime in ('TP1_BREAKEVEN', 'TP1_BE_AND_MID_ADVANCE'):
                    sl_price = min(sl_price, entry_price)

        if (i - entry_i) >= 72:
            exit_price = cur_c
            exit_level = 'TIMEOUT'
            break

    if exit_price is None:
        exit_price = df['Close'].iloc[-1]
        exit_level = 'EOD'

    if is_long:
        exact_pct = ((exit_price - entry_price) / entry_price) * 100.0
    else:
        exact_pct = ((entry_price - exit_price) / entry_price) * 100.0

    if exact_pct > 0.0001:
        outcome = 'WIN'
    elif exact_pct < -0.0001:
        outcome = 'LOSS'
    else:
        outcome = 'BREAKEVEN'

    return {
        'regime': regime,
        'entry_price': round(float(entry_price), 4),
        'exit_price': round(float(exit_price), 4),
        'exact_pct': round(float(exact_pct), 4),
        'outcome': outcome,
        'exit_level': exit_level,
        'hit_tp1': hit_tp1,
        'hit_tp2': hit_tp2,
        'hit_tp3': hit_tp3,
        'hit_tp4': (exit_level == 'TP4'),
        'bars_held': int(i - entry_i)
    }


def compute_vbt_metrics(trades: list) -> dict:
    if not trades:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'sharpe': 0.0,
            'sortino': 0.0, 'calmar': 0.0, 'kelly_pct': 0.0,
            'annualized_return': 0.0, 'max_consec_losses': 0
        }

    total = len(trades)
    wins = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    bes = [t for t in trades if t['outcome'] == 'BREAKEVEN']

    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(bes)

    win_rate = (win_count / total * 100.0) if total > 0 else 0.0

    returns = [t['exact_pct'] for t in trades]
    net_return = sum(returns)
    expectancy = net_return / total if total > 0 else 0.0

    win_returns = [t['exact_pct'] for t in wins]
    loss_returns = [abs(t['exact_pct']) for t in losses]

    gross_profit = sum(win_returns)
    gross_loss = sum(loss_returns)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    avg_win = float(np.mean(win_returns)) if win_returns else 0.0
    avg_loss = float(np.mean(loss_returns)) if loss_returns else 0.0
    realized_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    p = win_rate / 100.0
    b = realized_rr
    if b > 0 and p > 0:
        kelly = (p * b - (1.0 - p)) / b
        kelly_pct = max(0.0, kelly * 100.0)
    else:
        kelly_pct = 0.0

    cum_returns = pd.Series(returns).cumsum()
    peak = cum_returns.cummax()
    drawdown = peak - cum_returns
    max_drawdown = float(drawdown.max()) if len(drawdown) > 0 else 0.0

    ret_series = pd.Series(returns) / 100.0
    mean_ret = float(ret_series.mean())
    std_ret = float(ret_series.std())
    downside_returns = ret_series[ret_series < 0]
    downside_std = float(downside_returns.std()) if len(downside_returns) > 1 else std_ret

    ann_factor = np.sqrt(252 * 7)
    sharpe = float((mean_ret / std_ret) * ann_factor) if std_ret > 0 else 0.0
    sortino = float((mean_ret / downside_std) * ann_factor) if downside_std > 0 else 0.0
    calmar = float(net_return / max_drawdown) if max_drawdown > 0 else 0.0

    max_consec = 0
    cur_consec = 0
    for t in trades:
        if t['outcome'] == 'LOSS':
            cur_consec += 1
            if cur_consec > max_consec:
                max_consec = cur_consec
        else:
            cur_consec = 0

    return {
        'total_trades': total,
        'wins': win_count,
        'losses': loss_count,
        'breakevens': be_count,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'net_return': round(net_return, 2),
        'expectancy': round(expectancy, 4),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'realized_rr': round(realized_rr, 2),
        'max_drawdown': round(max_drawdown, 2),
        'sharpe': round(sharpe, 2),
        'sortino': round(sortino, 2),
        'calmar': round(calmar, 2),
        'kelly_pct': round(kelly_pct, 2),
        'annualized_return': round(net_return, 2),
        'max_consec_losses': max_consec
    }


def run_trailing_sl_analysis():
    print("=" * 105)
    print("   TLCS v4.0: VECTORBT TRAILING SL QUANTITATIVE COMPARATIVE ANALYSIS")
    print("   Comparing: [A] Pre-TP1 Mid  VS  [B] Mid TP1-TP2  VS  [C] TP1 BE  VS  [D] TP1 BE + Mid Advance")
    print("=" * 105)

    trades_a = []
    trades_b = []
    trades_c = []
    trades_d = []
    pairwise_comparisons = []

    for sym, info in TARGET_ASSETS.items():
        ticker = info['ticker']
        cache_file = os.path.join(CACHE_DIR, f"{sym}_1y_1h.parquet")

        df_raw = None
        if os.path.exists(cache_file):
            try:
                df_raw = pd.read_parquet(cache_file)
            except Exception:
                df_raw = None

        if df_raw is None or len(df_raw) < 100:
            print(f"[*] Downloading {sym:10} ({info['name']}: {ticker})...")
            try:
                df_raw = yf.download(ticker, period='1y', interval='1h', progress=False)
                if df_raw.empty or len(df_raw) < 100:
                    print(f"  [!] Insufficient data for {sym}, skipping.")
                    continue
                if isinstance(df_raw.columns, pd.MultiIndex):
                    df_raw.columns = df_raw.columns.get_level_values(0)
                df_raw.to_parquet(cache_file)
            except Exception as e:
                print(f"  [X] Download error on {sym}: {e}")
                continue
        else:
            print(f"[*] Loaded cached {sym:10} ({len(df_raw)} bars)")

        df_ind = compute_indicators(df_raw)
        sigs = generate_all_signals_v3(df_ind)

        for sig_name, (sig_series, is_long, base_type) in sigs.items():
            for i in range(1, len(df_ind) - 1):
                if sig_series.iloc[i]:
                    entry_i = i + 1
                    cur_atr = df_ind['ATR'].iloc[i]
                    if np.isnan(cur_atr) or cur_atr <= 0:
                        continue
                    entry_price = df_ind['Open'].iloc[entry_i]

                    t_a = simulate_single_trade(df_ind, entry_i, is_long, entry_price, cur_atr, 'PRE_TP1_MID')
                    t_b = simulate_single_trade(df_ind, entry_i, is_long, entry_price, cur_atr, 'MIDPOINT_TP1_TP2')
                    t_c = simulate_single_trade(df_ind, entry_i, is_long, entry_price, cur_atr, 'TP1_BREAKEVEN')
                    t_d = simulate_single_trade(df_ind, entry_i, is_long, entry_price, cur_atr, 'TP1_BE_AND_MID_ADVANCE')

                    t_a['symbol'] = sym
                    t_a['signal'] = sig_name
                    t_a['base_type'] = base_type
                    t_b['symbol'] = sym
                    t_b['signal'] = sig_name
                    t_b['base_type'] = base_type
                    t_c['symbol'] = sym
                    t_c['signal'] = sig_name
                    t_c['base_type'] = base_type
                    t_d['symbol'] = sym
                    t_d['signal'] = sig_name
                    t_d['base_type'] = base_type

                    trades_a.append(t_a)
                    trades_b.append(t_b)
                    trades_c.append(t_c)
                    trades_d.append(t_d)

                    pairwise_comparisons.append({
                        'symbol': sym,
                        'signal': sig_name,
                        'base_type': base_type,
                        'ret_a': t_a['exact_pct'],
                        'out_a': t_a['outcome'],
                        'exit_a': t_a['exit_level'],
                        'ret_b': t_b['exact_pct'],
                        'out_b': t_b['outcome'],
                        'exit_b': t_b['exit_level'],
                        'ret_c': t_c['exact_pct'],
                        'out_c': t_c['outcome'],
                        'exit_c': t_c['exit_level'],
                        'ret_d': t_d['exact_pct'],
                        'out_d': t_d['outcome'],
                        'exit_d': t_d['exit_level'],
                        'delta_b_vs_a': round(t_b['exact_pct'] - t_a['exact_pct'], 4),
                        'delta_d_vs_b': round(t_d['exact_pct'] - t_b['exact_pct'], 4),
                        'delta_d_vs_a': round(t_d['exact_pct'] - t_a['exact_pct'], 4)
                    })

    if not trades_a:
        print("[!] No trades simulated.")
        return

    m_a = compute_vbt_metrics(trades_a)
    m_b = compute_vbt_metrics(trades_b)
    m_c = compute_vbt_metrics(trades_c)
    m_d = compute_vbt_metrics(trades_d)

    print("\n" + "=" * 105)
    print("   HEAD-TO-HEAD VECTORBT PERFORMANCE: TRAILING SL REGIME COMPARISON")
    print("=" * 105)

    comp_rows = [
        {
            'Trailing SL Regime': 'A: Pre-TP1 Midpoint (Old v3.0)',
            'Trades': m_a['total_trades'],
            'W / L / BE': f"{m_a['wins']} / {m_a['losses']} / {m_a['breakevens']}",
            'Win Rate': f"{m_a['win_rate']:.2f}%",
            'Profit Factor': f"{m_a['profit_factor']:.2f}",
            'Net Return': f"{m_a['net_return']:+.2f}%",
            'Expectancy': f"{m_a['expectancy']:+.4f}%",
            'Realized R:R': f"{m_a['realized_rr']:.2f}R",
            'Max DD': f"-{m_a['max_drawdown']:.2f}%",
            'Sharpe': f"{m_a['sharpe']:.2f}",
            'Sortino': f"{m_a['sortino']:.2f}",
            'Kelly %': f"{m_a['kelly_pct']:.2f}%"
        },
        {
            'Trailing SL Regime': 'B: Midpoint TP1-TP2 (Prev Baseline)',
            'Trades': m_b['total_trades'],
            'W / L / BE': f"{m_b['wins']} / {m_b['losses']} / {m_b['breakevens']}",
            'Win Rate': f"{m_b['win_rate']:.2f}%",
            'Profit Factor': f"{m_b['profit_factor']:.2f}",
            'Net Return': f"{m_b['net_return']:+.2f}%",
            'Expectancy': f"{m_b['expectancy']:+.4f}%",
            'Realized R:R': f"{m_b['realized_rr']:.2f}R",
            'Max DD': f"-{m_b['max_drawdown']:.2f}%",
            'Sharpe': f"{m_b['sharpe']:.2f}",
            'Sortino': f"{m_b['sortino']:.2f}",
            'Kelly %': f"{m_b['kelly_pct']:.2f}%"
        },
        {
            'Trailing SL Regime': 'C: Pure TP1 Breakeven',
            'Trades': m_c['total_trades'],
            'W / L / BE': f"{m_c['wins']} / {m_c['losses']} / {m_c['breakevens']}",
            'Win Rate': f"{m_c['win_rate']:.2f}%",
            'Profit Factor': f"{m_c['profit_factor']:.2f}",
            'Net Return': f"{m_c['net_return']:+.2f}%",
            'Expectancy': f"{m_c['expectancy']:+.4f}%",
            'Realized R:R': f"{m_c['realized_rr']:.2f}R",
            'Max DD': f"-{m_c['max_drawdown']:.2f}%",
            'Sharpe': f"{m_c['sharpe']:.2f}",
            'Sortino': f"{m_c['sortino']:.2f}",
            'Kelly %': f"{m_c['kelly_pct']:.2f}%"
        },
        {
            'Trailing SL Regime': 'D: TP1 BE + Mid Advance (New Mandate)',
            'Trades': m_d['total_trades'],
            'W / L / BE': f"{m_d['wins']} / {m_d['losses']} / {m_d['breakevens']}",
            'Win Rate': f"{m_d['win_rate']:.2f}%",
            'Profit Factor': f"{m_d['profit_factor']:.2f}",
            'Net Return': f"{m_d['net_return']:+.2f}%",
            'Expectancy': f"{m_d['expectancy']:+.4f}%",
            'Realized R:R': f"{m_d['realized_rr']:.2f}R",
            'Max DD': f"-{m_d['max_drawdown']:.2f}%",
            'Sharpe': f"{m_d['sharpe']:.2f}",
            'Sortino': f"{m_d['sortino']:.2f}",
            'Kelly %': f"{m_d['kelly_pct']:.2f}%"
        }
    ]

    df_comp = pd.DataFrame(comp_rows)
    print(df_comp.to_string(index=False))

    b_wins_more = [p for p in pairwise_comparisons if p['delta_b_vs_a'] > 0.0001]
    a_wins_more = [p for p in pairwise_comparisons if p['delta_b_vs_a'] < -0.0001]
    identical = [p for p in pairwise_comparisons if abs(p['delta_b_vs_a']) <= 0.0001]

    be_to_win = [p for p in pairwise_comparisons if p['out_a'] == 'BREAKEVEN' and p['out_b'] == 'WIN']
    be_to_loss = [p for p in pairwise_comparisons if p['out_a'] == 'BREAKEVEN' and p['out_b'] == 'LOSS']
    win_to_win_more = [p for p in pairwise_comparisons if p['out_a'] == 'WIN' and p['out_b'] == 'WIN' and p['delta_b_vs_a'] > 0]

    net_delta = m_b['net_return'] - m_a['net_return']
    wr_delta = m_b['win_rate'] - m_a['win_rate']
    pf_delta = m_b['profit_factor'] - m_a['profit_factor']
    exp_delta = m_b['expectancy'] - m_a['expectancy']

    net_delta_d_vs_b = m_d['net_return'] - m_b['net_return']
    wr_delta_d_vs_b = m_d['win_rate'] - m_b['win_rate']
    pf_delta_d_vs_b = m_d['profit_factor'] - m_b['profit_factor']
    exp_delta_d_vs_b = m_d['expectancy'] - m_b['expectancy']

    d_wins_more_b = [p for p in pairwise_comparisons if p['delta_d_vs_b'] > 0.0001]
    b_wins_more_d = [p for p in pairwise_comparisons if p['delta_d_vs_b'] < -0.0001]

    print("\n" + "─" * 105)
    print(f"PAIRWISE TRANSITION ANALYSIS (REGIME D [New Mandate] vs REGIME B [Prev Baseline] across {len(pairwise_comparisons)} trades):")
    print(f"   * Net Return Edge:            {net_delta_d_vs_b:+.2f}% total return delta ({m_d['net_return']:+.2f}% vs {m_b['net_return']:+.2f}%)")
    print(f"   * Win Rate Delta:             {wr_delta_d_vs_b:+.2f}% ({m_d['win_rate']:.2f}% vs {m_b['win_rate']:.2f}%)")
    print(f"   * Profit Factor Delta:        {pf_delta_d_vs_b:+.2f} ({m_d['profit_factor']:.2f} vs {m_b['profit_factor']:.2f})")
    print(f"   * Expectancy Delta:           {exp_delta_d_vs_b:+.4f}% per trade ({m_d['expectancy']:+.4f}% vs {m_b['expectancy']:+.4f}%)")
    print(f"   * Trades where D outperformed B (Protected Gains):      {len(d_wins_more_b)} trades (+{sum(p['delta_d_vs_b'] for p in d_wins_more_b):.2f}% gained)")
    print(f"   * Trades where B outperformed D:                        {len(b_wins_more_d)} trades ({sum(p['delta_d_vs_b'] for p in b_wins_more_d):.2f}% given back)")
    print("─" * 105)

    setup_types = sorted(list(set(p['base_type'] for p in pairwise_comparisons)))
    print("\n" + "=" * 105)
    print("   SETUP FAMILY BREAKDOWN: REGIME B VS REGIME D")
    print("=" * 105)
    setup_rows = []
    for st in setup_types:
        st_trades_b = [t for t in trades_b if t['base_type'] == st]
        st_trades_d = [t for t in trades_d if t['base_type'] == st]
        st_m_b = compute_vbt_metrics(st_trades_b)
        st_m_d = compute_vbt_metrics(st_trades_d)
        setup_rows.append({
            'Setup': st,
            'Count': len(st_trades_b),
            'WR [B]': f"{st_m_b['win_rate']:.1f}%",
            'WR [D]': f"{st_m_d['win_rate']:.1f}%",
            'PF [B]': f"{st_m_b['profit_factor']:.2f}",
            'PF [D]': f"{st_m_d['profit_factor']:.2f}",
            'Net [B]': f"{st_m_b['net_return']:+.2f}%",
            'Net [D]': f"{st_m_d['net_return']:+.2f}%",
            'Return Delta (D - B)': f"{(st_m_d['net_return'] - st_m_b['net_return']):+.2f}%"
        })
    df_st = pd.DataFrame(setup_rows)
    print(df_st.to_string(index=False))

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trailing_sl_comparison_results.json')
    result_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'period': '1 Year Hourly Continuous Data',
        'total_evaluated_trades': len(pairwise_comparisons),
        'regime_a_pre_tp1_mid': m_a,
        'regime_b_midpoint_tp1_tp2': m_b,
        'regime_c_tp1_breakeven': m_c,
        'regime_d_tp1_be_mid_advance': m_d,
        'edge_delta_d_vs_b': {
            'net_return_delta': round(net_delta_d_vs_b, 2),
            'win_rate_delta': round(wr_delta_d_vs_b, 2),
            'profit_factor_delta': round(pf_delta_d_vs_b, 2),
            'expectancy_delta': round(exp_delta_d_vs_b, 4),
            'd_outperformed_b_count': len(d_wins_more_b),
            'b_outperformed_d_count': len(b_wins_more_d)
        },
        'by_setup': setup_rows
    }

    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)

    print(f"\n[✓] Detailed analysis results saved to {output_path}")


if __name__ == '__main__':
    run_trailing_sl_analysis()
