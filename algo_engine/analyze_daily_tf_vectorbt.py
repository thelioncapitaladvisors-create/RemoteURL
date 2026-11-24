"""
TLCS Version 5.0: VectorBT Daily (1D Swing) Quantitative Performance Analysis
=============================================================================
Evaluates the 5 Canonical Core Swing Execution Strategies on Daily (1D) OHLC candles
anchored to Weekly Multi-Timeframe Framework (Weekly CPR, Value Area, Camarilla):
  1. Missile (Breakout through Weekly CPR boundaries)
  2. Scalp (Pullback bounce / retest of Weekly Central Pivot WP)
  3. Lightning (Confluence of Missile + Scalp)
  4. Extreme Reversal (Bollinger Band extreme exhaustion rejection)
  5. Regular Divergence (Zigzag swing mean reversion divergence with RSI)
  6. Hidden Divergence (Trend continuation divergence with Weekly CPR/VA spatial gating)
  7. Confluence Setups (Core Trend + Divergence within 5 days)

Regime Rules:
  - Divergence Signals: DIV_SL_0.5_AVG10 (Confirmation bar midpoint touch entry + SL at D/H candle extreme ± 0.5 * AvgCandleSize10)
  - Core Trend Signals: CORE_SL_BAR_EXTREME (Option B: Signal bar extreme ± 0.50 * ATR)
  - Weekly Framework: CPR, Camarilla, and Value Area calculated strictly from completed prior week (W-1)
  - Symmetrical DMI Directional Momentum Gating:
      Long: not (minus > plus)  /  Short: not (plus > minus)
  - Trade Management:
      TP1=1*ATR, TP2=2*ATR, TP3=3*ATR, TP4=4*ATR
      Breakeven at 50% midpoint between TP1 and TP2 (1.5*ATR)
      At TP3: SL moves to TP2
      At TP4: SL moves to TP3
      Post-TP4: 32-EMA trailing SL with TP3 protective floor

Dataset: 22,469 Daily Bars across 17 Multi-Asset Instruments over 5 Years (2021-2026)
"""

import os
os.environ["NUMBA_DISABLE_CACHING"] = "1"
import sys
import json
import numpy as np
import pandas as pd
import vectorbt as vbt
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

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


def load_daily_data(symbol: str) -> pd.DataFrame:
    file_path = os.path.join(CACHE_DIR, f"{symbol}_5y_1d.parquet")
    if not os.path.exists(file_path):
        return None
    df = pd.read_parquet(file_path)
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df = df.set_index('Datetime')
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # Normalize index to timezone-naive
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df


