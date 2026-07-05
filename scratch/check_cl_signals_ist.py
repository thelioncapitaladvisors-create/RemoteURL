import urllib.request
import json
from datetime import datetime, timezone

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Check for signals from Saturday 0:00 AM IST onwards (Friday 18:30:00 UTC)
url = f"{SUPABASE_URL}/rest/v1/signals?symbol=eq.CL1!&created_at=gte.2026-07-03T18:30:00Z"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        signals = json.loads(response.read().decode())
        print(f"Total CL1! signals from Saturday IST: {len(signals)}")
        for s in signals:
            print(f"ID: {s['id']} | CreatedAt: {s['created_at']} | Outcome: {s['outcome']} | Status: {s['status']}")
except Exception as e:
    print(f"Error: {e}")
