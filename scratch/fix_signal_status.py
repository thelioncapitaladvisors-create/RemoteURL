import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Fix trade 5765ffd0-542e-4b38-be99-e9442f348c9f
url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.5765ffd0-542e-4b38-be99-e9442f348c9f"
data = json.dumps({"status": "Hit Initial SL"}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='PATCH')
with urllib.request.urlopen(req) as response:
    print("Updated trade 5765ffd0-542e-4b38-be99-e9442f348c9f status to Hit Initial SL. Status code:", response.status)

# Find any other losing trades with TP in status
url_find = f"{SUPABASE_URL}/rest/v1/signals?outcome=eq.LOSS&select=id,symbol,status,outcome,metadata&limit=500"
req_f = urllib.request.Request(url_find, headers={
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
})
with urllib.request.urlopen(req_f) as response:
    signals = json.loads(response.read().decode())
    corrupt = []
    for s in signals:
        st = (s.get('status') or '').upper()
        if 'TP1' in st or 'TP2' in st or 'TP3' in st or 'TP4' in st or 'TARGET' in st:
            corrupt.append(s['id'])
    print(f"Found {len(corrupt)} losing trades with corrupt TP status strings.")
    for sid in corrupt:
        url_patch = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{sid}"
        d = json.dumps({"status": "Hit Initial SL"}).encode('utf-8')
        r = urllib.request.Request(url_patch, data=d, headers=headers, method='PATCH')
        with urllib.request.urlopen(r) as res:
            print(f"Patched signal {sid} status -> Hit Initial SL")
