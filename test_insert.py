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

# Payload simulating what TradingView might send for an ENTRY
payload = {
    "symbol": "HSI",
    "exchange": "HKEX",
    "type": "SHORT SCALP",
    "entry": 18000,
    "stop": 18050,
    "target": 17950,
    "action": "ENTRY",
    "trigger": "Entry",
    "secret": "675d6a2593..."
}

url = "https://thelioncapitaladvisors-create.netlify.app/.netlify/functions/process-webhook-background"

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.getcode()}")
        print(response.read().decode())
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())
