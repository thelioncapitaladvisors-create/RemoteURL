import requests
import json
import os
import datetime

with open('.env.local', 'r') as f:
    env = dict(line.strip().split('=', 1) for line in f if '=' in line)

SUPABASE_URL = env['NEXT_PUBLIC_SUPABASE_URL']
SUPABASE_KEY = env['NEXT_PUBLIC_SUPABASE_ANON_KEY']

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

payload = {
    "symbol": "BTCUSDT",
    "exchange": "BINANCE",
    "type": "LONG",
    "entry": 60000,
    "status": "Active",
    "signal_ts": datetime.datetime.utcnow().isoformat(),
    "metadata": {"opening_bias": "Bullish", "day_type": "Trend"}
}

res = requests.post(f"{SUPABASE_URL}/rest/v1/signals", headers=headers, json=payload)
print(res.status_code)
print(res.text)
