import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

url = f"{SUPABASE_URL}/rest/v1/pivots?select=symbol,updated_at&order=updated_at.desc&limit=5"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for p in data:
            print(f"{p['symbol']} -> {p['updated_at']}")
except Exception as e:
    print(f"Error: {e}")
