import os
from supabase import create_client
import datetime

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

two_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=2)).isoformat()
resp = supabase.table('signals').select('id, symbol, status, outcome, created_at, entry, stop, type').gte('created_at', two_days_ago).order('created_at', desc=True).execute()
signals = resp.data

print(f"Total signals in last 48h: {len(signals)}")

from collections import Counter
c = Counter([s['status'] for s in signals])
for status, count in c.items():
    print(f"Status '{status}': {count}")

print("\nWin Trades Check:")
wins = [s for s in signals if s['outcome'] == 'WIN' or 'TP' in (s['status'] or '').upper() or 'TARGET' in (s['status'] or '').upper()]
print(f"Total WIN trades: {len(wins)}")
for w in wins:
    print(f"  {w['symbol']} | {w['created_at']} | {w['status']} | {w['outcome']}")

print("\nBreakEven Trades Check:")
bes = [s for s in signals if s['outcome'] == 'BREAKEVEN' or 'B/E' in (s['status'] or '').upper()]
print(f"Total BREAKEVEN trades: {len(bes)}")

print("\nLoss Trades Check:")
losses = [s for s in signals if s['outcome'] == 'LOSS' or 'SL' in (s['status'] or '').upper()]
print(f"Total LOSS trades: {len(losses)}")
