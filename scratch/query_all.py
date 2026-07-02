import requests
import os
import json

with open('.env.local', 'r') as f:
    env = dict(line.strip().split('=', 1) for line in f if '=' in line)

SUPABASE_URL = env['NEXT_PUBLIC_SUPABASE_URL']
SUPABASE_KEY = env['NEXT_PUBLIC_SUPABASE_ANON_KEY']

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

res = requests.get(f"{SUPABASE_URL}/rest/v1/signals?select=id,symbol,created_at,type,status,message,metadata,trigger&order=created_at.desc&limit=10", headers=headers)
print(json.dumps(res.json(), indent=2))
