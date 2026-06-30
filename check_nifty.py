import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/signals?select=symbol,outcome,r_multiple,status&symbol=like.NIFTY*&exit_price=not.is.null"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        wins = 0
        losses = 0
        be = 0
        r_sum = 0
        for s in data:
            print(f"{s['symbol']} | {s['outcome']} | R: {s['r_multiple']} | {s['status']}")
            if s['outcome'] == 'WIN': wins += 1
            if s['outcome'] == 'LOSS': losses += 1
            if s['outcome'] == 'BREAKEVEN': be += 1
            if s['r_multiple']: r_sum += float(s['r_multiple'])
        print(f"Wins: {wins}, Losses: {losses}, BE: {be}, Total R: {r_sum}")
except Exception as e:
    print(f"Error: {e}")
