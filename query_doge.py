import os
from supabase import create_client

url = 'https://dwepduvhzuhzeehbeaaz.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg'
supabase = create_client(url, key)

res = supabase.table('signals').select('*').eq('symbol', 'DOGEUSDT').order('created_at', desc=True).limit(5).execute()

for d in res.data:
    print(f"created: {d.get('created_at')}, outcome: {d.get('outcome')}, status: {d.get('status')}")
    print(f"opening_bias: '{d.get('opening_bias')}', day_type: '{d.get('day_type')}'")
    print(f"metadata: {d.get('metadata')}")
    print("-------------------")
