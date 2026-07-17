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

resp = supabase.table('signals').select('id, symbol, status, outcome, created_at, entry').order('created_at', desc=True).limit(500).execute()
signals = resp.data

open_trades = [s for s in signals if s['status'] == 'Active' or s['status'] == 'OPEN']
closed_trades = [s for s in signals if s['status'] != 'Active' and s['status'] != 'OPEN']

print(f"Total active trades in last 500: {len(open_trades)}")
print(f"Total closed trades in last 500: {len(closed_trades)}")

# Check for ghost trades (Hit SL/TP without outcome or exit price)
ghost_trades = [s for s in signals if (s['status'] != 'Active' and s['status'] != 'OPEN') and not s['outcome']]
print(f"Total ghost trades (Hit SL/TP but no outcome): {len(ghost_trades)}")

import json
with open('debug_db.json', 'w') as f:
    json.dump(signals, f, indent=2)
