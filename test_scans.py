import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv('algo_engine/.env')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
res = supabase.table('scanners').select('*').limit(10).execute()
print(f"Got {len(res.data)} scanners")
if res.data:
    for r in res.data:
        if r.get('name') == 'TLCS DAY TYPE SCANNER' or r.get('name') == 'PIVOTBOSS COMBINED SCANNER':
            print("Found scanner data!")
            print(json.dumps(r.get('data', {}), indent=2))
