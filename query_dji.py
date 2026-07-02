from supabase import create_client
import os
import json

def get_env():
    env = {}
    with open('TLCS_Website_Deploy/.env.local', 'r') as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                env[k] = v
    return env

env = get_env()
url = env.get('SUPABASE_URL') or env.get('NEXT_PUBLIC_SUPABASE_URL')
key = env.get('SUPABASE_SERVICE_KEY') or env.get('SUPABASE_ANON_KEY') or env.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')

supabase = create_client(url, key)
res = supabase.table('signals').select('*').eq('symbol', 'DJI').order('created_at', desc=True).limit(2).execute()
print(json.dumps(res.data, indent=2))
