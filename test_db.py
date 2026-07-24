import os
from supabase import create_client
url = 'https://dwepduvhzuhzeehbeaaz.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg'
supabase = create_client(url, key)
res = supabase.table('signals').select('*').gte('created_at', '2026-07-23T00:00:00.000Z').order('created_at', desc=True).execute()
for r in res.data:
    meta = r.get('metadata') or {}
    epct = meta.get('exact_pct')
    if epct is not None and epct > 0 and (r.get('outcome') in ['LOSS', 'BREAKEVEN'] or r.get('status') in ['Hit Initial SL', 'Hit B/E']):
        print("--------------------------------------------------")
        print(f"Symbol: {r.get('symbol')}, Type: {r.get('type')}, Status: {r.get('status')}, Outcome: {r.get('outcome')}")
        print(f"Entry: {r.get('entry')}, ExitPrice: {r.get('exit_price')}, Stop: {r.get('stop')}, Target: {r.get('target')}")
        print(f"Metadata: {meta}")



