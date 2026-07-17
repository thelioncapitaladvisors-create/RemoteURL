import os
from supabase import create_client

supabase_url = os.environ.get("SUPABASE_URL", "https://qeqhvyvjohphtqpsixif.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_key:
    if os.path.exists(".env.local"):
        with open(".env.local") as f:
            for line in f:
                if line.startswith("NEXT_PUBLIC_SUPABASE_URL="):
                    supabase_url = line.strip().split("=")[1].strip('"\'')
                elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                    supabase_key = line.strip().split("=")[1].strip('"\'')

supabase = create_client(supabase_url, supabase_key)

resp = supabase.table('signals').select('id, symbol, status, outcome, exit_price, trigger, created_at, entry').in_('symbol', ['EURJPY', 'GC1!']).order('created_at', desc=True).limit(10).execute()
for r in resp.data:
    print(r)
