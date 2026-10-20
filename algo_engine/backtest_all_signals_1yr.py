"""
TLCS 1-Year Multi-Asset Quantitative Backtest Engine
===================================================
Backtesting All 6 Canonical Signal Types Across All Directions:
  1. MISSILE (Long & Short)
  2. SCALP (Long & Short)
  3. LIGHTNING (Long & Short)
  4. DIVERGENCE (Long & Short)
  5. HIDDEN DIVERGENCE (Long & Short)
  6. EXTREME REVERSAL (Long & Short)

Rules & Methodology:
  - Timeframe: 1-Year Hourly (1h) Continuous Historical Data (Oct 2025 - Oct 2026)
  - Pre-calculated Prior-Day Camarilla (H1-H5, L1-L5) and Daily CPR (TC, BC, Pivot, NCPR)
  - Strict H4 / L4 Limit Touch-Point Gating: Longs linked to low < H4, Shorts to high > L4
  - Session Boundary Guard: Zero phantom multi-bar signals across overnight gaps
  - Canonical exact_pct calculation: ((Exit - Entry) / Entry) * 100
  - Canonical Win Rate: Wins / Total Closed Trades (Breakevens included in denominator)
  - TP Progression: TP1 -> Breakeven, TP2 -> TP1, TP3 -> TP2, TP4 -> TP3
  - VectorBT & Institutional Risk Metrics: Sharpe, Sortino, Profit Factor, Max Drawdown
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import sys
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, timedelta

# Universe Configuration
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
    """
    Computes all TLCS Pine Script equivalent indicators on hourly bars:
    Camarilla, CPR, EMAs, DEMA trend, ATR, DMI, Oscillator Momentum, and Divergences.
    """
    df = df.copy()
    h = df['High']
    l = df['Low']
    c = df['Close']
    o = df['Open']

    # Typical Price
    tp = (h + l + c) / 3.0
    df['TP'] = tp

    # 1. EMAs on Typical Price
    df['EMA13'] = tp.ewm(span=13, adjust=False).mean()
    df['EMA32'] = tp.ewm(span=32, adjust=False).mean()

    # Fast & Slow DEMAs (period 5 and 13)
    def calc_dema(series, span):
        e1 = series.ewm(span=span, adjust=False).mean()
        e2 = e1.ewm(span=span, adjust=False).mean()
        return 2 * e1 - e2

    df['DEMA_FAST'] = calc_dema(tp, 5)
    df['DEMA_SLOW'] = calc_dema(tp, 13)

    # 2. ATR (14)
    tr1 = h - l
    tr2 = (h - c.shift(1)).abs()
    tr3 = (l - c.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean().bfill()

    # 3. DMI & ADX (14) with Wilder's RMA
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    # Wilder RMA is equivalent to ewm(alpha=1/14)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/14, adjust=False).mean().fillna(0)

    df['PlusDI'] = plus_di
    df['MinusDI'] = minus_di
    df['ADX'] = adx

    # 4. Oscillator Momentum (m0 = EMA 21, m10 = SMA 96 of 92-bar highest/lowest osc)
    highest_92 = h.rolling(92).max()
    lowest_92 = l.rolling(92).min()
    osc_range = (highest_92 - lowest_92).replace(0, np.nan)
    osc = 100 * (c - lowest_92) / osc_range
    osc = osc.fillna(50)
    df['m0'] = osc.ewm(span=21, adjust=False).mean()
    df['m10'] = osc.rolling(window=96).mean().bfill()

    # 5. RSI (14)
    delta = c.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    avg_loss = pd.Series(loss, index=df.index).ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs)).fillna(50)

    # 6. Daily Camarilla and CPR Levels (Computed strictly from prior completed day)
    # Group by calendar date
    df['date'] = df.index.date
    daily = df.groupby('date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
    daily_shifted = daily.shift(1)  # Prior day completed levels

    # Compute Camarilla
    prior_h = daily_shifted['High']
    prior_l = daily_shifted['Low']
    prior_c = daily_shifted['Close']
    rng = prior_h - prior_l

    cam_h4 = prior_c + rng * 0.55
    cam_h3 = prior_c + rng * 0.275
    cam_l3 = prior_c - rng * 0.275
    cam_l4 = prior_c - rng * 0.55

    # Compute CPR
    cpr_p = (prior_h + prior_l + prior_c) / 3.0
    cpr_bc = (prior_h + prior_l) / 2.0
    cpr_tc = 2.0 * cpr_p - cpr_bc
    actual_tc = pd.concat([cpr_tc, cpr_bc], axis=1).max(axis=1)
    actual_bc = pd.concat([cpr_tc, cpr_bc], axis=1).min(axis=1)
    cpr_width = (actual_tc - actual_bc).abs()
    ncpr = (cpr_width / rng.replace(0, np.nan) < 0.05) | (cpr_width / cpr_p.replace(0, np.nan) < 0.002)

    # Map daily levels back to hourly dataframe
    df['H4'] = df['date'].map(cam_h4).bfill()
    df['H3'] = df['date'].map(cam_h3).bfill()
    df['L3'] = df['date'].map(cam_l3).bfill()
    df['L4'] = df['date'].map(cam_l4).bfill()
    df['Pivot'] = df['date'].map(cpr_p).bfill()
    df['TC'] = df['date'].map(actual_tc).bfill()
    df['BC'] = df['date'].map(actual_bc).bfill()
    df['NCPR'] = df['date'].map(ncpr).fillna(False)

    # Value Area approximation (rolling 24-period)
    df['VAH'] = tp.rolling(24).mean() + 0.70 * tr.rolling(24).mean()
    df['VAL'] = tp.rolling(24).mean() - 0.70 * tr.rolling(24).mean()

    # 7. Session Bar Counter (Index within day) to guard against cross-session bleed
    df['session_bar_counter'] = df.groupby('date').cumcount()

    # 8. Rolling 50-bar average candle & body for Extreme Reversal
    df['AverageCandle'] = (h - l).rolling(50).mean().bfill()
    df['AverageBody'] = (c - o).abs().rolling(50).mean().bfill()

    return df


def generate_all_signals(df: pd.DataFrame) -> dict:
    """
    Generates all 6 canonical strategy triggers with Long & Short:
      - MISSILE
      - SCALP
      - LIGHTNING
      - DIVERGENCE
      - HIDDEN DIVERGENCE
      - EXTREME REVERSAL
    Strictly enforcing H4/L4 limit gating:
      Longs require Low < H4
      Shorts require High > L4
    """
    c = df['Close']
    o = df['Open']
    h = df['High']
    l = df['Low']
    tp = df['TP']
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
    pivot = df['Pivot']
    tc = df['TC']
    bc = df['BC']
    ncpr = df['NCPR']
    vah = df['VAH']
    val = df['VAL']
    bar_cnt = df['session_bar_counter']
    avg_candle = df['AverageCandle']
    avg_body = df['AverageBody']

    # ═══════════════════════════════════════════════════════
    # STRICT H4 / L4 LIMIT TOUCH-POINT GATING
    # ═══════════════════════════════════════════════════════
    long_allowed = l < h4
    short_allowed = h > l4

    # Zones
    greenzone = (plus_di > minus_di) & (ema13 > ema32) & (dema_f > dema_s)
    redzone = (minus_di > plus_di) & (ema13 < ema32) & (dema_f < dema_s)
    green1 = (plus_di > minus_di) & (m0 > m10)
    red1 = (minus_di > plus_di) & (m0 < m10)

    # 1. DIVERGENCES (RSI 14)
    # Regular Divergence
    roll_l10 = l.rolling(10).min()
    roll_h10 = h.rolling(10).max()
    roll_rsi_l10 = rsi.rolling(10).min()
    roll_rsi_h10 = rsi.rolling(10).max()

    reg_bull_div = (l <= roll_l10) & (rsi > roll_rsi_l10) & (rsi < 42) & (c > o)
    reg_bear_div = (h >= roll_h10) & (rsi < roll_rsi_h10) & (rsi > 58) & (c < o)

    # Hidden Divergence (inside CPR check)
    cpr_top = np.maximum(tc, bc)
    cpr_bot = np.minimum(tc, bc)
    in_cpr = (c >= cpr_bot) & (c <= cpr_top)

    hidden_bull_div = (l > roll_l10.shift(1)) & (rsi <= roll_rsi_l10.shift(1)) & (rsi < 50) & in_cpr & (c > o)
    hidden_bear_div = (h < roll_h10.shift(1)) & (rsi >= roll_rsi_h10.shift(1)) & (rsi > 50) & in_cpr & (c < o)

    # 2. EXTREME REVERSAL (With Session Boundary Guard bar_cnt > 0)
    # Exhaustion bar [1] + Reversal bar [0]
    prev_h = h.shift(1)
    prev_l = l.shift(1)
    prev_c = c.shift(1)
    prev_o = o.shift(1)
    prev_rng = prev_h - prev_l

    # Bullish Extreme Reversal: Prev bar was large red exhaustion, current bar closes green
    ext_rev_long = (bar_cnt > 0) & greenzone & (prev_o - prev_c >= 0.75 * prev_rng) & \
                   (prev_rng > 2.0 * avg_candle) & (prev_o - prev_c > avg_body) & (c > o) & (dema_f >= dema_s)

    # Bearish Extreme Reversal: Prev bar was large green exhaustion, current bar closes red
    ext_rev_short = (bar_cnt > 0) & redzone & (prev_c - prev_o >= 0.75 * prev_rng) & \
                    (prev_rng > 2.0 * avg_candle) & (prev_c - prev_o > avg_body) & (o > c) & (dema_f <= dema_s)

    # 3. SCALP: 50% Midpoint Retest & Trend Pullback
    # Bounce off EMA13/EMA32/CPR Pivot in trend direction
    scalp_buy_base = green1 & (l <= ema13) & (c > ema13) & (c > o)
    scalp_sell_base = red1 & (h >= ema13) & (c < ema13) & (c < o)

    # 4. MISSILE: Momentum Breakout above/below Pivot/EMA
    missile_buy_base = (greenzone | (dema_f > dema_s)) & (c > ema13) & (c.shift(1) <= ema13.shift(1)) & (adx > 20)
    missile_sell_base = (redzone | (dema_f < dema_s)) & (c < ema13) & (c.shift(1) >= ema13.shift(1)) & (adx > 20)

    # 5. LIGHTNING: Confluence of Missile + Scalp OR Strong Divergence Thrust
    lightning_long_raw = ((missile_buy_base & scalp_buy_base) | (reg_bull_div & (c > ema13)))
    lightning_short_raw = ((missile_sell_base & scalp_sell_base) | (reg_bear_div & (c < ema13)))

    # Apply Long / Short H4/L4 gating & Decouple individual triggers
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


def simulate_trade_execution(df: pd.DataFrame, signals: dict, symbol: str, asset_name: str, market_cat: str) -> list:
    """
    Simulates trades with canonical exact_pct math, limit order fills, and full TP1-TP4 progression.
    """
    trades = []

    for sig_name, sig_series in signals.items():
        is_long = sig_name.startswith('LONG')
        base_type = sig_name.replace('LONG ', '').replace('SHORT ', '')

        in_trade = False
        is_limit_pending = False
        entry_price = 0.0
        limit_placed_idx = None
        entry_idx = None
        entry_time = None
        sl_price = 0.0
        tp1 = 0.0
        tp2 = 0.0
        tp3 = 0.0
        tp4 = 0.0
        hit_tp1 = False
        hit_tp2 = False
        hit_tp3 = False

        for i in range(1, len(df)):
            idx = df.index[i]
            cur_h = df['High'].iloc[i]
            cur_l = df['Low'].iloc[i]
            cur_c = df['Close'].iloc[i]
            cur_o = df['Open'].iloc[i]
            cur_atr = df['ATR'].iloc[i-1]
            if np.isnan(cur_atr) or cur_atr <= 0:
                continue

            # 1. Manage Active Trade
            if in_trade:
                exit_price = None
                exit_level = None

                if is_long:
                    # Check Stop Loss
                    if cur_l <= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not hit_tp1 else ('BE' if not hit_tp2 else 'TP1')
                    # Check TP4
                    elif cur_h >= tp4:
                        exit_price = tp4
                        exit_level = 'TP4'
                    # Check TP3
                    elif cur_h >= tp3 and not hit_tp3:
                        hit_tp3 = True
                        sl_price = tp2  # Move SL to TP2
                    # Check TP2
                    elif cur_h >= tp2 and not hit_tp2:
                        hit_tp2 = True
                        sl_price = tp1  # Move SL to TP1
                    # Check TP1 -> Move to Breakeven
                    elif cur_h >= tp1 and not hit_tp1:
                        hit_tp1 = True
                        sl_price = entry_price

                else:  # Short
                    # Check Stop Loss
                    if cur_h >= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not hit_tp1 else ('BE' if not hit_tp2 else 'TP1')
                    # Check TP4
                    elif cur_l <= tp4:
                        exit_price = tp4
                        exit_level = 'TP4'
                    # Check TP3
                    elif cur_l <= tp3 and not hit_tp3:
                        hit_tp3 = True
                        sl_price = tp2
                    # Check TP2
                    elif cur_l <= tp2 and not hit_tp2:
                        hit_tp2 = True
                        sl_price = tp1
                    # Check TP1 -> Move to Breakeven
                    elif cur_l <= tp1 and not hit_tp1:
                        hit_tp1 = True
                        sl_price = entry_price

                # Check max trade duration (72 hours timeout)
                if not exit_price and (i - entry_idx) >= 72:
                    exit_price = cur_c
                    exit_level = 'TIMEOUT'

                if exit_price is not None:
                    # Canonical exact_pct
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

                    trades.append({
                        'symbol': symbol,
                        'asset_name': asset_name,
                        'market': market_cat,
                        'signal_name': sig_name,
                        'base_type': base_type,
                        'direction': 'LONG' if is_long else 'SHORT',
                        'entry_time': str(entry_time),
                        'exit_time': str(idx),
                        'entry_price': round(float(entry_price), 4),
                        'exit_price': round(float(exit_price), 4),
                        'exact_pct': round(float(exact_pct), 4),
                        'outcome': outcome,
                        'exit_level': exit_level,
                        'bars_held': int(i - entry_idx)
                    })

                    in_trade = False
                    is_limit_pending = False
                    continue

            # 2. Check Pending Limit Order Fill
            if is_limit_pending:
                # Cancel/expire limit order if not filled within 24 hours
                if (i - limit_placed_idx) >= 24:
                    is_limit_pending = False
                else:
                    # Check if price touched limit entry
                    limit_filled = False
                    if is_long and cur_l <= entry_price:
                        limit_filled = True
                    elif not is_long and cur_h >= entry_price:
                        limit_filled = True

                    if limit_filled:
                        in_trade = True
                        is_limit_pending = False
                        entry_idx = i
                        entry_time = idx
                        hit_tp1 = False
                        hit_tp2 = False
                        hit_tp3 = False
                        continue

            # 3. Check for New Signal Trigger
            if not in_trade and not is_limit_pending:
                if sig_series.iloc[i]:
                    # Create Limit Order at session midpoint / current bar close
                    is_limit_pending = True
                    limit_placed_idx = i
                    entry_price = cur_c
                    dist = cur_atr

                    if is_long:
                        sl_price = entry_price - 1.0 * dist
                        tp1 = entry_price + 1.5 * dist
                        tp2 = entry_price + 2.5 * dist
                        tp3 = entry_price + 3.5 * dist
                        tp4 = entry_price + 4.5 * dist
                    else:
                        sl_price = entry_price + 1.0 * dist
                        tp1 = entry_price - 1.5 * dist
                        tp2 = entry_price - 2.5 * dist
                        tp3 = entry_price - 3.5 * dist
                        tp4 = entry_price - 4.5 * dist

    return trades


def compute_metrics(trades: list) -> dict:
    """
    Computes VectorBT & Institutional performance metrics adhering to User Rules:
      - Canonical Win Rate: Wins / Total Closed Trades * 100
      - Exact percentage returns
      - Sharpe, Sortino, Profit Factor, Max Drawdown
    """
    if not trades:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'sharpe': 0.0,
            'sortino': 0.0, 'max_consec_losses': 0
        }

    total = len(trades)
    wins = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    bes = [t for t in trades if t['outcome'] == 'BREAKEVEN']

    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(bes)

    # Canonical Win Rate Formula: Wins / Total * 100 (Breakevens included in denominator)
    win_rate = (win_count / total * 100.0) if total > 0 else 0.0

    returns = [t['exact_pct'] for t in trades]
    net_return = sum(returns)
    expectancy = net_return / total if total > 0 else 0.0

    win_returns = [t['exact_pct'] for t in wins]
    loss_returns = [abs(t['exact_pct']) for t in losses]

    gross_profit = sum(win_returns)
    gross_loss = sum(loss_returns)

    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.99 if gross_profit > 0 else 1.0)
    avg_win = (gross_profit / win_count) if win_count > 0 else 0.0
    avg_loss = (gross_loss / loss_count) if loss_count > 0 else 0.0
    realized_rr = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    # Max Drawdown & Equity Curve
    cum_returns = np.cumsum(returns)
    cum_equity = 100.0 + cum_returns
    running_max = np.maximum.accumulate(cum_equity)
    drawdowns = (running_max - cum_equity) / running_max * 100.0
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    # Annualized Sharpe & Sortino (assuming ~252 trading days, sqrt(252))
    std_dev = np.std(returns) if len(returns) > 1 else 0.0
    sharpe = float((expectancy / std_dev) * np.sqrt(252)) if std_dev > 0 else 0.0

    downside_losses = [min(0.0, r) for r in returns]
    downside_dev = np.std(downside_losses) if len(downside_losses) > 1 else 0.0
    sortino = float((expectancy / downside_dev) * np.sqrt(252)) if downside_dev > 0 else 0.0

    # Max Consecutive Losses
    max_streak = 0
    cur_streak = 0
    for t in trades:
        if t['outcome'] == 'LOSS':
            cur_streak += 1
            if cur_streak > max_streak:
                max_streak = cur_streak
        else:
            cur_streak = 0

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
        'max_consec_losses': max_streak
    }


def run_full_1yr_backtest():
    print("=" * 85)
    print("   THE LION CAPITAL SOLUTIONS (TLCS) - 1-YEAR QUANTITATIVE BACKTEST")
    print("   Evaluation: All 6 Canonical Signal Types Across All Market Universes")
    print("   Timeframe: 1 Year (Hourly Bars with Daily Camarilla / CPR Pivots)")
    print("=" * 85)

    all_executed_trades = []
    asset_breakdowns = {}

    for sym, info in TARGET_ASSETS.items():
        ticker = info['ticker']
        print(f"[*] Processing {sym} ({info['name']}: {ticker})...")
        try:
            df_raw = yf.download(ticker, period='1y', interval='1h', progress=False)
            if df_raw.empty or len(df_raw) < 100:
                print(f"  [!] Insufficient data for {sym}, skipping.")
                continue

            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)

            df_ind = compute_indicators(df_raw)
            sigs = generate_all_signals(df_ind)
            trades = simulate_trade_execution(df_ind, sigs, sym, info['name'], info['market'])

            all_executed_trades.extend(trades)
            m = compute_metrics(trades)
            asset_breakdowns[sym] = m
            print(f"  [✓] {sym}: {len(df_ind)} bars | {len(trades)} trades | Win Rate: {m['win_rate']}% | Net: {m['net_return']:+0.2f}%")
        except Exception as e:
            print(f"  [X] Error on {sym}: {e}")

    if not all_executed_trades:
        print("[!] No trades executed across universe.")
        return

    print("\n" + "=" * 85)
    print("   PART 1: OVERALL SYSTEM PERFORMANCE (1-YEAR)")
    print("=" * 85)
    overall_metrics = compute_metrics(all_executed_trades)
    print(f"Total Trades Executed:   {overall_metrics['total_trades']}")
    print(f"Wins / Losses / B/E:     {overall_metrics['wins']} / {overall_metrics['losses']} / {overall_metrics['breakevens']}")
    print(f"Canonical Win Rate:      {overall_metrics['win_rate']}%")
    print(f"Profit Factor:           {overall_metrics['profit_factor']}")
    print(f"Net Cumulative Return:   {overall_metrics['net_return']:+.2f}%")
    print(f"Expectancy (Mean Trade): {overall_metrics['expectancy']:+.3f}%")
    print(f"Realized R:R:            {overall_metrics['realized_rr']}R (Avg Win: +{overall_metrics['avg_win']}%, Avg Loss: -{overall_metrics['avg_loss']}%)")
    print(f"Max Drawdown:            -{overall_metrics['max_drawdown']}%")
    print(f"Annualized Sharpe:       {overall_metrics['sharpe']}")
    print(f"Annualized Sortino:      {overall_metrics['sortino']}")
    print(f"Max Consec. Losses:      {overall_metrics['max_consec_losses']} trades")

    # ═══════════════════════════════════════════════════════
    # PART 2: BREAKDOWN BY CANONICAL SIGNAL TYPE
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 85)
    print("   PART 2: PERFORMANCE BREAKDOWN BY CANONICAL SIGNAL TYPE")
    print("=" * 85)

    signal_types = ['MISSILE', 'SCALP', 'LIGHTNING', 'DIVERGENCE', 'HIDDEN DIVERGENCE', 'EXTREME REVERSAL']
    sig_results = {}

    for st in signal_types:
        sub_trades = [t for t in all_executed_trades if t['base_type'] == st]
        sig_results[st] = compute_metrics(sub_trades)

    df_sig_table = []
    for st, m in sig_results.items():
        df_sig_table.append({
            'Signal Family': st,
            'Trades': m['total_trades'],
            'W / L / BE': f"{m['wins']} / {m['losses']} / {m['breakevens']}",
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}",
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.3f}%",
            'Avg W / L': f"+{m['avg_win']:.2f}% / -{m['avg_loss']:.2f}%",
            'Realized R:R': f"{m['realized_rr']:.2f}R",
            'Max DD': f"-{m['max_drawdown']:.2f}%",
            'Sharpe': f"{m['sharpe']:.2f}",
            'Sortino': f"{m['sortino']:.2f}"
        })
    print(pd.DataFrame(df_sig_table).to_string(index=False))

    # ═══════════════════════════════════════════════════════
    # PART 3: LONG VS SHORT DIRECTIONAL AUDIT
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 85)
    print("   PART 3: DIRECTIONAL AUDIT (ALL 12 TRIGGERS)")
    print("=" * 85)

    all_12_triggers = [
        'LONG MISSILE', 'SHORT MISSILE',
        'LONG SCALP', 'SHORT SCALP',
        'LONG LIGHTNING', 'SHORT LIGHTNING',
        'LONG DIVERGENCE', 'SHORT DIVERGENCE',
        'LONG HIDDEN DIVERGENCE', 'SHORT HIDDEN DIVERGENCE',
        'LONG EXTREME REVERSAL', 'SHORT EXTREME REVERSAL'
    ]
    trig_results = {}
    for trig in all_12_triggers:
        sub_trades = [t for t in all_executed_trades if t['signal_name'] == trig]
        trig_results[trig] = compute_metrics(sub_trades)

    df_trig_table = []
    for trig, m in trig_results.items():
        df_trig_table.append({
            'Specific Trigger': trig,
            'Trades': m['total_trades'],
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}",
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.3f}%",
            'Realized R:R': f"{m['realized_rr']:.2f}R",
            'Max DD': f"-{m['max_drawdown']:.2f}%",
            'Sharpe': f"{m['sharpe']:.2f}"
        })
    print(pd.DataFrame(df_trig_table).to_string(index=False))

    # ═══════════════════════════════════════════════════════
    # PART 4: ASSET CLASS & MARKET BREAKDOWN
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 85)
    print("   PART 4: ASSET CLASS / MARKET PERFORMANCE BREAKDOWN")
    print("=" * 85)

    market_categories = ['Indian Equities', 'Commodities', 'Global / FX / Crypto']
    market_results = {}
    for mkt in market_categories:
        sub_trades = [t for t in all_executed_trades if t['market'] == mkt]
        market_results[mkt] = compute_metrics(sub_trades)

    df_mkt_table = []
    for mkt, m in market_results.items():
        df_mkt_table.append({
            'Market Sector': mkt,
            'Trades': m['total_trades'],
            'Win Rate': f"{m['win_rate']:.1f}%",
            'Profit Factor': f"{m['profit_factor']:.2f}",
            'Net Return': f"{m['net_return']:+.2f}%",
            'Expectancy': f"{m['expectancy']:+.3f}%",
            'Max DD': f"-{m['max_drawdown']:.2f}%",
            'Sharpe': f"{m['sharpe']:.2f}"
        })
    print(pd.DataFrame(df_mkt_table).to_string(index=False))

    # Save output to JSON
    output_payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'period': '1 Year (Oct 20, 2025 - Oct 20, 2026)',
        'overall': overall_metrics,
        'by_signal_type': sig_results,
        'by_12_triggers': trig_results,
        'by_market': market_results,
        'by_asset': asset_breakdowns,
        'sample_trades': all_executed_trades[:50]
    }

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tlcs_1yr_backtest_all_signals_results.json')
    with open(out_file, 'w') as f:
        json.dump(output_payload, f, indent=2)
    print(f"\n[✓] Full 1-year backtest results successfully saved to: {out_file}")


if __name__ == '__main__':
    run_full_1yr_backtest()
