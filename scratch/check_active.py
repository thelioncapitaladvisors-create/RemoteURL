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

resp = supabase.table('signals').select('*').in_('status', ['Active', 'OPEN']).execute()
signals = resp.data

print(f"Total open trades currently in DB: {len(signals)}")
from collections import Counter
c = Counter([s['symbol'] for s in signals])
for sym, count in c.most_common(10):
    print(f"{sym}: {count}")

# Check if there are any ghost trades that might match these open trades
resp2 = supabase.table('signals').select('*').not_.in_('status', ['Active', 'OPEN']).is_('outcome', 'null').execute()
ghosts = resp2.data

print(f"\nTotal ghost trades (Hit SL/TP but no outcome): {len(ghosts)}")
for g in ghosts:
    print(f"Ghost: {g['symbol']} {g['status']} at {g['created_at']} (Entry: {g['entry']})")
