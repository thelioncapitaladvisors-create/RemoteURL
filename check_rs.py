import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/signals?select=symbol,outcome,r_multiple,status&exit_price=not.is.null"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        wins = []
        losses = []
        for s in data:
            r = float(s['r_multiple']) if s.get('r_multiple') is not None else 0
            if s['outcome'] == 'WIN': wins.append(r)
            if s['outcome'] == 'LOSS': losses.append(r)
        
        avg_w = sum(wins)/len(wins) if wins else 0
        avg_l = sum(losses)/len(losses) if losses else 0
        print(f"Wins ({len(wins)}): {wins}")
        print(f"Losses ({len(losses)}): {losses}")
        print(f"Avg Win: {avg_w}, Avg Loss: {avg_l}")
except Exception as e:
    print(f"Error: {e}")
