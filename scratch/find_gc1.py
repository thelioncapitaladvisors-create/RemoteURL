import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/signals?symbol=eq.GC1!&select=*&order=created_at.desc&limit=50"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    signals = json.loads(response.read().decode())
    for s in signals:
        if s.get('entry') and abs(s['entry'] - 4051.95) < 5:
            print("FOUND ENTRY MATCH:", json.dumps(s, indent=2))
