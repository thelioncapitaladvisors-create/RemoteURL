import re

def isNSESymbol(symbol, exchange):
    sym = (symbol or '').upper()
    exch = (exchange or '').upper()
    if exch in ['NSE', 'BSE', 'NFO', 'MCX', 'INDEX']: return True
    if re.match(r'^(NIFTY|BANKNIFTY|FINNIFTY|MIDCPNIFTY|SENSEX)', sym): return True
    if not exch and re.match(r'^[A-Z&]{2,20}$', sym) and not sym.endswith('USDT') and len(sym) <= 15: return True
    return False

def is24x7Symbol(symbol, exchange):
    sym = (symbol or '').upper()
    exch = (exchange or '').upper()
    if sym.endswith('USDT') or sym.endswith('BTC') or sym.endswith('ETH'): return True
    if exch in ['BINANCE', 'COINBASE', 'CRYPTO']: return True
    if exch in ['FX_IDC', 'FX', 'OANDA', 'FXCM']: return True
    if len(sym) == 6 and re.match(r'^[A-Z]{6}$', sym): return True
    worldIdx = ['UKX','HSI','NI225','DAX','CAC40','SX5E','DJI','SPX','NDX','RUT','XJO']
    if sym in worldIdx: return True
    if re.match(r'^[A-Z]{2}1!$', sym) and not sym.startswith('NIFTY') and not sym.startswith('BANK') and not sym.startswith('FINN'): return True
    return False

print(f"HSI HKEX: NSE={isNSESymbol('HSI', 'HKEX')} 24x7={is24x7Symbol('HSI', 'HKEX')}")
print(f"EURJPY '': NSE={isNSESymbol('EURJPY', '')} 24x7={is24x7Symbol('EURJPY', '')}")