def compute_weekly_framework(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Weekly CPR, Camarilla, and Value Area from completed prior weeks (W-1).
    Aligns with Pine Script:
    [wHigh1, wLow1, wClose1] = request.security(syminfo.tickerid, 'W', [high[1], low[1], close[1]])
    """
    df = df.copy()

    # Resample daily data to calendar weekly (W-SUN or W-FRI)
    weekly = df.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

    # Prior week levels (shift 1 week forward so bar in week W sees W-1)
    w_high1 = weekly['High'].shift(1)
    w_low1 = weekly['Low'].shift(1)
    w_close1 = weekly['Close'].shift(1)

    # Weekly CPR
    w_p = (w_high1 + w_low1 + w_close1) / 3.0
    w_bc = (w_high1 + w_low1) / 2.0
    w_tc = (w_p - w_bc) + w_p
    w_top_cpr = np.maximum(w_tc, w_bc)
    w_bot_cpr = np.minimum(w_tc, w_bc)

    # Weekly Camarilla
    w_range = np.maximum(w_high1 - w_low1, 0.0001)
    w_h4 = w_close1 + w_range * 1.1 / 2.0
    w_l4 = w_close1 - w_range * 1.1 / 2.0
    w_h3 = w_close1 + w_range * 1.1 / 4.0
    w_l3 = w_close1 - w_range * 1.1 / 4.0

    # Weekly Value Area (68% TPO model)
    w_va_half = w_range * 0.68 / 2.0
    w_vah = np.minimum(w_p + w_va_half, w_high1)
    w_val = np.maximum(w_p - w_va_half, w_low1)

    weekly_levels = pd.DataFrame({
        'wHigh1': w_high1,
        'wLow1': w_low1,
        'wClose1': w_close1,
        'wP': w_p,
        'wTC': w_tc,
        'wBC': w_bc,
        'wTopCPR': w_top_cpr,
        'wBotCPR': w_bot_cpr,
        'wH4': w_h4,
        'wL4': w_l4,
        'wH3': w_h3,
        'wL3': w_l3,
        'wVAH': w_vah,
        'wVAL': w_val
    }, index=weekly.index)

    # Reindex and forward-fill to daily dates
    # We reindex to daily dates using asof or reindex + ffill
    daily_weekly = weekly_levels.reindex(df.index, method='ffill')
    for col in daily_weekly.columns:
        df[col] = daily_weekly[col]

    return df


def compute_daily_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    h = df['High']
    l = df['Low']
    c = df['Close']
    o = df['Open']

    # Trend EMAs (13 & 32)
    df['EMA13'] = c.ewm(span=13, adjust=False).mean()
    df['EMA32'] = c.ewm(span=32, adjust=False).mean()
    df['emaCanBuy'] = (c > df['EMA13']) & (df['EMA13'] > df['EMA32'])
    df['emaCanSell'] = (c < df['EMA13']) & (df['EMA13'] < df['EMA32'])

    # True Range & ATR(14)
    tr1 = h - l
    tr2 = (h - c.shift(1)).abs()
    tr3 = (l - c.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean().bfill()
    df['AvgCandleSize10'] = (h - l).rolling(window=10).mean().bfill()

    # DMI (14)
    up_move = h - h.shift(1)
    down_move = l.shift(1) - l
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    df['PlusDI'] = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])
    df['MinusDI'] = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, adjust=False).mean() / df['ATR'])

    # Bollinger Bands (20, 2.0)
    bb_basis = c.rolling(window=20).mean()
    bb_dev = 2.0 * c.rolling(window=20).std()
    df['BBUpper'] = bb_basis + bb_dev
    df['BBLower'] = bb_basis - bb_dev

    # RSI(14)
    delta = c.diff()
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = pd.Series(gain, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    avg_loss = pd.Series(loss, index=df.index).ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

    # Zigzag / Local Extremes for Divergence (lookback = 5)
    df['SwingHigh'] = (h == h.rolling(window=11, center=True).max())
    df['SwingLow'] = (l == l.rolling(window=11, center=True).min())

    return df


def generate_daily_signals(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Generates authentic Daily Timeframe Swing signals aligned with TLCS_Daily_TF_Indicator.pine
    """
    h = df['High']
    l = df['Low']
    c = df['Close']
    o = df['Open']
    plus = df['PlusDI']
    minus = df['MinusDI']
    rsi = df['RSI']

    w_top_cpr = df['wTopCPR']
    w_bot_cpr = df['wBotCPR']
    w_p = df['wP']
    w_vah = df['wVAH']
    w_val = df['wVAL']
    ema_can_buy = df['emaCanBuy']
    ema_can_sell = df['emaCanSell']
    bb_lower = df['BBLower']
    bb_upper = df['BBUpper']

    # 1. MISSILE
    # MissileBuy  = close > open and low < wTopCPR and close > wTopCPR and emaCanBuy and (plus >= minus)
    # MissileSell = close < open and high > wBotCPR and close < wBotCPR and emaCanSell and (minus >= plus)
    missile_buy = (c > o) & (l < w_top_cpr) & (c > w_top_cpr) & ema_can_buy & (plus >= minus)
    missile_sell = (c < o) & (h > w_bot_cpr) & (c < w_bot_cpr) & ema_can_sell & (minus >= plus)

    # 2. SCALP
    # ScalpBuy  = close > open and low <= wP and close > wP and emaCanBuy and (plus >= minus)
    # ScalpSell = close < open and high >= wP and close < wP and emaCanSell and (minus >= plus)
    scalp_buy = (c > o) & (l <= w_p) & (c > w_p) & ema_can_buy & (plus >= minus)
    scalp_sell = (c < o) & (h >= w_p) & (c < w_p) & ema_can_sell & (minus >= plus)

    # 3. LIGHTNING
    lightning_buy = missile_buy & scalp_buy
    lightning_sell = missile_sell & scalp_sell

    # Isolated (Just) Missile and Scalp
    just_missile_buy = missile_buy & (~lightning_buy)
    just_missile_sell = missile_sell & (~lightning_sell)
    just_scalp_buy = scalp_buy & (~lightning_buy)
    just_scalp_sell = scalp_sell & (~lightning_sell)

    # 4. EXTREME REVERSAL
    # ExtremeReversalBuy  = low < bbLower and close > open and close > bbLower and not (minus > plus)
    # ExtremeReversalSell = high > bbUpper and close < open and close < bbUpper and not (plus > minus)
    ext_rev_buy = (l < bb_lower) & (c > o) & (c > bb_lower) & (~(minus > plus))
    ext_rev_sell = (h > bb_upper) & (c < o) & (c < bb_upper) & (~(plus > minus))

    # 5. DIVERGENCE (Regular & Hidden)
    n = len(df)
    reg_bull = pd.Series(False, index=df.index)
    reg_bear = pd.Series(False, index=df.index)
    hidden_bull = pd.Series(False, index=df.index)
    hidden_bear = pd.Series(False, index=df.index)

    div_low = pd.Series(np.nan, index=df.index)
    div_high = pd.Series(np.nan, index=df.index)

    lows_idx = df.index[df['SwingLow']].tolist()
    highs_idx = df.index[df['SwingHigh']].tolist()

    # Bullish Divergences on Lows
    for i in range(1, len(lows_idx)):
        prev_idx = lows_idx[i-1]
        curr_idx = lows_idx[i]
        bar_dist = df.index.get_loc(curr_idx) - df.index.get_loc(prev_idx)
        if 3 <= bar_dist <= 35:
            p_prev, p_curr = df.loc[prev_idx, 'Low'], df.loc[curr_idx, 'Low']
            r_prev, r_curr = df.loc[prev_idx, 'RSI'], df.loc[curr_idx, 'RSI']

            # Regular Bullish Div: Lower Low in Price, Higher Low in RSI
            if p_curr < p_prev and r_curr > r_prev:
                # Find confirmation candle within 1-5 bars of curr_idx
                curr_loc = df.index.get_loc(curr_idx)
                for step in range(1, 6):
                    if curr_loc + step < n:
                        c_idx = df.index[curr_loc + step]
                        # Confirmation: close > open and close > close[1] and not (minus > plus)
                        if df.loc[c_idx, 'Close'] > df.loc[c_idx, 'Open'] and df.loc[c_idx, 'Close'] > df.loc[df.index[curr_loc + step - 1], 'Close'] and not (df.loc[c_idx, 'MinusDI'] > df.loc[c_idx, 'PlusDI']):
                            reg_bull.loc[c_idx] = True
                            div_low.loc[c_idx] = p_curr
                            break

            # Hidden Bullish Div: Higher Low in Price, Lower Low in RSI
            elif p_curr > p_prev and r_curr < r_prev:
                # Spatial gating: must form touching CPR or within Value Area
                cpr_b = min(df.loc[curr_idx, 'wTopCPR'], df.loc[curr_idx, 'wBotCPR'])
                cpr_t = max(df.loc[curr_idx, 'wTopCPR'], df.loc[curr_idx, 'wBotCPR'])
                val_l = min(df.loc[curr_idx, 'wVAH'], df.loc[curr_idx, 'wVAL'])
                vah_t = max(df.loc[curr_idx, 'wVAH'], df.loc[curr_idx, 'wVAL'])
                in_cpr = (p_curr >= cpr_b) and (p_curr <= cpr_t)
                in_va = (p_curr >= val_l) and (p_curr <= vah_t)

                if in_cpr or in_va:
                    curr_loc = df.index.get_loc(curr_idx)
                    for step in range(1, 6):
                        if curr_loc + step < n:
                            c_idx = df.index[curr_loc + step]
                            if df.loc[c_idx, 'Close'] > df.loc[c_idx, 'Open'] and df.loc[c_idx, 'Close'] > df.loc[df.index[curr_loc + step - 1], 'Close'] and not (df.loc[c_idx, 'MinusDI'] > df.loc[c_idx, 'PlusDI']):
                                hidden_bull.loc[c_idx] = True
                                div_low.loc[c_idx] = p_curr
                                break

    # Bearish Divergences on Highs
    for i in range(1, len(highs_idx)):
        prev_idx = highs_idx[i-1]
        curr_idx = highs_idx[i]
        bar_dist = df.index.get_loc(curr_idx) - df.index.get_loc(prev_idx)
        if 3 <= bar_dist <= 35:
            p_prev, p_curr = df.loc[prev_idx, 'High'], df.loc[curr_idx, 'High']
            r_prev, r_curr = df.loc[prev_idx, 'RSI'], df.loc[curr_idx, 'RSI']

            # Regular Bearish Div: Higher High in Price, Lower High in RSI
            if p_curr > p_prev and r_curr < r_prev:
                curr_loc = df.index.get_loc(curr_idx)
                for step in range(1, 6):
                    if curr_loc + step < n:
                        c_idx = df.index[curr_loc + step]
                        if df.loc[c_idx, 'Close'] < df.loc[c_idx, 'Open'] and df.loc[c_idx, 'Close'] < df.loc[df.index[curr_loc + step - 1], 'Close'] and not (df.loc[c_idx, 'PlusDI'] > df.loc[c_idx, 'MinusDI']):
                            reg_bear.loc[c_idx] = True
                            div_high.loc[c_idx] = p_curr
                            break

            # Hidden Bearish Div: Lower High in Price, Higher High in RSI
            elif p_curr < p_prev and r_curr > r_prev:
                cpr_b = min(df.loc[curr_idx, 'wTopCPR'], df.loc[curr_idx, 'wBotCPR'])
                cpr_t = max(df.loc[curr_idx, 'wTopCPR'], df.loc[curr_idx, 'wBotCPR'])
                val_l = min(df.loc[curr_idx, 'wVAH'], df.loc[curr_idx, 'wVAL'])
                vah_t = max(df.loc[curr_idx, 'wVAH'], df.loc[curr_idx, 'wVAL'])
                in_cpr = (p_curr >= cpr_b) and (p_curr <= cpr_t)
                in_va = (p_curr >= val_l) and (p_curr <= vah_t)

                if in_cpr or in_va:
                    curr_loc = df.index.get_loc(curr_idx)
                    for step in range(1, 6):
                        if curr_loc + step < n:
                            c_idx = df.index[curr_loc + step]
                            if df.loc[c_idx, 'Close'] < df.loc[c_idx, 'Open'] and df.loc[c_idx, 'Close'] < df.loc[df.index[curr_loc + step - 1], 'Close'] and not (df.loc[c_idx, 'PlusDI'] > df.loc[c_idx, 'MinusDI']):
                                hidden_bear.loc[c_idx] = True
                                div_high.loc[c_idx] = p_curr
                                break

    df['div_low'] = div_low
    df['div_high'] = div_high

    return {
        'LONG MISSILE': just_missile_buy,
        'SHORT MISSILE': just_missile_sell,
        'LONG MISSILE_ALL': missile_buy,
        'SHORT MISSILE_ALL': missile_sell,
        'LONG SCALP': just_scalp_buy,
        'SHORT SCALP': just_scalp_sell,
        'LONG SCALP_ALL': scalp_buy,
        'SHORT SCALP_ALL': scalp_sell,
        'LONG LIGHTNING': lightning_buy,
        'SHORT LIGHTNING': lightning_sell,
        'LONG EXTREME REVERSAL': ext_rev_buy,
        'SHORT EXTREME REVERSAL': ext_rev_sell,
        'LONG REGULAR DIV': reg_bull,
        'SHORT REGULAR DIV': reg_bear,
        'LONG HIDDEN DIV': hidden_bull,
        'SHORT HIDDEN DIV': hidden_bear
    }


def simulate_daily_trades(df: pd.DataFrame, signals: Dict[str, pd.Series], max_holding_days: int = 40) -> list:
    """
    Executes bar-by-bar trade simulation on Daily TF:
    - Divergence: Midpoint touch entry + DIV_SL_0.5_AVG10
    - Core Trend: Signal bar close entry + Option B (CORE_SL_BAR_EXTREME)
    - Full multi-target and trailing SL logic
    """
    trades = []
    n = len(df)
    c = df['Close'].values
    h = df['High'].values
    l = df['Low'].values
    o = df['Open'].values
    atr = df['ATR'].values
    avg_size = df['AvgCandleSize10'].values
    dates = df.index

    for sig_name, sig_series in signals.items():
        is_long = 'LONG' in sig_name
        is_div = 'DIV' in sig_name
        sig_indices = np.where(sig_series.values)[0]

        for s_idx in sig_indices:
            if s_idx >= n - 1:
                continue

            atr_val = atr[s_idx]
            avg_size_val = avg_size[s_idx]

            # 1. Determine Entry & Initial SL
            if is_div:
                # Midpoint limit entry
                entry_lvl = round((h[s_idx] + l[s_idx]) / 2.0, 4)
                if is_long:
                    div_ext = df['div_low'].iloc[s_idx]
                    if np.isnan(div_ext):
                        div_ext = l[s_idx]
                    sl_lvl = round(div_ext - 0.5 * avg_size_val, 4)
                else:
                    div_ext = df['div_high'].iloc[s_idx]
                    if np.isnan(div_ext):
                        div_ext = h[s_idx]
                    sl_lvl = round(div_ext + 0.5 * avg_size_val, 4)

                # Wait for touch fill on future candles
                fill_idx = None
                for future_idx in range(s_idx + 1, min(s_idx + 10, n)):
                    # Check if SL hit before fill -> cancelled
                    if is_long and l[future_idx] <= sl_lvl:
                        break
                    if (not is_long) and h[future_idx] >= sl_lvl:
                        break

                    # Check touch fill
                    if is_long and l[future_idx] <= entry_lvl:
                        fill_idx = future_idx
                        break
                    elif (not is_long) and h[future_idx] >= entry_lvl:
                        fill_idx = future_idx
                        break

                if fill_idx is None:
                    continue  # Limit order never filled

                entry_idx = fill_idx
                entry_price = entry_lvl

            else:
                # Core Trend Signal: enters on next bar open (or current close)
                entry_idx = s_idx + 1
                entry_price = o[entry_idx]
                # Option B: Signal bar extreme ± 0.50 * ATR
                if is_long:
                    sl_lvl = round(l[s_idx] - 0.50 * atr_val, 4)
                else:
                    sl_lvl = round(h[s_idx] + 0.50 * atr_val, 4)

            # Targets mathematically extended from entry
            if is_long:
                tp1 = entry_price + 1.0 * atr_val
                tp2 = entry_price + 2.0 * atr_val
                tp3 = entry_price + 3.0 * atr_val
                tp4 = entry_price + 4.0 * atr_val
                mid_be = entry_price + 1.5 * atr_val
            else:
                tp1 = entry_price - 1.0 * atr_val
                tp2 = entry_price - 2.0 * atr_val
                tp3 = entry_price - 3.0 * atr_val
                tp4 = entry_price - 4.0 * atr_val
                mid_be = entry_price - 1.5 * atr_val

            current_sl = sl_lvl
            hit_tp1 = False
            hit_tp2 = False
            hit_tp3 = False
            hit_tp4 = False
            hit_be = False

            outcome = None
            exit_price = None
            exit_idx = None

            # Bar-by-bar progression
            for curr in range(entry_idx, min(entry_idx + max_holding_days, n)):
                bar_h = h[curr]
                bar_l = l[curr]
                bar_c = c[curr]
                bar_o = o[curr]

                if is_long:
                    # Check SL hit
                    if bar_l <= current_sl:
                        outcome = 'BREAKEVEN' if hit_be and abs(current_sl - entry_price) < 1e-4 else 'LOSS'
                        exit_price = min(current_sl, bar_o)
                        exit_idx = curr
                        break

                    # Check Target progression
                    if bar_h >= mid_be and not hit_be:
                        hit_be = True
                        current_sl = entry_price  # Move SL to Breakeven

                    if bar_h >= tp3 and not hit_tp3:
                        hit_tp3 = True
                        current_sl = max(current_sl, tp2)

                    if bar_h >= tp4 and not hit_tp4:
                        hit_tp4 = True
                        current_sl = max(current_sl, tp3)

                    # Post TP4 trailing stop: 32-EMA
                    if hit_tp4:
                        ema32_val = df['EMA32'].iloc[curr]
                        current_sl = max(current_sl, ema32_val)

                    # Win by hitting TP1+
                    if bar_h >= tp1:
                        hit_tp1 = True

                else: # Short trade
                    # Check SL hit
                    if bar_h >= current_sl:
                        outcome = 'BREAKEVEN' if hit_be and abs(current_sl - entry_price) < 1e-4 else 'LOSS'
                        exit_price = max(current_sl, bar_o)
                        exit_idx = curr
                        break

                    # Check Target progression
                    if bar_l <= mid_be and not hit_be:
                        hit_be = True
                        current_sl = entry_price

                    if bar_l <= tp3 and not hit_tp3:
                        hit_tp3 = True
                        current_sl = min(current_sl, tp2)

                    if bar_l <= tp4 and not hit_tp4:
                        hit_tp4 = True
                        current_sl = min(current_sl, tp3)

                    if hit_tp4:
                        ema32_val = df['EMA32'].iloc[curr]
                        current_sl = min(current_sl, ema32_val)

                    if bar_l <= tp1:
                        hit_tp1 = True

            # If trade didn't exit by SL within max holding days
            if outcome is None:
                exit_idx = min(entry_idx + max_holding_days - 1, n - 1)
                exit_price = c[exit_idx]
                if is_long:
                    outcome = 'WIN' if exit_price > entry_price else ('BREAKEVEN' if abs(exit_price - entry_price) < 1e-4 else 'LOSS')
                else:
                    outcome = 'WIN' if exit_price < entry_price else ('BREAKEVEN' if abs(exit_price - entry_price) < 1e-4 else 'LOSS')

            if is_long:
                pct = ((exit_price - entry_price) / entry_price) * 100.0
            else:
                pct = ((entry_price - exit_price) / entry_price) * 100.0

            if outcome == 'LOSS' and pct > 0:
                outcome = 'WIN'
            elif outcome == 'WIN' and pct < 0:
                outcome = 'LOSS'

            trades.append({
                'signal': sig_name,
                'is_long': is_long,
                'entry_idx': entry_idx,
                'entry_date': dates[entry_idx],
                'exit_idx': exit_idx,
                'exit_date': dates[exit_idx],
                'duration_days': exit_idx - entry_idx,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'initial_sl': sl_lvl,
                'outcome': outcome,
                'exact_pct': pct
            })

    return trades


def compute_metrics(trades: list) -> dict:
    if not trades:
        return {
            'total_trades': 0, 'wins': 0, 'losses': 0, 'breakevens': 0,
            'win_rate': 0.0, 'win_rate_no_be': 0.0, 'profit_factor': 0.0,
            'net_return': 0.0, 'max_drawdown': 0.0, 'expectancy': 0.0,
            'avg_duration': 0.0
        }

    w = [t['exact_pct'] for t in trades if t['outcome'] == 'WIN']
    l = [t['exact_pct'] for t in trades if t['outcome'] == 'LOSS']
    be = [t['exact_pct'] for t in trades if t['outcome'] == 'BREAKEVEN']

    gross_profit = sum(w)
    gross_loss = abs(sum(l))
    net_return = gross_profit - gross_loss

    if gross_loss > 0:
        pf = round(gross_profit / gross_loss, 2)
    elif gross_profit > 0:
        pf = 999.0
    else:
        pf = 0.0

    total_eval = len(w) + len(l)
    wr_standard = round((len(w) / len(trades) * 100.0), 2) if len(trades) > 0 else 0.0
    wr_no_be = round((len(w) / total_eval * 100.0), 2) if total_eval > 0 else 0.0

    # Max Drawdown
    chrono = sorted(trades, key=lambda t: t['entry_date'])
    eq = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in chrono:
        eq += t['exact_pct']
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd

    durations = [t['duration_days'] for t in trades]
    avg_dur = round(float(np.mean(durations)), 1) if durations else 0.0
    expectancy = round(net_return / len(trades), 2) if trades else 0.0

    return {
        'total_trades': len(trades),
        'wins': len(w),
        'losses': len(l),
        'breakevens': len(be),
        'win_rate': wr_standard,
        'win_rate_no_be': wr_no_be,
        'profit_factor': pf,
        'net_return': round(net_return, 2),
        'max_drawdown': round(max_dd, 2),
        'expectancy': expectancy,
        'avg_duration': avg_dur
    }


def run_daily_vbt_analysis():
    print("=" * 110)
    print("   TLCS Version 5.0: VECTORBT DAILY (1D SWING) QUANTITATIVE BACKTEST ANALYSIS")
    print("   Canonical Weekly Framework + Daily Swing Strategies across 22,469 Bars (5 Years: 2021-2026)")
    print("=" * 110)

    processed_assets = {}
    total_bars = 0

    for symbol, meta in TARGET_ASSETS.items():
        df_raw = load_daily_data(symbol)
        if df_raw is None or len(df_raw) < 100:
            print(f"[!] Warning: Insufficient data for {symbol}, skipping.")
            continue

        df_weekly = compute_weekly_framework(df_raw)
        df_ind = compute_daily_indicators(df_weekly)
        signals = generate_daily_signals(df_ind)

        processed_assets[symbol] = {
            'df': df_ind,
            'signals': signals,
            'meta': meta
        }
        total_bars += len(df_ind)
        print(f"[*] Processed {symbol:10} ({meta['name']}): {len(df_ind)} bars ({meta['market']})")

    print(f"\n[+] Total Universe: {len(processed_assets)} assets, {total_bars:,} daily candles processed.")

    # 1. Define Strategy Models & Confluences
    strategies = {
        'MISSILE_JUST': {'filter': lambda name: name in ('LONG MISSILE', 'SHORT MISSILE')},
        'MISSILE_ALL': {'filter': lambda name: name in ('LONG MISSILE_ALL', 'SHORT MISSILE_ALL')},
        'SCALP_JUST': {'filter': lambda name: name in ('LONG SCALP', 'SHORT SCALP')},
        'SCALP_ALL': {'filter': lambda name: name in ('LONG SCALP_ALL', 'SHORT SCALP_ALL')},
        'LIGHTNING': {'filter': lambda name: name in ('LONG LIGHTNING', 'SHORT LIGHTNING')},
        'EXTREME_REVERSAL': {'filter': lambda name: name in ('LONG EXTREME REVERSAL', 'SHORT EXTREME REVERSAL')},
        'REGULAR_DIV': {'filter': lambda name: name in ('LONG REGULAR DIV', 'SHORT REGULAR DIV')},
        'HIDDEN_DIV': {'filter': lambda name: name in ('LONG HIDDEN DIV', 'SHORT HIDDEN DIV')},
    }

    # Simulate trades per strategy
    strategy_trades = {}
    for strat, cfg in strategies.items():
        all_strat_trades = []
        for symbol, data in processed_assets.items():
            df = data['df']
            sigs = {k: v for k, v in data['signals'].items() if cfg['filter'](k)}
            trades = simulate_daily_trades(df, sigs)
            for t in trades:
                t['symbol'] = symbol
                t['market'] = data['meta']['market']
            all_strat_trades.extend(trades)
        strategy_trades[strat] = all_strat_trades

    # Confluence Setups: Core Trend Signal + Divergence within 5 bars
    confluence_models = ['MISSILE_DIV', 'SCALP_DIV', 'LIGHTNING_TRIPLE']
    for c_mod in confluence_models:
        c_trades = []
        for symbol, data in processed_assets.items():
            df = data['df']
            sigs = data['signals']

            bull_div = sigs['LONG REGULAR DIV'] | sigs['LONG HIDDEN DIV']
            bear_div = sigs['SHORT REGULAR DIV'] | sigs['SHORT HIDDEN DIV']
            bull_div_recent = bull_div.rolling(5).max().fillna(0).astype(bool)
            bear_div_recent = bear_div.rolling(5).max().fillna(0).astype(bool)

            if c_mod == 'MISSILE_DIV':
                long_sig = sigs['LONG MISSILE'] & bull_div_recent
                short_sig = sigs['SHORT MISSILE'] & bear_div_recent
            elif c_mod == 'SCALP_DIV':
                long_sig = sigs['LONG SCALP'] & bull_div_recent
                short_sig = sigs['SHORT SCALP'] & bear_div_recent
            elif c_mod == 'LIGHTNING_TRIPLE':
                long_sig = sigs['LONG LIGHTNING'] & bull_div_recent
                short_sig = sigs['SHORT LIGHTNING'] & bear_div_recent

            conf_signals = {
                f'LONG {c_mod}': long_sig,
                f'SHORT {c_mod}': short_sig
            }
            trades = simulate_daily_trades(df, conf_signals)
            for t in trades:
                t['symbol'] = symbol
                t['market'] = data['meta']['market']
            c_trades.extend(trades)
        strategy_trades[c_mod] = c_trades

    # 2. Performance Summary Matrix
    results_summary = {}
    print("\n" + "=" * 110)
    print("   TABLE 1: 5-YEAR DAILY SWING STRATEGY PERFORMANCE MATRIX (2021-2026)")
    print("=" * 110)
    header = f"{'Strategy / Confluence Model':<32} | {'Trades':<8} | {'WinRate (No BE)':<16} | {'Std WR':<8} | {'PF':<6} | {'Net Return':<12} | {'Max DD':<9} | {'Expectancy':<10} | {'Avg Hold':<8}"
    print(header)
    print("-" * 110)

    for strat, trades in strategy_trades.items():
        m = compute_metrics(trades)
        results_summary[strat] = m
        wr_str = f"{m['win_rate_no_be']:.2f}% ({m['wins']}W/{m['losses']}L)"
        std_wr_str = f"{m['win_rate']:.1f}%"
        net_str = f"{'+' if m['net_return'] > 0 else ''}{m['net_return']:.2f}%"
        dd_str = f"{m['max_drawdown']:.2f}%"
        exp_str = f"{'+' if m['expectancy'] > 0 else ''}{m['expectancy']:.2f}%"
        dur_str = f"{m['avg_duration']:.1f}d"
        print(f"{strat:<32} | {m['total_trades']:<8} | {wr_str:<16} | {std_wr_str:<8} | {m['profit_factor']:<6} | {net_str:<12} | {dd_str:<9} | {exp_str:<10} | {dur_str:<8}")

    # 3. Robustness: In-Sample (Past 70%) vs Out-of-Sample (Future 30% Forward-Walk)
    print("\n" + "=" * 110)
    print("   TABLE 2: IN-SAMPLE (PAST 70%) VS OUT-OF-SAMPLE (FUTURE 30% FORWARD-WALK)")
    print("=" * 110)
    print(f"{'Strategy Model':<28} | {'In-Sample (Past 70%)':<35} | {'Out-of-Sample (Future 30%)':<35}")
    print(f"{'':<28} | {'Trades':<7} {'WinRate':<10} {'PF':<6} {'Net Ret':<10} | {'Trades':<7} {'WinRate':<10} {'PF':<6} {'Net Ret':<10}")
    print("-" * 110)

    robustness_results = {}
    for strat, trades in strategy_trades.items():
        if not trades:
            continue
        chrono = sorted(trades, key=lambda t: t['entry_date'])
        split_idx = int(len(chrono) * 0.70)
        past_trades = chrono[:split_idx]
        future_trades = chrono[split_idx:]

        m_past = compute_metrics(past_trades)
        m_future = compute_metrics(future_trades)

        robustness_results[strat] = {
            'past': m_past,
            'future': m_future
        }

        p_str = f"{m_past['total_trades']:<7} {m_past['win_rate_no_be']:>5.1f}%    {m_past['profit_factor']:>5.2f} {('+' if m_past['net_return']>0 else '') + str(round(m_past['net_return'],1))+'%':>9}"
        f_str = f"{m_future['total_trades']:<7} {m_future['win_rate_no_be']:>5.1f}%    {m_future['profit_factor']:>5.2f} {('+' if m_future['net_return']>0 else '') + str(round(m_future['net_return'],1))+'%':>9}"
        print(f"{strat:<28} | {p_str:<35} | {f_str:<35}")

    # 4. Asset Class Breakdown
    print("\n" + "=" * 110)
    print("   TABLE 3: PERFORMANCE BY ASSET CLASS (5 CORE STRATEGIES COMPOSITE)")
    print("=" * 110)
    print(f"{'Asset Class / Market':<28} | {'Trades':<8} | {'WinRate (No BE)':<16} | {'PF':<6} | {'Net Return':<12} | {'Max DD':<9} | {'Expectancy':<10}")
    print("-" * 110)

    markets = ['Indian Equities', 'Commodities', 'Global / FX / Crypto']
    market_results = {}
    for mkt in markets:
        mkt_trades = []
        for strat in ['MISSILE_JUST', 'SCALP_JUST', 'LIGHTNING', 'EXTREME_REVERSAL', 'REGULAR_DIV', 'HIDDEN_DIV']:
            mkt_trades.extend([t for t in strategy_trades[strat] if t.get('market') == mkt])
        m_mkt = compute_metrics(mkt_trades)
        market_results[mkt] = m_mkt
        wr_str = f"{m_mkt['win_rate_no_be']:.2f}% ({m_mkt['wins']}W/{m_mkt['losses']}L)"
        net_str = f"{'+' if m_mkt['net_return'] > 0 else ''}{m_mkt['net_return']:.2f}%"
        dd_str = f"{m_mkt['max_drawdown']:.2f}%"
        exp_str = f"{'+' if m_mkt['expectancy'] > 0 else ''}{m_mkt['expectancy']:.2f}%"
        print(f"{mkt:<28} | {m_mkt['total_trades']:<8} | {wr_str:<16} | {m_mkt['profit_factor']:<6} | {net_str:<12} | {dd_str:<9} | {exp_str:<10}")

    # 5. Directional Breakdown: Long vs Short
    print("\n" + "=" * 110)
    print("   TABLE 4: DIRECTIONAL PERFORMANCE BREAKDOWN (LONG VS SHORT SWING TRADES)")
    print("=" * 110)
    print(f"{'Strategy / Direction':<28} | {'Trades':<8} | {'WinRate (No BE)':<16} | {'PF':<6} | {'Net Return':<12} | {'Max DD':<9} | {'Expectancy':<10}")
    print("-" * 110)

    directional_results = {}
    for strat in ['MISSILE_JUST', 'SCALP_JUST', 'LIGHTNING', 'EXTREME_REVERSAL', 'REGULAR_DIV', 'HIDDEN_DIV']:
        trades = strategy_trades[strat]
        long_trades = [t for t in trades if t['is_long']]
        short_trades = [t for t in trades if not t['is_long']]

        m_long = compute_metrics(long_trades)
        m_short = compute_metrics(short_trades)
        directional_results[strat] = {'long': m_long, 'short': m_short}

        l_wr = f"{m_long['win_rate_no_be']:.1f}% ({m_long['wins']}W/{m_long['losses']}L)"
        l_net = f"{'+' if m_long['net_return']>0 else ''}{m_long['net_return']:.1f}%"
        print(f"{strat + ' [LONG]':<28} | {m_long['total_trades']:<8} | {l_wr:<16} | {m_long['profit_factor']:<6} | {l_net:<12} | {m_long['max_drawdown']:<9.1f}% | {('+' if m_long['expectancy']>0 else '') + str(m_long['expectancy']) + '%'}")

        s_wr = f"{m_short['win_rate_no_be']:.1f}% ({m_short['wins']}W/{m_short['losses']}L)"
        s_net = f"{'+' if m_short['net_return']>0 else ''}{m_short['net_return']:.1f}%"
        print(f"{strat + ' [SHORT]':<28} | {m_short['total_trades']:<8} | {s_wr:<16} | {m_short['profit_factor']:<6} | {s_net:<12} | {m_short['max_drawdown']:<9.1f}% | {('+' if m_short['expectancy']>0 else '') + str(m_short['expectancy']) + '%'}")
        print("-" * 110)

    # 6. Export results to JSON
    output_data = {
        'total_bars': total_bars,
        'strategies': results_summary,
        'robustness': robustness_results,
        'markets': market_results,
        'directional': directional_results
    }
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'daily_tf_vectorbt_results.json')
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"\n[+] Detailed analysis results saved to {output_path}")

    return output_data


if __name__ == '__main__':
    run_daily_vbt_analysis()
