import requests
import json
import os

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

res = requests.get(f"{SUPABASE_URL}/rest/v1/pivots?select=symbol,updated_at,opening_bias,day_type&order=updated_at.desc&limit=5", headers=headers)
print(json.dumps(res.json(), indent=2))
