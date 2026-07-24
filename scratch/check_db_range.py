import urllib.request
import json

SUPABASE_URL = "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Oldest signal
url = f"{SUPABASE_URL}/rest/v1/signals?select=created_at&order=created_at.asc&limit=5"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as response:
    oldest = json.loads(response.read().decode())
    print("Oldest signals:", oldest)

# Count total
headers["Prefer"] = "count=exact"
url_count = f"{SUPABASE_URL}/rest/v1/signals?select=id&limit=1"
req_c = urllib.request.Request(url_count, headers=headers)
with urllib.request.urlopen(req_c) as response:
    cr = response.headers.get("Content-Range")
    print("Content-Range:", cr)
