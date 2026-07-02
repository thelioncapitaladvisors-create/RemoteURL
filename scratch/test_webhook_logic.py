import datetime
import time

def check_recency(sym, exch, provided_ts_ms):
    now_ms = int(time.time() * 1000)
    print(f"provided_ts_ms: {provided_ts_ms}, now_ms: {now_ms}")
    
    # Simulating JS logic
    def get_tz(s, e):
        s = (s or '').upper()
        e = (e or '').upper()
        if 'NIFTY' in s or s.endswith('.NS') or s.endswith('.BO') or s in ['ITC', 'SBIN', 'RELIANCE']:
            return 'Asia/Kolkata'
        if s in ['GOLD', 'CRUDEOIL', 'CRUDEOIL1!', 'NATURALGAS1!', 'NATURALGAS', 'SILVER', 'SILVERM', 'GOLDM']:
            return 'Asia/Kolkata'
        if e in ['NSE', 'MCX', 'BSE']:
            return 'Asia/Kolkata'
        return 'America/New_York'
        
    import pytz
    tz = pytz.timezone(get_tz(sym, exch))
    
    dt_sig = datetime.datetime.fromtimestamp(provided_ts_ms/1000, tz)
    dt_now = datetime.datetime.fromtimestamp(now_ms/1000, tz)
    
    print(f"Sig date: {dt_sig.strftime('%Y-%m-%d')}, Now date: {dt_now.strftime('%Y-%m-%d')}")
    if dt_sig.strftime('%Y-%m-%d') != dt_now.strftime('%Y-%m-%d'):
        print("REJECTED")
    else:
        print("ACCEPTED")

check_recency("BTCUSDT", "BINANCE", int(time.time()*1000))

