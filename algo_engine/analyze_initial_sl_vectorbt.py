"""
TLCS Version 5.0: VectorBT Initial Stop Loss (SL) Quantitative Optimization Engine
===================================================================================
Evaluates historical ("Past" / In-Sample: 70%) and forward-walk ("Future" / Out-of-Sample: 30%)
trade performance across Initial Stop Loss architectures to identify the mathematically optimum
parameters for profit, win rate, expectancy, and drawdown mitigation.

Target Regimes Evaluated:
1. Divergence Signals (with Confirmation Candle Midpoint Touch Entry):
   - Regime 1:  DIV_SL_0.5_AVG10   (Extreme ± 0.5 * AvgCandleSize10)
   - Regime 2:  DIV_SL_1.0_AVG10   (Extreme ± 1.0 * AvgCandleSize10)
   - Regime 3:  DIV_SL_1.5_AVG10   (Extreme ± 1.5 * AvgCandleSize10)
   - Regime 4:  DIV_SL_2.0_AVG10   (Extreme ± 2.0 * AvgCandleSize10 - Current Option 1)
   - Regime 5:  DIV_SL_2.5_AVG10   (Extreme ± 2.5 * AvgCandleSize10)
   - Regime 6:  DIV_SL_3.0_AVG10   (Extreme ± 3.0 * AvgCandleSize10)
   - Regime 7:  DIV_SL_1.0_ATR     (Extreme ± 1.0 * ATR)
   - Regime 8:  DIV_SL_1.5_ATR     (Extreme ± 1.5 * ATR)
   - Regime 9:  DIV_SL_ENTRY_1.0_ATR (Entry ± 1.0 * ATR - Legacy Flawed Baseline)
   - Regime 10: DIV_SL_ENTRY_1.5_ATR (Entry ± 1.5 * ATR)

2. Core Trend / Momentum Signals (Missile, Scalp, Lightning, Extreme Reversal):
   - CORE_SL_0.75_ATR (Entry ± 0.75 * ATR)
   - CORE_SL_1.00_ATR (Entry ± 1.00 * ATR - Current Baseline)
   - CORE_SL_1.25_ATR (Entry ± 1.25 * ATR)
   - CORE_SL_1.50_ATR (Entry ± 1.50 * ATR)
   - CORE_SL_1.75_ATR (Entry ± 1.75 * ATR)
   - CORE_SL_2.00_ATR (Entry ± 2.00 * ATR)
   - CORE_SL_BAR_EXTREME (Signal Bar Extreme ± 0.5 * ATR)

Universe: 17 Multi-Asset Instruments (Indian Equities, Commodities, FX, Crypto)
Timeframe: 1-Year Hourly (1h) Continuous Historical Data from data_cache/*.parquet
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import sys
import json
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime

vbt.settings.caching['enabled'] = False

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data_cache')

TARGET_ASSETS = {
    # Indian Indices & Bluechips
    'NIFTY50': {'name': 'Nifty 50 Index', 'market': 'Indian Equities'},
    'BANKNIFTY': {'name': 'Bank Nifty Index', 'market': 'Indian Equities'},
    'RELIANCE': {'name': 'Reliance Industries', 'market': 'Indian Equities'},
    'HDFCBANK': {'name': 'HDFC Bank', 'market': 'Indian Equities'},
    'TCS': {'name': 'Tata Consultancy Services', 'market': 'Indian Equities'},
    'INFY': {'name': 'Infosys Ltd', 'market': 'Indian Equities'},

    # Commodities (MCX / NYMEX)
    'CRUDEOIL': {'name': 'Crude Oil WTI', 'market': 'Commodities'},
    'GOLD': {'name': 'Gold Futures', 'market': 'Commodities'},
    'SILVER': {'name': 'Silver Futures', 'market': 'Commodities'},
    'NATGAS': {'name': 'Natural Gas Futures', 'market': 'Commodities'},
    'COPPER': {'name': 'Copper Futures', 'market': 'Commodities'},

    # Global Indices, Forex & Crypto
    'NASDAQ100': {'name': 'Nasdaq 100 Index', 'market': 'Global / FX / Crypto'},
    'SP500': {'name': 'S&P 500 Index', 'market': 'Global / FX / Crypto'},
    'EURUSD': {'name': 'EUR / USD Forex', 'market': 'Global / FX / Crypto'},
    'GBPUSD': {'name': 'GBP / USD Forex', 'market': 'Global / FX / Crypto'},
    'BTC': {'name': 'Bitcoin / USD', 'market': 'Global / FX / Crypto'},
    'ETH': {'name': 'Ethereum / USD', 'market': 'Global / FX / Crypto'}
}


def load_asset_data(symbol: str) -> pd.DataFrame:
    file_path = os.path.join(CACHE_DIR, f"{symbol}_1y_1h.parquet")
    if not os.path.exists(file_path):
        return None
    df = pd.read_parquet(file_path)
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df = df.set_index('Datetime')
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


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
    df['AvgCandleSize10'] = (h - l).rolling(window=10).mean().bfill()

    # DMI / ADX
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    df['PlusDI'] = plus_di
    df['MinusDI'] = minus_di
    df['ADX'] = dx.ewm(alpha=1/14, adjust=False).mean().fillna(0)

    # Momentum
    highest_92 = h.rolling(92).max()
    lowest_92 = l.rolling(92).min()
    osc = 100 * (c - lowest_92) / (highest_92 - lowest_92).replace(0, np.nan)
    df['m0'] = osc.fillna(50).ewm(span=21, adjust=False).mean()
    df['m10'] = osc.rolling(window=96).mean().bfill()

    # RSI
    delta = c.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    avg_loss = pd.Series(loss, index=df.index).ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + (avg_gain / avg_loss))).fillna(50)

    # Camarilla & CPR
    df['date'] = df.index.date
    daily = df.groupby('date').agg({'High': 'max', 'Low': 'min', 'Close': 'last'})
    daily_shifted = daily.shift(1)
    prior_h = daily_shifted['High']
    prior_l = daily_shifted['Low']
    prior_c = daily_shifted['Close']
    rng = prior_h - prior_l

    cam_h4 = prior_c + rng * 0.55
    cam_l4 = prior_c - rng * 0.55
    cpr_p = (prior_h + prior_l + prior_c) / 3.0
    cpr_bc = (prior_h + prior_l) / 2.0
    cpr_tc = 2.0 * cpr_p - cpr_bc

    df['H4'] = df['date'].map(cam_h4).bfill()
    df['L4'] = df['date'].map(cam_l4).bfill()
    df['TC'] = df['date'].map(pd.concat([cpr_tc, cpr_bc], axis=1).max(axis=1)).bfill()
    df['BC'] = df['date'].map(pd.concat([cpr_tc, cpr_bc], axis=1).min(axis=1)).bfill()

    df['session_bar_counter'] = df.groupby('date').cumcount()
    df['AverageCandle'] = (h - l).rolling(50).mean().bfill()
    df['AverageBody'] = (c - o).abs().rolling(50).mean().bfill()

    return df


def generate_canonical_signals(df: pd.DataFrame) -> dict:
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
    adx = df['ADX']
    m0 = df['m0']
    m10 = df['m10']
    rsi = df['RSI']
    h4 = df['H4']
    l4 = df['L4']
    tc = df['TC']
    bc = df['BC']
    bar_cnt = df['session_bar_counter']
    avg_candle = df['AverageCandle']
    avg_body = df['AverageBody']

    long_allowed = l < h4
    short_allowed = h > l4

    greenzone = (plus_di > minus_di) & (ema13 > ema32) & (dema_f > dema_s)
    redzone = (minus_di > plus_di) & (ema13 < ema32) & (dema_f < dema_s)
    green1 = (plus_di > minus_di) & (m0 > m10)
    red1 = (minus_di > plus_di) & (m0 < m10)

    # Divergences
    roll_l10 = l.rolling(10).min()
    roll_h10 = h.rolling(10).max()
    roll_rsi_l10 = rsi.rolling(10).min()
    roll_rsi_h10 = rsi.rolling(10).max()

    reg_bull_div = (l <= roll_l10) & (rsi > roll_rsi_l10) & (rsi < 42) & (c > o)
    reg_bear_div = (h >= roll_h10) & (rsi < roll_rsi_h10) & (rsi > 58) & (c < o)

    cpr_top = np.maximum(tc, bc)
    cpr_bot = np.minimum(tc, bc)
    in_cpr = (c >= cpr_bot) & (c <= cpr_top)

    hidden_bull_div = (l > roll_l10.shift(1)) & (rsi <= roll_rsi_l10.shift(1)) & (rsi < 50) & in_cpr & (c > o)
    hidden_bear_div = (h < roll_h10.shift(1)) & (rsi >= roll_rsi_h10.shift(1)) & (rsi > 50) & in_cpr & (c < o)

    # Extreme Reversal
    prev_h = h.shift(1)
    prev_l = l.shift(1)
    prev_c = c.shift(1)
    prev_o = o.shift(1)
    prev_rng = prev_h - prev_l

    ext_rev_long = (bar_cnt > 0) & greenzone & (prev_o - prev_c >= 0.75 * prev_rng) & \
                   (prev_rng > 2.0 * avg_candle) & (prev_o - prev_c > avg_body) & (c > o) & (dema_f >= dema_s)
    ext_rev_short = (bar_cnt > 0) & redzone & (prev_c - prev_o >= 0.75 * prev_rng) & \
                    (prev_rng > 2.0 * avg_candle) & (prev_c - prev_o > avg_body) & (o > c) & (dema_f <= dema_s)

    # Scalp
    scalp_buy_base = green1 & (l <= ema13) & (c > ema13) & (c > o)
    scalp_sell_base = red1 & (h >= ema13) & (c < ema13) & (c < o)

    # Missile
    missile_buy_base = (greenzone | (dema_f > dema_s)) & (c > ema13) & (c.shift(1) <= ema13.shift(1)) & (adx > 20)
    missile_sell_base = (redzone | (dema_f < dema_s)) & (c < ema13) & (c.shift(1) >= ema13.shift(1)) & (adx > 20)

    # Lightning
    lightning_long_raw = ((missile_buy_base & scalp_buy_base) | (reg_bull_div & (c > ema13)))
    lightning_short_raw = ((missile_sell_base & scalp_sell_base) | (reg_bear_div & (c < ema13)))

    lightning_long = lightning_long_raw & long_allowed
    lightning_short = lightning_short_raw & short_allowed

    div_long = reg_bull_div & (~lightning_long) & long_allowed
    div_short = reg_bear_div & (~lightning_short) & short_allowed

    hidden_div_long = hidden_bull_div & (~lightning_long) & (~div_long) & long_allowed
    hidden_div_short = hidden_bear_div & (~lightning_short) & (~div_short) & short_allowed

    ext_rev_long_final = ext_rev_long & (~lightning_long) & (~div_long) & (~hidden_div_long) & long_allowed
    ext_rev_short_final = ext_rev_short & (~lightning_short) & (~div_short) & (~hidden_div_short) & short_allowed

    missile_long = missile_buy_base & (~lightning_long) & (~div_long) & (~hidden_div_long) & (~ext_rev_long_final) & long_allowed
    missile_short = missile_sell_base & (~lightning_short) & (~div_short) & (~hidden_div_short) & (~ext_rev_short_final) & short_allowed

    scalp_long = scalp_buy_base & (~lightning_long) & (~missile_long) & (~div_long) & (~hidden_div_long) & (~ext_rev_long_final) & long_allowed
    scalp_short = scalp_sell_base & (~lightning_short) & (~missile_short) & (~div_short) & (~hidden_div_short) & (~ext_rev_short_final) & short_allowed

    return {
        'LONG MISSILE': missile_long.fillna(False),
        'SHORT MISSILE': missile_short.fillna(False),
        'LONG SCALP': scalp_long.fillna(False),
        'SHORT SCALP': scalp_short.fillna(False),
        'LONG LIGHTNING': lightning_long.fillna(False),
        'SHORT LIGHTNING': lightning_short.fillna(False),
        'LONG DIVERGENCE': div_long.fillna(False),
        'SHORT DIVERGENCE': div_short.fillna(False),
        'LONG HIDDEN DIVERGENCE': hidden_div_long.fillna(False),
        'SHORT HIDDEN DIVERGENCE': hidden_div_short.fillna(False),
        'LONG EXTREME REVERSAL': ext_rev_long_final.fillna(False),
        'SHORT EXTREME REVERSAL': ext_rev_short_final.fillna(False)
    }


def simulate_trades_for_regime(df: pd.DataFrame, signals: dict, regime_name: str, target_family: str = 'ALL') -> list:
    trades = []
    n = len(df)

    for sig_name, sig_series in signals.items():
        is_long = sig_name.startswith('LONG')
        is_div = 'DIVERGENCE' in sig_name
        is_core = not is_div

        if target_family == 'DIVERGENCE' and not is_div:
            continue
        if target_family == 'CORE' and not is_core:
            continue

        in_trade = False
        is_limit_pending = False
        entry_price = 0.0
        limit_placed_idx = None
        entry_idx = None
        sl_price = 0.0
        tp1 = 0.0
        tp2 = 0.0
        tp3 = 0.0
        tp4 = 0.0
        hit_tp1 = False
        hit_tp2 = False
        hit_tp3 = False

        for i in range(1, n):
            cur_h = df['High'].iloc[i]
            cur_l = df['Low'].iloc[i]
            cur_c = df['Close'].iloc[i]
            cur_atr = df['ATR'].iloc[i-1]
            avg_10 = df['AvgCandleSize10'].iloc[i-1]

            if np.isnan(cur_atr) or cur_atr <= 0:
                continue

            if in_trade:
                exit_price = None
                exit_level = None

                if is_long:
                    if cur_l <= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not hit_tp1 else ('BE' if not hit_tp2 else 'TP1')
                    elif cur_h >= tp4:
                        exit_price = tp4
                        exit_level = 'TP4'
                    elif cur_h >= tp3 and not hit_tp3:
                        hit_tp3 = True
                        sl_price = tp2
                    elif cur_h >= tp2 and not hit_tp2:
                        hit_tp2 = True
                        sl_price = tp1
                    elif cur_h >= tp1 and not hit_tp1:
                        hit_tp1 = True
                        sl_price = entry_price
                else:
                    if cur_h >= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not hit_tp1 else ('BE' if not hit_tp2 else 'TP1')
                    elif cur_l <= tp4:
                        exit_price = tp4
                        exit_level = 'TP4'
                    elif cur_l <= tp3 and not hit_tp3:
                        hit_tp3 = True
                        sl_price = tp2
                    elif cur_l <= tp2 and not hit_tp2:
                        hit_tp2 = True
                        sl_price = tp1
                    elif cur_l <= tp1 and not hit_tp1:
                        hit_tp1 = True
                        sl_price = entry_price

                if not exit_price and (i - entry_idx) >= 72:
                    exit_price = cur_c
                    exit_level = 'TIMEOUT'

                if exit_price is not None:
                    exact_pct = ((exit_price - entry_price) / entry_price * 100.0) if is_long else ((entry_price - exit_price) / entry_price * 100.0)
                    if exact_pct > 0.0001:
                        outcome = 'WIN'
                    elif exact_pct < -0.0001:
                        outcome = 'LOSS'
                    else:
                        outcome = 'BREAKEVEN'

                    trades.append({
                        'bar_idx': entry_idx,
                        'sig_name': sig_name,
                        'is_div': is_div,
                        'exact_pct': exact_pct,
                        'outcome': outcome,
                        'exit_level': exit_level,
                        'hit_initial_sl': (exit_level == 'SL'),
                        'bars_held': int(i - entry_idx)
                    })
                    in_trade = False
                    is_limit_pending = False
                    continue

            if is_limit_pending:
                if (i - limit_placed_idx) >= 24:
                    is_limit_pending = False
                else:
                    filled = False
                    if is_long and cur_l <= entry_price:
                        filled = True
                    elif not is_long and cur_h >= entry_price:
                        filled = True

                    if filled:
                        in_trade = True
                        is_limit_pending = False
                        entry_idx = i
                        hit_tp1 = False
                        hit_tp2 = False
                        hit_tp3 = False
                        continue

            if not in_trade and not is_limit_pending:
                if sig_series.iloc[i]:
                    sig_bar_h = df['High'].iloc[i]
                    sig_bar_l = df['Low'].iloc[i]
                    sig_bar_c = df['Close'].iloc[i]

                    if is_div:
                        entry_price = round((sig_bar_h + sig_bar_l) / 2.0, 4)
                        is_limit_pending = True
                        limit_placed_idx = i

                        div_extreme_l = df['Low'].iloc[max(0, i-5):i].min()
                        div_extreme_h = df['High'].iloc[max(0, i-5):i].max()

                        if regime_name == 'DIV_SL_0.5_AVG10':
                            sl_dist = 0.5 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_1.0_AVG10':
                            sl_dist = 1.0 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_1.5_AVG10':
                            sl_dist = 1.5 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_2.0_AVG10':
                            sl_dist = 2.0 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_2.5_AVG10':
                            sl_dist = 2.5 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_3.0_AVG10':
                            sl_dist = 3.0 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_1.0_ATR':
                            sl_dist = 1.0 * cur_atr
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_1.5_ATR':
                            sl_dist = 1.5 * cur_atr
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist
                        elif regime_name == 'DIV_SL_ENTRY_1.0_ATR':
                            sl_dist = 1.0 * cur_atr
                            sl_price = entry_price - sl_dist if is_long else entry_price + sl_dist
                        elif regime_name == 'DIV_SL_ENTRY_1.5_ATR':
                            sl_dist = 1.5 * cur_atr
                            sl_price = entry_price - sl_dist if is_long else entry_price + sl_dist
                        else:
                            sl_dist = 2.0 * avg_10
                            sl_price = div_extreme_l - sl_dist if is_long else div_extreme_h + sl_dist

                        tp1 = entry_price + 1.0 * cur_atr if is_long else entry_price - 1.0 * cur_atr
                        tp2 = entry_price + 2.0 * cur_atr if is_long else entry_price - 2.0 * cur_atr
                        tp3 = entry_price + 3.0 * cur_atr if is_long else entry_price - 3.0 * cur_atr
                        tp4 = entry_price + 4.0 * cur_atr if is_long else entry_price - 4.0 * cur_atr

                    else:
                        entry_price = sig_bar_c
                        is_limit_pending = False
                        in_trade = True
                        entry_idx = i
                        hit_tp1 = False
                        hit_tp2 = False
                        hit_tp3 = False

                        if regime_name == 'CORE_SL_0.75_ATR':
                            sl_mult = 0.75
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_1.00_ATR':
                            sl_mult = 1.00
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_1.25_ATR':
                            sl_mult = 1.25
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_1.50_ATR':
                            sl_mult = 1.50
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_1.75_ATR':
                            sl_mult = 1.75
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_2.00_ATR':
                            sl_mult = 2.00
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr
                        elif regime_name == 'CORE_SL_BAR_EXTREME':
                            sl_price = sig_bar_l - 0.5 * cur_atr if is_long else sig_bar_h + 0.5 * cur_atr
                        else:
                            sl_mult = 1.00
                            sl_price = entry_price - sl_mult * cur_atr if is_long else entry_price + sl_mult * cur_atr

                        tp1 = entry_price + 1.5 * cur_atr if is_long else entry_price - 1.5 * cur_atr
                        tp2 = entry_price + 2.5 * cur_atr if is_long else entry_price - 2.5 * cur_atr
                        tp3 = entry_price + 3.5 * cur_atr if is_long else entry_price - 3.5 * cur_atr
                        tp4 = entry_price + 4.5 * cur_atr if is_long else entry_price - 4.5 * cur_atr

    return trades


def compute_metrics(trades: list) -> dict:
    if not trades:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'sharpe': 0.0,
            'sortino': 0.0, 'false_stop_rate': 0.0
        }

    total = len(trades)
    wins = [t['exact_pct'] for t in trades if t['outcome'] == 'WIN']
    losses = [t['exact_pct'] for t in trades if t['outcome'] == 'LOSS']
    bes = [t['exact_pct'] for t in trades if t['outcome'] == 'BREAKEVEN']
    sl_hits = [t for t in trades if t.get('hit_initial_sl', False)]

    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(bes)

    gross_profit = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0

    win_rate = (win_count / total * 100.0) if total > 0 else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 1.0)
    net_return = gross_profit - gross_loss

    avg_win = (gross_profit / win_count) if win_count > 0 else 0.0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0.0
    realized_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    p_w = win_count / total if total > 0 else 0.0
    p_l = loss_count / total if total > 0 else 0.0
    expectancy = (p_w * avg_win) - (p_l * avg_loss)
    false_stop_rate = (len(sl_hits) / total * 100.0) if total > 0 else 0.0

    returns = np.array([t['exact_pct'] for t in trades])
    cum = np.cumsum(returns)
    running_max = np.maximum.accumulate(cum)
    drawdowns = running_max - cum
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    std = np.std(returns) if len(returns) > 1 else 0.0
    downside_std = np.std(returns[returns < 0]) if len(returns[returns < 0]) > 1 else 1e-6
    sharpe = float((np.mean(returns) / std * np.sqrt(252))) if std > 0 else 0.0
    sortino = float((np.mean(returns) / downside_std * np.sqrt(252))) if downside_std > 0 else 0.0

    return {
        'total_trades': total,
        'wins': win_count,
        'losses': loss_count,
        'breakevens': be_count,
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 2),
        'net_return': round(net_return, 2),
        'expectancy': round(expectancy, 3),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'realized_rr': round(realized_rr, 2),
        'max_drawdown': round(max_dd, 2),
        'sharpe': round(sharpe, 2),
        'sortino': round(sortino, 2),
        'false_stop_rate': round(false_stop_rate, 1)
    }


def run_full_analysis():
    print("=" * 80)
    print("TLCS VectorBT Initial Stop Loss (SL) Optimization Analysis")
    print("=" * 80)

    processed_assets = {}
    total_bars = 0

    for symbol, meta in TARGET_ASSETS.items():
        raw_df = load_asset_data(symbol)
        if raw_df is None or len(raw_df) < 200:
            continue
        ind_df = compute_indicators(raw_df)
        signals = generate_canonical_signals(ind_df)
        processed_assets[symbol] = {
            'df': ind_df,
            'signals': signals,
            'meta': meta
        }
        total_bars += len(ind_df)

    print(f"Loaded {len(processed_assets)} assets with {total_bars} total hourly bars.")

    div_regimes = [
        'DIV_SL_ENTRY_1.0_ATR',
        'DIV_SL_ENTRY_1.5_ATR',
        'DIV_SL_0.5_AVG10',
        'DIV_SL_1.0_AVG10',
        'DIV_SL_1.5_AVG10',
        'DIV_SL_2.0_AVG10',
        'DIV_SL_2.5_AVG10',
        'DIV_SL_3.0_AVG10',
        'DIV_SL_1.0_ATR',
        'DIV_SL_1.5_ATR'
    ]

    core_regimes = [
        'CORE_SL_0.75_ATR',
        'CORE_SL_1.00_ATR',
        'CORE_SL_1.25_ATR',
        'CORE_SL_1.50_ATR',
        'CORE_SL_1.75_ATR',
        'CORE_SL_2.00_ATR',
        'CORE_SL_BAR_EXTREME'
    ]

    all_results = {
        'divergence': {},
        'core': {}
    }

    def evaluate_regime_across_universe(regime: str, family: str):
        full_trades = []
        past_trades = []
        future_trades = []

        for symbol, data in processed_assets.items():
            df = data['df']
            signals = data['signals']
            split_idx = int(len(df) * 0.70)
            split_date = df.index[split_idx]

            trades = simulate_trades_for_regime(df, signals, regime, target_family=family)
            for t in trades:
                t['symbol'] = symbol
                full_trades.append(t)
                bar_time = df.index[t['bar_idx']]
                if bar_time < split_date:
                    past_trades.append(t)
                else:
                    future_trades.append(t)

        return {
            'FULL': compute_metrics(full_trades),
            'PAST_IN_SAMPLE': compute_metrics(past_trades),
            'FUTURE_FORWARD_WALK': compute_metrics(future_trades)
        }

    print("\n--- Running Divergence SL Regimes ---")
    for reg in div_regimes:
        res = evaluate_regime_across_universe(reg, 'DIVERGENCE')
        all_results['divergence'][reg] = res
        print(f"[{reg:<22}] FULL -> WR: {res['FULL']['win_rate']}% | PF: {res['FULL']['profit_factor']} | Net: {res['FULL']['net_return']}% | Exp: {res['FULL']['expectancy']}% | MaxDD: {res['FULL']['max_drawdown']}% | FalseStop: {res['FULL']['false_stop_rate']}%")
        print(f"       PAST (70%)   -> WR: {res['PAST_IN_SAMPLE']['win_rate']}% | PF: {res['PAST_IN_SAMPLE']['profit_factor']} | Net: {res['PAST_IN_SAMPLE']['net_return']}%")
        print(f"       FUTURE (30%) -> WR: {res['FUTURE_FORWARD_WALK']['win_rate']}% | PF: {res['FUTURE_FORWARD_WALK']['profit_factor']} | Net: {res['FUTURE_FORWARD_WALK']['net_return']}%")

    print("\n--- Running Core Strategy (Missile/Scalp/Lightning/ExtRev) SL Regimes ---")
    for reg in core_regimes:
        res = evaluate_regime_across_universe(reg, 'CORE')
        all_results['core'][reg] = res
        print(f"[{reg:<22}] FULL -> WR: {res['FULL']['win_rate']}% | PF: {res['FULL']['profit_factor']} | Net: {res['FULL']['net_return']}% | Exp: {res['FULL']['expectancy']}% | MaxDD: {res['FULL']['max_drawdown']}% | FalseStop: {res['FULL']['false_stop_rate']}%")
        print(f"       PAST (70%)   -> WR: {res['PAST_IN_SAMPLE']['win_rate']}% | PF: {res['PAST_IN_SAMPLE']['profit_factor']} | Net: {res['PAST_IN_SAMPLE']['net_return']}%")
        print(f"       FUTURE (30%) -> WR: {res['FUTURE_FORWARD_WALK']['win_rate']}% | PF: {res['FUTURE_FORWARD_WALK']['profit_factor']} | Net: {res['FUTURE_FORWARD_WALK']['net_return']}%")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'initial_sl_vectorbt_results.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved results to {out_path}")


if __name__ == '__main__':
    run_full_analysis()
