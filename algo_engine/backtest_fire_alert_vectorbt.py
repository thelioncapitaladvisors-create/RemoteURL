"""
TLCS Version 3.0: VectorBT Fire Alert Quantitative Edge Analysis Engine
=======================================================================
Conducts rigorous multi-asset VectorBT backtesting comparing:
  1. FIRE_ALERT Signals (Canonical setups triggered exclusively in NEUTRAL ZONE)
  2. NON-FIRE / IN-ZONE Signals (Canonical setups triggered in GREENZONE / REDZONE)
  3. ALL UNFILTERED SIGNALS (All canonical setups combined)
  4. Signal Family Cohort Breakdown:
     - MISSILE (Fire Alert vs Non-Fire vs All)
     - SCALP (Fire Alert vs Non-Fire vs All)
     - LIGHTNING (Fire Alert vs Non-Fire vs All)
     - DIVERGENCE (Fire Alert vs Non-Fire vs All)
     - HIDDEN DIVERGENCE (Fire Alert vs Non-Fire vs All)
     - EXTREME REVERSAL (Fire Alert vs Non-Fire vs All)

Universe: 17 Multi-Asset Instruments
  - Indian Equities: NIFTY 50 (^NSEI), BANKNIFTY (^NSEBANK), RELIANCE (RELIANCE.NS),
                     HDFCBANK (HDFCBANK.NS), TCS (TCS.NS), INFY (INFY.NS)
  - Commodities: CRUDE OIL (CL=F), GOLD (GC=F), SILVER (SI=F), NATURAL GAS (NG=F), COPPER (HG=F)
  - Global / FX / Crypto: NASDAQ 100 (^NDX), S&P 500 (^GSPC), EUR/USD (EURUSD=X),
                          GBP/USD (GBPUSD=X), BITCOIN (BTC-USD), ETHEREUM (ETH-USD)

Rules & Methodology:
  - Timeframe: 1-Year Hourly (1h) Continuous Historical Data (Oct 2025 - Oct 2026)
  - Daily Camarilla (H1-H5, L1-L5) & Daily CPR (TC, BC, Pivot, NCPR)
  - Strict H4 / L4 Limit Gating: Longs linked to low < H4, Shorts to high > L4 (Divergences exempt)
  - Symmetrical Neutral Zone Fire_Alert Gate: Fire_Alert = Anysignal and not (Greenzcol or Redzcol)
  - Complete Elimination of Engulfing Trend Limit Candles (highTrendLimitLevel/lowTrendLimitLevel)
  - Pre-TP1 Midpoint Breakeven Trailing SL: 50% midpoint distance moves SL to entry
  - Trailing Targets: TP1 (SL -> BE), TP2 (SL -> TP1), TP3 (SL -> TP2), TP4 (SL -> TP3)
  - Canonical Win Rate Formula: Wins / Total Closed Trades (Breakevens included in denominator)
  - Single Source of Truth exact_pct: ((Exit - Entry) / Entry) * 100
  - VectorBT Metrics: Sharpe, Sortino, Calmar, Max Drawdown, Profit Factor, Kelly Criterion
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import sys
import json
import warnings
import numpy as np
import pandas as pd
import yfinance as yf
import vectorbt as vbt
from datetime import datetime, timezone, timedelta

# Disable vectorbt caching
vbt.settings.caching['enabled'] = False

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
    df['date'] = df.index.date
    daily = df.groupby('date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
    daily_shifted = daily.shift(1)  # Prior day completed levels

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

    # Value Area approximation (rolling 24-period)
    df['VAH'] = tp.rolling(24).mean() + 0.70 * tr.rolling(24).mean()
    df['VAL'] = tp.rolling(24).mean() - 0.70 * tr.rolling(24).mean()

    # Session Bar Counter (Index within day)
    df['session_bar_counter'] = df.groupby('date').cumcount()

    # Rolling 50-bar average candle & body for Extreme Reversal
    df['AverageCandle'] = (h - l).rolling(50).mean().bfill()
    df['AverageBody'] = (c - o).abs().rolling(50).mean().bfill()

    # ════════════════════════════════════════════════════════════════════
    # VERSION 3.0 MOMENTUM ZONES & NEUTRAL FIRE_ALERT GATE
    # ════════════════════════════════════════════════════════════════════
    # Greenzone: PlusDI > MinusDI and EMA13 > EMA32 and DEMA_Fast > DEMA_Slow
    greenzone = (df['PlusDI'] > df['MinusDI']) & (df['EMA13'] > df['EMA32']) & (df['DEMA_FAST'] > df['DEMA_SLOW'])
    # Redzone: MinusDI > PlusDI and EMA13 < EMA32 and DEMA_Fast < DEMA_Slow
    redzone = (df['MinusDI'] > df['PlusDI']) & (df['EMA13'] < df['EMA32']) & (df['DEMA_FAST'] < df['DEMA_SLOW'])

    df['Greenzone'] = greenzone
    df['Redzone'] = redzone
    # Strictly Neutral Zone (Neither Greenzone nor Redzone)
    df['IsInFireZone'] = ~(greenzone | redzone)

    return df


def generate_all_signals_v3(df: pd.DataFrame) -> dict:
    """
    Generates all canonical Version 3.0 strategy triggers with Long & Short:
      - MISSILE
      - SCALP
      - LIGHTNING (native Missile + Scalp confluence)
      - DIVERGENCE (Regular Divergence without ternary trend filter, exempt from H4/L4)
      - HIDDEN DIVERGENCE (CPR / VAH-VAL formation, exempt from H4/L4)
      - EXTREME REVERSAL (Exhaustion reversal with session boundary guard)
    Engulfing candles are completely excluded per user directive.
    """
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
    vah = df['VAH']
    val = df['VAL']
    bar_cnt = df['session_bar_counter']
    avg_candle = df['AverageCandle']
    avg_body = df['AverageBody']
    greenzone = df['Greenzone']
    redzone = df['Redzone']

    # Strict H4/L4 limit touch-point gating for standard setups
    long_allowed = l < h4
    short_allowed = h > l4

    green1 = (plus_di > minus_di) & (m0 > m10)
    red1 = (minus_di > plus_di) & (m0 < m10)

    # 1. DIVERGENCES (RSI 14)
    roll_l10 = l.rolling(10).min()
    roll_h10 = h.rolling(10).max()
    roll_rsi_l10 = rsi.rolling(10).min()
    roll_rsi_h10 = rsi.rolling(10).max()

    # Regular Divergence (D): Ternary directional condition permanently removed
    # Fully exempt from H4/L4 gating
    reg_bull_div = (l <= roll_l10) & (rsi > roll_rsi_l10) & (rsi < 42) & (c > o)
    reg_bear_div = (h >= roll_h10) & (rsi < roll_rsi_h10) & (rsi > 58) & (c < o)

    # Hidden Divergence (H): Gated to formation within CPR or Value Area (VAH/VAL)
    # Fully exempt from H4/L4 gating
    cpr_top = np.maximum(tc, bc)
    cpr_bot = np.minimum(tc, bc)
    vah_top = np.maximum(vah, val)
    val_bot = np.minimum(vah, val)

    in_cpr = (c >= cpr_bot) & (c <= cpr_top)
    in_va = (c >= val_bot) & (c <= vah_top)
    hidden_div_allowed = in_cpr | in_va

    hidden_bull_div = (l > roll_l10.shift(1)) & (rsi <= roll_rsi_l10.shift(1)) & (rsi < 50) & hidden_div_allowed & (c > o)
    hidden_bear_div = (h < roll_h10.shift(1)) & (rsi >= roll_rsi_h10.shift(1)) & (rsi > 50) & hidden_div_allowed & (c < o)

    # 2. EXTREME REVERSAL (With Session Boundary Guard bar_cnt > 0)
    prev_h = h.shift(1)
    prev_l = l.shift(1)
    prev_c = c.shift(1)
    prev_o = o.shift(1)
    prev_rng = prev_h - prev_l

    ext_rev_long = (bar_cnt > 0) & greenzone & (prev_o - prev_c >= 0.75 * prev_rng) & \
                   (prev_rng > 2.0 * avg_candle) & (prev_o - prev_c > avg_body) & (c > o) & (dema_f >= dema_s) & long_allowed

    ext_rev_short = (bar_cnt > 0) & redzone & (prev_c - prev_o >= 0.75 * prev_rng) & \
                    (prev_rng > 2.0 * avg_candle) & (prev_c - prev_o > avg_body) & (o > c) & (dema_f <= dema_s) & short_allowed

    # 3. SCALP: 50% Midpoint Retest & Trend Pullback
    scalp_buy_base = green1 & (l <= ema13) & (c > ema13) & (c > o) & long_allowed
    scalp_sell_base = red1 & (h >= ema13) & (c < ema13) & (c < o) & short_allowed

    # 4. MISSILE: Momentum Breakout above/below Pivot/EMA
    missile_buy_base = (greenzone | (dema_f > dema_s)) & (c > ema13) & (c.shift(1) <= ema13.shift(1)) & (adx > 20) & long_allowed
    missile_sell_base = (redzone | (dema_f < dema_s)) & (c < ema13) & (c.shift(1) >= ema13.shift(1)) & (adx > 20) & short_allowed

    # 5. LIGHTNING: Pure native Missile + Scalp confluence (decoupled from regular divergence per v3.0)
    lightning_long = (missile_buy_base & scalp_buy_base)
    lightning_short = (missile_sell_base & scalp_sell_base)

    # Standalone Divergences (exempt from H4/L4)
    div_long = reg_bull_div & (~lightning_long)
    div_short = reg_bear_div & (~lightning_short)

    hidden_div_long = hidden_bull_div & (~lightning_long) & (~div_long)
    hidden_div_short = hidden_bear_div & (~lightning_short) & (~div_short)

    ext_rev_long_final = ext_rev_long & (~lightning_long) & (~div_long) & (~hidden_div_long)
    ext_rev_short_final = ext_rev_short & (~lightning_short) & (~div_short) & (~hidden_div_short)

    missile_long = missile_buy_base & (~lightning_long) & (~div_long) & (~hidden_div_long) & (~ext_rev_long_final)
    missile_short = missile_sell_base & (~lightning_short) & (~div_short) & (~hidden_div_short) & (~ext_rev_short_final)

    scalp_long = scalp_buy_base & (~lightning_long) & (~missile_long) & (~div_long) & (~hidden_div_long) & (~ext_rev_long_final)
    scalp_short = scalp_sell_base & (~lightning_short) & (~missile_short) & (~div_short) & (~hidden_div_short) & (~ext_rev_short_final)

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


def simulate_trade_execution_with_fire_tag(df: pd.DataFrame, signals: dict, symbol: str, asset_name: str, market_cat: str) -> list:
    """
    Simulates trades with canonical exact_pct math, limit order fills, pre-TP1 midpoint breakeven,
    and accurately tags every trade as FIRE_ALERT (Neutral Zone) or NON_FIRE (Green/Red Zone).
    """
    trades = []
    is_in_fire_zone = df['IsInFireZone']
    greenzone = df['Greenzone']
    redzone = df['Redzone']

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
        hit_midpoint_be = False

        # Fire alert status established at signal trigger bar
        sig_is_fire = False
        sig_fire_zone = 'NEUTRAL'

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

                mid_tp1 = (entry_price + tp1) / 2.0

                if is_long:
                    # Version 1.0 Pre-TP1 Midpoint Breakeven Trailing SL Synchronization Mandate:
                    # Upon reaching or crossing 50% midpoint prior to TP1, SL immediately moved to Entry (Breakeven)
                    if not hit_tp1 and not hit_midpoint_be and cur_h >= mid_tp1:
                        hit_midpoint_be = True
                        sl_price = max(sl_price, entry_price)

                    # Check Stop Loss
                    if cur_l <= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not (hit_tp1 or hit_midpoint_be) else ('BE' if not hit_tp2 else 'TP1')
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
                    # Check TP1 -> SL at Entry (Breakeven)
                    elif cur_h >= tp1 and not hit_tp1:
                        hit_tp1 = True
                        sl_price = entry_price

                else:  # Short
                    if not hit_tp1 and not hit_midpoint_be and cur_l <= mid_tp1:
                        hit_midpoint_be = True
                        sl_price = min(sl_price, entry_price)

                    # Check Stop Loss
                    if cur_h >= sl_price:
                        exit_price = sl_price
                        exit_level = 'SL' if not (hit_tp1 or hit_midpoint_be) else ('BE' if not hit_tp2 else 'TP1')
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
                    # Check TP1 -> SL at Entry (Breakeven)
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
                        'is_fire_alert': sig_is_fire,
                        'fire_zone': sig_fire_zone,
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
                if (i - limit_placed_idx) >= 24:
                    is_limit_pending = False
                else:
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
                        hit_midpoint_be = False
                        continue

            # 3. Check for New Signal Trigger
            if not in_trade and not is_limit_pending:
                if sig_series.iloc[i]:
                    is_limit_pending = True
                    limit_placed_idx = i
                    entry_price = cur_c
                    dist = cur_atr

                    # Confluence Zone evaluated at trigger bar
                    sig_is_fire = bool(is_in_fire_zone.iloc[i])
                    if sig_is_fire:
                        sig_fire_zone = 'NEUTRAL'
                    elif bool(greenzone.iloc[i]):
                        sig_fire_zone = 'GREENZONE'
                    elif bool(redzone.iloc[i]):
                        sig_fire_zone = 'REDZONE'
                    else:
                        sig_fire_zone = 'ZONE'

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


def compute_vbt_metrics(trades: list, freq: str = '1h') -> dict:
    """
    Computes comprehensive VectorBT & Institutional performance metrics adhering to User Rules:
      - Canonical Win Rate: Wins / Total Closed Trades * 100
      - Exact percentage returns
      - VectorBT Returns Accessor integration for Sharpe, Sortino, Calmar, Max Drawdown
      - Profit Factor, Kelly Criterion, Expectancy
    """
    if not trades:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'profit_factor': 0.0, 'net_return': 0.0,
            'expectancy': 0.0, 'avg_win': 0.0, 'avg_loss': 0.0,
            'realized_rr': 0.0, 'max_drawdown': 0.0, 'sharpe': 0.0,
            'sortino': 0.0, 'calmar': 0.0, 'kelly_pct': 0.0,
            'annualized_return': 0.0, 'annualized_vol': 0.0,
            'max_consec_losses': 0
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

    # Kelly Criterion (Half-Kelly)
    kw_dec = win_count / total if total > 0 else 0.0
    kl_dec = loss_count / total if total > 0 else 0.0
    kelly = 0.0
    if realized_rr > 0:
        kelly = max(0.0, ((kw_dec - (kl_dec / realized_rr)) * 100.0) * 0.5)

    # Max Drawdown & Equity Curve
    cum_returns = np.cumsum(returns)
    cum_equity = 100.0 + cum_returns
    running_max = np.maximum.accumulate(cum_equity)
    drawdowns = (running_max - cum_equity) / running_max * 100.0
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    # VectorBT Returns Processing
    # Convert trade returns into chronologically resampled Series for VectorBT Accessor
    try:
        df_trades = pd.DataFrame(trades)
        df_trades['dt'] = pd.to_datetime(df_trades['exit_time'])
        df_trades.set_index('dt', inplace=True)
        df_trades.sort_index(inplace=True)
        # Decimal returns for VectorBT
        dec_returns = (df_trades['exact_pct'] / 100.0).groupby(df_trades.index).sum()

        vbt_ret = dec_returns.vbt.returns(freq=freq)
        sharpe = float(vbt_ret.sharpe_ratio()) if not np.isnan(vbt_ret.sharpe_ratio()) else 0.0
        sortino = float(vbt_ret.sortino_ratio()) if not np.isnan(vbt_ret.sortino_ratio()) else 0.0
        calmar = float(vbt_ret.calmar_ratio()) if not np.isnan(vbt_ret.calmar_ratio()) else 0.0
        ann_ret = float(vbt_ret.annualized()) * 100.0 if not np.isnan(vbt_ret.annualized()) else 0.0
        ann_vol = float(vbt_ret.annualized_volatility()) * 100.0 if not np.isnan(vbt_ret.annualized_volatility()) else 0.0
    except Exception as e:
        # Fallback to standard annualization if vbt returns resample errors
        std_dev = np.std(returns) if len(returns) > 1 else 0.0
        sharpe = float((expectancy / std_dev) * np.sqrt(252)) if std_dev > 0 else 0.0
        downside_losses = [min(0.0, r) for r in returns]
        downside_dev = np.std(downside_losses) if len(downside_losses) > 1 else 0.0
        sortino = float((expectancy / downside_dev) * np.sqrt(252)) if downside_dev > 0 else 0.0
        calmar = (net_return / max_dd) if max_dd > 0 else 0.0
        ann_ret = net_return
        ann_vol = std_dev * np.sqrt(252)

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
        'kelly_pct': round(kelly, 2),
        'max_drawdown': round(max_dd, 2),
        'sharpe': round(sharpe, 2),
        'sortino': round(sortino, 2),
        'calmar': round(calmar, 2),
        'annualized_return': round(ann_ret, 2),
        'annualized_vol': round(ann_vol, 2),
        'max_consec_losses': max_streak
    }


def run_fire_alert_vectorbt_analysis():
    print("=" * 95)
    print("   THE LION CAPITAL SOLUTIONS (TLCS) - VECTORBT FIRE ALERT EDGE ANALYSIS")
    print("   Evaluating Quantitative Confluence Edge: Fire_Alert (Neutral Zone) vs In-Zone Signals")
    print("   Universe: 17 Multi-Asset Instruments | 1-Year Hourly Historical Candles")
    print("=" * 95)

    all_trades = []
    asset_summaries = {}

    for sym, info in TARGET_ASSETS.items():
        ticker = info['ticker']
        print(f"[*] Ingesting & Analyzing {sym:10} ({info['name']}: {ticker})...")
        try:
            df_raw = yf.download(ticker, period='1y', interval='1h', progress=False)
            if df_raw.empty or len(df_raw) < 100:
                print(f"  [!] Insufficient data for {sym}, skipping.")
                continue

            if isinstance(df_raw.columns, pd.MultiIndex):
                df_raw.columns = df_raw.columns.get_level_values(0)

            df_ind = compute_indicators(df_raw)
            sigs = generate_all_signals_v3(df_ind)
            trades = simulate_trade_execution_with_fire_tag(df_ind, sigs, sym, info['name'], info['market'])

            all_trades.extend(trades)

            fire_trades = [t for t in trades if t['is_fire_alert']]
            non_fire_trades = [t for t in trades if not t['is_fire_alert']]

            m_all = compute_vbt_metrics(trades)
            m_fire = compute_vbt_metrics(fire_trades)
            m_non_fire = compute_vbt_metrics(non_fire_trades)

            asset_summaries[sym] = {
                'all': m_all,
                'fire_alert': m_fire,
                'non_fire': m_non_fire
            }

            fire_wr = f"{m_fire['win_rate']:.1f}%" if fire_trades else "N/A"
            fire_pf = f"{m_fire['profit_factor']:.2f}" if fire_trades else "N/A"
            fire_ret = f"{m_fire['net_return']:+.2f}%" if fire_trades else "N/A"
            non_fire_wr = f"{m_non_fire['win_rate']:.1f}%" if non_fire_trades else "N/A"

            print(f"  [✓] {sym:10}: Total={len(trades):3} | FIRE={len(fire_trades):2} (WR={fire_wr}, PF={fire_pf}, Net={fire_ret}) | NON-FIRE={len(non_fire_trades):3} (WR={non_fire_wr})")
        except Exception as e:
            print(f"  [X] Error on {sym}: {e}")

    if not all_trades:
        print("[!] No trades executed across universe.")
        return

    # Filter cohorts
    fire_alert_trades = [t for t in all_trades if t['is_fire_alert']]
    non_fire_trades = [t for t in all_trades if not t['is_fire_alert']]

    # Compute high-level cohorts
    metrics_all = compute_vbt_metrics(all_trades)
    metrics_fire = compute_vbt_metrics(fire_alert_trades)
    metrics_non_fire = compute_vbt_metrics(non_fire_trades)

    print("\n" + "=" * 95)
    print("   HEAD-TO-HEAD VECTORBT PERFORMANCE: FIRE_ALERT VS IN-ZONE VS ALL SIGNALS")
    print("=" * 95)

    head_to_head = [
        {
            'Cohort': '🔥 FIRE_ALERT (NEUTRAL ZONE)',
            'Trades': metrics_fire['total_trades'],
            'W / L / BE': f"{metrics_fire['wins']} / {metrics_fire['losses']} / {metrics_fire['breakevens']}",
            'Win Rate': f"{metrics_fire['win_rate']:.2f}%",
            'Profit Factor': f"{metrics_fire['profit_factor']:.2f}",
            'Net Return': f"{metrics_fire['net_return']:+.2f}%",
            'Expectancy': f"{metrics_fire['expectancy']:+.3f}%",
            'Realized R:R': f"{metrics_fire['realized_rr']:.2f}R",
            'Max DD': f"-{metrics_fire['max_drawdown']:.2f}%",
            'Sharpe': f"{metrics_fire['sharpe']:.2f}",
            'Sortino': f"{metrics_fire['sortino']:.2f}",
            'Calmar': f"{metrics_fire['calmar']:.2f}",
            'Kelly %': f"{metrics_fire['kelly_pct']:.2f}%",
            'Max Losses': f"{metrics_fire['max_consec_losses']}"
        },
        {
            'Cohort': '⚡ IN-ZONE (GREEN/RED ZONES)',
            'Trades': metrics_non_fire['total_trades'],
            'W / L / BE': f"{metrics_non_fire['wins']} / {metrics_non_fire['losses']} / {metrics_non_fire['breakevens']}",
            'Win Rate': f"{metrics_non_fire['win_rate']:.2f}%",
            'Profit Factor': f"{metrics_non_fire['profit_factor']:.2f}",
            'Net Return': f"{metrics_non_fire['net_return']:+.2f}%",
            'Expectancy': f"{metrics_non_fire['expectancy']:+.3f}%",
            'Realized R:R': f"{metrics_non_fire['realized_rr']:.2f}R",
            'Max DD': f"-{metrics_non_fire['max_drawdown']:.2f}%",
            'Sharpe': f"{metrics_non_fire['sharpe']:.2f}",
            'Sortino': f"{metrics_non_fire['sortino']:.2f}",
            'Calmar': f"{metrics_non_fire['calmar']:.2f}",
            'Kelly %': f"{metrics_non_fire['kelly_pct']:.2f}%",
            'Max Losses': f"{metrics_non_fire['max_consec_losses']}"
        },
        {
            'Cohort': '🌐 ALL SIGNALS (UNFILTERED)',
            'Trades': metrics_all['total_trades'],
            'W / L / BE': f"{metrics_all['wins']} / {metrics_all['losses']} / {metrics_all['breakevens']}",
            'Win Rate': f"{metrics_all['win_rate']:.2f}%",
            'Profit Factor': f"{metrics_all['profit_factor']:.2f}",
            'Net Return': f"{metrics_all['net_return']:+.2f}%",
            'Expectancy': f"{metrics_all['expectancy']:+.3f}%",
            'Realized R:R': f"{metrics_all['realized_rr']:.2f}R",
            'Max DD': f"-{metrics_all['max_drawdown']:.2f}%",
            'Sharpe': f"{metrics_all['sharpe']:.2f}",
            'Sortino': f"{metrics_all['sortino']:.2f}",
            'Calmar': f"{metrics_all['calmar']:.2f}",
            'Kelly %': f"{metrics_all['kelly_pct']:.2f}%",
            'Max Losses': f"{metrics_all['max_consec_losses']}"
        }
    ]
    df_h2h = pd.DataFrame(head_to_head)
    print(df_h2h.to_string(index=False))

    # Calculate Edge Delta
    wr_edge = metrics_fire['win_rate'] - metrics_non_fire['win_rate']
    pf_edge = metrics_fire['profit_factor'] - metrics_non_fire['profit_factor']
    exp_edge = metrics_fire['expectancy'] - metrics_non_fire['expectancy']
    dd_edge = metrics_non_fire['max_drawdown'] - metrics_fire['max_drawdown']  # positive = lower DD
    sharpe_edge = metrics_fire['sharpe'] - metrics_non_fire['sharpe']
    sortino_edge = metrics_fire['sortino'] - metrics_non_fire['sortino']

    print("\n" + "─" * 95)
    print(f"🔥 STATISTICAL CONFLUENCE EDGE OF FIRE_ALERT (VS IN-ZONE SIGNALS):")
    print(f"   • Win Rate Edge:        {wr_edge:+.2f}% percentage points")
    print(f"   • Profit Factor Edge:   {pf_edge:+.2f} ({metrics_fire['profit_factor']} vs {metrics_non_fire['profit_factor']})")
    print(f"   • Expectancy per Trade: {exp_edge:+.3f}% return advantage per fill")
    print(f"   • Risk Management:      Drawdown reduced by {dd_edge:.2f}% (-{metrics_fire['max_drawdown']}% vs -{metrics_non_fire['max_drawdown']}%)")
    print(f"   • Sharpe Ratio Edge:    {sharpe_edge:+.2f} ({metrics_fire['sharpe']} vs {metrics_non_fire['sharpe']})")
    print(f"   • Sortino Ratio Edge:   {sortino_edge:+.2f} ({metrics_fire['sortino']} vs {metrics_non_fire['sortino']})")
    print("─" * 95)

    # ═══════════════════════════════════════════════════════
    # PART 2: BREAKDOWN BY CANONICAL SIGNAL FAMILY
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 95)
    print("   PART 2: CANONICAL SIGNAL FAMILY BREAKDOWN (FIRE_ALERT VS IN-ZONE)")
    print("=" * 95)

    signal_families = ['MISSILE', 'SCALP', 'LIGHTNING', 'DIVERGENCE', 'HIDDEN DIVERGENCE', 'EXTREME REVERSAL']
    family_breakdown = {}
    family_table_rows = []

    for fam in signal_families:
        fam_all = [t for t in all_trades if t['base_type'] == fam]
        fam_fire = [t for t in all_trades if t['base_type'] == fam and t['is_fire_alert']]
        fam_non = [t for t in all_trades if t['base_type'] == fam and not t['is_fire_alert']]

        m_f_all = compute_vbt_metrics(fam_all)
        m_f_fire = compute_vbt_metrics(fam_fire)
        m_f_non = compute_vbt_metrics(fam_non)

        family_breakdown[fam] = {
            'all': m_f_all,
            'fire_alert': m_f_fire,
            'non_fire': m_f_non
        }

        family_table_rows.append({
            'Signal Family': fam,
            'Category': '🔥 FIRE_ALERT',
            'Trades': m_f_fire['total_trades'],
            'Win Rate': f"{m_f_fire['win_rate']:.1f}%",
            'PF': f"{m_f_fire['profit_factor']:.2f}",
            'Net Return': f"{m_f_fire['net_return']:+.2f}%",
            'Expectancy': f"{m_f_fire['expectancy']:+.3f}%",
            'Max DD': f"-{m_f_fire['max_drawdown']:.2f}%",
            'Sharpe': f"{m_f_fire['sharpe']:.2f}"
        })
        family_table_rows.append({
            'Signal Family': fam,
            'Category': '⚡ IN-ZONE',
            'Trades': m_f_non['total_trades'],
            'Win Rate': f"{m_f_non['win_rate']:.1f}%",
            'PF': f"{m_f_non['profit_factor']:.2f}",
            'Net Return': f"{m_f_non['net_return']:+.2f}%",
            'Expectancy': f"{m_f_non['expectancy']:+.3f}%",
            'Max DD': f"-{m_f_non['max_drawdown']:.2f}%",
            'Sharpe': f"{m_f_non['sharpe']:.2f}"
        })
        family_table_rows.append({
            'Signal Family': fam,
            'Category': '🌐 ALL',
            'Trades': m_f_all['total_trades'],
            'Win Rate': f"{m_f_all['win_rate']:.1f}%",
            'PF': f"{m_f_all['profit_factor']:.2f}",
            'Net Return': f"{m_f_all['net_return']:+.2f}%",
            'Expectancy': f"{m_f_all['expectancy']:+.3f}%",
            'Max DD': f"-{m_f_all['max_drawdown']:.2f}%",
            'Sharpe': f"{m_f_all['sharpe']:.2f}"
        })

    print(pd.DataFrame(family_table_rows).to_string(index=False))

    # ═══════════════════════════════════════════════════════
    # PART 3: DIRECTIONAL BREAKDOWN (LONG VS SHORT FIRE_ALERT)
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 95)
    print("   PART 3: DIRECTIONAL AUDIT (LONG FIRE_ALERT VS SHORT FIRE_ALERT)")
    print("=" * 95)

    long_fire = [t for t in fire_alert_trades if t['direction'] == 'LONG']
    short_fire = [t for t in fire_alert_trades if t['direction'] == 'SHORT']
    long_non = [t for t in non_fire_trades if t['direction'] == 'LONG']
    short_non = [t for t in non_fire_trades if t['direction'] == 'SHORT']

    m_long_fire = compute_vbt_metrics(long_fire)
    m_short_fire = compute_vbt_metrics(short_fire)
    m_long_non = compute_vbt_metrics(long_non)
    m_short_non = compute_vbt_metrics(short_non)

    directional_table = [
        {'Direction': '🟢 LONG FIRE_ALERT', 'Trades': m_long_fire['total_trades'], 'Win Rate': f"{m_long_fire['win_rate']:.1f}%", 'PF': f"{m_long_fire['profit_factor']:.2f}", 'Net Return': f"{m_long_fire['net_return']:+.2f}%", 'Expectancy': f"{m_long_fire['expectancy']:+.3f}%", 'Sharpe': f"{m_long_fire['sharpe']:.2f}"},
        {'Direction': '🟢 LONG IN-ZONE', 'Trades': m_long_non['total_trades'], 'Win Rate': f"{m_long_non['win_rate']:.1f}%", 'PF': f"{m_long_non['profit_factor']:.2f}", 'Net Return': f"{m_long_non['net_return']:+.2f}%", 'Expectancy': f"{m_long_non['expectancy']:+.3f}%", 'Sharpe': f"{m_long_non['sharpe']:.2f}"},
        {'Direction': '🔴 SHORT FIRE_ALERT', 'Trades': m_short_fire['total_trades'], 'Win Rate': f"{m_short_fire['win_rate']:.1f}%", 'PF': f"{m_short_fire['profit_factor']:.2f}", 'Net Return': f"{m_short_fire['net_return']:+.2f}%", 'Expectancy': f"{m_short_fire['expectancy']:+.3f}%", 'Sharpe': f"{m_short_fire['sharpe']:.2f}"},
        {'Direction': '🔴 SHORT IN-ZONE', 'Trades': m_short_non['total_trades'], 'Win Rate': f"{m_short_non['win_rate']:.1f}%", 'PF': f"{m_short_non['profit_factor']:.2f}", 'Net Return': f"{m_short_non['net_return']:+.2f}%", 'Expectancy': f"{m_short_non['expectancy']:+.3f}%", 'Sharpe': f"{m_short_non['sharpe']:.2f}"}
    ]
    print(pd.DataFrame(directional_table).to_string(index=False))

    # ═══════════════════════════════════════════════════════
    # PART 4: ASSET CLASS / SECTOR BREAKDOWN
    # ═══════════════════════════════════════════════════════
    print("\n" + "=" * 95)
    print("   PART 4: ASSET CLASS / SECTOR BREAKDOWN")
    print("=" * 95)

    sectors = ['Indian Equities', 'Commodities', 'Global / FX / Crypto']
    sector_table = []
    sector_breakdown = {}

    for s in sectors:
        s_fire = [t for t in fire_alert_trades if t['market'] == s]
        s_non = [t for t in non_fire_trades if t['market'] == s]
        s_all = [t for t in all_trades if t['market'] == s]

        m_s_fire = compute_vbt_metrics(s_fire)
        m_s_non = compute_vbt_metrics(s_non)
        m_s_all = compute_vbt_metrics(s_all)

        sector_breakdown[s] = {
            'all': m_s_all,
            'fire_alert': m_s_fire,
            'non_fire': m_s_non
        }

        sector_table.append({
            'Market Sector': s,
            'FIRE Trades': m_s_fire['total_trades'],
            'FIRE WR': f"{m_s_fire['win_rate']:.1f}%",
            'FIRE PF': f"{m_s_fire['profit_factor']:.2f}",
            'FIRE Net': f"{m_s_fire['net_return']:+.2f}%",
            'NON-FIRE Trades': m_s_non['total_trades'],
            'NON-FIRE WR': f"{m_s_non['win_rate']:.1f}%",
            'NON-FIRE PF': f"{m_s_non['profit_factor']:.2f}",
            'NON-FIRE Net': f"{m_s_non['net_return']:+.2f}%"
        })

    print(pd.DataFrame(sector_table).to_string(index=False))

    # Save output to JSON
    output_payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'period': '1 Year (Oct 20, 2025 - Oct 20, 2026)',
        'head_to_head': {
            'fire_alert': metrics_fire,
            'in_zone': metrics_non_fire,
            'all_signals': metrics_all,
            'edge_delta': {
                'win_rate_edge': round(wr_edge, 2),
                'profit_factor_edge': round(pf_edge, 2),
                'expectancy_edge': round(exp_edge, 3),
                'drawdown_reduction': round(dd_edge, 2),
                'sharpe_edge': round(sharpe_edge, 2),
                'sortino_edge': round(sortino_edge, 2)
            }
        },
        'by_signal_family': family_breakdown,
        'by_direction': {
            'long_fire': m_long_fire,
            'short_fire': m_short_fire,
            'long_non_fire': m_long_non,
            'short_non_fire': m_short_non
        },
        'by_sector': sector_breakdown,
        'by_asset': asset_summaries,
        'sample_fire_trades': fire_alert_trades[:25]
    }

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fire_alert_vectorbt_edge_results.json')
    with open(out_file, 'w') as f:
        json.dump(output_payload, f, indent=2)
    print(f"\n[✓] Fire Alert VectorBT Edge results successfully saved to: {out_file}")

    return output_payload


if __name__ == '__main__':
    run_fire_alert_vectorbt_analysis()
