import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Get all signals from Saturday IST
url = f"{SUPABASE_URL}/rest/v1/signals?created_at=gte.2026-07-03T18:30:00Z"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        signals = json.loads(response.read().decode())
        print(f"Total signals from Saturday IST: {len(signals)}")
        for s in signals:
            print(f"Symbol: {s['symbol']} | Exchange: {s['exchange']} | CreatedAt: {s['created_at']}")
except Exception as e:
    print(f"Error: {e}")
