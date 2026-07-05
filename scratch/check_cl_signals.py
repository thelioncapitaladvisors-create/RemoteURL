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

today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
url = f"{SUPABASE_URL}/rest/v1/signals?symbol=eq.CL1!&created_at=gte.{today_str}T00:00:00Z"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        signals = json.loads(response.read().decode())
        print(f"Total CL1! signals from today: {len(signals)}")
        for s in signals:
            print(s)
except Exception as e:
    print(f"Error: {e}")
