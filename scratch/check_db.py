import os
from supabase import create_client

supabase_url = os.environ.get("SUPABASE_URL", "https://qeqhvyvjohphtqpsixif.supabase.co")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_key:
    # Try to read from .env.local
    if os.path.exists(".env.local"):
        with open(".env.local") as f:
            for line in f:
                if line.startswith("NEXT_PUBLIC_SUPABASE_URL="):
                    supabase_url = line.strip().split("=")[1].strip('"\'')
                elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                    supabase_key = line.strip().split("=")[1].strip('"\'')

supabase = create_client(supabase_url, supabase_key)

resp = supabase.table('signals').select('symbol, status, outcome, exit_price, metadata, created_at, exit_at, entry, stop').order('created_at', desc=True).limit(5).execute()
for r in resp.data:
    meta = r.get('metadata')
    print(f"{r['symbol']} | {r['status']} | {r['outcome']} | exit_price: {r['exit_price']} | metadata: {meta}")
