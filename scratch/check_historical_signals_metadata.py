import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Fetch last 50 signals
url = f"{SUPABASE_URL}/rest/v1/signals?select=symbol,exchange,created_at,metadata&order=created_at.desc&limit=100"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        signals = json.loads(response.read().decode())
        has_bias_count = 0
        for s in signals:
            meta = s.get('metadata', {})
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            bias = meta.get('opening_bias') or meta.get('opening_print') or meta.get('bias')
            dt = meta.get('day_type') or meta.get('cpr_type')
            if bias or dt:
                has_bias_count += 1
                print(f"Symbol: {s['symbol']} | CreatedAt: {s['created_at']} | Bias: {bias} | DayType: {dt}")
        print(f"Total signals checked: {len(signals)} | With Bias/DayType: {has_bias_count}")
except Exception as e:
    print(f"Error: {e}")
